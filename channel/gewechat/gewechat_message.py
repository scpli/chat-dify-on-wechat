from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger


class GeWeChatMessage(ChatMessage):
    def __init__(self, gewechat_msg, is_group=False):
        super().__init__(gewechat_msg)
        # Initialize the message attributes
        pass
