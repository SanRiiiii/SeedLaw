import re
import markdown
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Tuple, Optional


class LegalDocumentProcessor:
    """法律文档处理器，专门处理具有法律特性的文档结构"""

    def __init__(self,
                 max_chunk_size: int = 1500,
                 overlap_size: int = 0):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

        # 法律文档结构正则表达式模式
        self.patterns = {
            'chapter': r'^第[一二三四五六七八九十百千]+章',  # 章
            'section': r'^第[一二三四五六七八九十百千]+节',  # 节
            'article': r'^第[一二三四五六七八九十百千]+条',  # 条
            'item': r'^[（(]\s*[一二三四五六七八九十]+\s*[）)]',  # 款：(一)
            'point': r'^[（(]\s*\d+\s*[）)]',  # 项：(1)
            'number_item': r'^\d+\.\s',  # 编号项：1.
            'number_only': r'^\d+、',  # 序号项：1、
        }

    def process_legal_markdown(self, file_path: str) -> List[Dict[str, Any]]:
        """
        处理法律类型的 Markdown 文件

        Args:
            file_path: 文件路径

        Returns:
            处理后的文本块
        """
        try:
            # 读取文件
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()

            # 提取文件元数据
            file_metadata = self._extract_metadata_from_filename(file_path)

            # 转换为 HTML
            html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            soup = BeautifulSoup(html, 'html.parser')

            # 处理 HTML
            chunks = self._process_legal_html(soup, file_metadata)

            return chunks

        except Exception as e:
            print(f"处理法律文档 {file_path} 时发生错误: {e}")
            return []

    def _extract_metadata_from_filename(self, file_path: str) -> Dict[str, Any]:
        """从文件名提取基本元数据（不包含文档类型判断）"""
        import os
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)

        # 返回基本信息
        return {
            "source": file_path,
            "filename": filename,
            "document_name": name
        }

    def _process_legal_html(self,
                            soup: BeautifulSoup,
                            file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理法律文档 HTML"""
        chunks = []

        # 当前法律结构上下文
        legal_context = {
            "chapter": "",
            "section": "",
            "article": "",
            "item": "",
            "point": ""
        }

        # 标题上下文
        heading_context = {f"h{i}": "" for i in range(1, 7)}
        heading_path = ""

        # 当前文本收集器
        current_text = []
        current_metadata = {}

        # 遍历所有顶级元素
        for element in soup.find_all(recursive=False):
            new_chunks = self._process_legal_element(
                element,
                legal_context,
                heading_context,
                heading_path,
                file_metadata
            )
            chunks.extend(new_chunks)

        return chunks

    def _process_legal_element(self,
                               element: Tag,
                               legal_context: Dict[str, str],
                               heading_context: Dict[str, str],
                               heading_path: str,
                               file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理法律文档中的单个元素"""
        chunks = []

        # 如果是标题元素
        if element.name and element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            level = int(element.name[1])
            text = element.get_text().strip()

            # 更新标题上下文
            heading_context[element.name] = text

            # 清除所有更低级别的标题
            for i in range(level + 1, 7):
                heading_context[f"h{i}"] = ""

            # 更新标题路径
            heading_path = self._build_heading_path(heading_context)

            # 检查是否是法律结构标记
            for context_type, pattern in self.patterns.items():
                if re.search(pattern, text):
                    if context_type == 'chapter':
                        legal_context['chapter'] = text
                        # 进入新章节时，清除下级结构
                        legal_context['section'] = ""
                        legal_context['article'] = ""
                        legal_context['item'] = ""
                        legal_context['point'] = ""
                    elif context_type == 'section':
                        legal_context['section'] = text
                        # 进入新节时，清除下级结构
                        legal_context['article'] = ""
                        legal_context['item'] = ""
                        legal_context['point'] = ""
                    break

        # 如果是段落或其他文本块
        elif element.name and element.name in ['p', 'div', 'blockquote']:
            text = element.get_text().strip()
            if text:
                # 检查段落是否包含法律特定结构
                structure_type = None
                for context_type, pattern in self.patterns.items():
                    if re.search(pattern, text):
                        structure_type = context_type
                        if context_type == 'article':
                            legal_context['article'] = text
                            # 新条时，清除下级结构
                            legal_context['item'] = ""
                            legal_context['point'] = ""
                        elif context_type == 'item':
                            legal_context['item'] = text
                            legal_context['point'] = ""
                        elif context_type == 'point':
                            legal_context['point'] = text
                        break

                # 构建块元数据
                metadata = file_metadata.copy()
                metadata.update({
                    "headings": {k: v for k, v in heading_context.items() if v},
                    "heading_path": heading_path,
                    "legal_context": {k: v for k, v in legal_context.items() if v},
                })

                # 如果是条款，单独成块
                if structure_type == 'article':
                    chunks.append({
                        "content": text,
                        **metadata,
                        "structure_type": structure_type
                    })
                else:
                    # 应用法律文档特殊分块规则
                    legal_chunks = self._split_legal_text(text, metadata, structure_type)
                    chunks.extend(legal_chunks)

        # 处理列表
        elif element.name and element.name in ['ul', 'ol']:
            list_chunks = self._process_legal_list(
                element,
                legal_context,
                heading_context,
                heading_path,
                file_metadata
            )
            chunks.extend(list_chunks)

        # 递归处理子元素
        elif hasattr(element, 'children'):
            for child in element.children:
                if isinstance(child, Tag):
                    child_chunks = self._process_legal_element(
                        child,
                        legal_context,
                        heading_context,
                        heading_path,
                        file_metadata
                    )
                    chunks.extend(child_chunks)

        return chunks

    def _process_legal_list(self,
                            list_element: Tag,
                            legal_context: Dict[str, str],
                            heading_context: Dict[str, str],
                            heading_path: str,
                            file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理法律文档中的列表"""
        chunks = []

        # 构建元数据
        metadata = file_metadata.copy()
        metadata.update({
            "headings": {k: v for k, v in heading_context.items() if v},
            "heading_path": heading_path,
            "legal_context": {k: v for k, v in legal_context.items() if v},
        })

        # 收集列表项文本
        list_items = []
        for li in list_element.find_all('li', recursive=False):
            list_items.append(li.get_text().strip())

        # 如果列表项少且短，合并为一个块
        if len(list_items) <= 5 and sum(len(item) for item in list_items) < self.max_chunk_size:
            combined_text = "\n- " + "\n- ".join(list_items)
            chunks.append({
                "content": combined_text,
                **metadata,
                "structure_type": "list"
            })
        else:
            # 否则每个列表项单独成块
            for item in list_items:
                # 检查列表项是否是法律结构项
                structure_type = None
                for context_type, pattern in self.patterns.items():
                    if re.search(pattern, item):
                        structure_type = context_type
                        break

                legal_chunks = self._split_legal_text(item, metadata, structure_type)
                chunks.extend(legal_chunks)

        return chunks

    def _split_legal_text(self,
                          text: str,
                          metadata: Dict[str, Any],
                          structure_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """根据法律文档特性分割文本"""
        chunks = []

        # 如果是特定结构类型，添加标记
        if structure_type:
            metadata = metadata.copy()
            metadata["structure_type"] = structure_type

        # 如果文本较短，直接作为一个块
        if len(text) <= self.max_chunk_size:
            chunks.append({
                "content": text,
                **metadata
            })
            return chunks

        # 尝试在自然段落处分割
        paragraphs = re.split(r'\n\s*\n', text)

        current_chunk = ""

        for para in paragraphs:
            # 如果当前段落本身就超过最大长度
            if len(para) > self.max_chunk_size:
                # 如果当前块不为空，先保存它
                if current_chunk:
                    chunks.append({
                        "content": current_chunk,
                        **metadata
                    })
                    current_chunk = ""

                # 按句子分割大段落
                sentences = re.split(r'([。！？；:;])', para)
                current_sentence = ""

                for i in range(0, len(sentences), 2):
                    if i + 1 < len(sentences):
                        sentence = sentences[i] + sentences[i + 1]
                    else:
                        sentence = sentences[i]

                    if len(current_sentence) + len(sentence) <= self.max_chunk_size:
                        current_sentence += sentence
                    else:
                        if current_sentence:
                            chunks.append({
                                "content": current_sentence,
                                **metadata
                            })
                        current_sentence = sentence

                if current_sentence:
                    chunks.append({
                        "content": current_sentence,
                        **metadata
                    })

            # 正常处理段落
            elif len(current_chunk) + len(para) + 2 <= self.max_chunk_size:
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
            else:
                chunks.append({
                    "content": current_chunk,
                    **metadata
                })
                current_chunk = para

        # 添加最后一个块
        if current_chunk:
            chunks.append({
                "content": current_chunk,
                **metadata
            })

        return chunks

    def _build_heading_path(self, headings: Dict[str, str]) -> str:
        """构建标题路径"""
        parts = []
        for i in range(1, 7):
            if headings.get(f"h{i}"):
                parts.append(headings[f"h{i}"])
        return " > ".join(parts)


# 使用示例
if __name__ == "__main__":
    processor = LegalDocumentProcessor(max_chunk_size=500)
    chunks = processor.process_legal_markdown("contract_example.md")

    print(f"共生成 {len(chunks)} 个文本块")

    for i, chunk in enumerate(chunks[:5]):  # 打印前5个块作为示例
        print(f"\n=== 块 {i + 1} ===")
        if "legal_context" in chunk:
            legal_ctx = chunk["legal_context"]
            if "chapter" in legal_ctx and legal_ctx["chapter"]:
                print(f"章节: {legal_ctx['chapter']}")
            if "article" in legal_ctx and legal_ctx["article"]:
                print(f"条款: {legal_ctx['article']}")
        print(f"内容: {chunk['content'][:100]}..." if len(chunk['content']) > 100 else f"内容: {chunk['content']}")