import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import json
from ragas import evaluate
from ragas import EvaluationDataset
from ragas.metrics import LLMContextRecall, Faithfulness, FactualCorrectness
from backend.app.rag.RAGChain import RAGChain
from backend.app.rag.reflection import reflection_llm
from backend.app.rag.HybridRetriever import HybridRetriever
from backend.app.rag.response_generator import Generator
import asyncio
from app.core.config import settings

# 导入langchain包装器
from ragas_langchain_wrapper import get_langchain_llm_for_ragas

retriever = HybridRetriever()
response_generator = Generator()

def get_ragas_llm():
    """
    获取Ragas评估所需的LLM（使用Langchain适配器）
    
    Returns:
        LLM实例
    """
    print("使用Langchain适配器包装器...")
    llm = get_langchain_llm_for_ragas()
    return llm


def run_evaluation():
    """
    运行评估
    """
    print("开始使用Langchain适配器进行评估...")
    
    # 获取模型
    llm = get_ragas_llm()
    
    # 从已保存的JSON文件读取数据集
    EVALUATION_DATASET_PATH = ''
    with open(EVALUATION_DATASET_PATH, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    evaluation_dataset = EvaluationDataset.from_list(dataset)
    
    try:
        result = evaluate(
            dataset=evaluation_dataset,
            metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()],
            llm=llm
        )
        print(f"评估完成，结果: {result}")
        
        # 保存评估结果
        EVALUATION_RESULTS_PATH = ''
        with open(EVALUATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
            result_dict = result.to_dict() if hasattr(result, 'to_dict') else dict(result)
            json.dump(result_dict, f, ensure_ascii=False, indent=4)
            
        return result
        
    except Exception as e:
        print(f"评估过程中遇到错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行评估
    result = run_evaluation()
    
    if result:
        print("\n评估结果:")
        if hasattr(result, 'to_dict'):
            result_dict = result.to_dict()
            for metric, score in result_dict.items():
                print(f"  {metric}: {score}")
        else:
            print(f"  {result}")
    else:
        print("评估失败")


