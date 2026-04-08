"""
简化的 WebuiManager，用于测试 browser-use 集成
"""
import json
from typing import Optional, Dict, List, Any
import uuid
import asyncio
import os
import logging

logger = logging.getLogger(__name__)


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

        # 初始化代理和浏览器
        self.init_browser_use_agent()

    def init_browser_use_agent(self) -> None:
        """
        初始化 browser-use agent
        """
        self.bu_agent: Optional[Any] = None
        self.bu_browser_session: Optional[Any] = None
        self.bu_controller: Optional[Any] = None
        self.bu_chat_history: List[Dict[str, Optional[str]]] = []
        self.bu_current_task: Optional[asyncio.Task] = None
        self.bu_agent_task_id: Optional[str] = None
        self.bu_is_running: bool = False

    async def run_browser_use_agent(self, task: str, config: dict) -> str:
        """
        运行浏览器使用代理 (简化版本)
        """
        self.bu_agent_task_id = str(uuid.uuid4())
        self.bu_is_running = True
        self.bu_chat_history = []

        try:
            # 初始化浏览器和控制器
            if self.bu_browser_session is None:
                try:
                    from browser_use.browser.session import BrowserSession
                    self.bu_browser_session = BrowserSession()
                    logger.info("BrowserSession created successfully")
                except Exception as e:
                    logger.error(f"Failed to create BrowserSession: {e}")
                    self.bu_is_running = False
                    raise e

            if self.bu_controller is None:
                try:
                    from browser_use.controller import Controller
                    self.bu_controller = Controller()
                    logger.info("Controller created successfully")
                except Exception as e:
                    logger.error(f"Failed to create Controller: {e}")
                    self.bu_is_running = False
                    raise e

            # 初始化 Agent
            if self.bu_agent is None:
                try:
                    from browser_use.agent.service import Agent
                    from browser_use.llm import ChatOpenAI

                    # 创建 LLM
                    llm_config = config.get('agentSettings', {})
                    llm = ChatOpenAI(
                        model=llm_config.get('model_name', 'gpt-4o'),
                        temperature=llm_config.get('temperature', 0.0)
                    )

                    self.bu_agent = Agent(
                        task=task,
                        llm=llm,
                        browser_session=self.bu_browser_session,
                        controller=self.bu_controller,
                        **llm_config
                    )
                    logger.info("Agent created successfully")
                except Exception as e:
                    logger.error(f"Failed to create Agent: {e}")
                    self.bu_is_running = False
                    raise e

            # 运行代理任务
            self.bu_current_task = asyncio.create_task(self._run_agent_task(task))
            return self.bu_agent_task_id

        except Exception as e:
            self.bu_is_running = False
            logger.error(f"Error in run_browser_use_agent: {e}")
            raise e

    async def _run_agent_task(self, task: str):
        """
        内部代理任务执行方法 (简化版本)
        """
        try:
            if self.bu_agent:
                await self.bu_agent.run(max_steps=10)  # 使用较小的步数进行测试
            else:
                logger.error("Agent is None")
        except Exception as e:
            logger.error(f"Agent run error: {e}")
        finally:
            self.bu_is_running = False
            self.bu_current_task = None

    async def stop_browser_use_agent(self) -> None:
        """
        停止浏览器使用代理 (简化版本)
        """
        if self.bu_agent and self.bu_is_running:
            try:
                self.bu_agent.stop()
            except Exception as e:
                logger.error(f"Error stopping agent: {e}")

        if self.bu_current_task and not self.bu_current_task.done():
            self.bu_current_task.cancel()

        self.bu_is_running = False
        self.bu_current_task = None

    async def get_browser_use_agent_status(self, task_id: str) -> dict:
        """
        获取浏览器使用代理状态 (简化版本)
        """
        if self.bu_agent_task_id != task_id:
            return {
                "success": False,
                "message": "Invalid task_id"
            }

        status = {
            "success": True,
            "task_id": task_id,
            "status": "running" if self.bu_is_running else "completed",
            "is_paused": False,
            "is_waiting_for_help": False,
            "chat_history": self.bu_chat_history,
            "browser_view": "",
            "task_outputs": False
        }

        return status

    async def respond_to_browser_use_agent(self, task_id: str, message: str) -> None:
        """
        响应浏览器使用代理的帮助请求 (简化版本)
        """
        if self.bu_agent_task_id == task_id:
            self.bu_chat_history.append({
                "role": "user",
                "content": message
            })