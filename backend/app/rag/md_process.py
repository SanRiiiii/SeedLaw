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
            effectiveness_info = self._check_law_effectiveness(md_content,file_metadata["effective_date"])

            # 将字典中的值添加到file_metadata
            file_metadata["is_effective"] = effectiveness_info["is_effective"]
            file_metadata["effective_date"] = effectiveness_info["effective_date"]
          

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
        
        # 先尝试提取带括号的日期格式 (YYYY-MM-DD)
        date_match = re.search(r'\((\d{4}-\d{1,2}-\d{1,2})\)', name)
        if date_match:
            # 提取日期并转换为YYYYMMDD格式
            date_str = date_match.group(1)
            try:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                effective_date = date_obj.strftime('%Y%m%d')
                # 移除日期部分，得到纯法律名称
                law_name = name.split('(')[0].strip()
            except ValueError:
                effective_date = ""
                law_name = name
        else:
            # 尝试提取格式：法律名称-YYYYMMDD 或 法律名称_YYYYMMDD
            date_match = re.search(r'[-_](\d{8})$', name)
            if date_match:
                effective_date = date_match.group(1)
                # 移除日期部分，得到纯法律名称
                law_name = re.sub(r'[-_]\d{8}$', '', name)
            else:
                effective_date = ""
                law_name = name
            
        # 返回基本信息
        return {
            "document_name": law_name,
            "effective_date": effective_date
        }

    def _check_law_effectiveness(self, content: str, effective_date: str) -> Dict[str, Any]:
        """
        检查法律是否生效
        通过检查文档末尾的附则来判断法律是否生效
        """
        # 获取最后2000个字符进行检查
        end_content = content[-2000:]
        
        # 检查生效日期
        # 部分文件的生效日期与发布日期不同，以此适配
        effective_date_match = re.search(r"本(?:法|条例|规定|细则|办法|规则|通知|决定)自(\d{4}年\d{1,2}月\d{1,2}日)起(?:施行|生效|实施)", end_content)

        # 从文件内容提取到的生效日期
        content_date = ""
        if effective_date_match:
            # 提取日期
            date_str = effective_date_match.group(1)
            date_str = re.sub(r'[年月]', '-', date_str).replace('日', '')
            try:
                # 转换为datetime对象再转回字符串，确保格式一致
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                content_date = date_obj.strftime('%Y%m%d')
            except ValueError:
                content_date = ""
        
        # 优先使用文件内容提取的日期，如果没有则使用文件名中的日期
        final_date = content_date if content_date else effective_date
        
        # 判断是否生效（仅用于比较）
        is_effective = True
        
        # 如果有日期，判断是否生效
        if final_date:
            try:
                # 将日期字符串转为datetime进行比较
                date_obj = datetime.strptime(final_date, '%Y%m%d')
                # 如果生效日期在未来，则标记为未生效
                if date_obj > datetime.now():
                    is_effective = False
            except ValueError:
                # 日期格式不正确，默认为生效
                pass
            
        # 检查是否有废止或失效的明确标记
        ineffective_patterns = [
            r"本法(已)?废止",
            r"本法(已)?失效",
            r"本法自\d{4}年\d{1,2}月\d{1,2}日(起)?废止",
        ]
        
        for pattern in ineffective_patterns:
            if re.search(pattern, end_content):
                is_effective = False
                break
            
        return {
            "is_effective": is_effective,
            "effective_date": final_date  # 返回字符串格式的日期
        }
               

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

