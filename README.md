# emotion-bot

一个基于本地 GGUF 模型的情感陪伴机器人，支持 RAG 检索、长期记忆、多用户画像、主动对话触发和浏览器 TTS 输出。

## 能力

- 使用 `model/qwen-finetune-download/qwen35-2b-sft-merged-q4_k_m.gguf` 作为本地对话模型。
- 将聊天消息、长期记忆、用户画像和知识库分片保存到 SQLite。
- 支持多用户，通过 `user_id` 隔离聊天历史和记忆。
- 支持记忆模式：自动、始终、关闭。
- 支持长期记忆、聊天历史、知识库三类上下文权重。
- 支持时间、场景、长时间未聊天等主动对话触发。
- 前端支持浏览器 TTS 朗读模型回复。

## 快速开始

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

确认模型文件存在：

```text
model/qwen-finetune-download/qwen35-2b-sft-merged-q4_k_m.gguf
```

启动服务：

```bash
uvicorn emotion_bot.main:app --app-dir src --host 127.0.0.1 --port 8000
```

浏览器打开：

```text
http://127.0.0.1:8000
```

首次调试前端和记忆链路时，可以先使用 mock 模式避免加载大模型：

```bash
$env:EMOTION_BOT_LLM_BACKEND="mock"
uvicorn emotion_bot.main:app --app-dir src --host 127.0.0.1 --port 8000
```

更多说明见 [docs/usage.md](docs/usage.md)。
