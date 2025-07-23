'''
elasticSearch 关键词搜索器 版本为ES8.x
最后的search接口langchain的结构进行集成，作为检索器的一部分

支持能力：
搜索: def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]
 result = {
                    "uuid": doc.get("uuid", ""),
                    "content": content,
                    "document_name": doc.get("document_name", ""),
                    "chapter": doc.get("chapter", ""),
                    "section": doc.get("section", ""),
                    "effective_date": doc.get("effective_date", ""),
                    "is_effective": doc.get("is_effective", False),
                }


'''
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from typing import List, Dict, Any
from app.db.es_search import ESSearcher


class SparseSearch:
    """Elasticsearch搜索器，替代BM25搜索实现"""

    def __init__(self):
        self.es_search = ESSearcher()

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        return self.es_search.search(query, top_k)

# if __name__ == "__main__":
#     sparse_search = SparseSearch()
#     results = sparse_search.search(query="公司注册需要哪些材料", top_k=10)
#     print(results)
       