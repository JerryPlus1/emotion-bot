#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
本地模型调用模块

使用 train_model 训练好的模型进行推理。
支持 LoRA 和合并后的模型。
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 模型路径配置
MODEL_PATH = "/root/autodl-tmp/model/qwen3-1.7b"
LORA_PATH = Path(__file__).parent.parent / "train_model" / "output" / "bestie_chat_lora"
MERGED_PATH = Path(__file__).parent.parent / "train_model" / "export_model" / "bestie_chat_lora_merged"


class LocalModel:
    """
    本地模型推理类
    
    使用 Qwen3-1.7B + LoRA 或合并模型进行推理。
    """
    
    _instance: Optional["LocalModel"] = None
    
    def __init__(self, use_merged: bool = True):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.use_merged = use_merged
        
        self._load_model()
    
    @classmethod
    def get_instance(cls, use_merged: bool = True) -> "LocalModel":
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(use_merged=use_merged)
        return cls._instance
    
    def _load_model(self):
        """加载模型"""
        print("=" * 60)
        print("加载本地模型...")
        print("=" * 60)
        
        # 确定模型路径
        if self.use_merged and MERGED_PATH.exists():
            model_path = str(MERGED_PATH)
            print(f"使用合并模型: {model_path}")
        elif LORA_PATH.exists():
            model_path = MODEL_PATH
            print(f"使用基础模型 + LoRA: {model_path}")
            print(f"LoRA 权重: {LORA_PATH}")
        else:
            model_path = MODEL_PATH
            print(f"警告: LoRA 权重不存在，使用基础模型")
            print(f"基础模型: {model_path}")
        
        # 加载 tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_path,
            trust_remote_code=True
        )
        
        # 加载模型
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            device_map="auto",
            torch_dtype=torch.bfloat16,
            trust_remote_code=True,
        )
        
        # 加载 LoRA 权重（如果使用）
        if not self.use_merged and not MERGED_PATH.exists() and LORA_PATH.exists():
            from peft import PeftModel
            self.model = PeftModel.from_pretrained(
                self.model,
                str(LORA_PATH),
            )
            print("LoRA 权重已加载")
        
        self.model.eval()
        print(f"模型加载完成，设备: {self.device}")
        print("=" * 60)
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
    ) -> str:
        """
        对话生成
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词（会覆盖 messages 中的 system）
            max_new_tokens: 最大生成 token 数
            temperature: 温度参数
            top_p: top_p 采样
            top_k: top_k 采样
            repetition_penalty: 重复惩罚
        
        Returns:
            生成的回复文本
        """
        import re
        
        # 合并系统提示词
        if system_prompt:
            final_messages = [{"role": "system", "content": system_prompt}]
            # 过滤掉原有的 system 消息
            final_messages.extend([m for m in messages if m.get("role") != "system"])
        else:
            final_messages = messages
        
        # 构建输入文本
        input_text = self._build_prompt(final_messages)
        
        # 添加 /no_think 指令
        input_text += " /no_think"
        
        # Tokenize
        inputs = self.tokenizer(
            [input_text],
            return_tensors="pt",
            padding=True,
        ).to(self.device)
        
        # 生成
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
                repetition_penalty=repetition_penalty,
                do_sample=True,
                pad_token_id=self.tokenizer.pad_token_id or self.tokenizer.eos_token_id,
            )
        
        # 解码
        output_text = self.tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True,
        )
        
        # 移除思考过程
        output_text = self._extract_answer(output_text)
        
        return output_text.strip()
    
    def _build_prompt(self, messages: List[Dict[str, str]]) -> str:
        """构建提示词"""
        # Qwen3 格式
        prompt_parts = []
        
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"<|system|>\n{content}")
            elif role == "user":
                prompt_parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                prompt_parts.append(f"<|assistant|>\n{content}")
        
        prompt_parts.append("<|assistant|>\n")
        
        return "\n".join(prompt_parts)
    
    def _extract_answer(self, text: str) -> str:
        """提取实际回复内容"""
        import re
        
        # 移除<think>...</think>标签对
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        text = re.sub(r'<think>', '', text)
        text = re.sub(r'</think>', '', text)

        return text.strip()


def get_local_model(use_merged: bool = True) -> LocalModel:
    """获取本地模型实例"""
    return LocalModel.get_instance(use_merged=use_merged)


# ═══════════════════════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("本地模型测试")
    print("=" * 60)
    
    # 测试加载
    model = get_local_model()
    
    # 测试对话
    messages = [
        {"role": "user", "content": "你好，今天心情怎么样？"}
    ]
    
    print("\n测试对话:")
    print("用户: 你好，今天心情怎么样？")
    
    response = model.chat(
        messages,
        system_prompt="你是一个温柔可爱的AI闺蜜。",
        temperature=0.8,
    )
    
    print(f"模型: {response}")
