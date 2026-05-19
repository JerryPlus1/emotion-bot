# emotion-bot

一个本地运行的中文情感陪伴机器人，使用 GGUF 对话模型，支持长期记忆、RAG 知识库、多用户画像、主动对话和浏览器 TTS。

## 功能

- 使用 `llama-cpp-python` 加载本地 GGUF 模型，不依赖在线大模型服务。
- 支持聊天历史、长期记忆、用户画像和知识库检索。
- 支持多用户，通过 `user_id` 隔离历史、画像和长期记忆。
- 支持前端上传文本文件到知识库，并按文件内容对话。
- 支持 `fastembed` embedding 检索；不可用时自动回退到本地 hashing embedding。
- 支持早晨、中午、晚上、深夜、场景关键词、长时间未聊天等主动对话触发。
- 支持点击“主动对话”后由模型结合时间、场景、历史和记忆生成开场。
- 前端支持浏览器 TTS 朗读模型回复。
- 附带 `记忆实验室` 页面，用于测试记忆召回和主动对话能力。



## 项目结构

```text
src/emotion_bot/
  main.py          FastAPI 入口
  llm.py           GGUF / llama-cpp-python 模型适配
  chat.py          对话编排、RAG 上下文选择、主动对话生成
  storage.py       SQLite 存储
  memory.py        长期记忆抽取和用户画像总结
  proactive.py     主动对话触发规则
  text_index.py    embedding 检索
  knowledge.py     knowledge 目录文本导入
  static/          前端页面
tests/             单元测试
data/              本地运行数据和知识库文本
model/             本地模型目录，不提交到 Git
```

## 安装

建议使用 Python 3.12。

```powershell
# 进入你克隆下来的项目目录
cd emotion-bot
py -3.12 -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Windows 下当前依赖已包含 `llama-cpp-python` CPU wheel 的额外索引，通常不需要安装 C++ 编译器。如果要使用 CUDA 或其他加速方式，请按 `llama-cpp-python` 对应 wheel 重新安装。

## 模型

默认模型路径：

```text
model/qwen-finetune-download/qwen35-2b-sft-merged-q4_k_m.gguf
```

模型下载：

```powershell
git clone https://www.modelscope.cn/jiayi001/qwen-finetune-download.git model/qwen-finetune-download
```

如果模型放在其他位置，修改 `.env`：

```env
EMOTION_BOT_MODEL_PATH=model/your-model/model.gguf
```

当前项目运行对话模型时调用的是 `.gguf` 文件，不是 `safetensors`。`safetensors` 更适合 Transformers/PyTorch 训练或 GPU 推理；本项目默认使用 GGUF 是为了本地部署更简单、内存占用更低。

## 历史微调模型
1. Qwen-3.5-2B-Fine-Tune: https://www.modelscope.cn/models/jiayi001/Qwen-3.5-2B-Fine-Tune
2. Qwen2.5-3B-Finetune: https://www.modelscope.cn/models/jiayi001/Qwen2.5-3B-Finetune-ForAIToy
3. qwen2-3b-q4_k_m: https://www.modelscope.cn/models/jiayi001/qwen2-3b-q4_k_m
4. qwen3.5-2b-sft-merged: https://www.modelscope.cn/models/jiayi001/qwen35-2b-sft-merged


## 启动

真实模型模式：

```powershell
# 在项目根目录执行
.\.venv\Scripts\python.exe -m uvicorn emotion_bot.main:app --app-dir src --host 127.0.0.1 --port 8000
```

调试模式，不加载真实模型：

```powershell
# 在项目根目录执行
$env:EMOTION_BOT_LLM_BACKEND="mock"
.\.venv\Scripts\python.exe -m uvicorn emotion_bot.main:app --app-dir src --host 127.0.0.1 --port 8000
```

打开主页面：

```text
http://127.0.0.1:8000
```

记忆实验室：

```text
http://127.0.0.1:8000/memory-lab
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

## 配置

常用 `.env` 配置：

```env
EMOTION_BOT_MODEL_PATH=model/qwen-finetune-download/qwen35-2b-sft-merged-q4_k_m.gguf
EMOTION_BOT_DATA_DIR=data
EMOTION_BOT_KNOWLEDGE_DIR=data/knowledge
EMOTION_BOT_DB_PATH=data/emotion_bot.sqlite3
EMOTION_BOT_LLM_BACKEND=auto
EMOTION_BOT_EMBEDDING_BACKEND=auto
EMOTION_BOT_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMOTION_BOT_HOST=127.0.0.1
EMOTION_BOT_PORT=8000
EMOTION_BOT_N_CTX=4096
EMOTION_BOT_N_THREADS=8
EMOTION_BOT_N_GPU_LAYERS=0
EMOTION_BOT_N_BATCH=256
EMOTION_BOT_TEMPERATURE=0.72
EMOTION_BOT_TOP_P=0.9
EMOTION_BOT_MAX_TOKENS=512
EMOTION_BOT_AUTO_MEMORY_THRESHOLD=0.18
```

参数建议：

- CPU 运行可保持 `EMOTION_BOT_N_GPU_LAYERS=0`。
- 显存足够时可以尝试增加 `EMOTION_BOT_N_GPU_LAYERS`。
- 回复太短时增加 `EMOTION_BOT_MAX_TOKENS`。
- 自动记忆触发太频繁时提高 `EMOTION_BOT_AUTO_MEMORY_THRESHOLD`。
- 自动记忆触发太少时降低 `EMOTION_BOT_AUTO_MEMORY_THRESHOLD`。

## 记忆与 RAG

前端左侧可以调整：

- 记忆模式：`自动`、`始终`、`关闭`
- 长期记忆权重
- 聊天历史权重
- 知识库权重

长期记忆来自两部分：

- 所有聊天消息都会进入历史库，用于后续相关检索。
- 用户消息中的身份、偏好、目标、习惯、关系等会抽取成长期记忆，并汇总为用户画像。

相关度计算主要由两部分组成：

```text
相关度 = 向量相似度 * 0.75 + 关键词重叠度 * 0.25
最终分数 = 相关度 * 权重
```

对长期记忆，还会乘以该记忆自身的 `memory_item.weight`。自动模式下，系统会结合召回意图词、最高相关度阈值和用户画像决定是否加入上下文。

## 知识库

知识库有两种写入方式。

第一种是在前端右侧粘贴文本，填写标题后点击“写入”。

第二种是在前端选择本地文本文件上传。支持：

```text
.txt .md .csv .json .log
```

选择文件后，页面会读取文件内容并填入正文预览框；如果中文乱码，可以把编码切换为 `GB18030` 后重新选择文件。点击“写入”后，内容会进入当前 `user_id` 的知识库，之后聊天会根据“知识库”权重检索这些内容。

服务端启动时也会自动读取：

```text
data/knowledge/*.txt
```

这些文件会作为全局知识库写入，所有用户都可以检索到。例如：

```text
data/knowledge/《全球通史》.txt
```

embedding 配置：

```env
EMOTION_BOT_EMBEDDING_BACKEND=auto
EMOTION_BOT_EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
```

`auto` 会优先使用 `fastembed` 模型，不可用时回退到本地 hashing embedding。

## 主动对话

主动对话由 `src/emotion_bot/proactive.py` 判断触发条件，再由 `src/emotion_bot/chat.py` 调用模型生成主动开场。

触发来源包括：

- 时间段：早晨、中午、晚上、深夜
- 场景：工作、学习、压力、低落、睡前、久坐、运动、饭点
- 长时间未聊天
- 手动点击“主动对话”

前端“主动检查”会做轻量触发判断。“主动对话”会在后台调用模型，让模型结合当前时间、场景、最近聊天、长期记忆和用户画像生成开场，并把这条主动消息写入聊天历史。

接口：

```text
GET /api/proactive/check
```

常用参数：

- `user_id`
- `scenario`
- `persist`
- `force`
- `generate`

其中 `force=true&generate=true` 会强制让模型生成一条主动对话。

## 前端页面

主聊天页：

```text
/
```

功能：

- 发送聊天消息
- `Enter` 发送，`Shift + Enter` 换行
- 清屏
- 主动检查
- 主动对话
- 用户画像查看
- 相关上下文查看
- 知识库文本写入和文件上传
- TTS 播放

记忆实验室：

```text
/memory-lab
```

功能：

- 一键测试记忆召回
- 一键测试主动对话
- 展示命中的上下文
- 展示最近记忆快照

## 数据存储

运行时数据默认写入：

```text
data/emotion_bot.sqlite3
```

主要表：

- `users`
- `conversations`
- `messages`
- `memory_items`
- `documents`
- `proactive_events`

多用户通过 `user_id` 隔离数据。

## 常用接口

```text
GET  /api/health
POST /api/chat
GET  /api/users
GET  /api/users/{user_id}/memory
DELETE /api/users/{user_id}
POST /api/documents
GET  /api/proactive/check
```

聊天示例：

```powershell
curl -X POST http://127.0.0.1:8000/api/chat `
  -H "Content-Type: application/json" `
  -d "{\"user_id\":\"alice\",\"message\":\"我喜欢晚上写代码，也想练习英语。\"}"
```

写入知识库示例：

```powershell
curl -X POST http://127.0.0.1:8000/api/documents `
  -H "Content-Type: application/json" `
  -d "{\"title\":\"项目资料\",\"content\":\"这里是知识库内容\",\"user_id\":\"alice\",\"weight\":1.0}"
```

`user_id` 为空时表示全局知识；传入 `user_id` 时仅该用户可用。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

## 协作流程

- `dev` 是共享开发分支。
- 功能分支从 `dev` 创建，审查后合并回 `dev`。
- 提交应聚焦且描述清楚。
- 推送前运行可用检查。
- 不要提交本地密钥、SQLite 运行数据、日志或模型文件。

