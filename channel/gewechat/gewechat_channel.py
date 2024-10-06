import io
import os
import time
import json

import requests
import web

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.gewechat.gewechat_message import GeWeChatMessage
from common.log import logger
from common.singleton import singleton
from common.utils import compress_imgfile, fsize, split_string_by_utf8_length, convert_webp_to_png
from config import conf
from voice.audio_convert import any_to_amr, split_audio
from lib.gewechat import GewechatClient

MAX_UTF8_LEN = 2048

@singleton
class GeWeChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.base_url = conf().get("gewechat_base_url")
        self.download_url = conf().get("gewechat_download_url")
        self.token = conf().get("gewechat_token")
        self.app_id = conf().get("gewechat_app_id")
        logger.info(
            "[gewechat] init: base_url: {}, download_url: {}, token: {}, app_id: {}".format(
                self.base_url, self.download_url, self.token, self.app_id
            )
        )
        self.client = GewechatClient(self.base_url, self.download_url, self.token)

    def startup(self):
        urls = ("/v2/api/callback/collect", "channel.gewechat.gewechat_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = conf().get("gewechat_callback_server_port", 9919)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = reply.content
            texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
            if len(texts) > 1:
                logger.info("[gewechat] text too long, split into {} parts".format(len(texts)))
            for i, text in enumerate(texts):
                self.client.post_text(self.app_id, receiver, text)
                if i != len(texts) - 1:
                    time.sleep(0.5)
            logger.info("[gewechat] Do send text to {}: {}".format(receiver, reply_text))
        elif reply.type == ReplyType.VOICE:
            try:
                file_path = reply.content
                amr_file = os.path.splitext(file_path)[0] + ".amr"
                any_to_amr(file_path, amr_file)
                duration, files = split_audio(amr_file, 60 * 1000)
                if len(files) > 1:
                    logger.info("[gewechat] voice too long {}s > 60s , split into {} parts".format(duration / 1000.0, len(files)))
                for path in files:
                    with open(path, "rb") as f:
                        self.client.post_voice(self.app_id, receiver, f.read(), int(duration))
                    time.sleep(1)
            except Exception as e:
                logger.error("[gewechat] send voice failed: {}".format(e))
            finally:
                try:
                    os.remove(file_path)
                    if amr_file != file_path:
                        os.remove(amr_file)
                except:
                    pass
            logger.info("[gewechat] sendVoice={}, receiver={}".format(reply.content, receiver))
        elif reply.type == ReplyType.IMAGE_URL:
            img_url = reply.content
            pic_res = requests.get(img_url, stream=True)
            image_storage = io.BytesIO()
            for block in pic_res.iter_content(1024):
                image_storage.write(block)
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[gewechat] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[gewechat] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            if ".webp" in img_url:
                try:
                    image_storage = convert_webp_to_png(image_storage)
                except Exception as e:
                    logger.error(f"Failed to convert image: {e}")
                    return
            self.client.post_image(self.app_id, receiver, image_storage.getvalue())
            logger.info("[gewechat] sendImage url={}, receiver={}".format(img_url, receiver))
        elif reply.type == ReplyType.IMAGE:
            image_storage = reply.content
            sz = fsize(image_storage)
            if sz >= 10 * 1024 * 1024:
                logger.info("[gewechat] image too large, ready to compress, sz={}".format(sz))
                image_storage = compress_imgfile(image_storage, 10 * 1024 * 1024 - 1)
                logger.info("[gewechat] image compressed, sz={}".format(fsize(image_storage)))
            image_storage.seek(0)
            self.client.post_image(self.app_id, receiver, image_storage.read())
            logger.info("[gewechat] sendImage, receiver={}".format(receiver))

class Query:
    def GET(self):
        return "gewechat callback server running"

    def POST(self):
        channel = GeWeChatChannel()
        data = json.loads(web.data())
        logger.debug("[gewechat] receive data: {}".format(data))
        
        gewechat_msg = GeWeChatMessage(data, channel.client)
        
        context = channel._compose_context(
            gewechat_msg.ctype,
            gewechat_msg.content,
            isgroup=gewechat_msg.is_group,
            msg=gewechat_msg,
        )
        if context:
            channel.produce(context)
        return "success"
