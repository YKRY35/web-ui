import asyncio
import logging
from typing import Optional, Dict, Any

from browser_use.browser import BrowserSession
from browser_use.utils import time_execution_async

logger = logging.getLogger(__name__)


class CustomBrowserContext:
    """Custom BrowserContext for web-ui with enhanced functionality."""

    def __init__(self, config: BrowserSession, browser: BrowserSession):
        """Initialize custom browser context."""
        self.config = config
        self.browser = browser

    async def take_screenshot(self) -> str:
        """Take a screenshot of the current page."""
        if not self.browser:
            raise ValueError("Browser not initialized")

        # Use the browser session's screenshot method
        return await self.browser.take_screenshot()

    async def get_dom_element_by_index(self, index: int) -> Any:
        """Get DOM element by index."""
        if not self.browser:
            raise ValueError("Browser not initialized")

        # Use the browser session's DOM methods
        return await self.browser.get_dom_element_by_index(index)

    async def get_locate_element(self, element_info: Any) -> Any:
        """Locate an element."""
        if not self.browser:
            raise ValueError("Browser not initialized")

        # Use the browser session's element location methods
        return await self.browser.get_locate_element(element_info)

    def get_state(self) -> Dict[str, Any]:
        """Get the current browser state."""
        if not self.browser:
            raise ValueError("Browser not initialized")

        # Return a simplified state representation
        return {
            'url': self.browser.current_url,
            'title': self.browser.title,
            'page_count': len(self.browser.pages),
            'is_headless': self.config.headless if hasattr(self.config, 'headless') else False
        }

    async def close(self) -> None:
        """Close the browser context."""
        if self.browser:
            await self.browser.close()
            self.browser = None
            self.config = None

    def __repr__(self) -> str:
        return f"CustomBrowserContext(browser={self.browser}, config={self.config})"