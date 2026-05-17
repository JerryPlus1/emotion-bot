# Companion Engine Backend

## 安装依赖

```bash
pip install -r requirements.txt
```

## 启动服务

```bash
uvicorn main:app --reload
```

## 运行测试

```bash
pytest
```

## 本地 GGUF 模型

默认模型路径：

```text
../models/qwen35-2b-sft-merged-q4_k_m.gguf
```

也可以通过环境变量指定模型路径。

Windows PowerShell:

```powershell
$env:LOCAL_GGUF_MODEL_PATH="..\models\qwen35-2b-sft-merged-q4_k_m.gguf"
```

macOS/Linux:

```bash
export LOCAL_GGUF_MODEL_PATH="../models/qwen35-2b-sft-merged-q4_k_m.gguf"
```

调用接口时可通过 query 参数启用本地模型：

```text
POST /api/chat?use_local_model=true
```

## 健康检查

启动后访问：

```text
http://127.0.0.1:8000/health
```

应返回：

```json
{"status":"ok"}
```
