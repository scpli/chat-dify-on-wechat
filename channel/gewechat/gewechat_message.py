from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir
from reference_context.gewechat import GewechatClient

class GeWeChatMessage(ChatMessage):
    def __init__(self, msg, client: GewechatClient):
        super().__init__(msg)
        self.msg = msg
        self.client = client
        self.msg_id = msg['Data']['NewMsgId']
        self.create_time = msg['Data']['CreateTime']
        self.is_group = msg['Data']['FromUserName']['string'] != msg['Wxid']

        msg_type = msg['Data']['MsgType']
        if msg_type == 1:  # Text message
            self.ctype = ContextType.TEXT
            self.content = msg['Data']['Content']['string']
        elif msg_type == 34:  # Voice message
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + str(self.msg_id) + ".amr"
            self._prepare_fn = self.download_voice
        elif msg_type == 3:  # Image message
            self.ctype = ContextType.IMAGE
            self.content = TmpDir().path() + str(self.msg_id) + ".png"
            self._prepare_fn = self.download_image
        else:
            raise NotImplementedError("Unsupported message type: Type:{}".format(msg_type))

        self.from_user_id = msg['Data']['FromUserName']['string']
        self.to_user_id = msg['Data']['ToUserName']['string']
        self.other_user_id = self.from_user_id

    def download_voice(self):
        try:
            voice_data = self.client.download_file(self.msg['Wxid'], self.msg_id)
            with open(self.content, "wb") as f:
                f.write(voice_data)
        except Exception as e:
            logger.error(f"[gewechat] Failed to download voice file: {e}")

    def download_image(self):
        try:
            image_data = self.client.download_file(self.msg['Wxid'], self.msg_id)
            with open(self.content, "wb") as f:
                f.write(image_data)
        except Exception as e:
            logger.error(f"[gewechat] Failed to download image file: {e}")

    def prepare(self):
        if self._prepare_fn:
            self._prepare_fn()
