# encoding:utf-8

import time
import requests

from bot.bot import Bot
from bot.rasa.rasa_session import RasaSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

user_session = dict()


# RasaBot对话模型API
class RasaBot(Bot):
    def __init__(self):
        super().__init__()
        # openai.api_key = conf().get("open_ai_api_key")
        # openai.api_base = conf().get("open_ai_api_base", "https://api.deepseek.com/v1")
        # logger.info("[RasaBot] api key={}".format(openai.api_key))
        # # 配置代理
        # proxy = conf().get("proxy")
        # if proxy:
        #     openai.proxy = proxy
            
        self.sessions = SessionManager(RasaSession)
        
        # Rasa API参数
        self.args = {
            "model": conf().get("model", "rasa-chat"),
            "api_base": conf().get("rasa_ai_api_base", "http://localhost:5005"),
            "frequency_penalty": conf().get("frequency_penalty", 0.0),
            "presence_penalty": conf().get("presence_penalty", 0.0),
            "request_timeout": conf().get("request_timeout", 180),
        }
        logger.info("[RasaBot] args={}".format(self.args))

    def _chat(self, query, context, retry_count=0) -> Reply:
        """
        发起对话请求
        :param query: 请求提示词
        :param context: 对话上下文
        :param retry_count: 当前递归重试次数
        :return: 回复
        """
        if retry_count > 2:
            # exit from retry 2 times
            logger.info("[RasaBot] failed after maximum number of retry times")
            return Reply(ReplyType.TEXT, "请再问我一次吧")

        try:
            return Reply(ReplyType.TEXT, "test......")

        except Exception as e:
            logger.exception(e)
            # retry
            time.sleep(2)
            logger.warn(f"[RasaBot] do retry, times={retry_count}")
            return self._chat(query, context, retry_count + 1)

    def reply(self, query, context=None):
        # 处理查询请求
        if context and context.type:
            if context.type == ContextType.TEXT:
                logger.info("[RasaBot] query={}".format(context))
                session_id = context["session_id"]
                reply = None
                
                if query == "#清除记忆":
                    self.sessions.clear_session(session_id)
                    reply = Reply(ReplyType.INFO, "记忆已清除")
                    return reply
                    
                session = self.sessions.session_query(query, session_id)
                
                reply_content = self.reply_text(context["receiver"], query)
                
                if reply_content:
                    # 将回复添加到会话中
                    session.add_reply(reply_content)
                    
                    logger.info("[RasaBot] new reply={}".format(reply_content))
                    reply = Reply(ReplyType.TEXT, reply_content)
                else:
                    logger.error("[RasaBot] reply content is empty")
                    reply = Reply(ReplyType.ERROR, "对不起，我没有得到有效的回复。")
                    
                return reply
            elif context.type == ContextType.IMAGE_CREATE:
                # 不支持图像创建
                reply = Reply(ReplyType.ERROR, "抱歉，Rasa模型暂不支持图像创建。")
                return reply
        return Reply(ReplyType.ERROR, "处理消息失败")

    def reply_text(self, sender, messages, retry_count=0):
        """使用Rasa API生成回复"""
        try:
            logger.info("[RasaBot] session , messages={}".format(messages))
            logger.info("[RasaBot] sender :"+sender)
            reply_content = ""
            # 调用API获取回复
            headers = {"Content-Type":"application/json"}
            body = {"sender":sender, "message":messages}
            res = requests.post(url="http://host.docker.internal:5005/webhooks/rest/webhook",json=body,headers=headers,timeout=self.args['request_timeout'])
            if res.status_code == 200:
                # execute success
                response = res.json()
                logger.info(f"[RasaBot] reply={response}")

                if isinstance(response, list) and len(response) > 0:
                    reply_content = response[0].get('text', '')
                else:
                    reply_content = "未收到有效回复"
            else:
                response = res.json()
                error = response.get("error")
                reply_content = error.get('message')
                logger.error(f"[RasaBot] chat failed, status_code={res.status_code}, "
                             f"msg={error.get('message')}, type={error.get('type')}")
            # 提取回复内容
            return reply_content
            
        except Exception as e:
            # 处理异常情况
            logger.error("[RasaBot] Exception: {}".format(e))
            if retry_count < 2:
                logger.warn("[RasaBot] 第{}次重试".format(retry_count + 1))
                # time.sleep(3)
                # return self.reply_text(session, retry_count + 1)
            else:
                return "抱歉，我遇到了问题，请稍后再试。" 