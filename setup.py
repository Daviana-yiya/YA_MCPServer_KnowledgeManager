import subprocess
from pathlib import Path
from modules.YA_Common.utils.logger import get_logger

logger = get_logger("setup")


def install_package(package_name: str):
    """安装指定的Python包"""
    try:
        subprocess.check_call(["uv", "pip", "install", package_name])
        logger.info(f"Successfully installed {package_name}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install {package_name}: {e}")
        raise


IMPORT_NAME_MAP = {
    "beautifulsoup4": "bs4",
    "pytest-asyncio": "pytest_asyncio",
}


def check_and_install_dependencies():
    """检查并安装项目依赖"""
    required_packages = [
        "chromadb>=0.4.0",
        "aiosqlite>=0.19.0",
        "httpx>=0.27.0",
        "beautifulsoup4>=4.12.0",
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "jieba>=0.42.1",
        "sentence-transformers>=2.0.0",
    ]

    for package in required_packages:
        package_name = package.split(">=")[0]
        import_name = IMPORT_NAME_MAP.get(package_name, package_name)
        try:
            __import__(import_name)
            logger.info(f"{package_name} is already installed")
        except ImportError:
            logger.info(f"Installing {package}...")
            install_package(package)


def initialize_knowledge_base():
    """初始化知识库数据目录"""
    try:
        # 创建数据目录
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)

        # 创建SQLite数据库目录
        db_dir = data_dir / "database"
        db_dir.mkdir(exist_ok=True)

        # 创建向量存储目录
        vector_dir = data_dir / "vector_store"
        vector_dir.mkdir(exist_ok=True)

        logger.info("Knowledge base directories initialized")

    except Exception as e:
        logger.error(f"Failed to initialize knowledge base: {e}")
        raise


def warmup_vector_store():
    """预热向量存储，提前加载 SentenceTransformer 模型，避免首次工具调用超时。"""
    import os

    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    try:
        from core.vector_store import _get_collection
        from modules.YA_Common.utils.config import get_config

        vector_path = get_config("knowledge.vector_store.path")
        collection_name = get_config("knowledge.vector_store.collection_name")
        _get_collection(vector_path, collection_name)
        logger.info("Vector store warmed up.")
    except Exception as e:
        logger.warning(f"Vector store warmup failed (non-fatal): {e}")


def setup():
    """Setup your environment and dependencies here."""
    try:
        logger.info("Starting knowledge management system setup...")

        # 检查并安装依赖
        check_and_install_dependencies()

        # 初始化知识库
        initialize_knowledge_base()

        # 预热向量存储（提前加载模型，避免首次调用超时）
        warmup_vector_store()

        logger.info("Setup complete.")

    except Exception as e:
        logger.error(f"Setup failed: {e}")
        raise e
