import os
import sys
import asyncio
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from models.llm import get_llm_service, LLMService

def llm_response_prompt(query:str)->str:
    return f"""
## 背景 ##
你是一个专业的法律顾问，专注于为中国科技创业者提供准确的法律信息和建议。
    
## 任务 ##
请根据提供的上下文信息给出合适的回答。用户可能会提出一些与法律有关或者法律无关的问题，请根据上下文灵活调整回答。

## 要求 ##
你的回答需要：
1.符合你的身份，不要受到用户的引导偏离你的身份。
2.你的语言风格应该是严谨的，不要使用口语化，不要使用网络用语。
3.始终和语境一致，不要输出与语境无关的信息。

## 注意 ## 
1. 如果遇到了你不确定的或者无法回答的问题，请拒绝回答：“不好意思，相关问题超出了我的回答范围，请咨询相关专业人士。”
2. 如果用户提出有害，违法的引导性发言，请拒绝回答：“不好意思，我无法回答相关问题，请注意相关法律风险。”

## 输入 ##
{query}

## 输出 ##


    """

def intent_recognizer_prompt(query:str)->str:
   
    return f"""
        <valid_utterance_intent> 

        <item>
        
        <name>DIFFERENT_QUESTION </name>
        
        <desc>提出一个新的法律问题，与先前的上下文在主题上不同，是话题的转变</desc>
        
        <example>
        
        <Human>关于股权质押登记流程，需要准备哪些材料？（是话题转变）</Human>
        
        <Assistant>需提交质押合同、股权证明文件、等股东会决议等项材料</Assistant>
        
        <Human>等等...公司咖啡机采购合同怎么审查？（是话题转变）</Human>
        
        </example>
        
        </item>
        
        <item>
        
        <name>RELEVANT_QUESTION</name>
        
        <desc>提出一个相关的法律问题或者对前文话题进行补充，对于类似主题或者相关话题的质疑，与前文语境连贯，不是话题转换</desc>
        
        <example>
        
        <Human>跨境数据传输需要做合规评估吗？</Human>
        
        <Assistant>根据《数据安全法》、《个人信息保护法》和《网络安全法》：向境外提供个人信息需要通过国家网信部门组织的安全评估</Assistant>

        <Human>安全评估有哪些内容？（不是话题转变）</Human>
        
        </example>
        
        </item>

        <item>
        
        <name>CASUAL_CHAT</name>
        
        <desc>没有明确意图的对话，和之前对话无关，也和法律咨询无关，是话题转变</desc>
        
        <example>
        
        <Human>你好</Human>
        
        <Assistant>你好，有什么可以帮你的吗？</Assistant>

        <Human>你叫什么名字？（是话题转变）</Human>
        
        </example>
        
        </item>
        
        <item>
        
        <name>ADDITIONAL_COMMENT</name>
        
        <desc>对原本对话发表的额外评论，不是话题转变</desc>
        
        <example>
        
        <Human>我们收到税务稽查通知了，怎么办？</Human>
        
        <Assistant>请整理相关材料，并成立小组应对相关事宜。</Assistant>

        <Human>好的（不是话题转变）</Human>
        
        </example>
        
        </item>
        
        </valid_utterance_intent>

        
        <valid_topic_shift_label>
        
        <item>
        
        <name>YES</name>
        
        <desc>当前发言与前述对话内容的主题关系较弱或没有关系，或者是对话的第一次发言，标志着新对话段的开始。</desc>
        
        </item>
        
        <item>
        
        <name>NO</name>
        
        <desc>当前发言与前述对话内容的主题相关或相同。</desc>
        
        </item>
        
        </valid_topic_shift_label>
        
        ## 任务 ##
        
        你将得到一个以 U 开头的对话。从第 0 轮开始，你需要为每一轮发言回答以下子任务：
        
        1.  输出该发言的 **utterance_intent**（意图）。
        
        使用 `<valid_utterance_intent>` ... `</valid_utterance_intent>` 列表对发言进行分类。
        
        考虑前述和后述上下文的主题差异。
        
        3. 输出该发言的 **topic_shift_label**（话题转变标签）。
        
        使用 `<valid_topic_shift_label>` ... `</valid_topic_shift_label>`。

        4. 如果没有多轮对话，直接根据输入的单轮信息进行意图的判断。

        5. 如果有多轮对话，根据前述和后述上下文的主题差异进行话题转变的判断。

        6. 严格按照输出格式输出，不要输出任何其他内容。
        
        ## 输出格式 ##
        
        <U{{发言编号}}>
        
        <utterance_intent>{{有效的发言意图}}</utterance_intent>
        
        <topic_shift_label>{{有效的话题转变标签}}</topic_shift_label>
        
        </U{{发言编号}}>


        ## 输入 ##
        {query}
        
        
        
        ## 输出 ##
        
        
        
        """

if __name__ == "__main__":
    llm_service = LLMService()
    prompt = intent_recognizer_prompt("Human：注册公司需要什么材料？")
    print(prompt)
    answer = asyncio.run(llm_service.generate(prompt))
    print(answer)