import pandas as pd
import json
from tqdm.auto import tqdm
import math

def load_jsonl_to_dataframe(file_path):
    """
    读取JSONL文件并转换为pandas DataFrame
    
    Args:
        file_path (str): JSONL文件路径
    
    Returns:
        pd.DataFrame: 包含数据的DataFrame
    """
    data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip():
                json_obj = json.loads(line.strip())
                data.append(json_obj)
    
    df = pd.DataFrame(data)
    return df

def build_finetune_data(dataset_path,neg_batch_size = -1, n_neg_batch = 5):
    dataset = load_jsonl_to_dataframe(dataset_path)
    data = []
    for idx, row in tqdm(dataset.iterrows(),total = len(dataset)):
        question = row['question']
        answer = row['answer']
        neg_samples = dataset[dataset['question'] != question]['answer'].values.tolist()
        neg_batch_count = math.ceil((len(dataset)-1)/neg_batch_size)
        neg_batch_count = min(neg_batch_count,n_neg_batch)
        for neg_batch_idx in range(neg_batch_count):
            neg_batch_samples = neg_samples[neg_batch_idx*neg_batch_size:(neg_batch_idx+1)*neg_batch_size]
            neg_batch_samples = [item for item in neg_batch_samples if item != answer]
            data.append({
                'query':question,
                'pos':answer,
                'neg':neg_batch_samples
            })
    return data

def save_data(data,output_path):
    with open(output_path,'w') as f:
        for item in data:
            f.write(json.dumps(item,ensure_ascii=False))
            f.write('\n')

# 读取数据集
if __name__ == "__main__":
   dataset_path = "/Users/jing/Desktop/coding.../毕设/code_pycharm/pythonProject/legal-assistant/data/qa_dataset_finetune.jsonl"
   data = build_finetune_data(dataset_path,16,32)
   output_path = "/Users/jing/Desktop/coding.../毕设/code_pycharm/pythonProject/legal-assistant/data/qa_dataset_finetune_emb.jsonl"
   save_data(data,output_path)