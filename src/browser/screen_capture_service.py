"""
高性能浏览器画面捕获服务
High-performance Browser Screen Capture Service

提供极致性能的浏览器画面捕获功能，专门为实时画面传输优化：
- 使用 CDP (Chrome DevTools Protocol) 直接捕获
- 优化的 JPEG 压缩（70-80% 质量）
- 动态帧率调整
- 自动检测浏览器状态

This service provides extremely fast browser screen capture optimized for real-time streaming:
- Direct CDP (Chrome DevTools Protocol) capture
- Optimized JPEG compression (70-80% quality)
- Dynamic frame rate adjustment
- Automatic browser state detection
"""

import asyncio
import base64
import logging
from typing import Optional

from browser_use.browser.session import BrowserSession
from browser_use.browser.watchdogs.screenshot_watchdog import ScreenshotWatchdog
from browser_use.browser.events import ScreenshotEvent


logger = logging.getLogger(__name__)


class ScreenCaptureService:
    """
    高性能浏览器画面捕获服务

    High-performance browser screen capture service.
    """

    def __init__(
        self,
        browser_session: BrowserSession,
        broadcast_func,
        quality: int = 75,
        max_fps: int = 15
    ):
        """
        初始化捕获服务

        Args:
            browser_session: BrowserSession 实例
            broadcast_func: WebSocket 广播函数
            quality: JPEG 质量（0-100），建议 70-80
            max_fps: 最大帧率（fps），建议 15-30
        """
        self.browser_session = browser_session
        self.broadcast_func = broadcast_func
        self.quality = quality
        self.max_fps = max_fps
        self.frame_interval = 1.0 / max_fps

        # 运行状态
        self.is_running = False
        self.capture_task: Optional[asyncio.Task] = None

        # 性能统计
        self._frame_count = 0
        self._last_frame_time = 0.0

    async def start_capture(self):
        """开始画面捕获任务"""
        if self.is_running:
            logger.warning("Screen capture service already running")
            return

        logger.info(f"Starting screen capture service (quality: {self.quality}, max_fps: {self.max_fps})")

        self.is_running = True
        self.capture_task = asyncio.create_task(self._capture_loop())

    async def stop_capture(self):
        """停止画面捕获任务"""
        if not self.is_running:
            return

        logger.info("Stopping screen capture service")

        self.is_running = False
        if self.capture_task:
            self.capture_task.cancel()
            try:
                await self.capture_task
            except asyncio.CancelledError:
                pass
            self.capture_task = None

    async def _capture_loop(self):
        """内部捕获循环"""
        logger.debug("Capture loop started")

        while self.is_running:
            try:
                start_time = asyncio.get_event_loop().time()

                # 检查浏览器会话是否仍然有效
                if not self._is_browser_valid():
                    await asyncio.sleep(0.5)
                    continue

                # 捕获画面
                frame_data = await self._capture_frame()
                if frame_data:
                    await self._send_frame(frame_data)
                    self._frame_count += 1

                # 计算并调整延迟以维持目标帧率
                elapsed = asyncio.get_event_loop().time() - start_time
                delay = max(0.0, self.frame_interval - elapsed)

                if delay > 0:
                    await asyncio.sleep(delay)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Capture loop error: {e}", exc_info=True)
                await asyncio.sleep(0.5)

        logger.debug("Capture loop stopped")

    def _is_browser_valid(self) -> bool:
        """检查浏览器会话是否有效"""
        try:
            # 简单的有效性检查
            if not self.browser_session:
                return False

            # 检查是否有页面目标
            page_targets = self.browser_session.get_page_targets()
            return len(page_targets) > 0

        except Exception as e:
            logger.warning(f"Browser validity check failed: {e}")
            return False

    async def _capture_frame(self) -> Optional[str]:
        """
        捕获单个帧

        Returns:
            base64 编码的 JPEG 图像字符串，或 None
        """
        try:
            # 使用 BrowserSession 的 take_screenshot 方法
            screenshot_bytes = await self.browser_session.take_screenshot(
                format='jpeg',
                quality=self.quality,
                full_page=False  # 只捕获视口内容，提高性能
            )

            return base64.b64encode(screenshot_bytes).decode('utf-8')

        except Exception as e:
            logger.error(f"Frame capture failed: {e}")
            return None

    async def _send_frame(self, frame_data: str):
        """
        发送帧数据到客户端

        Args:
            frame_data: base64 编码的图像数据
        """
        try:
            message = {
                "type": "frame",
                "data": {
                    "image": frame_data,
                    "timestamp": asyncio.get_event_loop().time(),
                    "frame_count": self._frame_count
                }
            }

            await self.broadcast_func(message)
        except Exception as e:
            logger.error(f"Frame send failed: {e}")

    @property
    def frame_count(self) -> int:
        """获取已捕获的帧数"""
        return self._frame_count

    def __del__(self):
        """资源清理"""
        if self.is_running:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.stop_capture())
            except Exception:
                pass
