import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from app.rag.embedding import BGEEmbedding
import numpy as np

def test_embedding_dimension():
    """测试BGEEmbedding模型输出的向量维度"""
    # 初始化嵌入模型
    embedding_model = BGEEmbedding()
    
    # 测试单个文本
    test_text = "这是一个测试文本，用于检查嵌入向量的维度"
    print(f"测试文本: \"{test_text}\"")
    
    # 生成嵌入向量
    embedding_vector = embedding_model.encode([test_text])
    
    # 打印向量信息
    print("\n向量详细信息:")
    print(f"向量类型: {type(embedding_vector)}")
    
    if isinstance(embedding_vector, np.ndarray):
        print(f"向量形状: {embedding_vector.shape}")
        print(f"向量维度: {embedding_vector.shape[1]}")
        print(f"数据类型: {embedding_vector.dtype}")
    else:
        print(f"向量长度: {len(embedding_vector)}")
    
    # 打印向量的前5个值和后5个值
    if isinstance(embedding_vector, np.ndarray):
        print(f"\n向量前5个值: {embedding_vector[0][:5]}")
        print(f"向量后5个值: {embedding_vector[0][-5:]}")
    else:
        print(f"\n向量前5个值: {embedding_vector[:5]}")
        print(f"向量后5个值: {embedding_vector[-5:]}")
    
    # 测试处理单个字符串的情况
    print("\n测试单个字符串输入:")
    embedding_single = embedding_model.encode(test_text)
    
    if isinstance(embedding_single, np.ndarray):
        print(f"向量形状: {embedding_single.shape}")
        print(f"向量维度: {embedding_single.shape[0] if len(embedding_single.shape) == 1 else embedding_single.shape[1]}")
    else:
        print(f"向量类型: {type(embedding_single)}")
        print(f"向量长度: {len(embedding_single)}")
    
    # 检查向量是否为浮点数
    if isinstance(embedding_single, np.ndarray):
        print(f"是否为浮点数: {np.issubdtype(embedding_single.dtype, np.floating)}")
    elif isinstance(embedding_single, list):
        print(f"是否为浮点数: {all(isinstance(x, float) for x in embedding_single[:5])}")
    
    return embedding_vector

if __name__ == "__main__":
    print("开始测试BGEEmbedding模型输出维度...")
    try:
        vector = test_embedding_dimension()
        print("\n测试完成。")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}") 