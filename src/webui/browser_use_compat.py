"""
browser-use 兼容性模块
提供浏览器状态的兼容层
"""

# 检查 BrowserState 是否可用
try:
    from browser_use.browser.views import BrowserState
except ImportError:
    # 创建一个简单的兼容类
    class BrowserState:
        """浏览器状态兼容类"""
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

# 检查 AgentHistoryList 等是否可用
try:
    from browser_use.agent.views import AgentHistoryList, AgentOutput
except ImportError:
    # 创建兼容类
    from pydantic import BaseModel
    from typing import Any, List, Optional

    class AgentOutput(BaseModel):
        """Agent输出兼容类"""
        action: Any = None
        current_state: Any = None

    class AgentHistoryList(BaseModel):
        """Agent历史列表兼容类"""
        history: List[Any] = []

        def final_result(self) -> Any:
            return None

        def total_duration_seconds(self) -> float:
            return 0.0

        def total_input_tokens(self) -> int:
            return 0

        def errors(self) -> List[Any]:
            return []

# 导出所有可用的类
__all__ = ['BrowserState', 'AgentHistoryList', 'AgentOutput']