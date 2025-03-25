# app/rag/reranker.py
from typing import List, Dict, Any
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import os

class BAAIReranker:
    """使用BAAI模型进行文档重排序的类"""
    
    def __init__(self):
        load_dotenv()
        model_path = os.getenv("RERANKER_MODEL_PATH","BAAI/bge-reranker-large")
        self.model_name = model_path
        self.initialize_reranker()
        
    def initialize_reranker(self):
        """加载模型和tokenizer"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            
            # 如果有GPU，将模型移到GPU上
            # if torch.cuda.is_available():
            #     self.model = self.model.to("cuda")
            
            self.is_initialized = True
            print(f"BAAI重排序器初始化成功: {self.model_name}")
        except Exception as e:
            print(f"初始化BAAI重排序器失败: {e}")
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
            text_pairs.append([query, doc["text"]])
            
        # 计算相关性分数
        with torch.no_grad():
            inputs = self.tokenizer(
                text_pairs, 
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512
            )
            
            # 将输入移动到相应设备
            if torch.cuda.is_available():
                inputs = {k: v.to("cuda") for k, v in inputs.items()}
                
            outputs = self.model(**inputs)
            scores = outputs.logits.squeeze(-1).cpu().tolist()
            
        # 将分数与文档关联并排序
        scored_docs = [(doc, score) for doc, score in zip(documents, scores)]
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # 取top_k结果
        reranked_results = []
        for doc, score in scored_docs[:top_k]:
            result = doc.copy()
            result["reranker_score"] = score
            reranked_results.append(result)
            
        return reranked_results


# 测试代码
if __name__ == "__main__":
    reranker = BAAIReranker()
    
    # 测试数据
    query = "公司注册需要哪些材料"
    docs = [
        {"id": 1, "text": "公司注册需要准备的材料包括：营业执照、组织机构代码证、税务登记证等。"},
        {"id": 2, "text": "企业设立登记需要的材料：公司名称预先核准通知书、公司章程、股东会决议等。"},
        {"id": 3, "text": "这篇文章与公司注册无关，主要讨论了人工智能的发展历程。"}
    ]
    
    results = reranker.rerank(query, docs)
    
    print("重排序结果:")
    for i, doc in enumerate(results, 1):
        print(f"排名 {i}:")
        print(f"文档ID: {doc['id']}")
        print(f"文本: {doc['text']}")
        print(f"分数: {doc['reranker_score']:.4f}")
        print("-" * 50)