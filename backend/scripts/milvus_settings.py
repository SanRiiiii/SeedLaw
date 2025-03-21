from tqdm import tqdm
from vector_store import VectorStore
from core.config import settings
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
    return collection


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
    ids = []
    contents = []
    document_names = []
    chapters = []
    sections = []
    effective_dates = []
    is_effectives = []
    texts_to_embed = []
    
    for chunk in chunks:
        ids.append(chunk['uuid'])
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
        ids,
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
    for i in tqdm(range(0, len(ids), batch_size)):
        end = min(i + batch_size, len(ids))
        batch_entities = [entity[i:end] for entity in entities]
        collection.insert(batch_entities)
    
    # 刷新集合以确保数据可见
    collection.flush()
    
    print(f"成功将 {len(ids)} 个分块插入到 Milvus 集合 {collection_name}")
    
    # 显示集合统计信息
    print(f"集合统计: {collection.num_entities} 个实体")
    
    return collection

# 使用示例
if __name__ == "__main__":

    collection_name =settings.MILVUS_COLLECTION
    dim = settings.MILVUS_DIM

    # 设置集合
    fields = [
        FieldSchema(name="uuid", dtype=DataType.VARCHAR, is_primary=True, max_length=36),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=4096),
        FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="chapter", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="section", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="effective_date", dtype=DataType.VARCHAR, max_length=20),
        FieldSchema(name="is_effective", dtype=DataType.BOOL),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=dim)
    ]

    setup_milvus_collection(collection_name,fields=fields)  # BGE-large-zh 维度为1024
    
    # 加载数据
    chunks_file = "backend/data/processed_chunks/all_chunks.json"
    collection = load_chunks_to_milvus(chunks_file, collection_name)