import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from tqdm import tqdm
from app.db.vector_store import VectorStore
from app.core.config import settings
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.rag.embedding import BGEEmbedding
import json


def setup_milvus_collection(collection_name,fields):
    """设置Milvus集合"""
    # 连接到Milvus服务
    vector_db = VectorStore()
    vector_db.connect_to_milvus()
    if not vector_db.check_collection_exists(collection_name):
        vector_db.create_collection(fields,collection_name,description="法律文档分块集合")
    print(f"已成功创建集合 {collection_name} 并设置索引")
    return 


def load_chunks_to_milvus(chunks_file, collection_name):
    """将分块加载到Milvus"""
    # 加载分块
    with open(chunks_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # 初始化BGE嵌入模型
    embedder = BGEEmbedding()
    
    # 连接到Milvus
    connections.connect("default", host="localhost", port="19530")
    collection = Collection(collection_name)
    collection.load()
    
    # 准备数据
    uuids = []
    contents = []
    document_names = []
    chapters = []
    sections = []
    effective_dates = []
    is_effectives = []
    texts_to_embed = []
    
    for chunk in chunks:
        uuids.append(chunk['uuid'])
        contents.append(chunk['content'])
        
        # 提取元数据
        metadata = chunk['metadata']
        document_names.append(metadata.get('document_name', ''))
        chapters.append(metadata.get('chapter', ''))
        sections.append(metadata.get('section', ''))
        effective_dates.append(metadata.get('effective_date', ''))
        is_effectives.append(metadata.get('is_effective', True))
        
        # 准备文本进行嵌入
        texts_to_embed.append(chunk['content'])
    
    # 生成嵌入
    print("生成文本嵌入...")
    embeddings = embedder.encode(texts_to_embed)
    
    # 插入数据
    print("将数据插入Milvus...")
    entities = [
        uuids,
        contents,
        document_names,
        chapters,
        sections,
        effective_dates,
        is_effectives,
        embeddings
    ]
    
    # 分批插入以避免内存问题
    batch_size = 1000
    for i in tqdm(range(0, len(uuids), batch_size)):
        end = min(i + batch_size, len(uuids))
        batch_entities = [entity[i:end] for entity in entities]
        collection.insert(batch_entities)
    
    # 刷新集合以确保数据可见
    collection.flush()
    
    print(f"成功将 {len(uuids)} 个分块插入到 Milvus 集合 {collection_name}")
    
    # 显示集合统计信息
    print(f"集合统计: {collection.num_entities} 个实体")
    
    return collection

def test_vector_search(query, collection_name=None, top_k=5):
    """
    测试向量检索功能
    
    参数:
    - query: 用户查询字符串
    - collection_name: 要搜索的集合名称，默认使用配置中的集合
    - top_k: 返回的结果数量
    
    返回:
    - 检索到的文档列表
    """
    # 使用默认集合名称（如果未指定）
    if collection_name is None:
        collection_name = settings.MILVUS_COLLECTION
    
    # 初始化向量存储和嵌入模型
    vector_db = VectorStore()
    vector_db.connect_to_milvus()
    embedder = BGEEmbedding()
    
    # 检查集合是否存在
    if not vector_db.check_collection_exists(collection_name):
        print(f"错误: 集合 {collection_name} 不存在")
        return []
    
    # 对查询文本进行嵌入
    query_embedding = embedder.encode([query])[0]
    
    # 定义要返回的字段
    output_fields = ["content", "document_name", "chapter", "section", "effective_date", "is_effective"]
    
    # 执行搜索
    results = vector_db.search_vectors(
        collection_name=collection_name,
        query_embedding=query_embedding,
        limit=top_k,
        output_fields=output_fields
    )
    
    # 展示结果
    print(f"\n检索到 {len(results)} 条结果:")
    print("-" * 80)
    
    for i, result in enumerate(results):
        print(f"结果 #{i+1} (相似度: {result['score']:.4f})")
        print(f"文档: {result['document_name']}")
        print(f"章节: {result['chapter']} - {result['section']}")
        print(f"生效状态: {'已生效' if result['is_effective'] else '未生效'} (生效日期: {result['effective_date']})")
        print(f"内容: {result['content'][:200]}..." if len(result['content']) > 200 else f"内容: {result['content']}")
        print("-" * 80)
    
    return results

# 使用示例
if __name__ == "__main__":
    

    collection_name =settings.MILVUS_COLLECTION
    # dim = settings.EMBEDDING_DIMENSION

    # # 设置集合
    # fields = [
    #     FieldSchema(name="uuid", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
    #     FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
    #     FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=256),
    #     FieldSchema(name="chapter", dtype=DataType.VARCHAR, max_length=256),
    #     FieldSchema(name="section", dtype=DataType.VARCHAR, max_length=256),
    #     FieldSchema(name="effective_date", dtype=DataType.VARCHAR, max_length=20),
    #     FieldSchema(name="is_effective", dtype=DataType.BOOL),
    #     FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
    # ]

    # setup_milvus_collection(collection_name,fields=fields)  # BGE-large-zh 维度为1024
    
    # # 加载数据
    # chunks_file = "../data/chunks/公司法(2023-12-29)_chunks.json"
    # collection = load_chunks_to_milvus(chunks_file, collection_name)
    
    # 测试向量召回
    print("\n===== 测试向量召回功能 =====")
    test_query = input("请输入查询语句: ")
    test_vector_search(test_query, collection_name)    