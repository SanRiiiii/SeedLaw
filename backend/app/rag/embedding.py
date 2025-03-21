import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from tqdm import tqdm
from vector_store import VectorStore
from core.config import settings
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility

class BGEEmbedding:
    """BGE嵌入模型封装"""
    
    def __init__(self, model_name="BAAI/bge-large-zh-v1.5"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
    def encode(self, texts, batch_size=32, normalize=True):
        """将文本编码为向量"""
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            # 编码
            encoded_input = self.tokenizer(
                batch_texts, 
                padding=True, 
                truncation=True, 
                max_length=512, 
                return_tensors='pt'
            ).to(self.device)
            
            # 计算嵌入
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                batch_embeddings = model_output.last_hidden_state[:, 0]
                
                # 归一化
                if normalize:
                    batch_embeddings = torch.nn.functional.normalize(batch_embeddings, p=2, dim=1)
                
                embeddings.append(batch_embeddings.cpu().numpy())
        
        return np.vstack(embeddings)
