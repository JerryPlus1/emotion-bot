# RECOVERY

## 2026-05-14 小 PR：前端错误信息解析和展示

### 本轮只优化的问题

- 优化前端请求失败时的错误信息解析。
- 后端返回 JSON 错误时，前端优先展示 `detail.message`。
- 不修改后端、不修改数据库、不修改 Vite 配置、不修改聊天组件。

### 修改原因
 
此前 `frontend/src/api/client.ts` 在请求失败时直接读取 `response.text()` 并抛给 `App.tsx`。如果后端返回：

```json
{
  "detail": {
    "message": "本地模型输出不可用",
    "mock_disabled": true
  }
}
```

前端可能展示整段 JSON 字符串，用户不容易理解。

### 实际修改

- 修改 `frontend/src/api/client.ts`：
  - 新增 `isRecord(...)`。
  - 新增 `extractErrorMessage(status, bodyText)`。
  - 请求失败时解析响应体：
    - 优先展示 `detail.message`。
    - 如果 `detail` 是字符串，则展示 `detail`。
    - 如果是纯文本，则展示纯文本。
    - 如果响应体为空，则展示 `请求失败：HTTP ${status}`。
  - 成功请求路径仍保持 `return response.json() as Promise<T>`，不改变接口协议和函数签名。

### 验证

- 已查看 `frontend/package.json`。
- 当前前端脚本只有 `dev`、`build`、`preview`，没有 `typecheck` 或 `lint`。
- 已运行并通过：

```powershell
cd "D:\AI-ROBOT(2)\companion_engine\frontend"
npm run build
```

### 未修改

- 未修改 `frontend/src/App.tsx`，因为现有 `setError(err instanceof Error ? err.message : ...)` 已能展示新的解析结果。
- 未修改 `frontend/src/components/ChatPanel.tsx`。
- 未修改 `frontend/vite.config.ts`。
- 未修改后端 Python 文件。
- 未修改数据库。

本文档记录当前项目状态、已完成内容、未完成内容、当前问题和下一步计划。

## 当前项目状态

项目是一个本地陪伴机器人对话引擎 Demo，当前包含：

- React + Vite 前端页面，默认端口 `5173`。
- FastAPI 后端服务，当前推荐端口 `8001`。
- SQLite 本地数据库，默认路径 `data/companion.db`。
- 本地 GGUF 模型调用入口，基于 `llama-cpp-python`。
- mock fallback 回复，用于本地模型不可用或输出质量不合格时兜底。
- Debug 面板，可查看 raw/model/final/fallback 信息。

推荐启动方式：

```powershell
# 后端
cd "D:\AI-ROBOT(2)\companion_engine\backend"
$env:PATH="C:\Users\EDY\miniconda3\envs\py311;C:\Users\EDY\miniconda3\envs\py311\Library\bin;C:\Users\EDY\miniconda3\envs\py311\Scripts;" + $env:PATH
C:\Users\EDY\miniconda3\envs\py311\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8001
```

```powershell
# 前端
cd "D:\AI-ROBOT(2)\companion_engine\frontend"
npm run dev -- --config vite.config.ts --port 5173 --host 127.0.0.1
```

## 已完成内容

### 后端基础

- 已有 FastAPI 应用入口：`backend/main.py`。
- 已有 API 路由：`backend/app/api/routes.py`。
- 已有 `/health` 健康检查接口。
- 已有 `/api/chat` 对话接口。
- 已有 `/api/state/{user_id}` 状态读取接口。
- 已有 `/api/persona/{user_id}` persona 保存接口。
- 已有 `/api/reset/{user_id}` 测试数据重置接口。

### 对话引擎

- 核心逻辑位于 `backend/app/core/engine.py`。
- `handle_event(...)` 已串联：
  - 数据库初始化
  - 用户画像读取
  - persona 读取
  - 关系状态读取
  - 长期记忆读取
  - 意图、情绪、风险识别
  - 情绪轨迹记录
  - 策略选择
  - prompt 构造
  - 本地模型或 mock 回复
  - 真人感后处理
  - 对话日志写入
  - 硬件动作映射
  - debug 输出

### 本地模型接入

- 本地模型客户端位于 `backend/app/llm/local_gguf_client.py`。
- 默认模型路径为 `../models/qwen35-2b-sft-merged-q4_k_m.gguf`。
- 支持环境变量：
  - `LOCAL_GGUF_MODEL_PATH`
  - `LOCAL_GGUF_N_CTX`
- 已加入 `<think>` 清理。
- 已加入 `get_last_error()`，用于 debug。
- 已加入 `is_response_usable(...)`，用于判断本地模型输出是否适合展示给用户。
- 已验证 py311 conda 环境中本地模型可用。
- 已验证真实本地模型推理可以成功返回文本。

### 输出质量保护

- `engine.py` 已接入 `local_gguf_client.is_response_usable(raw_reply)`。
- 本地模型输出可用时，用户可见回复使用本地模型。
- 本地模型输出不可用时，用户可见回复回退到 `generate_mock_response(...)`。
- debug 保留：
  - `raw_reply`
  - `model_reply`
  - `local_model_error`
- debug 新增：
  - `local_model_reply_usable`
  - `used_model_fallback`
- 已加强提示词泄漏过滤，避免把 `<think>`、内部分析、乱码、prompt 内容直接展示给用户。
- 已增强 `structured_output.py`，可以从“废话 + JSON + 废话”的模型输出中提取 `reply_text`。
- 已增强 mock fallback，让它能根据本轮用户输入做轻量贴合，例如：
  - “你是谁”
  - “我在上班”
  - “我想去唱歌”
  - “我累了”

### 前端

- 前端主页面位于 `frontend/src/App.tsx`。
- 聊天面板位于 `frontend/src/components/ChatPanel.tsx`。
- Debug 面板位于 `frontend/src/components/DebugPanel.tsx`。
- API 请求封装位于 `frontend/src/api/client.ts`。
- 本地模型开关位于 `frontend/src/components/Header.tsx`。
- `frontend/vite.config.ts` 中 `/api` 和 `/health` 已代理到 `http://127.0.0.1:8001`。

### 验证记录

已执行过的关键验证包括：

- `py_compile` 关键后端文件。
- `pytest tests/test_db_init.py tests/test_local_gguf_client.py`，通过。
- `pytest tests/test_structured_output.py tests/test_mock_llm.py tests/test_local_gguf_client.py`，通过。
- 直接调用 `handle_event(..., use_local_model=True)` 冒烟测试。
- 前端 5173 代理 `/health` 到 8001 验证。
- 前端代理 `/api/chat?use_local_model=true` 验证。

## 未完成内容

- 本地模型回复质量仍不稳定，偶尔会输出：
  - prompt 残留
  - 分析过程
  - 格式不完整 JSON
  - 语气机械的短句
- 前端目录中仍存在旧的 `frontend/vite.config.js`，其中代理目标是旧端口 `8000`。
- 尚未把前端启动脚本固定为强制使用 `vite.config.ts`。
- 尚未做完整端到端自动化测试。
- 尚未做模型推理性能优化。
- 尚未做流式输出。
- 尚未做更自然的多轮对话策略。
- 硬件输出层目前主要是占位和映射，未真实接入硬件。
- 主动对话、记忆召回、关系推进等能力仍偏规则化。

## 当前问题

### 1. 前端启动配置容易踩坑

当前必须使用：

```powershell
npm run dev -- --config vite.config.ts --port 5173 --host 127.0.0.1
```

如果直接运行：

```powershell
npm run dev
```

Vite 可能加载旧的 `vite.config.js`，导致代理请求旧端口 `8000`。

### 2. 后端必须保持运行

如果浏览器访问：

```text
http://127.0.0.1:8001/health
```

显示连接失败，则后端没有运行。此时前端会显示 `offline` 或请求失败。

### 3. 本地模型推理慢

本地 GGUF 模型在当前机器上可能需要几十秒返回。第一次加载更慢。

### 4. 回复自然度仍需继续优化

虽然已经加入质量保护和 JSON 提取，但模型回复仍可能出现不够像真人的问题。后续需要继续优化 prompt、解析、fallback 和真人感后处理。

### 5. 工作区存在历史构建标记

当前 Git 状态中可能出现：

```text
m companion_engine/.build_src/llama_cpp_python-0.3.23
```

这是本地 llama-cpp-python 源码构建目录的历史标记，当前文档更新未处理它。

## 下一步计划

### 优先级 1：稳定运行链路

- 清理或统一 Vite 配置，避免 `vite.config.js` 和 `vite.config.ts` 冲突。
- 固定前端启动命令。
- 固定后端端口为 `8001`。
- 增加“后端未启动”的前端提示。

### 优先级 2：提升回复质量

- 继续优化 `prompt_builder.py`。
- 继续优化 `structured_output.py` 对坏 JSON 的解析。
- 继续扩展 `local_gguf_client.is_response_usable(...)`。
- 减少模板化 fallback。
- 增强多轮上下文使用，让回复更接住用户刚说的话。

### 优先级 3：测试和文档

- 补充端到端测试。
- 补充本地模型质量保护测试。
- 补充前端代理说明。
- 保持 `README.md`、`RECOVERY.md`、`ROADMAP.md` 同步更新。

### 优先级 4：产品化能力

- 增加流式输出。
- 增加模型加载状态。
- 增加更清晰的 Debug UI。
- 增加真实硬件适配验证。
- 优化数据库迁移和状态清理工具。
