#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Use WebUI - Backend API
将 Gradio 的功能暴露为 REST API
"""
import os
import sys
import glob

import json
import tempfile
import asyncio
from datetime import datetime
from typing import Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, WebSocket, WebSocketDisconnect, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel
import logging

from src.webui.webui_manager import WebuiManager
from src.webui.log_handler import WebSocketLogHandler
from src.webui.session_manager import session_manager
from src.webui.session import Session
from src.utils import config


class ConnectionManager:
    """管理 WebSocket 连接，支持向所有连接的客户端广播消息"""

    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """向所有连接的客户端广播 JSON 消息"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)


ws_manager = ConnectionManager()


# ===== Session 中间件和依赖注入 =====

class SessionMiddleware(BaseHTTPMiddleware):
    """从请求中提取 sessionId"""

    async def dispatch(self, request, call_next):
        # 从请求头获取 sessionId
        session_id = request.headers.get("X-Session-ID")
        # 也支持从查询参数获取（某些场景可能需要）
        if not session_id:
            session_id = request.query_params.get("sessionId")

        # 存储到 request.state
        request.state.session_id = session_id

        response = await call_next(request)
        return response


async def get_current_session(request: Request) -> Session:
    """
    依赖注入：获取当前会话

    如果请求中没有 sessionId，返回 400 错误
    如果会话不存在，自动创建
    """
    session_id = request.state.session_id

    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required (X-Session-ID header)")

    session = await session_manager.get_or_create_session(session_id)
    return session


# ===== 应用生命周期管理 =====

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动和关闭时的操作"""
    # 启动时
    logging.info("Starting application...")
    await session_manager.start_cleanup_task()
    logging.info("Session cleanup task started")

    yield

    # 关闭时
    logging.info("Shutting down application...")
    await session_manager.stop_cleanup_task()
    await session_manager.cleanup_all_sessions()
    logging.info("All sessions cleaned up")


#
#import pydevd_pycharm
#pydevd_pycharm.settrace('localhost', port=12321, stdoutToServer=True, stderrToServer=True)

app = FastAPI(
    title="Browser Use WebUI API",
    version="1.0.0",
    openapi_url=None,       # 禁用 OpenAPI 规范生成
    docs_url=None,          # 禁用 Swagger UI
    redoc_url=None,         # 禁用 ReDoc
    lifespan=lifespan       # 应用生命周期管理
)

# 添加 Session 中间件（必须在其他中间件之前）
app.add_middleware(SessionMiddleware)

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置 WebSocket 日志处理器
ws_log_handler = WebSocketLogHandler(session_manager)
ws_log_handler.setLevel(logging.DEBUG)
# 使用简洁的日志格式
ws_log_handler.setFormatter(logging.Formatter('%(levelname)s [%(name)s] %(message)s'))

# 将日志处理器添加到根日志器
root_logger = logging.getLogger()
root_logger.addHandler(ws_log_handler)

# 重要：将日志处理器添加到 browser_use 日志器
# browser-use 库使用了独立的日志器，设置了 propagate=False
browser_use_logger = logging.getLogger('browser_use')
browser_use_logger.addHandler(ws_log_handler)
browser_use_logger.setLevel(logging.DEBUG)

# 同时添加到其他关键日志器
for logger_name in ['browser_use.agent', 'browser_use.browser.session', 'browser_use.tools']:
    logger = logging.getLogger(logger_name)
    logger.addHandler(ws_log_handler)
    logger.setLevel(logging.DEBUG)

# 配置保存目录
SETTINGS_SAVE_DIR = "./tmp/webui_settings"
os.makedirs(SETTINGS_SAVE_DIR, exist_ok=True)

# 内存中的配置存储
current_agent_settings = {}
current_browser_settings = {}


def snake_to_camel(snake_str):
    """
    将下划线命名转换为驼峰命名
    例如: llm_provider -> llmProvider
    """
    components = snake_str.split('_')
    # 第一个单词保持小写，后面的单词首字母大写
    return components[0] + ''.join(x.title() for x in components[1:])


def camel_to_snake(camel_str):
    """
    将驼峰命名转换为下划线命名
    例如: llmProvider -> llm_provider
    """
    result = []
    for i, char in enumerate(camel_str):
        if char.isupper() and i > 0:
            result.append('_')
        result.append(char.lower())
    return ''.join(result)


def convert_to_gradio_config(agent_settings, browser_settings):
    """
    将当前配置转换为 Gradio 格式的配置
    Gradio 格式: { "agent_settings.llm_provider": "openai", ... }
    """
    result = {}

    # 特殊字段映射表 - 用于反向转换
    special_field_mappings = {
        "windowWidth": "window_w",
        "windowHeight": "window_h"
    }

    # 转换代理设置
    for camel_key, value in agent_settings.items():
        # 检查是否有特殊字段映射
        if camel_key in special_field_mappings:
            snake_key = special_field_mappings[camel_key]
        else:
            snake_key = camel_to_snake(camel_key)

        gradio_key = f"agent_settings.{snake_key}"
        result[gradio_key] = value

    # 转换浏览器设置
    for camel_key, value in browser_settings.items():
        # 检查是否有特殊字段映射
        if camel_key in special_field_mappings:
            snake_key = special_field_mappings[camel_key]
        else:
            snake_key = camel_to_snake(camel_key)

        gradio_key = f"browser_settings.{snake_key}"
        result[gradio_key] = value

    return result


def convert_dict_keys(data, converter):
    """
    转换字典的键名
    """
    if isinstance(data, dict):
        return {converter(k): convert_dict_keys(v, converter) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_dict_keys(item, converter) for item in data]
    else:
        return data


def normalize_browser_settings(settings: dict) -> dict:
    """
    标准化浏览器设置字段名，处理特殊字段映射
    """
    normalized = settings.copy()

    # 处理窗口大小字段的多种命名方式
    if 'window_height' in normalized:
        normalized['window_h'] = normalized.pop('window_height')
    if 'window_width' in normalized:
        normalized['window_w'] = normalized.pop('window_width')

    return normalized


# ===== 配置管理 =====

class ConfigSaveResponse(BaseModel):
    success: bool
    message: str
    filename: str
    path: str

class ConfigLoadResponse(BaseModel):
    success: bool
    message: str
    agentSettings: dict
    browserSettings: dict


def load_latest_config():
    """
    加载 tmp/webui_settings/ 目录中最新的配置文件
    """
    global current_agent_settings, current_browser_settings

    try:
        # 查找所有 .json 配置文件
        config_files = glob.glob(os.path.join(SETTINGS_SAVE_DIR, "*.json"))

        if config_files:
            # 按修改时间排序，获取最新的文件
            config_files.sort(key=os.path.getmtime, reverse=True)
            latest_file = config_files[0]

            print(f"INFO: Loading latest configuration from: {latest_file}")

            with open(latest_file, "r") as f:
                ui_settings = json.load(f)

            # 解析配置文件
            parsed_config = parse_gradio_config(ui_settings)

            # 更新全局配置
            current_agent_settings = convert_dict_keys(parsed_config["agentSettings"], camel_to_snake)
            current_browser_settings = convert_dict_keys(parsed_config["browserSettings"], camel_to_snake)

            print(f"INFO: Successfully loaded agent settings: {list(current_agent_settings.keys())}")
            print(f"INFO: Successfully loaded browser settings: {list(current_browser_settings.keys())}")

            return True
        else:
            print("INFO: No configuration files found, using defaults")
            return False

    except Exception as e:
        print(f"WARNING: Failed to load latest configuration: {str(e)}")
        return False



def parse_gradio_config(ui_settings):
    """
    解析 Gradio 格式的配置文件，按 tab 分组
    原格式: { "agent_settings.llm_provider": "openai", ... }
    新格式: { agentSettings: { llmProvider: "openai", ... }, browserSettings: { ... } }
    """
    # 特殊字段名映射表
    special_field_mappings = {
        "window_w": "windowWidth",
        "window_h": "windowHeight"
    }

    result = {
        "agentSettings": {},
        "browserSettings": {},
        "otherSettings": {}
    }

    for comp_id, comp_val in ui_settings.items():
        # 解析组件ID格式: tab_name.component_name
        if "." in comp_id:
            parts = comp_id.split(".", 1)
            tab_name = parts[0]
            comp_name = parts[1]

            # 检查是否有特殊字段映射
            if comp_name in special_field_mappings:
                camel_name = special_field_mappings[comp_name]
            else:
                # 将下划线命名转换为驼峰命名
                camel_name = snake_to_camel(comp_name)

            if tab_name == "agent_settings":
                result["agentSettings"][camel_name] = comp_val
            elif tab_name == "browser_settings":
                result["browserSettings"][camel_name] = comp_val
            else:
                result["otherSettings"][camel_name] = comp_val
        else:
            result["otherSettings"][comp_id] = comp_val

    return result


# 应用启动时加载最新配置
print("INFO: Starting backend API...")
load_latest_config()


@app.post("/api/load-config", response_model=ConfigLoadResponse)
async def load_config(file: UploadFile = File(...)):
    """加载 UI 配置"""
    try:
        content = await file.read()
        ui_settings = json.loads(content.decode("utf-8"))

        # 解析配置文件
        parsed_config = parse_gradio_config(ui_settings)

        # 更新全局配置 - 这里我们需要将驼峰转换为下划线存储
        global current_agent_settings, current_browser_settings
        current_agent_settings = convert_dict_keys(parsed_config["agentSettings"], camel_to_snake)
        current_browser_settings = convert_dict_keys(parsed_config["browserSettings"], camel_to_snake)

        # 但返回时使用驼峰格式
        return ConfigLoadResponse(
            success=True,
            message=f"Successfully loaded config: {file.filename}",
            agentSettings=parsed_config["agentSettings"],
            browserSettings=parsed_config["browserSettings"]
        )
    except Exception as e:
        return ConfigLoadResponse(
            success=False,
            message=f"Failed to load config: {str(e)}",
            agentSettings={},
            browserSettings={}
        )

@app.get("/api/save-config", response_model=ConfigSaveResponse)
async def save_config():
    """保存 UI 配置"""
    try:
        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        config_path = os.path.join(SETTINGS_SAVE_DIR, f"{config_name}.json")

        # 获取当前配置
        agent_settings = await get_agent_settings()
        browser_settings = await get_browser_settings()

        # 转换为 Gradio 格式的配置
        gradio_config = convert_to_gradio_config(
            agent_settings.get("settings", {}),
            browser_settings.get("settings", {})
        )

        with open(config_path, "w") as fw:
            json.dump(gradio_config, fw, indent=4)

        return ConfigSaveResponse(
            success=True,
            message="UI settings saved successfully",
            filename=f"{config_name}.json",
            path=config_path
        )
    except Exception as e:
        return ConfigSaveResponse(
            success=False,
            message=f"Failed to save config: {str(e)}",
            filename="",
            path=""
        )

# ===== 代理设置管理 =====

class AgentSettings(BaseModel):
    override_system_prompt: Optional[str] = ""
    extend_system_prompt: Optional[str] = ""
    llm_provider: Optional[str] = "openai"
    llm_model_name: Optional[str] = ""
    llm_temperature: Optional[float] = 0.6
    use_vision: Optional[bool] = True
    ollama_num_ctx: Optional[int] = 16000
    llm_base_url: Optional[str] = ""
    llm_api_key: Optional[str] = ""
    planner_llm_provider: Optional[str] = None
    planner_llm_model_name: Optional[str] = ""
    planner_llm_temperature: Optional[float] = 0.6
    planner_use_vision: Optional[bool] = False
    planner_ollama_num_ctx: Optional[int] = 16000
    planner_llm_base_url: Optional[str] = ""
    planner_llm_api_key: Optional[str] = ""
    max_steps: Optional[int] = 100
    max_actions: Optional[int] = 10
    max_input_tokens: Optional[int] = 128000
    tool_calling_method: Optional[str] = "auto"


@app.get("/api/agent-settings")
async def get_agent_settings():
    """获取代理设置"""
    try:
        global current_agent_settings
        if not current_agent_settings:
            # 返回默认值
            default_settings = AgentSettings()
            current_agent_settings = default_settings.model_dump()

        # 将下划线转换为驼峰返回
        return {
            "success": True,
            "settings": convert_dict_keys(current_agent_settings, snake_to_camel)
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@app.post("/api/agent-settings")
async def update_agent_settings(settings: dict):
    """更新代理设置"""
    try:
        global current_agent_settings
        # 将前端发送的驼峰命名转换为下划线命名
        converted_settings = convert_dict_keys(settings, camel_to_snake)

        # 使用转换后的数据验证模型
        agent_settings = AgentSettings(**converted_settings)
        current_agent_settings = agent_settings.model_dump()

        # 返回转换为驼峰格式的数据
        return {
            "success": True,
            "message": "Agent settings updated successfully",
            "settings": convert_dict_keys(current_agent_settings, snake_to_camel)
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# ===== 浏览器设置管理 =====

class BrowserSettings(BaseModel):
    browser_binary_path: Optional[str] = ""
    browser_user_data_dir: Optional[str] = ""
    use_own_browser: Optional[bool] = False
    keep_browser_open: Optional[bool] = True
    headless: Optional[bool] = False
    disable_security: Optional[bool] = False
    save_recording_path: Optional[str] = ""
    save_trace_path: Optional[str] = ""
    save_agent_history_path: Optional[str] = "./tmp/agent_history"
    save_download_path: Optional[str] = "./tmp/downloads"
    cdp_url: Optional[str] = ""
    wss_url: Optional[str] = ""
    window_h: Optional[int] = 1100
    window_w: Optional[int] = 1280


@app.get("/api/browser-settings")
async def get_browser_settings():
    """获取浏览器设置"""
    try:
        global current_browser_settings
        if not current_browser_settings:
            # 返回默认值
            default_settings = BrowserSettings()
            current_browser_settings = default_settings.model_dump()

        # 将下划线转换为驼峰返回
        return {
            "success": True,
            "settings": convert_dict_keys(current_browser_settings, snake_to_camel)
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


@app.post("/api/browser-settings")
async def update_browser_settings(settings: dict):
    """更新浏览器设置"""
    try:
        global current_browser_settings
        # 将前端发送的驼峰命名转换为下划线命名
        converted_settings = convert_dict_keys(settings, camel_to_snake)

        # 使用转换后的数据验证模型
        browser_settings = BrowserSettings(**converted_settings)
        current_browser_settings = browser_settings.model_dump()

        # 返回转换为驼峰格式的数据
        return {
            "success": True,
            "message": "Browser settings updated successfully",
            "settings": convert_dict_keys(current_browser_settings, snake_to_camel)
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# ===== 浏览器使用代理 =====

class BrowserUseAgentRequest(BaseModel):
    task: str

@app.post("/api/agent/run")
async def run_agent(data: BrowserUseAgentRequest, session: Session = Depends(get_current_session)):
    """运行代理"""
    try:
        # 发送启动日志
        logging.info(f"[Agent] Starting agent with task: {data.task} (session: {session.session_id})")

        # 获取当前配置 - 这里 get_agent_settings 已经返回了下划线格式
        agent_settings = await get_agent_settings()
        browser_settings = await get_browser_settings()

        # 转换键名并标准化浏览器设置
        agent_settings_converted = convert_dict_keys(agent_settings.get("settings", {}), camel_to_snake)
        browser_settings_converted = convert_dict_keys(browser_settings.get("settings", {}), camel_to_snake)
        browser_settings_normalized = normalize_browser_settings(browser_settings_converted)

        config = {
            "agentSettings": agent_settings_converted,
            "browserSettings": browser_settings_normalized
        }

        # 将配置传递给会话级 webui_manager
        session.manager.current_agent_settings = config['agentSettings']
        session.manager.current_browser_settings = config['browserSettings']

        # 运行代理任务
        task_id = await session.manager.run_browser_use_agent(data.task, config)

        logging.info(f"[Agent] Agent started successfully with task_id: {task_id}")

        return {
            "success": True,
            "task_id": task_id,
            "message": "Agent started successfully",
            "session_id": session.session_id
        }
    except Exception as e:
        logging.error(f"[Agent] Failed to start agent: {str(e)}")
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/stop")
async def stop_agent(task_id: str = Form(...), session: Session = Depends(get_current_session)):
    """停止代理"""
    try:
        await session.manager.stop_browser_use_agent()
        return {
            "success": True,
            "message": "Agent stopped successfully",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/pause")
async def pause_agent(task_id: str = Form(...), session: Session = Depends(get_current_session)):
    """暂停代理"""
    try:
        await session.manager.pause_browser_use_agent()
        return {
            "success": True,
            "message": "Agent paused",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/resume")
async def resume_agent(task_id: str = Form(...), session: Session = Depends(get_current_session)):
    """恢复代理"""
    try:
        await session.manager.resume_browser_use_agent()
        return {
            "success": True,
            "message": "Agent resumed",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.get("/api/agent/status")
async def get_agent_status(task_id: str, session: Session = Depends(get_current_session)):
    """获取代理状态"""
    try:
        status = await session.manager.get_browser_use_agent_status(task_id)
        status["session_id"] = session.session_id
        return status
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/respond")
async def respond_to_agent(task_id: str = Form(...), message: str = Form(...), session: Session = Depends(get_current_session)):
    """发送用户响应"""
    try:
        # TODO: 实现 respond_to_agent 功能
        return {
            "success": True,
            "message": "Response received",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

# ===== 深度研究代理 =====

class DeepResearchRequest(BaseModel):
    topic: str
    resume_task_id: Optional[str] = None
    parallel_num: Optional[int] = 1
    save_dir: Optional[str] = "./tmp/deep_research"

@app.post("/api/deep-research/run")
async def run_deep_research(data: DeepResearchRequest, session: Session = Depends(get_current_session)):
    """运行深度研究"""
    try:
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        return {
            "success": True,
            "task_id": task_id,
            "message": "Deep research started",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/deep-research/stop")
async def stop_deep_research(task_id: str = Form(...), session: Session = Depends(get_current_session)):
    """停止深度研究"""
    try:
        return {
            "success": True,
            "message": "Deep research stopped",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.get("/api/deep-research/report")
async def get_deep_research_report(task_id: str, session: Session = Depends(get_current_session)):
    """获取研究报告"""
    try:
        report_content = "# Research Report\n\nThis is a placeholder report."
        return {
            "success": True,
            "task_id": task_id,
            "report": report_content,
            "file_path": f"/tmp/{task_id}_report.md",
            "session_id": session.session_id
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }


# ===== 步骤历史查询接口 =====

@app.get("/api/agent/steps")
async def get_agent_steps(session: Session = Depends(get_current_session)):
    """获取当前任务的历史步骤列表（供新连接客户端补全历史）"""
    return {
        "success": True,
        "task_id": session.manager.bu_agent_task_id,
        "steps": session.manager.bu_step_history,
        "session_id": session.session_id
    }


# ===== 日志历史查询接口 =====

@app.get("/api/agent/logs")
async def get_agent_logs(session: Session = Depends(get_current_session)):
    """获取当前任务的历史日志列表（供新连接客户端补全历史）"""
    return {
        "success": True,
        "task_id": session.manager.bu_agent_task_id,
        "logs": session.manager.bu_log_history,
        "session_id": session.session_id
    }


# ===== LLM 日志历史查询接口 =====

@app.get("/api/agent/llm-logs")
async def get_agent_llm_logs(session: Session = Depends(get_current_session)):
    """获取当前任务的 LLM 日志列表（供新连接客户端补全历史）"""
    return {
        "success": True,
        "task_id": session.manager.bu_agent_task_id,
        "logs": session.manager.bu_llm_log_history,
        "session_id": session.session_id
    }


# ===== WebSocket 长连接 =====

@app.websocket("/ws/agent-events")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 长连接端点，用于实时推送代理执行事件（步骤、状态、日志等）。

    消息格式 (服务端推送):
    {
        "type": "step" | "status" | "error" | "history" | "log" | "log-history" | ... ,
        "data": { ... }
    }

    消息格式 (客户端发送):
    {
        "type": "register", "sessionId": "xxx"  # 连接后第一条消息
        "type": "ping"                          # 心跳消息
    }

    - type="step": 代理执行步骤数据（实时）
    - type="history": 连接时推送的历史步骤列表
    - type="status": 代理运行状态变更
    - type="error": 错误信息
    - type="log": 执行日志（实时）
    - type="log-history": 连接时推送的历史日志列表
    """
    await websocket.accept()
    session = None

    try:
        # 1. 等待注册消息（10秒超时）
        register_msg = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)

        if register_msg.get("type") != "register":
            await websocket.send_json({"type": "error", "message": "Must register first with sessionId"})
            await websocket.close()
            return

        session_id = register_msg.get("sessionId")
        if not session_id:
            await websocket.send_json({"type": "error", "message": "sessionId is required"})
            await websocket.close()
            return

        # 2. 获取或创建会话
        session = await session_manager.get_or_create_session(session_id)
        await session.add_websocket(websocket)

        # 3. 发送注册确认
        await websocket.send_json({
            "type": "registered",
            "sessionId": session_id
        })

        # 4. 推送历史数据
        if session.manager.bu_step_history:
            try:
                await websocket.send_json({
                    "type": "history",
                    "data": {
                        "task_id": session.manager.bu_agent_task_id,
                        "steps": session.manager.bu_step_history
                    }
                })
            except Exception:
                pass

        # 推送历史日志
        if session.manager.bu_log_history:
            try:
                await websocket.send_json({
                    "type": "log-history",
                    "data": {
                        "logs": session.manager.bu_log_history
                    }
                })
            except Exception:
                pass

        # 推送 LLM 历史日志
        if session.manager.bu_llm_log_history:
            try:
                await websocket.send_json({
                    "type": "llm-log-history",
                    "data": {
                        "logs": session.manager.bu_llm_log_history
                    }
                })
            except Exception:
                pass

        # 5. 消息循环（处理心跳）
        while True:
            message = await websocket.receive_json()

            if message.get("type") == "ping":
                # 更新心跳时间
                await session.update_heartbeat()
                # 发送心跳响应
                await websocket.send_json({"type": "pong"})

    except asyncio.TimeoutError:
        await websocket.send_json({"type": "error", "message": "Registration timeout (10s)"})
        await websocket.close()

    except WebSocketDisconnect:
        pass

    except Exception as e:
        logging.error(f"WebSocket error: {e}", exc_info=True)

    finally:
        if session:
            session.remove_websocket(websocket)


@app.websocket("/ws/screen")
async def websocket_screen_endpoint(websocket: WebSocket):
    """
    专用二进制 WebSocket 端点，用于实时推送浏览器画面帧。
    发送原始 JPEG 字节（binary frames），无 JSON 包装。
    客户端需将 binaryType 设为 'arraybuffer'。

    支持客户端发送 JSON 控制消息：
    - {"type": "quality", "quality": 70} - 调整 JPEG 质量 (10-100)
    - {"type": "register", "sessionId": "xxx"} - 注册会话
    """
    await websocket.accept()
    session = None

    try:
        # 1. 等待注册消息（10秒超时）
        register_msg = await asyncio.wait_for(websocket.receive(), timeout=10.0)

        # 处理文本消息（注册）
        if "text" in register_msg:
            try:
                msg = json.loads(register_msg["text"])
                if msg.get("type") == "register":
                    session_id = msg.get("sessionId")
                    if not session_id:
                        await websocket.send_json({"type": "error", "message": "sessionId is required"})
                        await websocket.close()
                        return

                    # 获取或创建会话
                    session = await session_manager.get_or_create_session(session_id)
                    await session.add_screen_websocket(websocket)

                    # 发送注册确认
                    await websocket.send_json({
                        "type": "registered",
                        "sessionId": session_id
                    })

                    # 2. 进入消息循环
                    while True:
                        data = await websocket.receive()

                        # 处理文本消息（控制命令）
                        if "text" in data:
                            try:
                                msg = json.loads(data["text"])
                                if msg.get("type") == "quality":
                                    quality = msg.get("quality", 70)
                                    # 通知 session.manager 更新质量
                                    if session and hasattr(session.manager, 'update_screencast_quality'):
                                        await session.manager.update_screencast_quality(quality)
                                elif msg.get("type") == "ping":
                                    # 心跳
                                    await session.update_heartbeat()
                                    await websocket.send_json({"type": "pong"})
                            except Exception as e:
                                logging.error(f"Error processing screen control message: {e}")

                        # 如果是二进制数据（客户端不需要发送，但保持兼容）
                        elif "bytes" in data:
                            pass

            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON"})
                await websocket.close()

        else:
            await websocket.send_json({"type": "error", "message": "Must register first with sessionId"})
            await websocket.close()

    except asyncio.TimeoutError:
        await websocket.send_json({"type": "error", "message": "Registration timeout (10s)"})
        await websocket.close()

    except WebSocketDisconnect:
        pass

    except Exception as e:
        logging.error(f"Screen WebSocket error: {e}", exc_info=True)

    finally:
        if session:
            session.remove_screen_websocket(websocket)

if __name__ == "__main__":
    import uvicorn
    # 检测是否在 PyCharm 调试模式下运行
    # is_pycharm_debug = 'PYCHARM_HOSTED' in os.environ or 'PYDEVD_DEBUG_INFO' in os.environ

    # # 在调试模式下使用不同的启动方式
    # if is_pycharm_debug:
    #     # 调试模式下使用简单的方式启动
    #     import asyncio
    #     config = uvicorn.Config(app, host="127.0.0.1", port=7788, log_level="info")
    #     server = uvicorn.Server(config)
    #     asyncio.run(server.serve())
    # else:
    #     # 正常模式下使用标准方式
    uvicorn.run(app, host="127.0.0.1", port=7788)