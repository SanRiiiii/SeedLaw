'''
提供和embedding模型交互的接口


'''
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
import torch
from transformers import AutoTokenizer, AutoModel
import numpy as np
from tqdm import tqdm
import logging
from core.config import Settings

logger = logging.getLogger(__name__)
settings = Settings()

class BGEEmbedding:
    """BGE嵌入模型封装"""
    
    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = settings.EMBEDDING_MODEL_PATH
        print(self.model_path)
        try:
    
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, local_files_only=True)
            self.model = AutoModel.from_pretrained(self.model_path, local_files_only=True)

            # 如果有GPU，将模型移到GPU上
            if torch.cuda.is_available():
                self.model = self.model.to("cuda")
            
            self.is_initialized = True
            logger.info(f"词向量器初始化成功: {self.model_path}")
        except Exception as e:
            logger.error(f"初始化词向量器失败: {e}")
            self.is_initialized = False

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
        print(result)

        # 如果输入是单个字符串，返回单个向量
        if single_input:
            return result[0]
        
     
            
        return result
    
if __name__ == "__main__":
    embedding = BGEEmbedding()
    embedding.encode("你好")
