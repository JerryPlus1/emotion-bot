# Emotion Bot 使用文档

## 1. 项目结构

```text
src/emotion_bot/
  main.py          FastAPI 入口
  llm.py           GGUF / llama-cpp-python 模型适配
  chat.py          对话编排、RAG 上下文选择
  storage.py       SQLite 存储
  memory.py        长期记忆抽取和用户画像总结
  proactive.py     主动对话触发
  text_index.py    本地稀疏向量检索
  static/          前端页面
```

运行时数据默认写入：

```text
data/emotion_bot.sqlite3
```

## 2. 安装

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

`llama-cpp-python` 在不同机器上安装速度可能不同。如果本机有 CUDA、Metal 或其他加速需求，请按 `llama-cpp-python` 官方方式安装对应构建版本。

## 3. 模型

默认模型路径：

```text
model/qwen-finetune-download/qwen35-2b-sft-merged-q4_k_m.gguf
```

如果模型放在别的位置，修改 `.env`：

```text
EMOTION_BOT_MODEL_PATH=D:\path\to\model.gguf
```

## 4. 启动

真实模型模式：

```bash
uvicorn emotion_bot.main:app --app-dir src --host 127.0.0.1 --port 8000
```

调试模式：

```bash
$env:EMOTION_BOT_LLM_BACKEND="mock"
uvicorn emotion_bot.main:app --app-dir src --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000
```

## 5. 记忆与 RAG

前端左侧可以调整：

- 记忆模式：`自动`、`始终`、`关闭`
- 长期记忆权重
- 聊天历史权重
- 知识库权重

自动模式下，系统会根据当前消息与历史内容的相关度决定是否加入上下文；例如用户提到“上次”“之前”“还记得”“我喜欢”等内容时，更容易触发记忆召回。

长期记忆来自两部分：

- 所有聊天消息都会进入历史库，支持后续相关检索。
- 用户消息中的偏好、身份、计划、习惯、关系等会抽取成长期记忆，并自动汇总为用户画像。

## 6. 多用户

前端左侧的“用户”字段就是 `user_id`。不同 `user_id` 的画像、长期记忆、历史消息互相隔离。

API 调用示例：

```bash
curl -X POST http://127.0.0.1:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"alice\",\"message\":\"我喜欢晚上写代码，也想练习英语。\"}"
```

## 7. 知识库

前端右侧可以写入知识库文本。服务端会自动切分文本并建立本地稀疏向量索引。

API 调用示例：

```bash
curl -X POST http://127.0.0.1:8000/api/documents `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"项目资料\",\"content\":\"这里是知识库内容\",\"user_id\":\"alice\",\"weight\":1.0}"
```

`user_id` 为空时表示全局知识，所有用户都可以检索到；传入 `user_id` 时仅该用户可用。

## 8. 主动对话

主动对话由 `src/emotion_bot/proactive.py` 控制，当前支持：

- 早上、中午、晚上、睡前时间段
- 长时间未聊天
- 场景关键词：工作、学习、压力、低落、睡前、久坐、运动、饭点

前端会定时调用：

```text
GET /api/proactive/check?user_id=alice&scenario=工作
```

如果命中触发条件，机器人会在聊天区主动发起一句话。触发内容会优先结合相关长期记忆；没有相关记忆时使用新的通用话题。

## 9. TTS

前端的“语音输出”使用浏览器内置 Web Speech API，不需要额外服务端依赖。不同浏览器可用的中文声音不同，建议使用 Edge 或 Chrome。

## 10. 常用接口

```text
GET  /api/health
POST /api/chat
GET  /api/users
GET  /api/users/{user_id}/memory
POST /api/documents
GET  /api/proactive/check
```

## 11. 参数建议

- CPU 运行可先保持 `EMOTION_BOT_N_GPU_LAYERS=0`。
- 如果显存足够，可以尝试增加 `EMOTION_BOT_N_GPU_LAYERS`。
- 模型回复太短时增加 `EMOTION_BOT_MAX_TOKENS`。
- 自动记忆触发太频繁时提高 `EMOTION_BOT_AUTO_MEMORY_THRESHOLD`。
- 自动记忆触发太少时降低 `EMOTION_BOT_AUTO_MEMORY_THRESHOLD`。
