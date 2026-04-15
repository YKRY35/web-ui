"""
LLM 日志包装器
拦截 LLM 调用，记录输入输出到 WebSocket
"""
from typing import Any, List
from browser_use.llm.messages import BaseMessage
from browser_use.llm.views import ChatInvokeCompletion


class LLMLogWrapper:
    """
    LLM 包装器，拦截 ainvoke 调用并记录日志
    """

    def __init__(self, llm, webui_manager):
        """
        初始化包装器

        Args:
            llm: 原始 LLM 实例
            webui_manager: WebuiManager 实例
        """
        self._llm = llm
        self._webui_manager = webui_manager

    async def ainvoke(self, messages: List[BaseMessage], output_format: Any = None, **kwargs: Any) -> ChatInvokeCompletion:
        """
        拦截 ainvoke 调用，记录输入输出

        Args:
            messages: 输入消息列表
            output_format: 输出格式
            **kwargs: 其他参数

        Returns:
            LLM 响应
        """
        # 记录输入
        try:
            for i, message in enumerate(messages):
                # 提取消息内容
                content = getattr(message, 'content', str(message))
                if isinstance(content, str):
                    # 截断过长的输入
                    display_content = content[:300] + "..." if len(content) > 300 else content
                    self._webui_manager.broadcast_llm_log(
                        level='info',
                        message=f"[Input {i+1}/{len(messages)}] [{message.__class__.__name__}] {display_content}",
                        log_type='input'
                    )
        except Exception as e:
            print(f"LLM log wrapper error (input logging): {e}")

        # 调用原始 LLM
        try:
            response = await self._llm.ainvoke(messages, output_format, **kwargs)
        except Exception as e:
            # 记录错误
            self._webui_manager.broadcast_llm_log(
                level='error',
                message=f"[Error] {str(e)}",
                log_type='error'
            )
            raise

        # 记录输出
        try:
            if hasattr(response, 'content'):
                # 提取输出内容
                output_content = response.content
                if isinstance(output_content, str):
                    # 截断过长的输出
                    display_output = output_content[:300] + "..." if len(output_content) > 300 else output_content
                    self._webui_manager.broadcast_llm_log(
                        level='info',
                        message=f"[Output] {display_output}",
                        log_type='output'
                    )
                elif hasattr(output_content, 'model_dump'):
                    # 如果是 Pydantic 模型，转为 JSON
                    import json
                    output_dict = output_content.model_dump()
                    output_str = json.dumps(output_dict, ensure_ascii=False, indent=2)
                    display_output = output_str[:500] + "..." if len(output_str) > 500 else output_str
                    self._webui_manager.broadcast_llm_log(
                        level='info',
                        message=f"[Output] {display_output}",
                        log_type='output'
                    )
        except Exception as e:
            print(f"LLM log wrapper error (output logging): {e}")

        return response

    def __getattr__(self, name):
        """
        代理所有其他属性到原始 LLM 对象

        Args:
            name: 属性名

        Returns:
            原始 LLM 的属性
        """
        return getattr(self._llm, name)

