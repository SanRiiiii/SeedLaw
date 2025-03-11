# test_embedding.py
from sentence_transformers import SentenceTransformer
from app.core.config import settings
import os



def test_embedding_model():
    try:
        # 打印当前工作目录和模型路径，用于调试
        print(f"当前工作目录: {os.getcwd()}")

        # 加载模型
        model = SentenceTransformer(settings.EMBEDDING_MODEL_PATH)
        print("模型加载成功!")

        # 测试编码
        test_texts = ["这是一个测试句子", "法律知识很重要"]
        embeddings = model.encode(test_texts)

        # 打印结果
        print(f"嵌入维度: {embeddings.shape}")
        print(f"第一个句子的嵌入向量前5个值: {embeddings[0][:5]}")

        return True
    except Exception as e:
        print(f"测试失败: {e}")
        return False


if __name__ == "__main__":
    test_embedding_model()