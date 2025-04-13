# scripts/load_knowledge_base.py
import os
import logging
import json
from dotenv import load_dotenv
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# from app.rag.document_processor import LegalDocumentProcessor
from app.rag.md_process import LegalDocumentProcessor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("knowledge_base_loading.log"),
        logging.StreamHandler()  # 同时保留控制台输出
    ]
)
logger = logging.getLogger(__name__)


def process_documents(docs_dir: str, output_dir: str, file_filter: str = None):
    """
    加载目录中的法律文档，处理并将拆分后的chunks保存为JSON文件

    Args:
        docs_dir: 法律文档目录路径
        output_dir: 输出目录路径，用于保存拆分后的JSON文件
        file_filter: 可选的文件名过滤器，例如 ".md" 或 "公司法"
    """
    # 加载环境变量
    load_dotenv()

    logger.info(f"开始处理目录: {docs_dir}")
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 初始化文档处理器
    processor = LegalDocumentProcessor()

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
                if file_name.endswith('.md'):
                    # 使用md_process处理markdown文件
                    chunks = processor.process_legal_markdown(file_path)
                # else:
                #     # 使用普通处理器处理其他文件
                #     chunks = processor.load_single_document(file_path)

                if not chunks:
                    logger.warning(f"文件 {file_name} 未生成任何文本块")
                    continue

                # 保存chunks到JSON文件
                output_file = os.path.join(output_dir, f"{os.path.splitext(file_name)[0]}_chunks.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(chunks, f, ensure_ascii=False, indent=2)

                logger.info(f"成功处理文件: {file_name}，生成 {len(chunks)} 个文本块，保存至 {output_file}")
                processed_files += 1
                total_chunks += len(chunks)

            except Exception as e:
                logger.error(f"处理文件 {file_name} 时出错: {str(e)}")

    logger.info(f"处理完成! 总共处理了 {processed_files}/{total_files} 个文件，生成了 {total_chunks} 个文本块")



if __name__ == "__main__":

    docs_dir = "../data/laws/related_laws"  # 法律文档目录路径
    output_dir = "../data/chunks/related_laws"  # 输出目录路径
    # file_filter = "公司法"  # 文件名过滤器
    process_documents(docs_dir, output_dir)
