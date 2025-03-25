import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from tqdm import tqdm
from dotenv import load_dotenv
import os

class BGEEmbedding:
    """BGE嵌入模型封装"""
    
    def __init__(self, model_name=None):
        # 从环境变量获取模型路径
        load_dotenv()
        
        # 使用环境变量中的模型路径，如果没有则使用默认值
        model_path = os.getenv("EMBEDDING_MODEL_PATH", "BAAI/bge-large-zh-v1.5")
        
        # 如果提供了model_name参数，则优先使用它
        if model_name:
            model_path = model_name
            
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModel.from_pretrained(model_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        
    def encode(self, texts, batch_size=32, normalize=True):
        """
        将文本编码为向量
        
        参数:
            texts: 字符串或字符串列表
            batch_size: 批处理大小
            normalize: 是否对向量进行L2归一化
            
        返回:
            如果输入是单个字符串，返回对应的向量（一维numpy数组）
            如果输入是字符串列表，返回包含所有向量的二维numpy数组
        """
        # 处理单个字符串输入的情况
        single_input = False
        if isinstance(texts, str):
            texts = [texts]
            single_input = True
            
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
        
        result = np.vstack(embeddings)
        
        # 如果输入是单个字符串，返回单个向量
        if single_input:
            return result[0]
            
        return result
