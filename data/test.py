#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RAG检索阶段Hit Rate评估脚本

该脚本用于测试RAG系统在法律问答数据集上的检索性能。
通过计算Hit Rate（命中率）来评估检索系统的效果。

Hit Rate = 检索结果中包含正确参考文档的问题数 / 总问题数
"""

import json
import os
import sys
import logging
from typing import List, Dict, Any
from tqdm import tqdm
import asyncio

# 添加项目根目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(os.path.dirname(current_dir), 'backend')
sys.path.insert(0, backend_dir)

# 导入RAG相关模块
from app.rag.RAGChain import RAGChain
from app.rag.HybridRetriever import HybridRetriever
from app.models.llm import get_llm_service
from app.core.config import Settings

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RAGEvaluator:
    """RAG检索评估器"""
    
    def __init__(self, use_dense=True, use_sparse=True, use_rerank=True):
        """
        初始化评估器
        
        Args:
            use_dense: 是否使用稠密检索（向量检索）
            use_sparse: 是否使用稀疏检索（关键词检索）
            use_rerank: 是否使用重排序
        """
        self.use_dense = use_dense
        self.use_sparse = use_sparse
        self.use_rerank = use_rerank
        
        # 初始化检索器（不需要生成器，只测试检索）
        self.retriever = HybridRetriever(
            use_dense=use_dense,
            use_sparse=use_sparse,
            use_rerank=use_rerank
        )
        
        logger.info(f"RAG评估器初始化完成 - Dense: {use_dense}, Sparse: {use_sparse}, Rerank: {use_rerank}")
    
    def load_test_dataset(self, dataset_path: str) -> List[Dict[str, Any]]:
        """
        加载测试数据集
        
        Args:
            dataset_path: 数据集文件路径
            
        Returns:
            测试数据列表
        """
        test_data = []
        try:
            with open(dataset_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        test_data.append(data)
            
            logger.info(f"成功加载测试数据集，共 {len(test_data)} 条数据")
            return test_data
            
        except FileNotFoundError:
            logger.error(f"测试数据集文件未找到: {dataset_path}")
            return []
        except Exception as e:
            logger.error(f"加载测试数据集失败: {e}")
            return []
    
    def extract_reference_info(self, reference: str) -> Dict[str, str]:
        """
        从reference字段提取法条信息
        
        Args:
            reference: 参考法条信息，如"公司法第一百七十三条"
            
        Returns:
            包含法条信息的字典
        """
        # 简单的法条信息提取
        # 可以根据实际数据格式进行调整
        return {
            'law_name': reference.split('第')[0] if '第' in reference else reference,
            'article': reference.split('第')[1].replace('条', '') if '第' in reference and '条' in reference else '',
            'full_reference': reference
        }
    
    def check_hit(self, retrieved_docs: List[Dict[str, Any]], reference: str) -> bool:
        """
        检查检索结果中是否包含正确的参考文档
        
        Args:
            retrieved_docs: 检索到的文档列表
            reference: 正确的参考文档
            
        Returns:
            是否命中正确文档
        """
        reference_info = self.extract_reference_info(reference)
        
        for doc in retrieved_docs:
            # 检查文档内容是否包含参考法条
            doc_content = doc.get('content', '')
            doc_name = doc.get('document_name', '')
            
            # 方法1: 检查文档内容是否包含完整的参考信息
            if reference in doc_content:
                return True
            
            # 方法2: 检查法律名称和条文号是否匹配
            law_name = reference_info['law_name']
            article = reference_info['article']
            
            if law_name in doc_name or law_name in doc_content:
                if article and (f"第{article}条" in doc_content or f"第 {article} 条" in doc_content):
                    return True
            
            # 方法3: 模糊匹配（处理可能的格式差异）
            if law_name in doc_content and article:
                # 检查是否包含条文号（考虑不同格式）
                article_patterns = [
                    f"第{article}条",
                    f"第 {article} 条", 
                    f"第{article}條",
                    f"第{article.zfill(2)}条",  # 补零格式
                    f"第{article.zfill(3)}条"   # 三位数格式
                ]
                
                for pattern in article_patterns:
                    if pattern in doc_content:
                        return True
        
        return False
    
    def evaluate_retrieval(self, test_data: List[Dict[str, Any]], top_k_list: List[int] = [5, 10, 20]) -> Dict[str, Any]:
        """
        评估检索性能
        
        Args:
            test_data: 测试数据列表
            top_k_list: 要测试的top-k值列表
            
        Returns:
            评估结果字典
        """
        results = {
            'total_questions': len(test_data),
            'top_k_results': {},
            'detailed_results': []
        }
        
        logger.info(f"开始评估检索性能，共 {len(test_data)} 个问题")
        
        for top_k in top_k_list:
            logger.info(f"评估 Top-{top_k} 检索性能")
            hit_count = 0
            detailed_results = []
            
            # 使用tqdm显示进度条
            for i, item in enumerate(tqdm(test_data, desc=f"Top-{top_k} 评估进度")):
                question = item['question']
                reference = item['reference']
                uuid = item['uuid']
                
                try:
                    # 执行检索
                    retrieved_docs = self.retriever.hybridRetrieve(question, top_k)
                    
                    # 检查是否命中
                    is_hit = self.check_hit(retrieved_docs, reference)
                    
                    if is_hit:
                        hit_count += 1
                    
                    # 记录详细结果
                    detail = {
                        'uuid': uuid,
                        'question': question,
                        'reference': reference,
                        'is_hit': is_hit,
                        'retrieved_count': len(retrieved_docs),
                        'top_doc_scores': [doc.get('score', 0) for doc in retrieved_docs[:3]]  # 前3个文档的分数
                    }
                    detailed_results.append(detail)
                    
                except Exception as e:
                    logger.error(f"处理问题 {i+1} 时出错: {e}")
                    detail = {
                        'uuid': uuid,
                        'question': question,
                        'reference': reference,
                        'is_hit': False,
                        'error': str(e)
                    }
                    detailed_results.append(detail)
            
            # 计算Hit Rate
            hit_rate = hit_count / len(test_data) if test_data else 0
            
            results['top_k_results'][f'top_{top_k}'] = {
                'hit_count': hit_count,
                'hit_rate': hit_rate,
                'total_questions': len(test_data)
            }
            
            logger.info(f"Top-{top_k} Hit Rate: {hit_rate:.4f} ({hit_count}/{len(test_data)})")
        
        results['detailed_results'] = detailed_results
        return results
    
    def save_results(self, results: Dict[str, Any], output_path: str):
        """
        保存评估结果到文件
        
        Args:
            results: 评估结果
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"评估结果已保存到: {output_path}")
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def print_summary(self, results: Dict[str, Any]):
        """
        打印评估结果摘要
        
        Args:
            results: 评估结果
        """
        print("\n" + "="*60)
        print("RAG检索性能评估结果")
        print("="*60)
        print(f"总问题数: {results['total_questions']}")
        print(f"检索配置: Dense={self.use_dense}, Sparse={self.use_sparse}, Rerank={self.use_rerank}")
        print("-"*60)
        
        for key, result in results['top_k_results'].items():
            top_k = key.replace('top_', '')
            hit_rate = result['hit_rate']
            hit_count = result['hit_count']
            total = result['total_questions']
            
            print(f"Top-{top_k:2s} Hit Rate: {hit_rate:.4f} ({hit_count:3d}/{total:3d}) - {hit_rate*100:.2f}%")
        
        print("="*60)

def main():
    """主函数"""
    
    # 配置参数
    DATASET_PATH = "qa_dataset.jsonl"  # 测试数据集路径
    OUTPUT_PATH = "rag_finetune_evaluation_results_finetune_hybrid.json"  # 结果输出路径

    # TOP_K_LIST = [5, 10, 20]  # 要测试的top-k值
    TOP_K_LIST = [1,3,5,10,20]
    
    # 检索配置 - 可以根据需要调整
    USE_DENSE = True    # 是否使用向量检索
    USE_SPARSE = True  # 是否使用关键词检索  
    USE_RERANK = True   # 是否使用重排序
    
    try:
        # 检查数据集文件是否存在
        if not os.path.exists(DATASET_PATH):
            logger.error(f"测试数据集文件不存在: {DATASET_PATH}")
            return
        
        # 初始化评估器
        evaluator = RAGEvaluator(
            use_dense=USE_DENSE,
            use_sparse=USE_SPARSE,
            use_rerank=USE_RERANK
        )
        
        # 加载测试数据
        test_data = evaluator.load_test_dataset(DATASET_PATH)
        if not test_data:
            logger.error("无法加载测试数据，程序退出")
            return
        
        # 执行评估
        results = evaluator.evaluate_retrieval(test_data, TOP_K_LIST)
        
        # 保存结果
        evaluator.save_results(results, OUTPUT_PATH)
        
        # 打印摘要
        evaluator.print_summary(results)
        
        # 额外统计信息
        print(f"\n详细结果已保存到: {OUTPUT_PATH}")
        print("评估完成！")
        
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
    except Exception as e:
        logger.error(f"程序执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()