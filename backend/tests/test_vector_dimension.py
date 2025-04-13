import sys
import os
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), './')))

from app.rag.embedding import BGEEmbedding
import numpy as np

def test_vector_dimension():
    """测试嵌入向量的维度"""
    print("初始化BGE嵌入模型...")
    embedding_model = BGEEmbedding()
    
    # 测试单个字符串输入
    test_text = "测试向量维度是否为1024"
    print(f"\n测试单个字符串输入: '{test_text}'")
    
    # 生成嵌入向量
    print("生成嵌入向量...")
    vector = embedding_model.encode(test_text)
    
    # 检查向量信息
    print("\n向量信息:")
    print(f"类型: {type(vector)}")
    if isinstance(vector, np.ndarray):
        print(f"形状: {vector.shape}")
        print(f"维度: {vector.shape[0]}")  # 维度应该是1024
        print(f"数据类型: {vector.dtype}")
    else:
        print(f"长度: {len(vector)}")  # 长度应该是1024
    
    # 输出向量的部分值
    print(f"\n向量的前5个值: {vector[:5]}")
    print(f"向量的后5个值: {vector[-5:]}")
    
    # 输出统计信息
    if isinstance(vector, np.ndarray):
        print(f"\n统计信息:")
        print(f"最小值: {vector.min()}")
        print(f"最大值: {vector.max()}")
        print(f"平均值: {vector.mean()}")
        print(f"标准差: {vector.std()}")
    
    # 测试字符串列表输入
    test_texts = ["第一个测试文本", "第二个测试文本"]
    print(f"\n测试字符串列表输入: {test_texts}")
    
    # 生成嵌入向量
    vectors = embedding_model.encode(test_texts)
    
    # 检查向量信息
    print("\n向量信息:")
    print(f"类型: {type(vectors)}")
    if isinstance(vectors, np.ndarray):
        print(f"形状: {vectors.shape}")
        print(f"样本数: {vectors.shape[0]}")
        print(f"维度: {vectors.shape[1]}")  # 维度应该是1024
        print(f"数据类型: {vectors.dtype}")
    
    # 返回单个向量的维度
    if isinstance(vector, np.ndarray):
        return vector.shape[0]
    else:
        return len(vector)

if __name__ == "__main__":
    print("开始测试向量维度...")
    try:
        dimension = test_vector_dimension()
        print(f"\n测试完成。向量维度为: {dimension}")
        if dimension == 1024:
            print("✓ 验证成功: 向量维度为预期的1024")
        else:
            print(f"× 验证失败: 向量维度为{dimension}，而非预期的1024")
    except Exception as e:
        print(f"\n测试过程中出现错误: {e}") 