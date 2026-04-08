"""
测试 browser-use LLM 集成
"""
import os
import sys

# 添加 browser-use 到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'browser-use'))

def test_llm_import():
    try:
        # 测试 browser-use LLM 导入
        from browser_use.llm import ChatOpenAI, ChatAnthropic, ChatGoogle, ChatOllama, ChatMistral
        from browser_use.llm.base import BaseChatModel
        from browser_use.agent.service import Agent
        from browser_use.browser import Browser
        from browser_use.browser.session import BrowserSession
        from browser_use.controller import Tools as BrowserUseTools
        print("✓ 所有 browser-use 模块导入成功")

        # 测试 LLM 创建
        llm = ChatOpenAI(model="gpt-4o", temperature=0.0)
        print("✓ ChatOpenAI 创建成功")

        # 测试其他 LLM
        llm2 = ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=0.0)
        print("✓ ChatAnthropic 创建成功")

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_webui_imports():
    try:
        # 测试 webui 模块
        from src.webui.webui_manager import WebuiManager
        print("✓ WebuiManager 导入成功")
        return True
    except Exception as e:
        print(f"✗ WebuiManager 导入失败: {e}")
        return False

if __name__ == "__main__":
    print("测试 browser-use LLM 集成...")
    success1 = test_llm_import()
    success2 = test_webui_import()

    if success1 and success2:
        print("\n✓ 所有测试通过!")
    else:
        print("\n✗ 测试失败")