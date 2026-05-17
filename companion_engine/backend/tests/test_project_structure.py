"""项目结构测试，确保第 0 阶段关键文件和目录存在。"""

from pathlib import Path


def test_key_files_exist() -> None:
    """测试关键文件已经创建。"""
    project_root = Path(__file__).resolve().parents[2]

    key_files = [
        "README.md",
        ".gitignore",
        "data/.gitkeep",
        "models/.gitkeep",
        "backend/main.py",
        "backend/requirements.txt",
        "backend/app/api/routes.py",
        "frontend/README.md",
    ]

    for relative_path in key_files:
        assert (project_root / relative_path).is_file()


def test_key_directories_exist() -> None:
    """测试关键目录已经创建。"""
    backend_root = Path(__file__).resolve().parents[1]

    key_directories = [
        "app/core",
        "app/schemas",
        "app/db",
        "app/memory",
        "app/persona",
        "app/relationship",
        "app/proactive",
        "app/understanding",
        "app/strategy",
        "app/llm",
        "app/evaluation",
        "app/safety",
        "app/output",
    ]

    for relative_path in key_directories:
        assert (backend_root / relative_path).is_dir()
