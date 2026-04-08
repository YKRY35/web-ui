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
        print("测试 browser-use 基本导入...")
        from browser_use.agent.service import Agent
        print("✓ Agent 导入成功")

        from browser_use.browser.session import BrowserSession
        print("✓ BrowserSession 导入成功")

        from browser_use.controller import Tools as BrowserUseTools
        print("✓ BrowserUseTools 导入成功")

        from browser_use.llm import ChatOpenAI, ChatAnthropic, ChatGoogle, ChatOllama, ChatMistral
        print("✓ LLM 类导入成功")

        return True
    except Exception as e:
        print(f"✗ 导入失败: {e}")
        return False

def test_webui_imports():
    """测试 webui 导入"""
    try:
        print("\n测试 webui 导入...")
        from src.webui.webui_manager import WebuiManager
        print("✓ WebuiManager 导入成功")
        return True
    except Exception as e:
        print(f"✗ WebuiManager 导入失败: {e}")
        return False

if __name__ == "__main__":
    print("开始测试 browser-use 集成...\n")

    success1 = test_basic_imports()
    success2 = test_webui_imports()

    if success1 and success2:
        print("\n✓ 所有测试通过!")
    else:
        print("\n✗ 测试失败")