from bridge.context import ContextType
from channel.chat_message import ChatMessage
from common.log import logger
from common.tmp_dir import TmpDir
from lib.gewechat import GewechatClient

class GeWeChatMessage(ChatMessage):
    def __init__(self, msg, client: GewechatClient):
        super().__init__(msg)
        self.msg = msg
        self.msg_id = msg['Data']['NewMsgId']
        self.create_time = msg['Data']['CreateTime']
        self.is_group = True if "@chatroom" in msg['Data']['FromUserName']['string'] else False

        self.client = client

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

        # 补充群聊信息
        if self.is_group:
            # TODO: 获取群聊信息与实际发送人信息
            self.other_user_id = self.from_user_id  # 群ID
            self.other_user_nickname = ''  # 群名称
            self.actual_user_id = self.msg.get('Data', {}).get('Content', {}).get('string', '').split(':', 1)[0]  # 实际发送者ID
            self.actual_user_nickname = ''  # 实际发送者昵称
            
            # 检查是否被@
            self.is_at = '在群聊中@了你' in self.msg.get('Data', {}).get('PushContent', '')

            # 如果是群消息，更新content为实际内容（去掉发送者ID）
            if ':' in self.content:
                self.content = self.content.split(':', 1)[1].strip()
        else:
            self.other_user_nickname = ''  # 单聊时可能需要额外获取昵称

        self.my_msg = self.msg['Wxid'] == self.from_user_id
        self.self_display_name = ''  # 可能需要额外获取自身在群中的展示名称

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
