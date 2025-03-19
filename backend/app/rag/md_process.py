import re
import markdown
from bs4 import BeautifulSoup, Tag
from typing import List, Dict, Any, Tuple, Optional
import os
from datetime import datetime
import uuid

'''
法规文件处理预期：
1. 单个条例成chunk
2. 每个chunk需要有的元数据：
- 法律/法规名称
- 立法层级 先不要
- 是否生效
- 章节条
'''

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
            'article': r'^第[一二三四五六七八九十百千]+条'  # 条
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
            
            # 检查法律是否生效
            is_effective = self._check_law_effectiveness(md_content)
            file_metadata["is_effective"] = is_effective

            # 转换为 HTML
            html = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            soup = BeautifulSoup(html, 'html.parser')

            # 递归处理html块
            chunks = self._process_legal_html(soup, file_metadata)

            return chunks

        except Exception as e:
            print(f"处理法律文档 {file_path} 时发生错误: {e}")
            return []

    def _extract_metadata_from_filename(self, file_path: str) -> Dict[str, Any]:
        """从文件名提取基本元数据"""
        filename = os.path.basename(file_path)
        name, _ = os.path.splitext(filename)
        
        # 提取法律名称和日期
        # 例如从 "公司法(2023-12-29).md" 提取 "公司法" 和 "2023-12-29"
        match = re.match(r"(.+)\((\d{4}-\d{2}-\d{2})\)", name)
        if match:
            law_name = match.group(1)
            effective_date = match.group(2)
        else:
            law_name = name
            effective_date = None

        # 返回基本信息
        return {
            "document_name": law_name,
            "effective_date": effective_date
        }

    def _check_law_effectiveness(self, content: str) -> bool:
        """
        检查法律是否生效
        通过检查文档末尾的附则来判断法律是否生效
        """
        # 获取最后2000个字符进行检查
        end_content = content[-2000:]
        
        # 检查是否有废止或失效的明确标记
        ineffective_patterns = [
            r"本法(已)?废止",
            r"本法(已)?失效",
            r"本法自\d{4}年\d{1,2}月\d{1,2}日(起)?废止",
        ]
        
        for pattern in ineffective_patterns:
            if re.search(pattern, end_content):
                return False
        
        # 检查生效日期
        effective_date_match = re.search(r"本(?:法|条例|规定|细则|办法|规则|通知|决定)自(\d{4}年\d{1,2}月\d{1,2}日)起(?:施行|生效|实施)", end_content)
        if effective_date_match:
            
            # 提取日期
            date_str = effective_date_match.group(1)
            date_str = re.sub(r'[年月]', '-', date_str).replace('日', '')
            effective_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # 如果生效日期在未来，则标记为未生效
            if effective_date > datetime.now():
                return False
        
        return True
    
    

    def _process_legal_html(self,
                            soup: BeautifulSoup,
                            file_metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理法律文档的HTML"""
        chunks = []
        current_chunk = None

        # 当前法律结构上下文
        legal_context = {
            "chapter": "",
            "section": ""
        }

        # 遍历所有元素
        for element in soup.find_all():
            text = element.get_text().strip()
            if not text:
                continue

            # 处理章节标题
            is_structure = False
            for context_type, pattern in self.patterns.items():
                if re.search(pattern, text):
                    if context_type == 'chapter':
                        legal_context['chapter'] = text
                        legal_context['section'] = ""
                        is_structure = True
                    elif context_type == 'section':
                        legal_context['section'] = text
                        is_structure = True
                    elif context_type == 'article':
                        # 如果有当前chunk，保存它
                        if current_chunk:
                            chunks.append(current_chunk)
                        
                        # 创建新的chunk
                        current_chunk = {
                            "content": text,  # 从条款标题开始
                            "metadata": {
                                **file_metadata,
                                "chapter": legal_context["chapter"],
                                "section": legal_context["section"]
                            }
                        }
                        is_structure = True
                    break
            
            # 如果不是结构标记且有当前chunk，将内容添加到当前chunk
            if not is_structure and current_chunk:
                current_chunk["content"] += "\n" + text

        # 保存最后一个chunk
        if current_chunk:
            chunks.append(current_chunk)

        for chunk in chunks:
            chunk['uuid'] = str(uuid.uuid4())

        return chunks

    def _split_legal_text(self,
                          text: str,
                          metadata: Dict[str, Any],
                          structure_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        chunk过长时进行段落分割
        根据法律文档特性分割文本
        """
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


'''
process_legal_markdown
  ├── _extract_metadata_from_filename
  ├── markdown.markdown (将 Markdown 转换为 HTML)
  ├── BeautifulSoup (解析 HTML)
  └── _process_legal_html
      └── _process_legal_element
          ├── _build_heading_path (如果是标题)
          ├── _split_legal_text (如果是段落或文本块)
          └── _process_legal_list (如果是列表)
              └── _split_legal_text (处理列表项)

'''

# 使用示例
if __name__ == "__main__":
    processor = LegalDocumentProcessor(max_chunk_size=1500)
    chunks = processor.process_legal_markdown("/Users/jing/Desktop/毕设/code_pycharm/pythonProject/legal-assistant/backend/data/laws/business_laws/公司法(2023-12-29).md")

    print(f"共生成 {len(chunks)} 个文本块")

    for i, chunk in enumerate(chunks[:50]):  # 打印前10个块作为示例
        print(f"\n=== 块 {i + 1} ===")
        # 打印元数据
        metadata = chunk["metadata"]
        print("元数据:")
        print(f"文档名称: {metadata['document_name']}")
        print(f"生效日期: {metadata['effective_date']}")
        print(f"是否生效: {metadata['is_effective']}")
        if metadata['chapter']:
            print(f"章: {metadata['chapter']}")
        if metadata['section']:
            print(f"节: {metadata['section']}")
        
        # 打印内容
        print("\n内容:")
        print(chunk['content'])
        print("-" * 80)