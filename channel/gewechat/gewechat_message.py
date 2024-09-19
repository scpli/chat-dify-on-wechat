from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger


class GeWeChatMessage(ChatMessage):
    def __init__(self, gewechat_msg, is_group=False):
        super().__init__(gewechat_msg)
        self.msg_id = gewechat_msg["MsgId"]
        self.create_time = gewechat_msg["CreateTime"]
        self.is_group = is_group

        if gewechat_msg["Type"] == TEXT:
            self.ctype = ContextType.TEXT
            self.content = gewechat_msg["Text"]
        elif gewechat_msg["Type"] == VOICE:
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + gewechat_msg["FileName"]
            self._prepare_fn = lambda: gewechat_msg.download(self.content)
        elif gewechat_msg["Type"] == PICTURE:
            self.ctype = ContextType.IMAGE
            self.content = TmpDir().path() + gewechat_msg["FileName"]
            self._prepare_fn = lambda: gewechat_msg.download(self.content)
        else:
            raise NotImplementedError("Unsupported message type: {}".format(gewechat_msg["Type"]))

        self.from_user_id = gewechat_msg["FromUserName"]
        self.to_user_id = gewechat_msg["ToUserName"]

        # Additional attribute initializations as needed
