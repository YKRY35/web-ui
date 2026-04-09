import json
from collections.abc import Generator
from typing import TYPE_CHECKING, Optional, Dict, List, Any
import os
import gradio as gr
from datetime import datetime
import uuid
import asyncio
import time

from browser_use.agent.service import Agent
from browser_use.browser.session import BrowserSession
from browser_use.controller import Controller as BrowserUseController
from src.controller.custom_controller import CustomController

# 导入兼容性模块
from src.webui.browser_use_compat import BrowserState, AgentHistoryList, AgentOutput


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings"):
        self.id_to_component: dict[str, "Component"] = {}
        self.component_to_id: dict["Component", str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

        # 初始化代理和浏览器
        self.init_browser_use_agent()
        self.init_deep_research_agent()

    def init_browser_use_agent(self) -> None:
        """
        init browser use agent using browser-use library
        """
        self.bu_agent: Optional[Agent] = None
        self.bu_browser_session: Optional[BrowserSession] = None
        self.bu_controller: Optional[BrowserUseController] = None
        self.bu_chat_history: List[Dict[str, Optional[str]]] = []
        self.bu_response_event: Optional[asyncio.Event] = None
        self.bu_user_help_response: Optional[str] = None
        self.bu_current_task: Optional[asyncio.Task] = None
        self.bu_agent_task_id: Optional[str] = None
        self.bu_is_running: bool = False
        self.bu_is_paused: bool = False
        self.bu_is_waiting_for_help: bool = False

        # 当前配置
        self.current_agent_settings = None
        self.current_browser_settings = None

    def init_deep_research_agent(self) -> None:
        """
        init deep research agent
        """
        # 暂时移除 DeepResearchAgent 支持，后续可添加
        pass

    def add_components(self, tab_name: str, components_dict: dict[str, "Component"]) -> None:
        """
        Add tab components
        """
        for comp_name, component in components_dict.items():
            comp_id = f"{tab_name}.{comp_name}"
            self.id_to_component[comp_id] = component
            self.component_to_id[component] = comp_id

    def get_components(self) -> list["Component"]:
        """
        Get all components
        """
        return list(self.id_to_component.values())

    def get_component_by_id(self, comp_id: str) -> "Component":
        """
        Get component by id
        """
        return self.id_to_component[comp_id]

    def get_id_by_component(self, comp: "Component") -> str:
        """
        Get id by component
        """
        return self.component_to_id[comp]

    def save_config(self, components: Dict["Component", str]) -> None:
        """
        Save config
        """
        cur_settings = {}
        for comp in components:
            if not isinstance(comp, gr.Button) and not isinstance(comp, gr.File) and str(
                    getattr(comp, "interactive", True)).lower() != "false":
                comp_id = self.get_id_by_component(comp)
                cur_settings[comp_id] = components[comp]

        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        with open(os.path.join(self.settings_save_dir, f"{config_name}.json"), "w") as fw:
            json.dump(cur_settings, fw, indent=4)

        return os.path.join(self.settings_save_dir, f"{config_name}.json")

    def load_config(self, config_path: str):
        """
        Load config
        """
        with open(config_path, "r") as fr:
            ui_settings = json.load(fr)

        update_components = {}
        for comp_id, comp_val in ui_settings.items():
            if comp_id in self.id_to_component:
                comp = self.id_to_component[comp_id]
                if comp.__class__.__name__ == "Chatbot":
                    update_components[comp] = comp.__class__(value=comp_val, type="messages")
                else:
                    update_components[comp] = comp.__class__(value=comp_val)
                    if comp_id == "agent_settings.planner_llm_provider":
                        yield update_components  # yield provider, let callback run
                        time.sleep(0.1)  # wait for Gradio UI callback

        config_status = self.id_to_component["load_save_config.config_status"]
        update_components.update(
            {
                config_status: config_status.__class__(value=f"Successfully loaded config: {config_path}")
            }
        )
        yield update_components

    async def run_browser_use_agent(self, task: str, config: dict) -> str:
        """
        运行浏览器使用代理 (使用 browser-use)
        """
        # 保存配置到实例变量
        self.current_agent_settings = config.get('agentSettings', {})
        self.current_browser_settings = config.get('browserSettings', {})

        self.bu_agent_task_id = str(uuid.uuid4())
        self.bu_is_running = True
        self.bu_is_paused = False
        self.bu_is_waiting_for_help = False
        self.bu_chat_history = []

        try:
            # 初始化浏览器和控制器
            if self.bu_browser_session is None:
                browser_config = self.current_browser_settings or {}

                # 构建浏览器参数
                browser_args = {
                    'window_size': {
                        'width': browser_config.get('windowWidth', 1280),
                        'height': browser_config.get('windowHeight', 1100)
                    },
                    'headless': not browser_config.get('keepBrowserOpen', True),
                }

                # 只有当 user_data_dir 不为空时才添加
                user_data_dir = browser_config.get('browserUserDataDir', '')
                if user_data_dir:
                    browser_args['user_data_dir'] = user_data_dir

                self.bu_browser_session = BrowserSession(**browser_args)

            if self.bu_controller is None:
                self.bu_controller = BrowserUseController()

            # 初始化 Agent
            if self.bu_agent is None:
                # 使用保存的配置创建 LLM
                agent_config = self.current_agent_settings or {}
                llm = self._create_llm_from_config(agent_config)

                # 合并所有配置
                agent_run_config = {
                    **agent_config,
                    'max_steps': agent_config.get('maxSteps', 100),
                    'max_actions': agent_config.get('maxActions', 10),
                    'max_input_tokens': agent_config.get('maxInputTokens', 128000),
                    'tool_calling_method': agent_config.get('toolCallingMethod', 'auto'),
                    'task': task
                }

                self.bu_agent = Agent(
                    llm=llm,
                    browser_session=self.bu_browser_session,
                    controller=self.bu_controller,
                    **agent_run_config
                )

            # 运行代理任务
            self.bu_current_task = asyncio.create_task(self._run_agent_task(task))
            return self.bu_agent_task_id

        except Exception as e:
            self.bu_is_running = False
            raise e

    def _create_llm_from_config(self, config: dict):
        """根据配置创建 LLM 实例"""
        provider = config.get('llm_provider', 'openai')
        model_name = config.get('llm_model_name', 'gpt-4o')
        temperature = config.get('llm_temperature', 0.0)
        base_url = config.get('llm_base_url')
        api_key = config.get('llm_api_key')
        num_ctx = config.get('ollama_num_ctx')

        print(f"DEBUG: _create_llm_from_config called with config: {config}")
        print(f"DEBUG: provider: {provider}, model: {model_name}, temp: {temperature}")
        print(f"DEBUG: base_url: {base_url}, api_key: {api_key if api_key else 'None'}")

        kwargs = {
            'model': model_name,
            'temperature': temperature,
        }

        if base_url:
            kwargs['base_url'] = base_url
        if api_key:
            kwargs['api_key'] = api_key
        if num_ctx and provider == 'ollama':
            kwargs['num_ctx'] = num_ctx

        print(f"DEBUG: LLM kwargs: {kwargs}")

        if provider == 'openai':
            from browser_use.llm import ChatOpenAI
            return ChatOpenAI(**kwargs)
        elif provider == 'anthropic':
            from browser_use.llm import ChatAnthropic
            return ChatAnthropic(**kwargs)
        elif provider == 'google':
            from browser_use.llm import ChatGoogle
            return ChatGoogle(**kwargs)
        elif provider == 'ollama':
            from browser_use.llm import ChatOllama
            return ChatOllama(**kwargs)
        elif provider == 'mistral':
            from browser_use.llm import ChatMistral
            return ChatMistral(**kwargs)
        else:
            # 默认使用 OpenAI
            from browser_use.llm import ChatOpenAI
            return ChatOpenAI(**kwargs)

    async def _run_agent_task(self, task: str):
        """
        内部代理任务执行方法 (使用 browser-use)
        """
        try:
            await self.bu_agent.run(max_steps=100)  # 使用 browser-use 的 run 方法
        except Exception as e:
            print(f"Agent run error: {e}")
        finally:
            self.bu_is_running = False
            self.bu_current_task = None

    async def stop_browser_use_agent(self) -> None:
        """
        停止浏览器使用代理 (使用 browser-use)
        """
        # 检查是否应该保持浏览器开启
        should_keep_open = False
        if self.current_browser_settings:
            should_keep_open = self.current_browser_settings.get('keepBrowserOpen', False)

        if self.bu_agent and self.bu_is_running and not should_keep_open:
            self.bu_agent.stop()  # 使用 browser-use 的 stop 方法

        if self.bu_current_task and not self.bu_current_task.done():
            self.bu_current_task.cancel()

        self.bu_is_running = False
        self.bu_current_task = None

    async def pause_browser_use_agent(self) -> None:
        """
        暂停浏览器使用代理 (使用 browser-use)
        """
        if self.bu_agent and self.bu_is_running:
            self.bu_agent.pause()  # 使用 browser-use 的 pause 方法
            self.bu_is_paused = True

    async def resume_browser_use_agent(self) -> None:
        """
        恢复浏览器使用代理 (使用 browser-use)
        """
        if self.bu_agent and self.bu_is_paused:
            self.bu_agent.resume()  # 使用 browser-use 的 resume 方法
            self.bu_is_paused = False

    async def get_browser_use_agent_status(self, task_id: str) -> dict:
        """
        获取浏览器使用代理状态
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
            "is_paused": self.bu_is_paused,
            "is_waiting_for_help": self.bu_is_waiting_for_help,
            "chat_history": self.bu_chat_history,
            "browser_view": "",
            "task_outputs": False
        }

        # 如果代理有状态信息，添加到响应中
        if self.bu_agent:
            # 获取聊天历史
            if hasattr(self.bu_agent, "_message_manager") and self.bu_agent._message_manager:
                pass  # 可以在这里添加获取聊天历史的逻辑

            # 获取浏览器视图
            if hasattr(self.bu_browser_session, "get_state"):
                pass  # 可以在这里添加获取浏览器视图的逻辑

        return status

    async def respond_to_browser_use_agent(self, task_id: str, message: str) -> None:
        """
        响应浏览器使用代理的帮助请求
        """
        if self.bu_agent_task_id == task_id and self.bu_is_waiting_for_help:
            self.bu_user_help_response = message
            if self.bu_response_event:
                self.bu_response_event.set()

