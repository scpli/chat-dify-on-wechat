# encoding:utf-8

"""
gewechat channel
"""
import io
import json
import os
import threading
import time
import requests

from bridge.context import *
from bridge.reply import *
from channel.chat_channel import ChatChannel
from channel import chat_channel
from channel.gewechat.gewechat_message import *
from common.expired_dict import ExpiredDict
from common.log import logger
from common.singleton import singleton
from config import conf, get_appdata_dir
from lib import gewechat

def _check(func):
    def wrapper(self, cmsg: ChatMessage):
        msgId = cmsg.msg_id
        if msgId in self.receivedMsgs:
            logger.info("GeWeChat message {} already received, ignore".format(msgId))
            return
        self.receivedMsgs[msgId] = True
        create_time = cmsg.create_time
        if conf().get("hot_reload") == True and int(create_time) < int(time.time()) - 60:
            logger.debug("[GEWX]history message {} skipped".format(msgId))
            return
        if cmsg.my_msg and not cmsg.is_group:
            logger.debug("[GEWX]my message {} skipped".format(msgId))
            return
        return func(self, cmsg)
    return wrapper

@singleton
class GeWeChatChannel(ChatChannel):
    NOT_SUPPORT_REPLYTYPE = []

    def __init__(self):
        super().__init__()
        self.receivedMsgs = ExpiredDict(conf().get("expires_in_seconds", 3600))

    def startup(self):
        try:
            gewechat.instance.receivingRetryCount = 600  # 修改断线超时时间
            # login by scan QRCode
            hotReload = conf().get("hot_reload", False)
            status_path = os.path.join(get_appdata_dir(), "gewechat.pkl")
            gewechat.auto_login(
                enableCmdQR=2,
                hotReload=hotReload,
                statusStorageDir=status_path,
                qrCallback=qrCallback,
                exitCallback=self.exitCallback,
                loginCallback=self.loginCallback
            )
            self.user_id = gewechat.instance.storageClass.userName
            self.name = gewechat.instance.storageClass.nickName
            logger.info("GeWeChat login success, user_id: {}, nickname: {}".format(self.user_id, self.name))
            # start message listener
            gewechat.run()
        except Exception as e:
            logger.exception(e)

    @_check
    def handle_single(self, cmsg: ChatMessage):
        if cmsg.other_user_id in ["geweixin"]:
            return
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("speech_recognition") != True:
                return
            logger.debug("[GEWX]receive voice msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[GEWX]receive image msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.PATPAT:
            logger.debug("[GEWX]receive patpat msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[GEWX]receive text msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
        else:
            logger.debug("[GEWX]receive msg: {}, cmsg={}".format(cmsg.content, cmsg))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=False, msg=cmsg)
        if context:
            self.produce(context)

    @_check
    def handle_group(self, cmsg: ChatMessage):
        if cmsg.ctype == ContextType.VOICE:
            if conf().get("group_speech_recognition") != True:
                return
            logger.debug("[GEWX]receive voice for group msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.IMAGE:
            logger.debug("[GEWX]receive image for group msg: {}".format(cmsg.content))
        elif cmsg.ctype in [ContextType.JOIN_GROUP, ContextType.PATPAT, ContextType.ACCEPT_FRIEND, ContextType.EXIT_GROUP]:
            logger.debug("[GEWX]receive note msg: {}".format(cmsg.content))
        elif cmsg.ctype == ContextType.TEXT:
            logger.debug("[GEWX]receive group msg: {}, cmsg={}".format(json.dumps(cmsg._rawmsg, ensure_ascii=False), cmsg))
        else:
            logger.debug("[GEWX]receive group msg: {}".format(cmsg.content))
        context = self._compose_context(cmsg.ctype, cmsg.content, isgroup=True, msg=cmsg)
        if context:
            self.produce(context)

    def send(self, reply: Reply, context: Context):
        receiver = context.get("receiver")
        if reply.type == ReplyType.TEXT:
            gewechat.send(reply.content, toUserName=receiver)
            logger.info("[GEWX] sendMsg={}, receiver={}".format(reply, receiver))
        elif reply.type == ReplyType.IMAGE:
            image_storage = reply.content
            image_storage.seek(0)
            gewechat.send_image(image_storage, toUserName=receiver)
            logger.info("[GEWX] sendImage, receiver={}".format(receiver))
        # Add other reply types as needed
def qrCallback(uuid, status, qrcode):
    # Implement qrCallback function
    pass

def _send_login_success():
    pass

def _send_logout():
    pass

def _send_qr_code(qrcode_list):
    pass