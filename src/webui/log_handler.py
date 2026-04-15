"""
WebSocket 日志处理器
将 Python logging 输出转发到 WebSocket 客户端
"""
import logging


class WebSocketLogHandler(logging.Handler):
    """
    自定义日志处理器，将日志消息发送到 WebSocket
    """

    def __init__(self, webui_manager):
        """
        初始化日志处理器

        Args:
            webui_manager: WebuiManager 实例，用于调用 broadcast_log 方法
        """
        super().__init__()
        self.webui_manager = webui_manager

        # 要忽略的日志器名称（避免推送过多无用日志）
        self.ignored_loggers = {
            'websockets.client',
            'cdp_use.cdp',
            'urllib3',
            'asyncio'
        }

    def emit(self, record):
        """
        发送日志记录到 WebSocket

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

            # 发送到 WebSocket
            # broadcast_log 内部会处理异步调用，确保不会阻塞
            self.webui_manager.broadcast_log(level, msg)

        except Exception:
            # 忽略错误，避免影响主程序运行
            self.handleError(record)


