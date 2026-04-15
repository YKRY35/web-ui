"""
WebSocket 日志处理器
将 Python logging 输出转发到 WebSocket 客户端
"""
import logging
import asyncio


class WebSocketLogHandler(logging.Handler):
    """
    自定义日志处理器，将日志消息发送到所有活跃会话的 WebSocket
    """

    def __init__(self, session_manager):
        """
        初始化日志处理器

        Args:
            session_manager: SessionManager 实例，用于向所有会话广播日志
        """
        super().__init__()
        self.session_manager = session_manager

        # 要忽略的日志器名称（避免推送过多无用日志）
        self.ignored_loggers = {
            'websockets.client',
            'cdp_use.cdp',
            'urllib3',
            'asyncio'
        }

    def emit(self, record):
        """
        发送日志记录到所有活跃会话的 WebSocket

        Args:
            record: LogRecord 日志记录对象
        """
        try:
            # 过滤掉不需要的日志
            if record.name in self.ignored_loggers:
                return

            # 过滤掉过于详细的调试日志（除非是浏览器操作相关的）
            if record.levelno == logging.DEBUG:
                # 只保留 browser_use.agent 和 browser_use.browser.session 的 DEBUG 日志
                if not (record.name.startswith('browser_use.agent') or
                        record.name.startswith('browser_use.browser.session')):
                    return

            # 格式化日志消息
            msg = self.format(record)

            # 映射日志级别
            level_map = {
                logging.DEBUG: 'debug',
                logging.INFO: 'info',
                logging.WARNING: 'warning',
                logging.ERROR: 'error',
                logging.CRITICAL: 'error'
            }
            level = level_map.get(record.levelno, 'info')

            # 向所有活跃会话广播日志
            self._broadcast_to_all_sessions(level, msg)

        except Exception:
            # 忽略错误，避免影响主程序运行
            self.handleError(record)

    def _broadcast_to_all_sessions(self, level: str, message: str):
        """
        向所有活跃会话广播日志消息

        Args:
            level: 日志级别
            message: 日志消息
        """
        # 创建广播任务
        async def broadcast_task():
            for session in self.session_manager.sessions.values():
                if session.is_active and session.websockets:
                    try:
                        await session._broadcast_to_websockets({
                            "type": "log",
                            "data": {
                                "level": level,
                                "message": message
                            }
                        })
                    except Exception:
                        pass  # 忽略单个会话的广播错误

        # 在事件循环中调度任务
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(broadcast_task())
        except Exception:
            pass  # 如果无法获取事件循环，静默失败

