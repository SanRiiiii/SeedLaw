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
from langchain_openai import ChatOpenAI
from ragas.llms import LangchainLLMWrapper
from backend.app.rag.response_generator import Generator
import asyncio
from app.core.config import settings
from backend.app.rag.hyde import HyDEGenerator

retriever = HybridRetriever()
response_generator = Generator()
hyde_generator = HyDEGenerator()

llm = LangchainLLMWrapper(ChatOpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.SILICONFLOW_API_URL,
    model=settings.SILICONFLOW_MODEL
))


if __name__ == "__main__":

    dataset = []
    DATASET_PATH = ''
    EVALUATION_DATASET_PATH = ''

    # 读取整个JSON文件
    with open(DATASET_PATH, 'r', encoding='utf-8') as f:
        qa_data = json.load(f)
    
    for data in qa_data:
        enhanced_query = asyncio.run(hyde_generator.generate_document(data['question']))
        relevant_docs = asyncio.run(reflection_llm(enhanced_query,retriever.hybridRetrieve(enhanced_query,5)))
        response = asyncio.run(response_generator.generate(data['question'],relevant_docs))
        
        # 提取字符串格式的数据供ragas使用
        # relevant_docs是字典列表，需要提取content字段
        retrieved_contexts = [doc.get('content', '') for doc in relevant_docs]
        
        # response是字典，需要提取answer字段
        response_text = response.get('answer', '') if isinstance(response, dict) else str(response)
        
        dataset.append({
            'user_input': data['question'],
            'retrieved_contexts': retrieved_contexts,
            'response': response_text,
            'reference': data['answer']
        })


         # 保存原始数据集到JSON文件
    with open(EVALUATION_DATASET_PATH, 'w', encoding='utf-8') as f:
         json.dump(dataset, f, ensure_ascii=False, indent=4)
     
    #  # 从已保存的JSON文件读取数据集
    # EVALUATION_DATASET_PATH = ''
    # with open(EVALUATION_DATASET_PATH, 'r', encoding='utf-8') as f:
    #      dataset = json.load(f)
    
    # evaluation_dataset = EvaluationDataset.from_list(dataset)
    # evaluator_llm = llm
    # try:
    #     result = evaluate(
    #             dataset=evaluation_dataset,
    #             metrics=[LLMContextRecall(), Faithfulness(), FactualCorrectness()],
    #             llm=evaluator_llm
    #         )
    # except Exception as e:
    #     print(f"评估过程中遇到错误: {e}")
    #     result = None
    # print(result)
    
    # # 保存评估结果
    # EVALUATION_RESULTS_PATH = ''
    # with open(EVALUATION_RESULTS_PATH, 'w', encoding='utf-8') as f:
    #     # 将评估结果转换为可序列化的字典
    #     result_dict = result.to_dict() if hasattr(result, 'to_dict') else dict(result)
    #     json.dump(result_dict, f, ensure_ascii=False, indent=4)
