"""
企业运营相关法律数据集构建脚本
从related_laws目录中选择30个企业运营相关的法律文件，每个文件提取10个chunk
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
import time
import json
import random
import threading
import concurrent.futures
import re
from pathlib import Path
from openai import OpenAI
from tqdm import tqdm
from backend.app.core.config import settings
import requests

# client = OpenAI(
#     api_key=settings.SILICONFLOW_API_KEY ,
#     base_url=settings.SILICONFLOW_API_URL
# )

def load_chunks_from_file(file_path):
    """从json文件中加载chunks"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # JSON文件本身就是chunk数组，每个元素是一个chunk对象
            if isinstance(data, list):
                return data
            else:
                print(f"Warning: {file_path} is not a list structure")
                return []
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return []

def select_chunks(chunks, num_chunks=10):
    """从chunks中选择指定数量的chunk"""
    if len(chunks) <= num_chunks:
        return chunks
    else:
        # 随机选择chunks，确保多样性
        return random.sample(chunks, num_chunks)

def build_enterprise_dataset():
    """构建企业运营相关的数据集"""
    
    # 定义20个与企业运营最相关的法律文件
    enterprise_law_files = [
        "公司法(2023-12-29)_chunks.json",
        "企业破产法(2006-08-27)_chunks.json", 
        "合伙企业法(2006-08-27)_chunks.json",
        "个人独资企业法(1999-08-30)_chunks.json",
        "外商投资法(2019-03-15)_chunks.json",
        "中小企业促进法(2017-09-01)_chunks.json",
        "企业国有资产法(2008-10-28)_chunks.json",
        "企业所得税法(2018-12-29)_chunks.json",
        "个人所得税法(2018-08-31)_chunks.json",
        "反垄断法(2022-06-24)_chunks.json",
        "反不正当竞争法(2019-04-23)_chunks.json",
        "广告法(2021-04-29)_chunks.json",
        "产品质量法(2018-12-29)_chunks.json",
        "消费者权益保护法(2013-10-25)_chunks.json",
        "电子商务法(2018-08-31)_chunks.json",
        "招标投标法(2017-12-27)_chunks.json",
        "劳动法(2018-12-29)_chunks.json",
        "民事诉讼法(2023-09-01)_chunks.json",
        "民法典-侵权责任编（2021-01-01）_chunks.json",
        "民法典-合同编（2021-01-01）_chunks.json",
        "民法典-总则（2021-01-01）_chunks.json",
   
    ]
    
    # 基础路径
    base_path = Path("/Users/jing/Desktop/coding.../毕设/code_pycharm/pythonProject/legal-assistant/backend/data/chunks/related_laws")
    
    # 存储所有选择的chunks
    selected_chunks = []
    
    print("开始构建企业运营数据集...")
    print(f"将从{len(enterprise_law_files)}个法律文件中各选择10个chunk")
    
    for law_file in enterprise_law_files:
        file_path = base_path / law_file
        
        if file_path.exists():
            print(f"处理文件: {law_file}")
            chunks = load_chunks_from_file(file_path)
            
            if chunks:
                # 选择10个chunk
                selected = select_chunks(chunks, 15)
                
                # 添加来源信息
                for chunk in selected:
                    chunk['source_law'] = law_file.replace('_chunks.json', '')
                    selected_chunks.append(chunk)
                
                print(f"  - 成功选择了 {len(selected)} 个chunk")
            else:
                print(f"  - 警告: 文件 {law_file} 中没有找到chunks")
        else:
            print(f"  - 错误: 文件 {law_file} 不存在")
    
    # 构建最终的数据集
    dataset = {
        "description": "企业运营相关法律条文数据集",
        "total_chunks": len(selected_chunks),
        "source_files": len(enterprise_law_files),
        "chunks_per_file": 10,
        "chunks": selected_chunks
    }
    
    # 保存到新的json文件
    srcdata_output_path = "/Users/jing/Desktop/coding.../毕设/code_pycharm/pythonProject/legal-assistant/data/enterprise_operation_dataset_finetune.json"
    if not os.path.exists(os.path.dirname(srcdata_output_path)):
        os.makedirs(os.path.dirname(srcdata_output_path))
    with open(srcdata_output_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
    
    print(f"\n数据集构建完成!")
    print(f"总共包含 {len(selected_chunks)} 个chunk")
    print(f"来源于 {len(enterprise_law_files)} 个法律文件")
    print(f"数据集已保存到: {srcdata_output_path}")
    
    return dataset
def make_single_qa_prompt(content):
    prompt = f""" 
        你是一个公司运营领域的法务专家，对公司运营涉及的法律，法规，政策等十分了解。
    现在，你需要根据某一条法律或者法规设想问题，并使用这个法条进行回答。注意，回答的范围不要超出这个法条。
    法条：
    {content}
    生成格式：
    {{
    "reference":"xx法第xx条",
    "question":"xxx",
    "answer":"xxx"
    }}
        """
    return prompt

def make_qa_multiple_qa_prompt(content,scenario):
    prompt = f"""
        你是一个公司运营领域的法务专家，对公司运营涉及的法律，法规，政策等十分了解。
    要求：
    1.你需要根据公司{scenario}运营场景构建真实的法律问题。
    2.并结合提供的法律给出具体的答案。
    3.回答的答案遵循如下的格式：1.给出总结性的回答。2.给出具体的法条（根据xxx法律的第xxx条...)。3.给出操作建议（如果有）
    4.注意：你的回答的全部内容都不可以超出你找出的具体法条
    法律：
    {content}
    生成格式：
    {{
    "reference":"xx法第xx条",
    "question":"xxx",
    "answer":"xxx"
    }}
    """
    return prompt

'''
import requests

url = "https://api.siliconflow.cn/v1/chat/completions"

payload = {
    "model": "Qwen/QwQ-32B",
    "messages": [
        {
            "role": "user",
            "content": "What opportunities and challenges will the Chinese large model industry face in 2025?"
        }
    ]
}
headers = {
    "Authorization": "Bearer <token>",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)
'''

def make_qa(prompt,max_retries=3, debug=False, model_name='Qwen/Qwen2.5-72B-Instruct',temperature=0.85, top_p=0.95):
    for i in range(max_retries):
        try:
            payload = {
                "model": model_name,
                "messages": [
                    {"role": "system", "content": "你是一个公司运营领域的法务专家，对公司运营涉及的法律，法规，政策等十分了解。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "top_p": top_p
            }
            headers = {
                "Authorization": f"Bearer {settings.SILICONFLOW_API_KEY}",
                "Content-Type": "application/json"
            }
            response = requests.request("POST", settings.SILICONFLOW_API_URL, json=payload, headers=headers)
            return response.json()['choices'][0]['message']['content']
        
        except Exception as e:
            print(f"Error making QA: {e}")
            if i < max_retries - 1:
                print(f"Retrying... ({i+1}/{max_retries})")
                sleep_seconds = random.randint(1,4)
                if debug:
                    print(f"Sleeping for {sleep_seconds} seconds...")
                time.sleep(sleep_seconds)
    return None

def process_chunk(chunk):
    """处理单个chunk生成QA"""
    content = chunk['content'] + chunk['metadata']['document_name']
    prompt = make_single_qa_prompt(content)
    
    # 生成QA
    result = make_qa(prompt, max_retries=3, debug=True)
    return result

def make_qa_multiple(chunk):
    pass

def build_qa_dataset(dataset_path, output_path):

    with open(dataset_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        chunks = data['chunks']
    
    print(f"加载了 {len(chunks)} 个chunks")
    
    # 检查点机制 - 直接使用原有的uuid作为唯一标识
    qa_ckpt = {}
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                qa_ckpt_lines = f.readlines()
                qa_ckpt_lines = [json.loads(line.strip()) for line in qa_ckpt_lines if line.strip() != '']
                qa_ckpt = {item['uuid']: item for item in qa_ckpt_lines}
                print(f'找到检查点文件，已处理项目数: {len(qa_ckpt)}')
        except Exception as e:
            print(f"加载检查点文件失败: {e}")
            qa_ckpt = {}
    
    # 过滤已处理的chunks
    chunks_to_process = [
        chunk for chunk in chunks 
        if chunk['uuid'] not in qa_ckpt
    ]
    
    print(f"需要处理的chunks数量: {len(chunks_to_process)}")
    
    if not chunks_to_process:
        print("所有chunks都已处理完成！")
        return qa_ckpt

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    file_lock = threading.Lock()
    max_workers = 4
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            chunk['uuid']: executor.submit(process_chunk, chunk) 
            for chunk in chunks_to_process
        }
        
        # 处理结果
        for uuid in tqdm(futures, desc="生成QA"):
            future = futures[uuid]
            try:
                result = future.result()
                if result is None:
                    continue
                
                chunk = next(c for c in chunks_to_process if c['uuid'] == uuid)
                
                # 尝试解析AI生成的JSON响应
                try:
                    # 清理响应文本，提取JSON部分
                    json_match = re.search(r'\{[^}]*"reference"[^}]*\}', result, re.DOTALL)
                    if json_match:
                        parsed_qa = json.loads(json_match.group())
                        reference = parsed_qa.get('reference', '')
                        question = parsed_qa.get('question', '')
                        answer = parsed_qa.get('answer', '')
                    else:
                        # 如果无法解析，使用默认值
                        reference = chunk.get('source_law', '')
                        question = "解析失败"
                        answer = result
                except Exception as parse_error:
                    print(f"解析AI响应失败 {uuid}: {parse_error}")
                    reference = chunk.get('source_law', '')
                    question = "解析失败"
                    answer = result
                
                item = {
                    'uuid': uuid,
                    'reference': reference,
                    'question': question,
                    'answer': answer,
                }
                
                qa_ckpt[uuid] = item
                
                with file_lock:
                    try:
                        with open(output_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps(item, ensure_ascii=False) + '\n')
                    except Exception as e:
                        print(f"写入文件失败: {e}")
                        
            except Exception as e:
                print(f"处理chunk {uuid} 时出错: {e}")
                continue
    
    print(f"\nQA数据集构建完成!")
    print(f"总共处理了 {len(qa_ckpt)} 个chunk")
    print(f"结果保存到: {output_path}")
    
    return qa_ckpt

if __name__ == "__main__":
    # 设置随机种子以确保可重现性
    random.seed(37)
    
    # 构建数据集
    # dataset = build_enterprise_dataset()
    
    # 构建QA数据集
    dataset_path = "/Users/jing/Desktop/coding.../毕设/code_pycharm/pythonProject/legal-assistant/data/enterprise_operation_dataset_finetune.json"
    qa_output_path = "/Users/jing/Desktop/coding.../毕设/code_pycharm/pythonProject/legal-assistant/data/qa_dataset_finetune.jsonl"
    
    print("\n开始构建QA数据集...")
    qa_dataset = build_qa_dataset(dataset_path, qa_output_path) 