#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Browser Use WebUI - Backend API
将 Gradio 的功能暴露为 REST API
"""
import os
import json
import tempfile
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.webui.webui_manager import WebuiManager
from src.utils import config

app = FastAPI(title="Browser Use WebUI API", version="1.0.0")

# 允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 WebuiManager
webui_manager = WebuiManager()

# 配置保存目录
SETTINGS_SAVE_DIR = "./tmp/webui_settings"
os.makedirs(SETTINGS_SAVE_DIR, exist_ok=True)

# ===== 配置管理 =====

class ConfigSaveResponse(BaseModel):
    success: bool
    message: str
    filename: str
    path: str

class ConfigLoadResponse(BaseModel):
    success: bool
    message: str
    config: dict

@app.post("/api/load-config", response_model=ConfigLoadResponse)
async def load_config(file: UploadFile = File(...)):
    """加载 UI 配置"""
    try:
        content = await file.read()
        config_data = json.loads(content.decode("utf-8"))

        return ConfigLoadResponse(
            success=True,
            message=f"Successfully loaded config: {file.filename}",
            config=config_data
        )
    except Exception as e:
        return ConfigLoadResponse(
            success=False,
            message=f"Failed to load config: {str(e)}",
            config={}
        )

@app.get("/api/save-config", response_model=ConfigSaveResponse)
async def save_config():
    """保存 UI 配置"""
    try:
        config_name = datetime.now().strftime("%Y%m%d-%H%M%S")
        config_path = os.path.join(SETTINGS_SAVE_DIR, f"{config_name}.json")

        # 这里需要获取当前 UI 组件的状态
        # 目前先返回简单的响应
        with open(config_path, "w") as fw:
            json.dump({"placeholder": "config data"}, fw, indent=4)

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
        # 这里应该从 webui_manager 获取实际设置
        default_settings = AgentSettings()
        return {
            "success": True,
            "settings": default_settings.model_dump()
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent-settings")
async def update_agent_settings(settings: AgentSettings):
    """更新代理设置"""
    try:
        # 这里应该保存到 webui_manager 和配置
        return {
            "success": True,
            "message": "Agent settings updated successfully",
            "settings": settings.model_dump()
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
        default_settings = BrowserSettings()
        return {
            "success": True,
            "settings": default_settings.model_dump()
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/browser-settings")
async def update_browser_settings(settings: BrowserSettings):
    """更新浏览器设置"""
    try:
        return {
            "success": True,
            "message": "Browser settings updated successfully",
            "settings": settings.model_dump()
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
async def run_agent(data: BrowserUseAgentRequest):
    """运行代理"""
    try:
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        return {
            "success": True,
            "task_id": task_id,
            "message": "Agent started successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/stop")
async def stop_agent(task_id: str = Form(...)):
    """停止代理"""
    try:
        return {
            "success": True,
            "message": "Agent stopped successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/pause")
async def pause_agent(task_id: str = Form(...)):
    """暂停代理"""
    try:
        return {
            "success": True,
            "message": "Agent paused"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/resume")
async def resume_agent(task_id: str = Form(...)):
    """恢复代理"""
    try:
        return {
            "success": True,
            "message": "Agent resumed"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.get("/api/agent/status")
async def get_agent_status(task_id: str):
    """获取代理状态"""
    try:
        return {
            "success": True,
            "task_id": task_id,
            "status": "running",
            "chat_history": [],
            "browser_view": "",
            "is_waiting_for_help": False,
            "task_outputs": False
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/agent/respond")
async def respond_to_agent(task_id: str = Form(...), message: str = Form(...)):
    """发送用户响应"""
    try:
        return {
            "success": True,
            "message": "Response received"
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
async def run_deep_research(data: DeepResearchRequest):
    """运行深度研究"""
    try:
        task_id = datetime.now().strftime("%Y%m%d%H%M%S")
        return {
            "success": True,
            "task_id": task_id,
            "message": "Deep research started"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.post("/api/deep-research/stop")
async def stop_deep_research(task_id: str = Form(...)):
    """停止深度研究"""
    try:
        return {
            "success": True,
            "message": "Deep research stopped"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

@app.get("/api/deep-research/report")
async def get_deep_research_report(task_id: str):
    """获取研究报告"""
    try:
        report_content = "# Research Report\n\nThis is a placeholder report."
        return {
            "success": True,
            "task_id": task_id,
            "report": report_content,
            "file_path": f"/tmp/{task_id}_report.md"
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=7788)