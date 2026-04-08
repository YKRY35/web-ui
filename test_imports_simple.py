#!/usr/bin/env python3
"""
测试 browser-use 集成 - 简化版本
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'browser-use'))

def test_basic_imports():
    """测试基本导入"""
    try:
        print("Testing browser-use basic imports...")
        from browser_use.agent.service import Agent
        print("SUCCESS: Agent imported")

        from browser_use.browser.session import BrowserSession
        print("SUCCESS: BrowserSession imported")

        from browser_use.controller import Tools as BrowserUseTools
        print("SUCCESS: BrowserUseTools imported")

        from browser_use.llm import ChatOpenAI, ChatAnthropic, ChatGoogle, ChatOllama, ChatMistral
        print("SUCCESS: LLM classes imported")

        return True
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_webui_imports():
    """测试 webui 导入"""
    try:
        print("\nTesting webui imports...")
        from src.webui.webui_manager import WebuiManager
        print("SUCCESS: WebuiManager imported")
        return True
    except Exception as e:
        print(f"FAILED: WebuiManager: {e}")
        return False

if __name__ == "__main__":
    print("Starting browser-use integration test...\n")

    success1 = test_basic_imports()
    success2 = test_webui_imports()

    if success1 and success2:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests FAILED")