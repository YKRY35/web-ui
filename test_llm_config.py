#!/usr/bin/env python3
"""
测试 LLM 配置和 API key 传递
"""
import sys
import os

# 添加路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'browser-use'))


def test_api_key_passing():
    """测试 API key 是如何传递的"""
    print("Testing LLM class initialization in browser-use...")

    from browser_use.llm import ChatOpenAI

    print("\n1. Testing ChatOpenAI with explicit api_key:")
    llm = ChatOpenAI(
        model='gpt-4o',
        temperature=0.0,
        api_key='test_key_123'
    )
    print(f"   Created LLM: {llm}")
    print(f"   Has api_key attribute: {'api_key' in dir(llm)}")
    if 'api_key' in dir(llm):
        print(f"   api_key value: {llm.api_key}")
    print(f"   Has _client: {'_client' in dir(llm)}")

    print("\n2. Testing with config dict (simulating web-ui):")
    config = {
        'llm_provider': 'openai',
        'model_name': 'gpt-4o',
        'temperature': 0.0,
        'api_key': 'config_key_456',
        'base_url': None
    }

    print(f"   Config: {config}")

    # 模拟 webui 的 _create_llm_from_config
    provider = config.get('llm_provider', 'openai')
    model_name = config.get('model_name', 'gpt-4o')
    temperature = config.get('temperature', 0.0)
    base_url = config.get('base_url')
    api_key = config.get('api_key')

    kwargs = {
        'model': model_name,
        'temperature': temperature,
    }

    if base_url:
        kwargs['base_url'] = base_url
    if api_key:
        kwargs['api_key'] = api_key

    print(f"   Kwargs: {kwargs}")

    llm2 = ChatOpenAI(**kwargs)
    print(f"   Created LLM with kwargs: {llm2}")
    print(f"   api_key in dir: {'api_key' in dir(llm2)}")
    if 'api_key' in dir(llm2):
        print(f"   api_key value: {llm2.api_key}")


if __name__ == "__main__":
    test_api_key_passing()