# 开发工作流程

## 分支

- `dev`：共享开发分支。
- 功能分支应从 `dev` 创建，并在审查后合并回去。

## 本地设置

1. 创建虚拟环境。
2. 使用 `pip install -r requirements.txt` 安装依赖项。
3. 将 `.env.example` 复制到 `.env` 并填写本地专用值。

## 协作

- 保持提交聚焦且描述性强。
- 在推送前运行可用检查。
- 不要提交本地密钥或生成的缓存文件。

## 模型下载

模型文件不提交到 Git 仓库，本地统一放在 `model/` 目录下。

```bash
git clone https://www.modelscope.cn/jiayi001/qwen-finetune-download.git model/qwen-finetune-download
```
