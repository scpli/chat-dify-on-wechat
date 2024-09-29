from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir

class GeWeChatMessage(ChatMessage):
    def __init__(self, msg, is_group=False):
        super().__init__(msg)
        self.msg_id = msg.get('MsgId')
        self.create_time = msg.get('CreateTime')
        self.is_group = is_group

        msg_type = msg.get('MsgType')
        if msg_type == 'text':
            self.ctype = ContextType.TEXT
            self.content = msg.get('Content')
        elif msg_type == 'voice':
            self.ctype = ContextType.VOICE
            self.content = TmpDir().path() + msg.get('MediaId') + ".amr"  # content直接存临时目录路径
            # TODO: Implement voice file downloading for Gewechat
        elif msg_type == 'image':
            self.ctype = ContextType.IMAGE
            self.content = TmpDir().path() + msg.get('MediaId') + ".png"  # content直接存临时目录路径
            # TODO: Implement image file downloading for Gewechat
        else:
            raise NotImplementedError("Unsupported message type: Type:{} ".format(msg_type))

        self.from_user_id = msg.get('FromUserName')
        self.to_user_id = msg.get('ToUserName')
        self.other_user_id = self.from_user_id

    def prepare(self):
        # This method can be used to perform any necessary preparations before processing the message
        pass
