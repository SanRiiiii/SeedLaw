# scripts/load_knowledge_base.py
import os
import argparse
import logging
from dotenv import load_dotenv
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.rag.document_processor import LegalDocumentProcessor
from app.rag.embedding import EmbeddingManager
from app.core.config import settings
from app.db.vector_store import connect_to_milvus

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def load_documents(docs_dir: str, file_filter: str = None):
    """
    加载目录中的所有法律文档，处理并索引到向量数据库

    Args:
        docs_dir: 法律文档目录路径
        file_filter: 可选的文件名过滤器，例如 ".pdf" 或 "公司法"
    """
    # 加载环境变量
    load_dotenv()

    logger.info(f"开始处理目录: {docs_dir}")

    # 初始化文档处理器
    processor = LegalDocumentProcessor(chunk_size=800, chunk_overlap=100)

    # 初始化向量管理器
    embedding_manager = EmbeddingManager()

    # 确保Milvus连接
    if not connect_to_milvus():
        logger.error("无法连接到Milvus向量数据库，请检查配置")
        return

    # 遍历目录
    total_files = 0
    processed_files = 0
    total_chunks = 0

    for root, _, files in os.walk(docs_dir):
        for file_name in files:
            file_path = os.path.join(root, file_name)

            # 应用文件过滤器（如果指定）
            if file_filter and file_filter not in file_name:
                continue

            total_files += 1
            logger.info(f"处理文件 {total_files}: {file_name}")

            try:
                # 处理文档
                chunks = processor.load_single_document(file_path)

                if not chunks:
                    logger.warning(f"文件 {file_name} 未生成任何文本块")
                    continue

                # 将文档添加到向量数据库
                success = embedding_manager.insert_documents(chunks)

                if success:
                    logger.info(f"成功处理文件: {file_name}，生成 {len(chunks)} 个文本块")
                    processed_files += 1
                    total_chunks += len(chunks)
                else:
                    logger.error(f"向量存储失败: {file_name}")

            except Exception as e:
                logger.error(f"处理文件 {file_name} 时出错: {str(e)}")

    logger.info(f"处理完成! 总共处理了 {processed_files}/{total_files} 个文件，生成了 {total_chunks} 个文本块")


def main():
    parser = argparse.ArgumentParser(description="加载法律文档到知识库")
    parser.add_argument(
        "--dir", type=str, required=True,
        help="法律文档目录的路径"
    )
    parser.add_argument(
        "--filter", type=str, default=None,
        help="可选的文件名过滤器"
    )

    args = parser.parse_args()

    load_documents(args.dir, args.filter)


if __name__ == "__main__":
    main()