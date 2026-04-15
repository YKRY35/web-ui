import json
from collections.abc import Generator
from typing import TYPE_CHECKING, Optional, Dict, List, Any
import os
import gradio as gr
from datetime import datetime
import uuid
import asyncio
import time
import logging

# 步骤历史最大缓存条数
MAX_STEP_HISTORY = 200
# 日志历史最大缓存条数
MAX_LOG_HISTORY = 1000

from browser_use.agent.service import Agent
from browser_use.browser.session import BrowserSession
from browser_use.controller import Controller as BrowserUseController
from src.controller.custom_controller import CustomController

# 导入兼容性模块
from src.webui.browser_use_compat import BrowserState, AgentHistoryList, AgentOutput


class WebuiManager:
    def __init__(self, settings_save_dir: str = "./tmp/webui_settings", ws_broadcast_func=None, screen_broadcast_func=None, session_id: Optional[str] = None):
        self.id_to_component: dict[str, "Component"] = {}
        self.component_to_id: dict["Component", str] = {}

        self.settings_save_dir = settings_save_dir
        os.makedirs(self.settings_save_dir, exist_ok=True)

        # 会话ID，用于标识会话级资源
        self.session_id = session_id

        # WebSocket 广播函数，用于实时推送步骤数据
        self.ws_broadcast_func = ws_broadcast_func

        # 屏幕流广播函数，用于推送浏览器画面帧
        self.screen_broadcast_func = screen_broadcast_func

        # 屏幕流 WebSocket 连接列表（已废弃，使用 screen_broadcast_func）
        self._screen_connections: list = []
        self._screencast_watchdog = None

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

        # 步骤历史缓存（内存，重启后清空）
        self.bu_step_history: List[Dict] = []

        # 日志历史缓存（内存，重启后清空）
        self.bu_log_history: List[Dict] = []

        # LLM 日志历史缓存
        self.bu_llm_log_history: List[Dict] = []

        # 当前配置
        self.current_agent_settings = None
        self.current_browser_settings = None

    def init_deep_research_agent(self) -> None:
        """
        init deep research agent
        """
        # 暂时移除 DeepResearchAgent 支持，后续可添加
        pass

    # ===== 屏幕流 WebSocket 管理 =====

    async def add_screen_connection(self, websocket) -> None:
        """已废弃：屏幕流连接现在由 Session 管理"""
        pass

    def remove_screen_connection(self, websocket) -> None:
        """已废弃：屏幕流连接现在由 Session 管理"""
        pass

    async def _broadcast_screen_frame(self, frame_bytes: bytes) -> None:
        """广播屏幕帧数据到所有连接的客户端"""
        if self.screen_broadcast_func:
            # 使用 Session 提供的广播函数
            await self.screen_broadcast_func(frame_bytes)
        else:
            # 向后兼容：如果没有提供广播函数，使用旧的 _screen_connections
            if not self._screen_connections:
                return
            disconnected = []
            for ws in self._screen_connections:
                try:
                    await ws.send_bytes(frame_bytes)
                except Exception:
                    disconnected.append(ws)
            for ws in disconnected:
                self.remove_screen_connection(ws)

    def _attach_screencast_watchdog(self) -> None:
        if self.bu_browser_session is None:
            return
        from src.webui.screencast_watchdog import ScreencastWatchdog
        self._screencast_watchdog = ScreencastWatchdog(
            event_bus=self.bu_browser_session.event_bus,
            browser_session=self.bu_browser_session,
        )
        self._screencast_watchdog._broadcast_frame = self._broadcast_screen_frame
        self._screencast_watchdog.attach_to_session()

    async def update_screencast_quality(self, quality: int) -> None:
        """更新投屏质量"""
        if self._screencast_watchdog:
            await self._screencast_watchdog.update_quality(quality)

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

        # 检查是否需要重置浏览器和代理（如果 keep_browser_open 为 False 或者组件不存在）
        should_keep_open = False
        if self.current_browser_settings:
            should_keep_open = self.current_browser_settings.get('keep_browser_open', False)

        self.bu_agent_task_id = str(uuid.uuid4())
        self.bu_is_running = True
        self.bu_is_paused = False
        self.bu_is_waiting_for_help = False
        self.bu_chat_history = []
        self.bu_step_history = []  # 每次新任务清空步骤历史
        self.bu_log_history = []   # 每次新任务清空日志历史
        self.bu_llm_log_history = []  # 每次新任务清空 LLM 日志历史

        try:
            browser_config = self.current_browser_settings or {}

            # 每次新任务都重新创建 browser_session 和 controller，
            # 确保新 Agent 的事件总线能正确注册到 BrowserSession 上。
            # 仅当 keep_browser_open=True 且 session 已存在时复用。
            if not should_keep_open or self.bu_browser_session is None:
                # 关闭旧 session（如果存在）
                if self.bu_browser_session is not None:
                    try:
                        await self.bu_browser_session.close()
                    except Exception:
                        pass
                    self.bu_browser_session = None

                # 构建浏览器参数
                browser_args = {
                    'window_size': {
                        'width': browser_config.get('window_w', 1280),
                        'height': browser_config.get('window_h', 1100)
                    },
                    'headless': browser_config.get('headless', False),  # headless 独立控制，不与 keep_browser_open 混淆
                    'keep_alive': should_keep_open,  # 关键：设置 keep_alive 让 browser-use 库知道是否保持浏览器打开
                    # 添加 Chrome 启动参数，禁用后台优化
                    'args': [
                        '--disable-background-timer-throttling',  # 禁用后台定时器节流
                        '--disable-backgrounding-occluded-windows',  # 禁用被遮挡窗口的后台化
                        '--disable-renderer-backgrounding',  # 禁用渲染器后台化
                        '--disable-features=CalculateNativeWinOcclusion',  # 禁用原生窗口遮挡计算
                        '--enable-features=NetworkService,NetworkServiceInProcess',  # 启用网络服务进程
                    ],
                }

                # 只有当 user_data_dir 不为空时才添加
                user_data_dir = browser_config.get('browserUserDataDir', '')
                if user_data_dir:
                    browser_args['user_data_dir'] = user_data_dir

                self.bu_browser_session = BrowserSession(**browser_args)
                self._attach_screencast_watchdog()

            if not should_keep_open or self.bu_controller is None:
                self.bu_controller = BrowserUseController()

            # 初始化 Agent（总是重新创建代理实例，避免事件总线问题）
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
                register_new_step_callback=self._on_agent_step,
                **agent_run_config
            )

            # 运行代理任务
            self.bu_current_task = asyncio.create_task(self._run_agent_task(task))
            return self.bu_agent_task_id

        except Exception as e:
            self.bu_is_running = False
            raise e

    def _on_agent_step(self, browser_state_summary, agent_output, step_number):
        """代理步骤回调 - 缓存步骤并通过 WebSocket 广播步骤数据"""
        # 提取所有操作元素的 XPath
        actions_with_xpath = []
        try:
            if agent_output and agent_output.action and hasattr(browser_state_summary, 'dom_state'):
                selector_map = browser_state_summary.dom_state.selector_map
                for action in agent_output.action:
                    action_dict = action.model_dump(exclude_unset=True)
                    action_name = next(iter(action_dict.keys()), None)
                    if action_name:
                        action_params = action_dict.get(action_name, {})
                        if isinstance(action_params, dict):
                            index = action_params.get('index')
                            xpath = None
                            if index is not None and selector_map and index in selector_map:
                                xpath = selector_map[index].xpath

                            actions_with_xpath.append({
                                'name': action_name,
                                'params': action_params,
                                'xpath': xpath
                            })
        except Exception:
            pass

        # 提取代理的用户意图（next_goal）
        next_goal = None
        try:
            if agent_output:
                next_goal = agent_output.next_goal
        except Exception:
            pass

        # 格式化步骤数据
        step_data = {
            "type": "step",
            "data": {
                "step_number": step_number,
                "timestamp": datetime.now().isoformat(),
                "next_goal": next_goal,
                "actions": actions_with_xpath,  # 新增：所有 actions 及其 xpath
                "model_output": agent_output.model_dump() if agent_output else None,
                "result": [r.model_dump() for r in browser_state_summary.result] if hasattr(browser_state_summary, 'result') else [],
                "state": {
                    "url": browser_state_summary.url,
                    "title": browser_state_summary.title,
                    "screenshot": browser_state_summary.screenshot,
                    "browser_errors": browser_state_summary.browser_errors,
                    "recent_events": browser_state_summary.recent_events
                }
            }
        }

        # 缓存步骤历史（上限 MAX_STEP_HISTORY 条）
        self.bu_step_history.append(step_data)
        if len(self.bu_step_history) > MAX_STEP_HISTORY:
            self.bu_step_history = self.bu_step_history[-MAX_STEP_HISTORY:]

        # 广播步骤数据（_on_agent_step 是同步回调，使用 asyncio.create_task 异步调度）
        if self.ws_broadcast_func:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.ws_broadcast_func(step_data))
                else:
                    loop.run_until_complete(self.ws_broadcast_func(step_data))
            except Exception as e:
                print(f"WebSocket broadcast error: {e}")

    def broadcast_log(self, level: str, message: str) -> None:
        """
        广播日志消息到 WebSocket

        Args:
            level: 日志级别 (info, warning, error, debug)
            message: 日志消息
        """
        log_data = {
            "type": "log",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message
            }
        }

        # 缓存日志历史（上限 MAX_LOG_HISTORY 条）
        self.bu_log_history.append(log_data)
        if len(self.bu_log_history) > MAX_LOG_HISTORY:
            self.bu_log_history = self.bu_log_history[-MAX_LOG_HISTORY:]

        # 广播日志数据
        if self.ws_broadcast_func:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.ws_broadcast_func(log_data))
                else:
                    loop.run_until_complete(self.ws_broadcast_func(log_data))
            except Exception as e:
                print(f"WebSocket broadcast log error: {e}")

    def broadcast_llm_log(self, level: str, message: str, log_type: str = 'info') -> None:
        """
        广播 LLM 日志消息到 WebSocket

        Args:
            level: 日志级别 (info, warning, error, debug)
            message: 日志消息
            log_type: 日志类型 (input, output, info)
        """
        log_data = {
            "type": "llm-log",
            "data": {
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message,
                "log_type": log_type
            }
        }

        # 缓存 LLM 日志历史（上限 MAX_LOG_HISTORY 条）
        self.bu_llm_log_history.append(log_data)
        if len(self.bu_llm_log_history) > MAX_LOG_HISTORY:
            self.bu_llm_log_history = self.bu_llm_log_history[-MAX_LOG_HISTORY:]

        # 广播 LLM 日志数据
        if self.ws_broadcast_func:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.ws_broadcast_func(log_data))
                else:
                    loop.run_until_complete(self.ws_broadcast_func(log_data))
            except Exception as e:
                print(f"WebSocket broadcast LLM log error: {e}")

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
            'remove_string_length_limits_from_schema': True,  # 移除不兼容的 string length 限制
        }

        if base_url:
            kwargs['base_url'] = base_url
        if api_key:
            kwargs['api_key'] = api_key
        if num_ctx and provider == 'ollama':
            kwargs['num_ctx'] = num_ctx

        print(f"DEBUG: LLM kwargs: {kwargs}")

        # 创建原始 LLM 实例
        llm = None
        if provider == 'openai':
            from browser_use.llm import ChatOpenAI
            llm = ChatOpenAI(**kwargs)
        elif provider == 'anthropic':
            from browser_use.llm import ChatAnthropic
            llm = ChatAnthropic(**kwargs)
        elif provider == 'google':
            from browser_use.llm import ChatGoogle
            llm = ChatGoogle(**kwargs)
        elif provider == 'ollama':
            from browser_use.llm import ChatOllama
            llm = ChatOllama(**kwargs)
        elif provider == 'mistral':
            from browser_use.llm import ChatMistral
            llm = ChatMistral(**kwargs)
        else:
            # 默认使用 OpenAI
            from browser_use.llm import ChatOpenAI
            llm = ChatOpenAI(**kwargs)

        # 包装 LLM 以记录日志
        from src.webui.llm_log_callback import LLMLogWrapper
        wrapped_llm = LLMLogWrapper(llm, self)
        return wrapped_llm

    async def _run_agent_task(self, task: str):
        """
        内部代理任务执行方法 (使用 browser-use)
        """
        try:
            await self.bu_agent.run(max_steps=100)  # 使用 browser-use 的 run 方法
        except asyncio.CancelledError:
            print('Agent task was cancelled')
            # 重新抛出 CancelledError 以便调用者知道任务被取消
            raise
        except Exception as e:
            print(f"Agent run error: {e}")
        finally:
            self.bu_is_running = False

            # 检查是否应该在任务完成后关闭浏览器
            should_keep_open = False
            if self.current_browser_settings:
                should_keep_open = self.current_browser_settings.get('keep_browser_open', False)

            if not should_keep_open:
                # 关闭浏览器会话
                if self.bu_browser_session is not None:
                    try:
                        await self.bu_browser_session.close()
                    except Exception as e:
                        print(f"Error closing browser session: {e}")
                    self.bu_browser_session = None
                # 重置代理和控制器，确保下次运行时重新初始化
                self.bu_agent = None
                self.bu_controller = None

    async def stop_browser_use_agent(self) -> None:
        """
        停止浏览器使用代理 (使用 browser-use)
        """
        # 检查是否应该保持浏览器开启
        should_keep_open = False
        if self.current_browser_settings:
            should_keep_open = self.current_browser_settings.get('keep_browser_open', False)

        if self.bu_agent and self.bu_is_running:
            # 调用 browser-use 的 stop 方法
            self.bu_agent.stop()

        # 取消并等待任务完成
        if self.bu_current_task and not self.bu_current_task.done():
            self.bu_current_task.cancel()
            try:
                await asyncio.wait_for(self.bu_current_task, timeout=5.0)
            except asyncio.CancelledError:
                pass
            except asyncio.TimeoutError:
                print("Warning: Task cancellation timed out")
            except Exception as e:
                print(f"Error while cancelling task: {e}")

        self.bu_is_running = False
        self.bu_current_task = None
        self.bu_is_paused = False
        self.bu_is_waiting_for_help = False

        # 总是重置代理，确保下次运行时创建新实例
        self.bu_agent = None
        self.bu_controller = None

        # 仅当 keep_browser_open=False 时关闭浏览器会话
        if not should_keep_open:
            if self.bu_browser_session is not None:
                try:
                    await self.bu_browser_session.close()
                except Exception as e:
                    print(f"Error closing browser session: {e}")
                self.bu_browser_session = None

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

