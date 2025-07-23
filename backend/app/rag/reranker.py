import os
import sys
from typing import List, Dict, Any
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.models.Rerankers.bge_reranker import BAAIReranker

'''
def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
返回chunk数据：doc，和rerank的分数：score
'''

class Reranker:
    def __init__(self):
        self.reranker = BAAIReranker()


    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10):
        return self.reranker.rerank(query, documents, top_k)