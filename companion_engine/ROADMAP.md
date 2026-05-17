# ROADMAP

本文档描述 Companion Engine 后续功能规划。规划按三个阶段推进，每个阶段都有目标和验收标准。

## 总体方向

Companion Engine 的目标是做一个可本地运行、可接入实体机器人硬件的陪伴式对话引擎。

长期目标：

- 本地可运行，不依赖云端模型。
- 对话自然，有分寸，不像客服或模板。
- 能记住用户偏好和重要信息。
- 能稳定处理本地模型坏输出。
- 能输出给硬件层，例如表情、灯光、动作、语音文本。
- 有清晰 Debug 能力，方便调试模型和策略。

## Phase 1：稳定可运行

### 目标

让项目在本地稳定启动，前端和后端链路清晰可靠。

重点是“能跑通、能定位问题、不会因为配置混乱卡住”。

### 主要任务

- 统一前端 Vite 配置。
- 移除或处理旧的 `frontend/vite.config.js` 配置冲突。
- 固定后端开发端口为 `8001`。
- 固定前端开发端口为 `5173`。
- 完善 README 启动说明。
- 增加前端对后端离线状态的明显提示。
- 明确本地模型开关状态。
- 保证 mock 模式下对话快速稳定。
- 保证 `/health`、`/api/chat`、`/api/state` 基础接口稳定。

### 验收标准

- 新人按 README 可以启动后端。
- 新人按 README 可以启动前端。
- 打开 `http://127.0.0.1:5173/` 能看到页面。
- 页面右上角后端状态能正确显示 `ok` 或 `offline`。
- 不打开本地模型时，发送消息能稳定返回 mock 回复。
- `http://127.0.0.1:8001/health` 返回：

```json
{"status":"ok"}
```

- `http://127.0.0.1:5173/health` 经前端代理返回：

```json
{"status":"ok"}
```

- 运行关键测试通过：

```powershell
pytest tests/test_db_init.py tests/test_local_gguf_client.py tests/test_structured_output.py tests/test_mock_llm.py
```

## Phase 2：提升回复质量

### 目标

让对话更像真人，减少机械模板、prompt 泄漏、内部分析、跑题回复。

重点是“用户说什么，机器人要先接住什么”。

### 主要任务

- 优化 `backend/app/llm/prompt_builder.py`。
- 优化 `backend/app/llm/structured_output.py`。
- 优化 `backend/app/llm/local_gguf_client.py` 的质量判断。
- 优化 `backend/app/llm/mock_llm.py` fallback 回复。
- 优化 `backend/app/humanlike/humanlike_controller.py`。
- 减少“我想更懂你一点”这类泛化模板。
- 减少“请输入你的回复”“请根据以上信息”等 prompt 残留。
- 增强对常见用户输入的贴合：
  - 你是谁
  - 我在上班
  - 我想去唱歌
  - 我很累
  - 我有点烦
  - 我不想说话
- 让 debug 能清楚显示：
  - `raw_reply`
  - `model_reply`
  - `final_reply`
  - `local_model_reply_usable`
  - `used_model_fallback`
  - `local_model_error`

### 验收标准

- 本地模型输出合法 JSON 时，能正确使用 `reply_text`。
- 本地模型输出“废话 + JSON + 废话”时，能提取 JSON 中的 `reply_text`。
- 本地模型输出 `<think>`、内部分析、prompt 残留时，不直接展示给用户。
- 用户问“你是谁”，回复能解释身份，而不是进入无关模板。
- 用户说“我在上班”，回复能接住上班场景。
- 用户说“我想去唱歌”，回复能接住唱歌场景。
- Debug 中能看出本地模型输出和最终回复的差异。
- 关键测试通过：

```powershell
pytest tests/test_structured_output.py tests/test_mock_llm.py tests/test_local_gguf_client.py
```

## Phase 3：产品化和机器人接入

### 目标

把 Demo 推向更接近真实机器人产品的状态。

重点是“可长期运行、可观察、可接硬件、可扩展”。

### 主要任务

- 增加流式输出，减少本地模型等待感。
- 增加模型加载状态和推理状态。
- 增加前端发送中状态和超时提示。
- 增加模型崩溃或后端断开时的恢复提示。
- 优化数据库结构和迁移方式。
- 增强长期记忆抽取和召回质量。
- 增强 Persona 控制，让机器人风格更稳定。
- 增强关系状态推进，让熟悉度变化更自然。
- 完善硬件动作输出：
  - 表情
  - 灯光
  - 动作
  - 语音文本
- 验证 HTTP、MQTT、串口适配器。
- 增加端到端测试。
- 增加启动脚本或一键开发命令。

### 验收标准

- 前端能清楚显示：
  - 后端在线状态
  - 模型加载状态
  - 发送中状态
  - 本地模型是否启用
  - fallback 是否发生
- 本地模型推理较慢时，用户不会误以为页面卡死。
- 后端异常退出后，前端能给出清晰提示。
- 长期记忆能影响后续回复。
- Persona 修改后能明显影响回复风格。
- `hardware_actions` 字段能稳定输出可用动作。
- 至少一种硬件输出适配器完成真实联调。
- 有一组端到端测试覆盖：
  - mock 对话
  - 本地模型对话
  - fallback 路径
  - debug 展示
  - 数据库存储

## 暂不优先

以下内容可以后置：

- 多用户权限系统。
- 云端同步。
- 移动端适配。
- 完整账号系统。
- 复杂 UI 主题系统。
- 大规模模型评测平台。

当前最重要的仍然是：

```text
稳定启动 -> 回复自然 -> Debug 清晰 -> 本地模型可靠 fallback -> 再接硬件
```
