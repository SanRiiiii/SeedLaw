#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import time
import random
from typing import List, Dict, Any, Set
import logging
from app.core.config import Settings
import numpy as np
from sklearn.metrics import precision_score, recall_score, f1_score, precision_recall_fscore_support

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入BM25搜索器类和HybridRetriever类
from app.rag.bm25_search import BM25Searcher
from app.rag.retriever import HybridRetriever

def load_chunks_from_json(file_path: str) -> List[Dict[str, Any]]:
    """从JSON文件加载文档块"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            logger.info(f"从 {file_path} 加载了 {len(chunks)} 个文档块")
            return chunks
    except Exception as e:
        logger.error(f"加载文档块失败: {e}")
        return []

def prepare_documents(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """准备文档格式，确保包含必要的字段"""
    documents = []
    for chunk in chunks:
        doc = {
            "uuid": chunk.get("uuid"),
            "content": chunk.get("content", ""),
        }
        # 添加元数据字段
        if "metadata" in chunk:
            for key, value in chunk["metadata"].items():
                doc[key] = value
        elif "document_name" in chunk:
            # 兼容其他格式
            for key in ["document_name", "chapter", "section", "is_effective", "effective_date"]:
                if key in chunk:
                    doc[key] = chunk[key]
        documents.append(doc)
    return documents

def create_realistic_test_queries() -> List[Dict[str, Any]]:
    """创建真实用户可能会问的问题"""
    test_queries = [
        {
            "query": "公司注册资本最低要求是多少",
            "description": "关于公司注册资本的最低限额要求",
            "expected_keywords": ["注册资本", "最低", "有限责任公司", "股份有限公司"]
        },
        {
            "query": "有限责任公司股东人数上限",
            "description": "询问有限责任公司最多允许多少个股东",
            "expected_keywords": ["有限责任公司", "股东", "人数", "五十"]
        },
        {
            "query": "股份有限公司发起人最少几个",
            "description": "关于股份有限公司发起人数量的最低要求",
            "expected_keywords": ["股份有限公司", "发起人", "人数", "五"]
        },
        {
            "query": "一人有限责任公司如何设立",
            "description": "一人有限公司的设立条件和流程",
            "expected_keywords": ["一人", "有限责任公司", "设立", "股东", "自然人"]
        },
        {
            "query": "董事会决议表决方式有哪些",
            "description": "公司董事会决议的合法表决方式",
            "expected_keywords": ["董事会", "决议", "表决", "过半数"]
        },
        {
            "query": "公司股东出资方式有哪些",
            "description": "公司股东可以采用的出资方式",
            "expected_keywords": ["出资", "货币", "实物", "知识产权", "土地使用权"]
        },
        {
            "query": "公司股东如何查询财务会计报告",
            "description": "股东查阅公司财务会计报告的权利与程序",
            "expected_keywords": ["股东", "查阅", "会计", "财务", "报告"]
        },
        {
            "query": "公司合并程序是怎样的",
            "description": "公司合并的法定程序和要求",
            "expected_keywords": ["合并", "决议", "通知", "债权人", "合并协议"]
        },
        {
            "query": "股东会会议通知时间规定",
            "description": "召开股东会会议前的通知时间要求",
            "expected_keywords": ["股东会", "会议", "通知", "日"]
        },
        {
            "query": "董事对公司承担什么责任",
            "description": "公司董事的法律责任",
            "expected_keywords": ["董事", "忠实", "勤勉", "责任", "损害赔偿"]
        },
        {
            "query": "公司破产清算的程序",
            "description": "公司破产清算的法定程序",
            "expected_keywords": ["破产", "清算", "清算组", "债权", "财产"]
        },
        {
            "query": "公司增资扩股的法律程序",
            "description": "公司如何合法进行增资扩股",
            "expected_keywords": ["增加", "注册资本", "股东会", "认缴", "决议"]
        },
        {
            "query": "股东可以退股吗",
            "description": "股东退出公司的法律规定",
            "expected_keywords": ["股东", "退", "股权", "转让", "公司法"]
        },
        {
            "query": "法定代表人变更需要哪些手续",
            "description": "公司变更法定代表人的程序",
            "expected_keywords": ["法定代表人", "变更", "工商", "登记", "决议"]
        },
        {
            "query": "公司经营范围变更流程",
            "description": "变更公司经营范围的法律程序",
            "expected_keywords": ["经营范围", "变更", "修改", "章程", "决议"]
        }
    ]
    
    logger.info(f"创建了 {len(test_queries)} 个真实用户测试查询")
    return test_queries

def test_bm25_indexing(documents: List[Dict[str, Any]], cache_dir: str = './bm25_test_cache') -> BM25Searcher:
    """测试BM25索引的创建和保存"""
    logger.info("开始测试BM25索引创建和保存...")
    
    # 确保缓存目录存在
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    
    # 初始化BM25搜索器
    start_time = time.time()
    searcher = BM25Searcher(cache_dir=cache_dir)
    
    # 构建索引
    success = searcher.build_index(documents)
    build_time = time.time() - start_time
    
    if success:
        logger.info(f"BM25索引创建成功! 用时: {build_time:.2f}秒")
        logger.info(f"索引信息: {searcher.get_index_info()}")
    else:
        logger.error("BM25索引创建失败!")
    
    return searcher

def test_bm25_loading(cache_dir: str = './bm25_test_cache') -> BM25Searcher:
    """测试BM25索引的加载"""
    logger.info("开始测试BM25索引加载...")
    
    # 初始化一个新的BM25搜索器
    start_time = time.time()
    searcher = BM25Searcher(cache_dir=cache_dir)
    
    # 尝试加载索引
    success = searcher.load_index()
    load_time = time.time() - start_time
    
    if success:
        logger.info(f"BM25索引加载成功! 用时: {load_time:.2f}秒")
        logger.info(f"索引信息: {searcher.get_index_info()}")
    else:
        logger.error("BM25索引加载失败!")
    
    return searcher

def calculate_hit_rate(results: List[Dict[str, Any]], expected_keywords: List[str]) -> Dict[str, float]:
    """
    计算检索结果的命中率
    
    Args:
        results: 检索结果列表
        expected_keywords: 预期应该包含的关键词列表
    
    Returns:
        包含命中率指标的字典
    """
    if not results or not expected_keywords:
        return {
            "hit_rate": 0.0,
            "keyword_match_rate": 0.0,
            "matched_keywords": [],
            "missing_keywords": expected_keywords
        }
    
    # 合并所有文档的内容
    all_content = ""
    for result in results:
        # 适应不同的结果格式
        if 'content' in result:
            all_content += result.get('content', '') + " "
        elif 'text' in result:
            all_content += result.get('text', '') + " "
            
    # 计算关键词匹配情况
    matched_keywords = []
    missing_keywords = []
    
    for keyword in expected_keywords:
        if keyword in all_content:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)
    
    # 计算命中率
    keyword_match_rate = len(matched_keywords) / len(expected_keywords) if expected_keywords else 0.0
    
    # 总体命中率（可以根据需要调整计算方式）
    # 这里简单地使用关键词匹配率作为命中率
    hit_rate = keyword_match_rate
    
    return {
        "hit_rate": hit_rate,
        "keyword_match_rate": keyword_match_rate,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords
    }

def test_bm25_search(searcher: BM25Searcher, test_queries: List[Dict[str, Any]], top_k: int = 10) -> Dict[str, Any]:
    """测试BM25搜索性能"""
    logger.info(f"开始测试BM25搜索性能，使用 {len(test_queries)} 个查询...")
    
    query_results = []
    total_time = 0
    total_hit_rate = 0.0
    total_keyword_match_rate = 0.0
    
    # 对每个测试查询执行搜索
    for i, query_obj in enumerate(test_queries):
        query = query_obj["query"]
        description = query_obj.get("description", "")
        expected_keywords = query_obj.get("expected_keywords", [])
        
        # 执行BM25搜索
        start_time = time.time()
        results = searcher.search(query, top_k=top_k)
        search_time = time.time() - start_time
        total_time += search_time
        
        # 计算命中率
        hit_metrics = calculate_hit_rate(results, expected_keywords)
        total_hit_rate += hit_metrics["hit_rate"]
        total_keyword_match_rate += hit_metrics["keyword_match_rate"]
        
        # 将结果添加到query_results
        query_results.append({
            "query": query,
            "description": description,
            "search_time": search_time,
            "results": results,
            "hit_metrics": hit_metrics
        })
        
        logger.info(f"查询 {i+1}/{len(test_queries)}: '{query}' - 检索时间: {search_time:.4f}秒, 命中率: {hit_metrics['hit_rate']:.4f}")
    
    # 计算平均值
    num_queries = len(test_queries)
    avg_time = total_time / num_queries if num_queries else 0
    avg_hit_rate = total_hit_rate / num_queries if num_queries else 0
    avg_keyword_match_rate = total_keyword_match_rate / num_queries if num_queries else 0
    
    logger.info(f"BM25搜索测试完成!")
    logger.info(f"平均检索时间: {avg_time:.4f}秒")
    logger.info(f"平均命中率: {avg_hit_rate:.4f}")
    logger.info(f"平均关键词匹配率: {avg_keyword_match_rate:.4f}")
    
    return {
        "avg_search_time": avg_time,
        "avg_hit_rate": avg_hit_rate,
        "avg_keyword_match_rate": avg_keyword_match_rate,
        "query_results": query_results
    }

def test_hybrid_retriever_real(test_queries: List[Dict[str, Any]], 
                               bm25_cache_dir: str, 
                               top_k: int = 5,
                               use_hybrid: bool = True) -> Dict[str, Any]:
    """使用HybridRetriever测试混合检索性能"""
    logger.info(f"开始使用HybridRetriever测试{'混合' if use_hybrid else '向量'}检索性能...")
    
    try:
        # 初始化混合检索器
        retriever = HybridRetriever(use_bm25=True, bm25_cache_dir=bm25_cache_dir)
        
        query_results = []
        total_time = 0
        total_hit_rate = 0.0
        total_keyword_match_rate = 0.0
        
        # 对每个查询执行检索
        for i, query_obj in enumerate(test_queries):
            query = query_obj["query"]
            description = query_obj.get("description", "")
            expected_keywords = query_obj.get("expected_keywords", [])
            
            logger.info(f"检索查询 {i+1}/{len(test_queries)}: '{query}'...")
            
            # 执行混合检索
            start_time = time.time()
            results = retriever.retrieve(query, top_k=top_k, use_bm25=use_hybrid)
            search_time = time.time() - start_time
            total_time += search_time
            
            # 计算命中率
            hit_metrics = calculate_hit_rate(results, expected_keywords)
            total_hit_rate += hit_metrics["hit_rate"]
            total_keyword_match_rate += hit_metrics["keyword_match_rate"]
            
            # 将结果添加到query_results
            query_results.append({
                "query": query,
                "description": description,
                "search_time": search_time,
                "results": results,
                "hit_metrics": hit_metrics
            })
            
            logger.info(f"查询 {i+1} 检索完成, 用时: {search_time:.4f}秒, 命中率: {hit_metrics['hit_rate']:.4f}")
            
        # 计算平均值
        num_queries = len(test_queries)
        avg_time = total_time / num_queries if num_queries else 0
        avg_hit_rate = total_hit_rate / num_queries if num_queries else 0
        avg_keyword_match_rate = total_keyword_match_rate / num_queries if num_queries else 0
        
        logger.info(f"HybridRetriever {'混合' if use_hybrid else '向量'}检索测试完成!")
        logger.info(f"平均检索时间: {avg_time:.4f}秒")
        logger.info(f"平均命中率: {avg_hit_rate:.4f}")
        logger.info(f"平均关键词匹配率: {avg_keyword_match_rate:.4f}")
        
        # 释放资源
        retriever.close()
        
        return {
            "avg_search_time": avg_time,
            "avg_hit_rate": avg_hit_rate,
            "avg_keyword_match_rate": avg_keyword_match_rate,
            "query_results": query_results
        }
    except Exception as e:
        logger.error(f"HybridRetriever测试失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}

def evaluate_retrieval_quality(results: Dict[str, Any], method_name: str):
    """评估检索质量"""
    logger.info(f"\n===== {method_name}检索质量评估 =====")
    logger.info(f"平均检索时间: {results['avg_search_time']:.4f}秒")
    logger.info(f"平均命中率: {results.get('avg_hit_rate', 0):.4f}")
    logger.info(f"平均关键词匹配率: {results.get('avg_keyword_match_rate', 0):.4f}")
    
    # 打印前3个查询的详细结果示例
    for i, query_result in enumerate(results["query_results"][:3], 1):
        logger.info(f"\n查询 {i}: {query_result['query']}")
        logger.info(f"描述: {query_result.get('description', '')}")
        logger.info(f"检索时间: {query_result['search_time']:.4f}秒")
        
        # 添加命中率信息
        hit_metrics = query_result.get("hit_metrics", {})
        if hit_metrics:
            logger.info(f"命中率: {hit_metrics.get('hit_rate', 0):.4f}")
            logger.info(f"关键词匹配率: {hit_metrics.get('keyword_match_rate', 0):.4f}")
            logger.info(f"匹配关键词: {', '.join(hit_metrics.get('matched_keywords', []))}")
            logger.info(f"未匹配关键词: {', '.join(hit_metrics.get('missing_keywords', []))}")
        
        logger.info(f"前3个检索结果:")
        for j, result in enumerate(query_result['results'][:3], 1):
            # 根据结果格式调整显示内容
            if isinstance(result, dict):
                if 'uuid' in result:  # BM25结果格式
                    doc_id = result.get('uuid', '')
                    score = result.get('score', 0.0)
                    content = result.get('content', '')[:100]  # 显示前100个字符
                    source = f"{result.get('document_name', '')} - {result.get('chapter', '')} {result.get('section', '')}"
                else:  # HybridRetriever结果格式
                    doc_id = result.get('id', '')
                    score = result.get('score', 0.0)
                    content = result.get('text', '')[:100]  # 显示前100个字符
                    source = f"{result.get('source', '')} - {result.get('title', '')} {result.get('article_number', '')}"
                
                logger.info(f"  结果 {j}:")
                logger.info(f"    ID: {doc_id}")
                logger.info(f"    来源: {source}")
                logger.info(f"    分数: {score:.4f}")
                logger.info(f"    内容: {content}...")
            else:
                logger.info(f"  结果 {j}: {result}")
                
        logger.info("-" * 50)

def main():
    # 设置路径和参数
    settings = Settings()
    chunk_file = "./data/chunks/公司法(2018-10-26)_chunks.json"  # 使用公司法文件
    cache_dir = settings.BM25_CACHE_DIR
    top_k = 10
    
    # 步骤1: 加载文档
    chunks = load_chunks_from_json(chunk_file)
    if not chunks:
        logger.error("没有找到文档，测试终止")
        return
    
    # 步骤2: 准备文档格式
    documents = prepare_documents(chunks)
    logger.info(f"准备了 {len(documents)} 个文档用于索引")
    
    # 步骤3: 创建真实用户测试查询
    test_queries = create_realistic_test_queries()
    if not test_queries:
        logger.error("无法创建测试查询，测试终止")
        return
    
    # 步骤4: 测试BM25索引创建（如果需要）
    bm25_searcher = test_bm25_indexing(documents, cache_dir=cache_dir)
    
    # 步骤5: 测试BM25搜索性能
    bm25_results = test_bm25_search(bm25_searcher, test_queries, top_k=top_k)
    
    # 步骤6: 评估BM25检索质量
    evaluate_retrieval_quality(bm25_results, "BM25")
    
    # 步骤7: 测试HybridRetriever混合检索
    hybrid_results = test_hybrid_retriever_real(test_queries, cache_dir, top_k=top_k, use_hybrid=True)
    
    # 步骤8: 评估混合检索质量
    if 'error' in hybrid_results:
        logger.error(f"混合检索测试失败: {hybrid_results['error']}")
    else:
        evaluate_retrieval_quality(hybrid_results, "混合检索")
    
    # 步骤9: 测试纯向量检索（不使用BM25混合）
    vector_results = test_hybrid_retriever_real(test_queries, cache_dir, top_k=top_k, use_hybrid=False)
    
    # 步骤10: 评估纯向量检索质量
    if 'error' in vector_results:
        logger.error(f"纯向量检索测试失败: {vector_results['error']}")
    else:
        evaluate_retrieval_quality(vector_results, "纯向量检索")
    
    # 步骤11: 比较三种检索方法的性能
    logger.info("\n===== 检索性能比较 =====")
    logger.info(f"方法\t\t平均命中率\t平均检索时间(秒)")
    logger.info(f"BM25:\t\t{bm25_results.get('avg_hit_rate', 0):.4f}\t{bm25_results['avg_search_time']:.4f}")
    
    if 'error' not in hybrid_results:
        logger.info(f"混合检索:\t{hybrid_results.get('avg_hit_rate', 0):.4f}\t{hybrid_results['avg_search_time']:.4f}")
    
    if 'error' not in vector_results:
        logger.info(f"纯向量检索:\t{vector_results.get('avg_hit_rate', 0):.4f}\t{vector_results['avg_search_time']:.4f}")

if __name__ == "__main__":
    main() 