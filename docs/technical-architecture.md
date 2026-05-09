# Emotion Bot 技术说明

## 1. 项目目标

Emotion Bot 是一个本地离线运行的 AI 情感陪伴机器人，核心目标是：

- 使用本地 `GGUF` 模型完成对话生成，不依赖在线大模型服务。
- 支持多用户聊天、长期记忆、历史召回和知识库检索。
- 在合适时间或场景下主动发起对话，而不是只被动回复。
- 提供一个可以直接操作的前端界面，以及一个专门验证记忆能力的测试页面。

## 2. 整体架构

系统采用单体本地应用结构：

1. 前端静态页面：位于 `src/emotion_bot/static/`
2. FastAPI 服务：位于 `src/emotion_bot/main.py`
3. 对话编排层：位于 `src/emotion_bot/chat.py`
4. 模型适配层：位于 `src/emotion_bot/llm.py`
5. 记忆与存储层：位于 `src/emotion_bot/storage.py`、`src/emotion_bot/memory.py`
6. 主动对话引擎：位于 `src/emotion_bot/proactive.py`
7. 本地检索层：位于 `src/emotion_bot/text_index.py`

## 3. 模型运行方式

默认模型文件：

```text
model/qwen-finetune-download/qwen35-2b-sft-merged-q4_k_m.gguf
```

运行方式：

- 使用 `llama-cpp-python` 加载本地 `GGUF` 文件。
- 后端通过 `create_chat_completion(...)` 调用模型。
- 当前健康检查接口会返回：

```text
effective_backend = llama-cpp-gguf
offline = true
```

这表示当前服务确实运行在离线 `GGUF` 模式，而不是 mock。

## 4. 记忆系统设计

记忆分成三层：

### 4.1 聊天历史

- 每条用户消息和助手回复都会写入 SQLite。
- 后续提问时可以从历史消息中做相关检索。

### 4.2 长期记忆

- 从用户消息中抽取稳定信息，例如身份、偏好、目标、习惯、关系。
- 例如：
  - `我叫小周`
  - `我喜欢夜跑`
  - `我最近在准备转岗面试`

- 这些内容会保存为 `memory_items`，并带有权重。
- 同时会自动汇总成用户画像摘要。

### 4.3 知识库

- 用户可以从前端写入资料文本。
- 服务端会切片并保存到 `documents` 表。
- 对话时可以与长期记忆、聊天历史一起参与召回。

## 5. 检索与 RAG 设计

当前实现通过 `src/emotion_bot/text_index.py` 提供统一 embedding 接口：

- `EMOTION_BOT_EMBEDDING_BACKEND=auto` 时优先使用 `fastembed` 本地 embedding 模型。
- 未安装或不可用时退回 hashing embedding，保证离线调试可运行。
- 最终排序结合向量相似度、关键词重叠和用户配置的权重。

启动时 `src/emotion_bot/knowledge.py` 会读取 `data/knowledge/*.txt`，自动切分并写入全局知识库。

检索来源包括三类：

- `memory`
- `history`
- `document`

前端可以分别调节：

- 长期记忆权重
- 聊天历史权重
- 知识库权重

## 6. 主动对话设计

主动对话由 `ProactiveEngine` 负责。

触发来源包括：

- 时间段：早晨、中午、晚上、深夜
- 场景：工作、学习、压力、久坐、运动、饭点、睡前
- 长时间未聊天
- 手动触发

接口：

```text
GET /api/proactive/check
```

支持参数：

- `user_id`
- `scenario`
- `persist`
- `force`

其中：

- `force=true` 时，即使当前没有自然触发条件，也会主动生成一个开场话题
- 这就是前端“主动对话”按钮所使用的模式

## 7. 前端页面设计

### 7.1 主聊天页

路径：

```text
/
```

功能：

- 聊天发送
- `Enter` 发送，`Shift + Enter` 换行
- 清屏
- 主动检查
- 主动对话
- 用户画像查看
- 上下文查看
- 知识库写入
- TTS 播放

### 7.2 记忆实验室

路径：

```text
/memory-lab
```

功能：

- 一键测试记忆召回
- 一键测试主动对话
- 展示命中的上下文
- 展示最近记忆快照
- 提供推荐测试脚本

## 8. 数据存储

当前使用 SQLite，本地文件默认位于：

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

## 9. 当前限制

- embedding 精度取决于当前后端；hashing embedding 适合离线保底，真实语义检索建议安装 `fastembed`。
- 主动对话仍然是规则触发，不是完全自主规划。
- TTS 使用浏览器自带语音，不是模型原生语音合成。
- 模型回复风格仍然受当前 `GGUF` 模型本身能力限制。

## 10. 后续可扩展方向

- 增加可视化知识库重建入口和 embedding 缓存管理。
- 增加记忆编辑、删除和人工确认机制。
- 引入定时任务或桌面提醒，让主动对话不只依赖页面轮询。
- 增加更细的人设控制和情绪陪伴 prompt 模板。
- 为主动对话增加优先级和冷却策略配置。
