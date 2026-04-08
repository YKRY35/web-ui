import asyncio
import logging
import os
from typing import Optional, Dict, Any

from browser_use.browser import BrowserSession, BrowserProfile
from browser_use.utils import time_execution_async
from .custom_context import CustomBrowserContext

logger = logging.getLogger(__name__)


class CustomBrowser(BrowserSession):
    """Custom BrowserSession for web-ui with enhanced configuration."""

    def __init__(self, config: Optional[BrowserProfile] = None, **kwargs):
        """Initialize custom browser with optional configuration."""
        # Create a BrowserProfile if not provided
        if config is None:
            config = BrowserProfile()

        # Initialize BrowserSession with the profile
        super().__init__(browser_profile=config, **kwargs)

        # Store the profile for easy access
        self.config = config

    async def new_context(self, config: Optional[BrowserProfile] = None) -> CustomBrowserContext:
        """Create a browser context with custom configuration."""
        # Use the browser's profile or the provided config
        browser_config = self.config
        if config is not None:
            browser_config = config

        # Create a context configuration from the profile
        context_config = browser_config.model_dump()

        return CustomBrowserContext(config=browser_config, browser=self)

    async def _setup_builtin_browser(self, playwright):
        """Setup the Playwright browser instance."""
        # This method is no longer needed in the new version
        # The BrowserSession handles this internally
        pass

    def get_window_size(self) -> Dict[str, int]:
        """Get the configured window size."""
        return {
            'width': self.config.new_context_config.window_width if hasattr(self.config, 'new_context_config') else 1920,
            'height': self.config.new_context_config.window_height if hasattr(self.config, 'new_context_config') else 1080
        }

    def get_chrome_args(self) -> list[str]:
        """Get Chrome arguments for the browser."""
        args = []

        # Add remote debugging port
        if self.config.chrome_remote_debugging_port:
            args.append(f'--remote-debugging-port={self.config.chrome_remote_debugging_port}')

        # Add headless mode
        if self.config.headless:
            args.append('--headless')

        # Add other browser arguments
        if self.config.extra_browser_args:
            args.extend(self.config.extra_browser_args)

        return args

    async def take_screenshot(self) -> str:
        """Take a screenshot of the current page."""
        if not self.browser_profile:
            raise ValueError("Browser profile not initialized")

        # Use the browser session's screenshot method
        return await self.take_screenshot()  # This will be handled by BrowserSession

    async def get_dom_element_by_index(self, index: int) -> Any:
        """Get DOM element by index."""
        if not self.browser_profile:
            raise ValueError("Browser profile not initialized")

        # Use the browser session's DOM methods
        return await self.get_dom_element_by_index(index)

    async def get_locate_element(self, element_info: Any) -> Any:
        """Locate an element."""
        if not self.browser_profile:
            raise ValueError("Browser profile not initialized")

        # Use the browser session's element location methods
        return await self.get_locate_element(element_info)