# encoding:utf-8

"""
gewechat channel
"""

from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel import chat_channel
from channel.gewechat.gewechat_message import *
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from config import conf
# Import your gewechat library here
# from lib import gewechat


@singleton
class GeWeChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.receivedMsgs = ExpiredDict(conf().get("expires_in_seconds", 3600))

    def startup(self):
        # Initialize and start the gewechat client
        # gewechat.auto_login()
        # self.user_id = gewechat.instance.storageClass.userName
        # self.name = gewechat.instance.storageClass.nickName
        # logger.info("GeWeChat login success, user_id: {}, nickname: {}".format(self.user_id, self.name))
        # gewechat.run()
        pass

    def handle_single(self, cmsg: ChatMessage):
        # Implement handling of single chat messages
        pass

    def handle_group(self, cmsg: ChatMessage):
        # Implement handling of group chat messages
        pass

    def send(self, reply: Reply, context: Context):
        # Implement sending messages
        pass