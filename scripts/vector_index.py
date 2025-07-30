#!/usr/bin/env python3
"""
重新索引脚本
使用新的embedding模型重新对/backend/data/chunks/related_laws里的数据进行索引
并存入Milvus的新集合finetune_data
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from tqdm import tqdm

# 添加项目路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from backend.app.db.milvus import VectorStore
from backend.app.models.Embeddings.bge_embedding import BGEEmbedding
from backend.app.core.config import Settings
from pymilvus import FieldSchema, DataType

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化配置
settings = Settings()

class VectorIndexer:
    def __init__(self):
        """初始化向量索引器"""
        self.embedding_model = BGEEmbedding()
        self.vector_store = VectorStore()
        self.collection_name = "finetune_data"
        self.data_dir = Path("../backend/data/chunks/related_laws")

        
        # 确保embedding模型初始化成功
        if not self.embedding_model.is_initialized:
            raise Exception("BGE embedding模型初始化失败")
        
        logger.info("向量索引器初始化完成")
    
    def create_collection_fields(self) -> List[FieldSchema]:
        """定义Milvus集合的字段结构"""
        """
        "{'auto_id': False, 'description': '法律文档分块集合', 
        'fields': [{'name': 'uuid', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 36}, 'is_primary': True, 'auto_id': False},
        {'name': 'content', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 4096}}, 
        {'name': 'document_name', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 256}},
        {'name': 'chapter', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 256}}, 
        {'name': 'section', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 256}}, 
        {'name': 'effective_date', 'description': '', 'type': <DataType.VARCHAR: 21>, 'params': {'max_length': 20}}, 
        {'name': 'is_effective', 'description': '', 'type': <DataType.BOOL: 1>}, 
        {'name': 'embedding', 'description': '', 'type': <DataType.FLOAT_VECTOR: 101>, 'params': {'dim': 1024}}], 'enable_dynamic_field': False}"
        """
        fields = [
            FieldSchema(name="uuid", dtype=DataType.VARCHAR, max_length=36, is_primary=True, auto_id=False),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.EMBEDDING_DIMENSION),
            FieldSchema(name="document_name", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="chapter", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="section", dtype=DataType.VARCHAR, max_length=256),
            FieldSchema(name="effective_date", dtype=DataType.VARCHAR, max_length=20),
            FieldSchema(name="is_effective", dtype=DataType.BOOL),
        ]
        return fields
    
    def load_chunks_from_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """从JSON文件中加载chunks"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                else:
                    logger.warning(f"文件 {file_path} 不是列表结构")
                    return []
        except Exception as e:
            logger.error(f"加载文件 {file_path} 失败: {e}")
            return []
    
    def load_all_chunks(self) -> List[Dict[str, Any]]:
        """加载所有related_laws目录下的chunks"""
        all_chunks = []
        
        if not self.data_dir.exists():
            raise Exception(f"数据目录 {self.data_dir} 不存在")
        
        json_files = list(self.data_dir.glob("*.json"))
        logger.info(f"找到 {len(json_files)} 个JSON文件")
        
        for json_file in tqdm(json_files, desc="加载数据文件"):
            # 跳过.DS_Store相关文件
            if ".DS_Store" in json_file.name:
                continue
                
            chunks = self.load_chunks_from_file(json_file)
            if chunks:
                logger.info(f"从 {json_file.name} 加载了 {len(chunks)} 个chunks")
                all_chunks.extend(chunks)
            else:
                logger.warning(f"文件 {json_file.name} 中没有找到有效chunks")
        
        logger.info(f"总共加载了 {len(all_chunks)} 个chunks")
        return all_chunks
    
    def save_embeddings_to_file(self, embeddings_data: Dict[str, Any], filename: str = "embeddings_cache.json"):
        """将向量化结果保存到JSON文件"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(embeddings_data, f, ensure_ascii=False, indent=2)
            logger.info(f"向量化结果已保存到 {filename}")
        except Exception as e:
            logger.error(f"保存向量化结果失败: {e}")
    
    def load_embeddings_from_file(self, filename: str = "embeddings_cache.json") -> Dict[str, Any]:
        """从JSON文件加载向量化结果"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"从 {filename} 加载了向量化缓存")
                return data
            else:
                logger.info(f"缓存文件 {filename} 不存在")
                return None
        except Exception as e:
            logger.error(f"加载向量化缓存失败: {e}")
            return None

    def compute_and_cache_embeddings(self, chunks: List[Dict[str, Any]], cache_filename: str) -> List[List[float]]:
        """计算向量并缓存到文件"""
        logger.info("开始向量化文本内容...")
        
        # 提取所有文本内容和UUID
        contents = [chunk['content'] for chunk in chunks]
        uuids = [chunk['uuid'] for chunk in chunks]
        
        # 分批向量化，带进度条
        batch_size = 32
        total_batches = (len(contents) + batch_size - 1) // batch_size
        embedding_list = []
        
        logger.info(f"对 {len(contents)} 个文本进行批量向量化，分 {total_batches} 批处理...")
        
        for i in tqdm(range(0, len(contents), batch_size), desc="向量化进度", unit="batch"):
            # 获取当前批次的内容
            batch_contents = contents[i:i + batch_size]
            
            # 对当前批次进行向量化
            batch_embeddings = self.embedding_model.encode(batch_contents, batch_size=len(batch_contents), normalize=True)
            
            # 处理embedding格式
            # 如果是单个向量(一维数组)，reshape为二维
            if batch_embeddings.ndim == 1:
                batch_embeddings = batch_embeddings.reshape(1, -1)
            
            # 转换当前批次的向量为列表格式
            for j in range(batch_embeddings.shape[0]):
                vector = batch_embeddings[j]
                if isinstance(vector, np.ndarray):
                    embedding_list.append(vector.astype(np.float32).tolist())
                else:
                    embedding_list.append(vector)
        
        
        # 保存到缓存文件
        cache_data = {
            'uuids': uuids,
            'embeddings': embedding_list,
            'total_count': len(chunks),
            'embedding_dimension': len(embedding_list[0]) if embedding_list else 0
        }
        self.save_embeddings_to_file(cache_data, cache_filename)
        logger.info(f"向量化完成，共生成 {len(embedding_list)} 个向量")
        
        return embedding_list
    


    def prepare_entities(self, chunks: List[Dict[str, Any]]) -> List[List[Any]]:
        """准备要插入Milvus的实体数据"""
        cache_filename = "embeddings_cache.json"
        
        # 尝试从缓存文件加载向量化结果
        cached_data = self.load_embeddings_from_file(cache_filename)
        
        if cached_data:
            logger.info("发现向量化缓存文件，检查是否匹配当前数据...")
            # 检查缓存的chunk数量是否匹配
            if len(cached_data.get('embeddings', [])) == len(chunks):
                # 验证UUID是否匹配
                cached_uuids = set(cached_data.get('uuids', []))
                current_uuids = set([chunk['uuid'] for chunk in chunks])
                
                if cached_uuids == current_uuids:
                    logger.info("缓存数据匹配，直接使用缓存的向量化结果")
                    embeddings_list = cached_data['embeddings']
                else:
                    logger.info("缓存数据UUID不匹配，重新计算向量")
                    embeddings_list = self.compute_and_cache_embeddings(chunks, cache_filename)
            else:
                logger.info("缓存数据数量不匹配，重新计算向量")
                embeddings_list = self.compute_and_cache_embeddings(chunks, cache_filename)
        else:
            logger.info("未找到缓存文件，开始计算向量...")
            embeddings_list = self.compute_and_cache_embeddings(chunks, cache_filename)
        
        # 准备实体数据
        entities = [
            [],  # uuid
            [],  # content
            [],  # embedding
            [],  # document_name
            [],  # chapter
            [],  # section
            [],  # effective_date
            [],  # is_effective
        ]
        
        for i, chunk in enumerate(tqdm(chunks, desc="准备实体数据")):
            # 获取metadata，提供默认值
            metadata = chunk.get('metadata', {})
            
            entities[0].append(chunk['uuid'])
            entities[1].append(chunk['content'])  # 限制长度
            entities[2].append(embeddings_list[i])  # 从缓存或新计算的向量列表中获取
            entities[3].append(metadata.get('document_name', ''))
            entities[4].append(metadata.get('chapter', ''))
            entities[5].append(metadata.get('section', ''))
            entities[6].append(str(metadata.get('effective_date', '')))
            entities[7].append(metadata.get('is_effective', True))
        
        logger.info(f"准备了 {len(entities[0])} 条实体数据")
        return entities
    
    def create_entities_from_cache(self, chunks: List[Dict[str, Any]], cache_filename: str = "embeddings_cache.json") -> List[List[Any]]:
        """直接从缓存文件创建实体，检查content长度"""
        
        # 加载缓存的向量
        cached_data = self.load_embeddings_from_file(cache_filename)
        if not cached_data:
            raise Exception("未找到缓存文件，请先运行向量化")
        
        embeddings_list = cached_data['embeddings']
        cached_uuids = cached_data['uuids']
        
        logger.info(f"从缓存加载了 {len(embeddings_list)} 个向量")
        
        # 验证数据匹配
        current_uuids = [chunk['uuid'] for chunk in chunks]
        if set(cached_uuids) != set(current_uuids):
            logger.warning("缓存UUID与当前数据不完全匹配")
        
        # 创建UUID到embedding的映射
        uuid_to_embedding = {uuid: emb for uuid, emb in zip(cached_uuids, embeddings_list)}
        
        # 准备实体数据
        entities = [
            [],  # uuid
            [],  # content
            [],  # embedding
            [],  # document_name
            [],  # chapter
            [],  # section
            [],  # effective_date
            [],  # is_effective
        ]
        
        problem_items = []
        
        for i, chunk in enumerate(tqdm(chunks, desc="检查并准备实体数据")):
            metadata = chunk.get('metadata', {})
            content = chunk['content']
            
            # 检查content长度
            content_char_len = len(content)
            content_byte_len = len(content.encode('utf-8'))
            
            if content_char_len > 32768 or content_byte_len > 65535:
                problem_item = {
                    'index': i,
                    'uuid': chunk['uuid'],
                    'content_char_length': content_char_len,
                    'content_byte_length': content_byte_len,
                    'content_preview': content[:200] + "..." if len(content) > 200 else content,
                    'document_name': metadata.get('document_name', ''),
                    'chapter': metadata.get('chapter', ''),
                    'section': metadata.get('section', ''),
                }
                problem_items.append(problem_item)
        
        if problem_items:
            print(f"\n🚨 发现 {len(problem_items)} 个content超长的项目:")
            for idx, item in enumerate(problem_items[:10]):  # 只显示前10个
                print(f"\n--- 问题项目 {idx+1} ---")
                print(f"Index: {item['index']}")
                print(f"UUID: {item['uuid']}")
                print(f"字符长度: {item['content_char_length']}")
                print(f"字节长度: {item['content_byte_length']}")
                print(f"文档: {item['document_name']}")
                print(f"章节: {item['chapter']}")
                print(f"小节: {item['section']}")
                print(f"内容预览: {item['content_preview']}")
            
            if len(problem_items) > 10:
                print(f"\n... 还有 {len(problem_items) - 10} 个类似问题")
            
            user_choice = input(f"\n是否继续处理？会自动截断超长content (y/N): ")
            if user_choice.lower() != 'y':
                print("操作已取消")
                return None
        
        # 继续处理，不再需要截断content
        for i, chunk in enumerate(tqdm(chunks, desc="创建实体数据")):
            metadata = chunk.get('metadata', {})
            content = chunk['content']
            
            # 获取对应的embedding
            embedding = uuid_to_embedding.get(chunk['uuid'])
            if embedding is None:
                logger.warning(f"未找到UUID {chunk['uuid']} 的embedding，跳过")
                continue
            
            entities[0].append(chunk['uuid'])
            entities[1].append(content)
            entities[2].append(embedding)
            entities[3].append(metadata.get('document_name', ''))
            entities[4].append(metadata.get('chapter', ''))
            entities[5].append(metadata.get('section', ''))
            entities[6].append(str(metadata.get('effective_date', '')))
            entities[7].append(metadata.get('is_effective', True))
        
        logger.info(f"准备了 {len(entities[0])} 条实体数据")
        return entities

    def create_and_populate_collection(self, chunks: List[Dict[str, Any]]):
        """创建集合并填充数据"""
        # 检查集合是否已存在
        if self.vector_store.check_collection_exists(self.collection_name):
            logger.warning(f"集合 {self.collection_name} 已存在")
            user_input = input("是否要删除现有集合并重新创建？(y/N): ")
            if user_input.lower() == 'y':
                self.vector_store.drop_collection(self.collection_name)
                logger.info(f"已删除现有集合 {self.collection_name}")
            else:
                logger.info("操作已取消")
                return
        
        # 创建集合
        fields = self.create_collection_fields()
        description = "使用新embedding模型重新索引的法律文档集合"
        
        logger.info(f"创建集合 {self.collection_name}...")
        collection = self.vector_store.create_collection(
            fields=fields,
            collection_name=self.collection_name,
            description=description
        )
        
        if not collection:
            raise Exception("创建集合失败")
        
        # 准备数据 - 直接从缓存创建实体
        entities = self.create_entities_from_cache(chunks)
        
        if entities is None:
            logger.info("用户取消操作")
            return
        
        # 批量插入数据
        batch_size = 1000
        total_entities = len(entities[0])
        
        logger.info(f"开始批量插入数据，总共 {total_entities} 条记录...")
        
        for i in tqdm(range(0, total_entities, batch_size), desc="插入数据"):
            end_idx = min(i + batch_size, total_entities)
            
            # 准备批次数据
            batch_entities = [entity[i:end_idx] for entity in entities]
            
            # 插入数据
            result = self.vector_store.insert_vectors(self.collection_name, batch_entities)
            if not result:
                logger.error(f"批次 {i//batch_size + 1} 插入失败")
            
        logger.info("数据插入完成")
        
        # 获取集合统计信息
        stats = self.vector_store.get_collection_stats(self.collection_name)
        logger.info(f"集合统计信息: {stats}")
    
    def run(self):
        """运行重新索引流程"""
        try:
            logger.info("开始重新索引流程...")
            
            # 加载所有chunks
            chunks = self.load_all_chunks()
            
            if not chunks:
                logger.error("没有找到任何数据")
                return
            
            # 创建集合并填充数据
            self.create_and_populate_collection(chunks)
            
            logger.info("重新索引完成！")
            
        except Exception as e:
            logger.error(f"重新索引失败: {e}")
            raise

def main():
    """主函数"""
    try:
        indexer = VectorIndexer()
        indexer.run()
    except Exception as e:
        logger.error(f"脚本执行失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        indexer = VectorIndexer()
        chunks = indexer.load_all_chunks()
        
        # 直接从缓存创建实体并插入Milvus
        logger.info("开始从缓存创建实体并插入Milvus...")
        
        # 创建集合并填充数据
        indexer.create_and_populate_collection(chunks)
        
        logger.info("完成！")
        
    except Exception as e:
        logger.error(f"执行失败: {e}")
        sys.exit(1)