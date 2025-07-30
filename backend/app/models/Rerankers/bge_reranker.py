# app/rag/reranker.py
from typing import List, Dict, Any
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import os
import sys
import logging
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from app.core.config import settings

logger = logging.getLogger(__name__)

class BAAIReranker:
    """
    使用BAAI模型进行文档重排序的类
    
    重排序器(Reranker)用于优化初步检索结果的排序，提高检索的精确度。
    它接收初始检索（如向量检索或关键词检索）的结果，然后使用交互式的文本匹配模型对查询和文档对
    进行精确相关性评分，最终返回按新得分重新排序的文档列表。
    
    与基于单文本编码的向量检索不同，重排序器同时考虑查询和文档内容的语义交互，能更精确地
    判断文档与查询的相关性，但计算成本较高，因此通常用于对少量候选结果进行精细排序。
    
    使用流程：
    1. 首先通过向量检索和/或关键词检索获取初始候选文档（如top-100）
    2. 使用重排序器对这些候选文档进行精确评分
    3. 返回评分最高的top-k文档作为最终结果
    """
    
    def __init__(self):
        model_path = settings.RERANKER_MODEL_PATH
        self.model_path = model_path
        self.initialize_reranker()
        
    def initialize_reranker(self):
        """加载模型和tokenizer"""
        try:
    
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path, local_files_only=True)

            # 如果有GPU，将模型移到GPU上
            # if torch.cuda.is_available():
            #     self.model = self.model.to("cuda")
            
            self.is_initialized = True
            logger.info(f"BAAI重排序器初始化成功: {self.model_path}")
        except Exception as e:
            logger.error(f"初始化BAAI重排序器失败: {e}")
            self.is_initialized = False


    def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        对文档进行重排序
        
        Args:
            query: 查询文本
            documents: 需要重排序的文档列表
            top_k: 返回的top-k文档数量
            
        Returns:
            重排序后的文档列表
        """
        if not self.is_initialized or not documents:
            return documents[:top_k]
            
        # 准备文本对
        text_pairs = []
        for doc in documents:
            text_pairs.append([query, doc["content"]])
            
        # 计算相关性分数
        with torch.no_grad():
            inputs = self.tokenizer(
                text_pairs, 
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
            outputs = self.model(**inputs)
            scores = outputs.logits.squeeze(-1).cpu().tolist()
            
        scored_docs = [(doc, score) for doc, score in zip(documents, scores)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 取top_k结果
        reranked_results = []
        for doc, score in scored_docs[:top_k]:
            result = {}
            result['doc'] = doc.copy()
            result["reranker_score"] = score
            reranked_results.append(result)
            
        return [result['doc'] for result in reranked_results]

