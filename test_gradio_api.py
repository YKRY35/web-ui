#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Gradio API接口
"""
import requests
import json

BASE_URL = "http://127.0.0.1:7788"

def test_health():
    """测试健康检查"""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"GET / Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type')}")
        print("=" * 50)
    except Exception as e:
        print(f"Error: {e}")

def test_gradio_api():
    """测试Gradio API接口"""
    try:
        # 获取API配置
        response = requests.get(f"{BASE_URL}/config")
        if response.status_code == 200:
            print("Gradio Config:")
            print(json.dumps(response.json(), indent=2))
            print("=" * 50)
    except Exception as e:
        print(f"Error getting config: {e}")

def test_gradio_endpoints():
    """测试Gradio的各种端点"""
    endpoints = [
        "/",
        "/config",
        "/api",
        "/run",
        "/predict",
        "/queue",
    ]

    for endpoint in endpoints:
        try:
            url = f"{BASE_URL}{endpoint}"
            response = requests.get(url, timeout=5)
            print(f"GET {endpoint} - Status: {response.status_code}")
            if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        print(f"Keys: {list(data.keys())}")
                except:
                    pass
        except Exception as e:
            print(f"GET {endpoint} - Error: {e}")

    print("=" * 50)

if __name__ == "__main__":
    print("Testing Gradio API endpoints...")
    print(f"Base URL: {BASE_URL}")
    print("=" * 50)
    test_health()
    test_gradio_endpoints()
    test_gradio_api()