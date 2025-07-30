import sys
import os
import asyncio
import json
import re
from typing import List, Dict, Any
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models.llm import get_llm_service, LLMService
from app.rag.HybridRetriever import HybridRetriever


async def reflection_llm(query: str, retrieved_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    使用LLM过滤检索到的文档，返回相关的法律依据
    
    Args:
        query: 用户问题
        retrieved_docs: 检索到的文档列表
    
    Returns:
        过滤后的相关文档列表
    """
    llm_service = LLMService()
    system_prompt = build_reflection_prompt(query, retrieved_docs)
    response = await llm_service.generate(system_prompt)
    
    # 解析LLM响应为结构化数据
    parsed_docs = parse_llm_response(response, retrieved_docs)
    return parsed_docs


def build_reflection_prompt(query: str, retrieved_docs: List[Dict[str, Any]]) -> str:
    """
    构建反思prompt，要求LLM以JSON格式返回过滤后的文档
    """
    # 将retrieved_docs格式化为更清晰的展示
    docs_text = ""
    for i, doc in enumerate(retrieved_docs):
        docs_text += f"[{i+1}] {doc}\n"
    
    return f"""
## 背景 ##
你是一个法律咨询顾问，帮助用户回答问题。

## 任务 ##
你会收到一个用户的问题（query），以及检索到的相关法律依据（retrieved_docs）。检索到的法律依据并不能完全回答用户的问题，
你的任务是过滤掉全部不相关的法律依据，确保给出的法律依据可以直接准确地回答用户的问题。

## 输入 ##
用户问题: {query}

检索到的法律依据:
{docs_text}

## 输出要求 ##
请仔细分析每个法律依据与用户问题的相关性，然后以JSON格式返回相关的法律依据。
输出格式必须是一个JSON数组，每个元素包含原始文档的所有字段。

**重要**: 
1. 只返回与用户问题直接相关的法律依据
2. 保持原始文档的完整格式和字段
3. 输出必须是有效的JSON格式
4. 如果没有相关的法律依据，返回空数组 []

## 输出示例 ##
```json
[
   {{
            "uuid": "1234567890",
            "score": 0.95,
            "content": "第一百四十条 上市公司应当依法披露股东、实际控制人的信息...",
            "document_name": "公司法",
            "chapter": "第五章 股份有限公司的设立和组织机构",
            "section": "第五节 上市公司组织机构的特别规定",
            "effective_status": "True",
            "effective_date": "2021-01-01"
        
    }}
    ,
    {{
        "content": "第一百六十六条 上市公司应当依照法律、行政法规的规定披露相关信息",
        "document_name": "公司法",
        "chapter": "第六章 股份有限公司的股份发行和转让",
        "section": "第二节 股份转让",
        "effective_status": "True",
        "effective_date": "2021-01-01"

    }}
]
```

## 输出 ##"""


def parse_llm_response(response: str, original_docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    解析LLM的响应，提取JSON格式的文档列表
    
    Args:
        response: LLM的原始响应
        original_docs: 原始文档列表，用作备用
    
    Returns:
        解析后的文档列表
    """
    try:
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            array_match = re.search(r'\[.*?\]', response, re.DOTALL)
            if array_match:
                json_str = array_match.group(0)
            else:
                print(f"Warning: 无法从响应中提取JSON格式: {response}")
                return original_docs
        
        parsed_data = json.loads(json_str)
        
        if isinstance(parsed_data, list):
            return parsed_data
        else:
            print(f"Warning: 解析的数据不是列表格式: {type(parsed_data)}")
            return original_docs
            
    except json.JSONDecodeError as e:
        print(f"Error: JSON解析失败: {e}")
        print(f"原始响应: {response}")
        return original_docs
    except Exception as e:
        print(f"Error: 解析响应时出错: {e}")
        return original_docs



# if __name__ == "__main__":
#     hybrid_retriever = HybridRetriever()
#     result = hybrid_retriever.hybridRetrieve("注册公司需要什么材料？",10)
#     print(asyncio.run(reflection_llm('注册公司需要什么材料？',result)))




