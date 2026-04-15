#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理 - Session 类
封装单个会话的所有资源和状态
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import asyncio
import logging
from dataclasses import dataclass, field

from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class Session:
    """
    会话数据类，封装单个会话的所有资源和状态

    每个会话对应前端的一个 tab 页，包含：
    - 会话级 WebUIManager（管理浏览器实例和任务）
    - WebSocket 连接列表（事件推送和屏幕流）
    - 心跳检测状态
    """

    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    manager: Optional[Any] = None  # WebuiManager 实例，避免循环导入
    websockets: List[WebSocket] = field(default_factory=list)
    screen_websockets: List[WebSocket] = field(default_factory=list)
    is_active: bool = True

    def __post_init__(self):
        """初始化会话级的 WebUIManager（延迟导入避免循环依赖）"""
        if self.manager is None:
            from src.webui.webui_manager import WebuiManager
            self.manager = WebuiManager(
                ws_broadcast_func=self._broadcast_to_websockets,
                screen_broadcast_func=self._broadcast_to_screen_websockets,
                session_id=self.session_id
            )

    async def update_heartbeat(self):
        """更新心跳时间"""
        self.last_heartbeat = datetime.now()
        logger.debug(f"Session {self.session_id} heartbeat updated")

    def is_expired(self, timeout_seconds: int = 60) -> bool:
        """
        检查会话是否过期

        Args:
            timeout_seconds: 心跳超时时间（秒）

        Returns:
            True 如果会话已过期或已失效
        """
        if not self.is_active:
            return True

        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed > timeout_seconds

    async def cleanup(self):
        """
        清理会话资源

        执行清理步骤：
        1. 标记会话为非活跃状态
        2. 停止运行中的任务
        3. 关闭浏览器实例
        4. 关闭所有 WebSocket 连接
        """
        if not self.is_active:
            return

        logger.info(f"Cleaning up session: {self.session_id}")
        self.is_active = False

        # 1. 停止运行中的任务
        if self.manager:
            try:
                if hasattr(self.manager, 'bu_is_running') and self.manager.bu_is_running:
                    logger.info(f"Stopping running agent for session {self.session_id}")
                    await self.manager.stop_browser_use_agent()
            except Exception as e:
                logger.error(f"Error stopping agent for session {self.session_id}: {e}")

            # 2. 关闭浏览器实例
            if hasattr(self.manager, 'bu_browser_session') and self.manager.bu_browser_session:
                try:
                    logger.info(f"Closing browser for session {self.session_id}")
                    await self.manager.bu_browser_session.close()
                except Exception as e:
                    logger.error(f"Error closing browser for session {self.session_id}: {e}")

        # 3. 关闭所有 WebSocket 连接（事件推送）
        for ws in self.websockets:
            try:
                await ws.close()
            except Exception:
                pass

        # 4. 关闭所有屏幕流 WebSocket 连接
        for ws in self.screen_websockets:
            try:
                await ws.close()
            except Exception:
                pass

        # 清空连接列表
        self.websockets.clear()
        self.screen_websockets.clear()

        logger.info(f"Session {self.session_id} cleaned up successfully")

    async def _broadcast_to_websockets(self, message: dict):
        """
        向该会话的所有 WebSocket 广播消息

        Args:
            message: 要广播的消息字典
        """
        disconnected = []

        for ws in self.websockets:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send message to websocket: {e}")
                disconnected.append(ws)

        # 移除断开的连接
        for ws in disconnected:
            if ws in self.websockets:
                self.websockets.remove(ws)

    async def _broadcast_to_screen_websockets(self, frame_bytes: bytes):
        """
        向该会话的所有屏幕流 WebSocket 广播帧数据

        Args:
            frame_bytes: 要广播的帧字节数据
        """
        if not self.screen_websockets:
            return

        disconnected = []

        for ws in self.screen_websockets:
            try:
                await ws.send_bytes(frame_bytes)
            except Exception as e:
                logger.debug(f"Failed to send frame to screen websocket: {e}")
                disconnected.append(ws)

        # 移除断开的连接
        for ws in disconnected:
            if ws in self.screen_websockets:
                self.screen_websockets.remove(ws)

    async def add_websocket(self, websocket: WebSocket):
        """添加 WebSocket 连接到会话"""
        self.websockets.append(websocket)
        logger.debug(f"WebSocket added to session {self.session_id}, total: {len(self.websockets)}")

    def remove_websocket(self, websocket: WebSocket):
        """从会话移除 WebSocket 连接"""
        if websocket in self.websockets:
            self.websockets.remove(websocket)
            logger.debug(f"WebSocket removed from session {self.session_id}, remaining: {len(self.websockets)}")

    async def add_screen_websocket(self, websocket: WebSocket):
        """添加屏幕流 WebSocket 连接到会话"""
        self.screen_websockets.append(websocket)
        logger.debug(f"Screen WebSocket added to session {self.session_id}, total: {len(self.screen_websockets)}")

    def remove_screen_websocket(self, websocket: WebSocket):
        """从会话移除屏幕流 WebSocket 连接"""
        if websocket in self.screen_websockets:
            self.screen_websockets.remove(websocket)
            logger.debug(f"Screen WebSocket removed from session {self.session_id}, remaining: {len(self.screen_websockets)}")

    def get_info(self) -> Dict[str, Any]:
        """获取会话信息摘要"""
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "is_active": self.is_active,
            "websocket_count": len(self.websockets),
            "screen_websocket_count": len(self.screen_websockets),
            "has_browser": self.manager and hasattr(self.manager, 'bu_browser_session') and self.manager.bu_browser_session is not None,
            "is_running": self.manager and hasattr(self.manager, 'bu_is_running') and self.manager.bu_is_running
        }
