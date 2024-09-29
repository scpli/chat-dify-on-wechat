import io
import os
import time

import requests
import web

from bridge.context import Context
from bridge.reply import Reply, ReplyType
from channel.chat_channel import ChatChannel
from channel.gewechat.gewechat_message import GeWeChatMessage
from common.log import logger
from common.singleton import singleton
from common.utils import compress_imgfile, fsize, split_string_by_utf8_length, convert_webp_to_png
from config import conf, subscribe_msg
from voice.audio_convert import any_to_amr, split_audio

MAX_UTF8_LEN = 2048

@singleton
class GeWeChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.corp_id = ""# conf().get("gewechat_corp_id")
        self.secret = "" # conf().get("gewechat_secret")
        self.agent_id = "" # conf().get("gewechat_agent_id")
        self.token = "" # conf().get("gewechat_token")
        logger.info(
            "[gewechat] init: corp_id: {}, secret: {}, agent_id: {}, token: {}".format(self.corp_id, self.secret, self.agent_id, self.token)
        )

    def startup(self):
        # start message listener
        urls = ("/gewechat/?", "channel.gewechat.gewechat_channel.Query")
        app = web.application(urls, globals(), autoreload=False)
        port = 9919 # conf().get("gewechat_port", 9919)
        web.httpserver.runsimple(app.wsgifunc(), ("0.0.0.0", port))

    def send(self, reply: Reply, context: Context):
        receiver = context["receiver"]
        if reply.type in [ReplyType.TEXT, ReplyType.ERROR, ReplyType.INFO]:
            reply_text = reply.content
            texts = split_string_by_utf8_length(reply_text, MAX_UTF8_LEN)
            if len(texts) > 1:
                logger.info("[gewechat] text too long, split into {} parts".format(len(texts)))
            for i, text in enumerate(texts):
                self._send_text(receiver, text)
                if i != len(texts) - 1:
                    time.sleep(0.5)  # 休眠0.5秒，防止发送过快乱序
            logger.info("[gewechat] Do send text to {}: {}".format(receiver, reply_text))
        elif reply.type == ReplyType.VOICE:
            # TODO: Implement voice sending for Gewechat
            pass
        elif reply.type == ReplyType.IMAGE_URL:
            # TODO: Implement image URL sending for Gewechat
            pass
        elif reply.type == ReplyType.IMAGE:
            # TODO: Implement image sending for Gewechat
            pass

    def _send_text(self, receiver, text):
        # TODO: Implement actual text sending for Gewechat
        logger.info(f"[gewechat] Sending text to {receiver}: {text}")

class Query:
    def GET(self):
        # TODO: Implement GET request handling for Gewechat
        return "success"

    def POST(self):
        channel = GeWeChatChannel()
        data = web.data()
        logger.debug("[gewechat] receive data: {}".format(data))
        
        # TODO: Parse the received data and create a GeWeChatMessage
        gewechat_msg = GeWeChatMessage(data)
        
        context = channel._compose_context(
            gewechat_msg.ctype,
            gewechat_msg.content,
            isgroup=False,
            msg=gewechat_msg,
        )
        if context:
            channel.produce(context)
        return "success"
