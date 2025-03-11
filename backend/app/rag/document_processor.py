# app/rag/document_processor.py
import re
import os
import json
from typing import List, Dict, Any, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader, PyPDFLoader, DirectoryLoader
import hashlib
import markdown
from bs4 import BeautifulSoup

'''
全部法律信息都会从网络爬取后转为markdown文件---legal_master爬一遍，可以提个pr看下
法律和司法解释可以直接通过“第x条”的正则匹配方式分chunk，如果一个chunk过长，考虑后续合并
案件分析可以通过总结来处理
'''


class LegalDocumentProcessor:
    """法律文档处理器，负责文档加载、解析和分块"""

    def __init__(self,
                 chunk_size: int = 1500,
                 chunk_overlap: int = 50,
                 metadata_fields: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.metadata_fields = metadata_fields or ["source", "title", "section", "article_number"]

        # 创建通用分块器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", "。", "，", " ", ""]
        )

    def load_single_document(self, file_path: str) -> List[Dict[str, Any]]:
        """加载单个文档并返回分块后的内容"""
        _, ext = os.path.splitext(file_path)

        if ext.lower() == '.pdf':
            return self._process_pdf(file_path)
        elif ext.lower() == '.txt':
            return self._process_txt(file_path)
        elif ext.lower() == '.md':
            return self._process_md(file_path)  # 修改：添加file_path参数
        else:
            raise ValueError(f"不支持的文件类型: {ext}")

    def load_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """加载目录下的所有支持文档并返回分块后的内容"""
        all_chunks = []

        # 遍历目录下的所有文件
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    chunks = self.load_single_document(file_path)
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {str(e)}")

        return all_chunks

    def _process_pdf(self, file_path: str) -> List[Dict[str, Any]]:
        """处理PDF文件"""
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        # 提取元数据
        base_metadata = self._extract_metadata_from_filename(file_path)

        # 分块处理
        chunks = []
        for doc in documents:
            page_number = doc.metadata.get("page", 0)
            # 合并元数据
            doc.metadata.update(base_metadata)
            doc.metadata["page"] = page_number

            # 应用特殊的法律文档分块规则
            page_chunks = self._split_legal_document(doc.page_content, doc.metadata)
            chunks.extend(page_chunks)

        return chunks
    def _process_txt(self, file_path: str) -> List[Dict[str, Any]]:
        """处理TXT文件"""
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()

        # 提取元数据
        metadata = self._extract_metadata_from_filename(file_path)

        # 应用特殊的法律文档分块规则
        all_chunks = []
        for doc in documents:
            doc.metadata.update(metadata)
            chunks = self._split_legal_document(doc.page_content, doc.metadata)
            all_chunks.extend(chunks)

        return all_chunks



    def _process_md(self, file_path: str) -> List[Dict[str, Any]]:
        """处理Markdown文件"""
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()

        # 提取元数据
        metadata = self._extract_metadata_from_filename(file_path)

        # 应用特殊的法律文档分块规则
        all_chunks = []
        for doc in documents:
            doc.metadata.update(metadata)
            chunks = self._split_legal_document(doc.page_content, doc.metadata)
            all_chunks.extend(chunks)

        return all_chunks

    def _process_json(self, file_path: str) -> List[Dict[str, Any]]:
        """处理JSON格式的法律文档"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        chunks = []

        # 假设JSON结构包含法律文档信息
        base_metadata = {
            "source": data.get("source", os.path.basename(file_path)),
            "title": data.get("title", ""),
            "law_type": data.get("type", ""),
            "publish_date": data.get("publish_date", ""),
            "effective_date": data.get("effective_date", ""),
        }

        # 处理条款部分
        articles = data.get("articles", [])
        for article in articles:
            article_id = article.get("id", "")
            article_title = article.get("title", "")
            article_content = article.get("content", "")

            # 增加条款特定的元数据
            article_metadata = base_metadata.copy()
            article_metadata.update({
                "article_id": article_id,
                "article_title": article_title,
                "section": article.get("section", ""),
                "chapter": article.get("chapter", ""),
            })

            # 对条款内容进行分块
            article_chunks = self._split_legal_document(article_content, article_metadata)
            chunks.extend(article_chunks)

        return chunks

    def _extract_metadata_from_filename(self, file_path: str) -> Dict[str, Any]:
        """从文件名和路径中提取元数据"""
        filename = os.path.basename(file_path)
        name_without_ext, _ = os.path.splitext(filename)

        # 尝试从文件名中提取信息，如 "中华人民共和国公司法_2018"
        parts = name_without_ext.split('_')
        title = parts[0] if parts else name_without_ext
        year = parts[1] if len(parts) > 1 else ""

        return {
            "source": filename,
            "file_path": file_path,
            "title": title,
            "year": year,
        }


    def _split_legal_document(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        使用法律文档特定的分块规则进行文本分块
        基于正则匹配进行分块：匹配第xx条
        一条分为一块
        文件名-catalog都是元数据
        """
        # 1. 首先尝试根据条款编号进行分块
        article_pattern = r'第[一二三四五六七八九十百千万零\d]+条'
        article_splits = re.split(f"({article_pattern})", text)

        chunks = []
        current_article = ""
        article_number = ""

        for i, split in enumerate(article_splits):
            if re.match(article_pattern, split):
                # 这是一个条款编号
                article_number = split
                if i + 1 < len(article_splits):
                    # 将条款编号与内容合并
                    article_content = article_number + article_splits[i + 1]

                    # 对长条款进行进一步分块
                    if len(article_content) > self.chunk_size:
                        sub_chunks = self.text_splitter.split_text(article_content)
                        for j, sub_chunk in enumerate(sub_chunks):
                            chunk_metadata = metadata.copy()
                            chunk_metadata.update({
                                "article_number": article_number,
                                "chunk_id": f"{article_number}_part_{j + 1}",
                                "is_complete_article": j == 0 and j == len(sub_chunks) - 1
                            })

                            # 为每个分块生成唯一ID
                            chunk_id = self._generate_chunk_id(sub_chunk, chunk_metadata)

                            chunks.append({
                                "id": chunk_id,
                                "text": sub_chunk,
                                "metadata": chunk_metadata
                            })
                    else:
                        # 短条款直接添加
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            "article_number": article_number,
                            "chunk_id": article_number,
                            "is_complete_article": True
                        })

                        # 为每个分块生成唯一ID
                        chunk_id = self._generate_chunk_id(article_content, chunk_metadata)

                        chunks.append({
                            "id": chunk_id,
                            "text": article_content,
                            "metadata": chunk_metadata
                        })
            elif i == 0 or (i % 2 == 0 and i > 0):
                # 处理前言或章节标题等非条款内容
                if split.strip():
                    # 分块非条款内容
                    non_article_chunks = self.text_splitter.split_text(split)
                    for j, sub_chunk in enumerate(non_article_chunks):
                        chunk_metadata = metadata.copy()
                        chunk_metadata.update({
                            "article_number": "",
                            "chunk_id": f"non_article_{i}_{j}",
                            "is_complete_article": False
                        })

                        # 为每个分块生成唯一ID
                        chunk_id = self._generate_chunk_id(sub_chunk, chunk_metadata)

                        chunks.append({
                            "id": chunk_id,
                            "text": sub_chunk,
                            "metadata": chunk_metadata
                        })

        # 处理没有明确条款结构的文本
        if not chunks and text.strip():
            standard_chunks = self.text_splitter.split_text(text)
            for i, chunk in enumerate(standard_chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_id": f"standard_{i}",
                    "is_complete_article": False
                })

                # 为每个分块生成唯一ID
                chunk_id = self._generate_chunk_id(chunk, chunk_metadata)

                chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": chunk_metadata
                })

        return chunks

    def _generate_chunk_id(self, text: str, metadata: Dict[str, Any]) -> str:
        """为文本块生成唯一ID"""
        # 组合文本和关键元数据
        id_source = text[:100]  # 使用前100个字符作为源
        for field in ["source", "title", "article_number"]:
            if field in metadata:
                id_source += str(metadata[field])

        # 使用SHA-256生成哈希值
        return hashlib.sha256(id_source.encode('utf-8')).hexdigest()


# 使用示例
if __name__ == "__main__":
    processor = LegalDocumentProcessor(chunk_size=800, chunk_overlap=100)
    chunks = processor.load_directory("../../data/laws/business_laws")
    print(f"总共生成了 {len(chunks)} 个文本块")

    # 查看前3个块的内容示例
    for chunk in chunks[:3]:
        print("-" * 50)
        print(f"ID: {chunk['id']}")
        print(f"Article: {chunk['metadata'].get('article_number', 'N/A')}")
        print(f"Text: {chunk['text'][:100]}...")
        print(f"Metadata: {chunk['metadata']}")