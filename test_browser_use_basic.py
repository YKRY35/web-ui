"""
测试 browser-use 基本功能
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'browser-use'))

def test_basic_imports():
    """测试基本导入"""
    try:
        print("1. Testing browser-use basic imports...")

        from browser_use.agent.service import Agent
        print("   ✓ Agent imported")

        from browser_use.browser.session import BrowserSession
        print("   ✓ BrowserSession imported")

        from browser_use.controller import Controller
        print("   ✓ Controller imported")

        from browser_use.llm import ChatOpenAI
        print("   ✓ ChatOpenAI imported")

        from browser_use.llm import ChatAnthropic
        print("   ✓ ChatAnthropic imported")

        from browser_use.llm import ChatGoogle
        print("   ✓ ChatGoogle imported")

        from browser_use.llm import ChatOllama
        print("   ✓ ChatOllama imported")

        from browser_use.llm import ChatMistral
        print("   ✓ ChatMistral imported")

        from browser_use.browser.profile import BrowserProfile
        print("   ✓ BrowserProfile imported")

        from browser_use.agent.views import AgentHistoryList, AgentOutput
        print("   ✓ Agent views imported")

        from browser_use.browser.views import BrowserState
        print("   ✓ BrowserState imported")

        return True
    except Exception as e:
        print(f"   ✗ {e}")
        return False

if __name__ == "__main__":
    print("Starting browser-use compatibility test...\n")

    success = test_basic_imports()

    if success:
        print("\n✓ All basic imports successful!")
    else:
        print("\n✗ Some imports failed")