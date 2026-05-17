# Companion Engine

Companion Engine 是一个本地运行的陪伴机器人对话引擎 Demo。它的目标不是做云端聊天产品，而是验证一条完整的离线对话链路：

```text
前端聊天页面 -> FastAPI 后端 -> 对话引擎 -> 本地模型或 mock fallback -> 数据库记忆 -> 返回前端展示
```

项目当前支持：

- React + Vite 前端聊天页面
- FastAPI 后端接口
- SQLite 本地数据库
- 用户画像、Persona、关系状态、短期对话、长期记忆
- 规则版意图、情绪、风险识别
- 本地 GGUF 模型调用入口
- 本地模型输出质量保护
- mock fallback 回复
- Debug 面板展示 raw/model/final/fallback 信息

本项目仍是工程原型，不应当作为医疗、心理咨询或危机干预系统使用。

## 启动方式

需要同时启动两个服务：

```text
后端：127.0.0.1:8001
前端：127.0.0.1:5173
```

两个终端窗口都要保持打开。

## 后端启动

打开 PowerShell：

```powershell
cd "D:\AI-ROBOT(2)\companion_engine\backend"
```

确保使用 py311 conda 环境：

```powershell
$env:PATH="C:\Users\EDY\miniconda3\envs\py311;C:\Users\EDY\miniconda3\envs\py311\Library\bin;C:\Users\EDY\miniconda3\envs\py311\Scripts;" + $env:PATH
```

启动后端：

```powershell
C:\Users\EDY\miniconda3\envs\py311\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

健康检查：

```text
http://127.0.0.1:8001/health
```

正常返回：

```json
{"status":"ok"}
```

## 前端启动

另开一个 PowerShell：

```powershell
cd "D:\AI-ROBOT(2)\companion_engine\frontend"
```

启动前端：

```powershell
npm run dev -- --config vite.config.ts --port 5173 --host 127.0.0.1
```

访问页面：

```text
http://127.0.0.1:5173/
```

注意：当前前端目录里同时存在 `vite.config.ts` 和旧的 `vite.config.js`。启动时必须显式指定：

```powershell
--config vite.config.ts
```

否则 Vite 可能加载旧配置，把接口代理到旧端口。

## 本地模型

推荐模型文件位置：

```text
models/qwen35-2b-sft-merged-q4_k_m.gguf
```

默认模型路径在：

```text
backend/app/llm/local_gguf_client.py
```

也可以通过环境变量覆盖：

```powershell
$env:LOCAL_GGUF_MODEL_PATH="..\models\qwen35-2b-sft-merged-q4_k_m.gguf"
```

前端页面右上角有“本地模型”开关：

- 关闭：使用 mock 回复，速度快，适合调试流程。
- 打开：调用本地 GGUF 模型，首次回复可能较慢。

## 主要目录

```text
companion_engine/
  README.md              # 项目说明
  RECOVERY.md            # 当前恢复记录和项目状态
  ROADMAP.md             # 后续规划
  data/                  # SQLite 数据库目录
  models/                # 本地 GGUF 模型目录

  backend/
    main.py              # FastAPI 后端入口
    app/
      api/               # HTTP API 路由
      core/              # 对话引擎主流程
      db/                # SQLite 连接和初始化
      evaluation/        # 用户反馈和回复评估
      humanlike/         # 真人感后处理
      llm/               # prompt、本地模型、mock、结构化解析
      memory/            # 用户画像、长短期记忆
      output/            # 硬件动作映射和输出适配
      persona/           # 机器人 persona
      proactive/         # 主动说话和主动问题规划
      relationship/      # 关系状态
      safety/            # 安全边界和危机回复
      schemas/           # Pydantic 数据结构
      strategy/          # 回复策略选择
      understanding/     # 意图、情绪、风险识别
    tests/               # 后端测试

  frontend/
    src/
      App.tsx            # 前端主组件
      main.tsx           # 前端入口
      api/client.ts      # 前端请求后端
      components/        # 页面组件
    vite.config.ts       # Vite 代理配置
```

## 重要文件

新人优先看这些：

```text
frontend/src/App.tsx
frontend/src/components/ChatPanel.tsx
frontend/src/api/client.ts
backend/main.py
backend/app/api/routes.py
backend/app/core/engine.py
backend/app/llm/local_gguf_client.py
backend/app/llm/prompt_builder.py
backend/app/llm/structured_output.py
backend/app/llm/mock_llm.py
backend/app/humanlike/humanlike_controller.py
backend/app/schemas/engine.py
```

## 核心调用链

```text
用户在前端输入
  -> ChatPanel.tsx 收集输入
  -> App.tsx handleSend()
  -> client.ts sendChat()
  -> POST /api/chat
  -> routes.py chat()
  -> engine.py handle_event()
  -> 读取数据库状态
  -> 理解用户意图、情绪、风险
  -> 选择策略
  -> 构造 prompt
  -> 调用本地模型或 mock
  -> 解析模型输出
  -> 质量保护和 fallback
  -> 真人感后处理
  -> 写入数据库
  -> 返回 EngineOutput
  -> 前端显示 response_text 和 debug
```

## 测试

进入后端目录：

```powershell
cd "D:\AI-ROBOT(2)\companion_engine\backend"
```

运行测试：

```powershell
pytest
```

运行指定测试示例：

```powershell
pytest tests/test_structured_output.py tests/test_mock_llm.py tests/test_local_gguf_client.py
```

## 常见问题

### 前端打不开 5173

说明 Vite 没启动。运行：

```powershell
cd "D:\AI-ROBOT(2)\companion_engine\frontend"
npm run dev -- --config vite.config.ts --port 5173 --host 127.0.0.1
```

### 前端显示后端 offline

说明后端 8001 没启动，或启动后崩了。运行：

```powershell
cd "D:\AI-ROBOT(2)\companion_engine\backend"
$env:PATH="C:\Users\EDY\miniconda3\envs\py311;C:\Users\EDY\miniconda3\envs\py311\Library\bin;C:\Users\EDY\miniconda3\envs\py311\Scripts;" + $env:PATH
C:\Users\EDY\miniconda3\envs\py311\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

### 前端请求失败 500

常见原因：

- 后端 8001 没运行。
- 本地模型推理时后端退出。
- 前端没有用 `--config vite.config.ts` 启动，代理走到了旧端口。
- 后端窗口里有 Python 异常。

先检查：

```text
http://127.0.0.1:8001/health
http://127.0.0.1:5173/health
```

### 本地模型回复慢

这是正常的。本地 GGUF 模型在 CPU 上可能需要几十秒。首次加载会更慢。
