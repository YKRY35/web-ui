#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
会话管理 - SessionManager 类
负责创建、查找、清理会话
"""
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime

from src.webui.session import Session

logger = logging.getLogger(__name__)


class SessionManager:
    """
    会话管理器，负责管理所有会话的生命周期

    主要职责：
    1. 创建和查找会话
    2. 定期清理过期会话
    3. 管理会话心跳超时
    """

    def __init__(self, heartbeat_timeout: int = 60, cleanup_interval: int = 30):
        """
        初始化会话管理器

        Args:
            heartbeat_timeout: 心跳超时时间（秒），默认60秒
            cleanup_interval: 清理任务运行间隔（秒），默认30秒
        """
        self.sessions: Dict[str, Session] = {}
        self.heartbeat_timeout = heartbeat_timeout
        self.cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

        logger.info(f"SessionManager initialized (timeout={heartbeat_timeout}s, interval={cleanup_interval}s)")

    async def start_cleanup_task(self):
        """启动后台清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("Session cleanup task started")

    async def stop_cleanup_task(self):
        """停止后台清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            logger.info("Session cleanup task stopped")

    async def _cleanup_loop(self):
        """定期清理过期会话的后台任务"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)

    async def get_or_create_session(self, session_id: str) -> Session:
        """
        获取或创建会话

        如果会话存在且活跃，返回现有会话
        如果会话不存在或已失效，创建新会话

        Args:
            session_id: 会话ID

        Returns:
            Session 实例
        """
        async with self._lock:
            # 检查会话是否存在且活跃
            if session_id in self.sessions and self.sessions[session_id].is_active:
                logger.debug(f"Returning existing session: {session_id}")
                return self.sessions[session_id]

            # 创建新会话
            session = Session(session_id=session_id)
            self.sessions[session_id] = session
            logger.info(f"Created new session: {session_id} (total sessions: {len(self.sessions)})")

            return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        获取会话（不自动创建）

        Args:
            session_id: 会话ID

        Returns:
            Session 实例，如果不存在返回 None
        """
        return self.sessions.get(session_id)

    async def remove_session(self, session_id: str):
        """
        移除会话并清理资源

        Args:
            session_id: 会话ID
        """
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                await session.cleanup()
                del self.sessions[session_id]
                logger.info(f"Removed session: {session_id} (remaining sessions: {len(self.sessions)})")

    async def cleanup_expired_sessions(self):
        """清理所有过期会话"""
        expired = []

        # 找出所有过期会话
        for session_id, session in self.sessions.items():
            if session.is_expired(self.heartbeat_timeout):
                expired.append(session_id)

        # 清理过期会话
        for session_id in expired:
            session = self.sessions.get(session_id)
            if session:
                elapsed = (datetime.now() - session.last_heartbeat).total_seconds()
                logger.warning(
                    f"Session {session_id} expired (no heartbeat for {elapsed:.1f}s, "
                    f"timeout={self.heartbeat_timeout}s)"
                )
                await self.remove_session(session_id)

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")

    async def cleanup_all_sessions(self):
        """清理所有会话（应用关闭时调用）"""
        logger.info(f"Cleaning up all {len(self.sessions)} sessions")
        session_ids = list(self.sessions.keys())

        for session_id in session_ids:
            await self.remove_session(session_id)

        logger.info("All sessions cleaned up")

    def get_all_session_info(self) -> List[Dict]:
        """获取所有会话的信息摘要"""
        return [session.get_info() for session in self.sessions.values() if session.is_active]

    def get_session_count(self) -> int:
        """获取活跃会话数量"""
        return sum(1 for session in self.sessions.values() if session.is_active)


# 全局会话管理器实例
session_manager = SessionManager(heartbeat_timeout=60, cleanup_interval=30)
