"""LLM 服务 - 本地模型版本。"""

import sys
from pathlib import Path
from typing import Optional, List, Dict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from logger import debug, info, error


class LLMService:
    """本地 LLM 服务"""

    _instance: Optional["LLMService"] = None

    def __init__(self):
        self.local_model = None
        self._init_local_model()

    @classmethod
    def get_instance(cls) -> "LLMService":
        """获取单例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_local_model(self) -> None:
        """初始化本地模型"""
        try:
            from local_model import get_local_model
            self.local_model = get_local_model()
            info("LLM服务: 本地模型已加载")
        except Exception as e:
            error(f"LLM服务: 本地模型加载失败: {e}")
            self.local_model = None

    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> Optional[str]:
        """聊天接口"""
        if not self.local_model:
            error("本地模型未加载")
            return None

        try:
            return self.local_model.chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=temperature,
                max_new_tokens=max_tokens,
            )
        except Exception as e:
            error(f"本地模型调用失败: {e}")
            return None

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Optional[str]:
        """生成回复（单轮）"""
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, system_prompt, temperature, max_tokens)


def get_llm_service() -> LLMService:
    """获取LLM服务实例"""
    return LLMService.get_instance()
