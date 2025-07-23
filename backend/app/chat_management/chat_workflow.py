import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from typing_extensions import TypedDict
from typing import List, Dict, Any, Optional, Literal, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from rag.RAGChain import RAGChain
from models.llm import LLMService
from app.chat_management.prompt_template import intent_recognizer_prompt, llm_response_prompt
import asyncio

def format_messages_for_llm(current_input: str = "", messages: Optional[List[BaseMessage]] = []) -> str:
    formatted = []
    if messages:
        for msg in messages:
            if isinstance(msg, HumanMessage):
                formatted.append(f"Human: {msg.content}")
            elif isinstance(msg, AIMessage):
                formatted.append(f"Assistant: {msg.content}")
    
    formatted.append(f"Human: {current_input}")
    
    return "\n".join(formatted)
llm_service = LLMService()
rag_chain = RAGChain()

class InputState(TypedDict):
    user_input: str

class OutputState(TypedDict):
    answer: Optional[str]
    sources: Optional[List[Any]]

class OverallState(TypedDict):
    # 来自InputState的字段
    user_input: str
    # 来自OutputState的字段
    answer: Optional[str]
    sources: Optional[List[Any]]

    intent: Optional[Literal["DIFFERENT_QUESTION", "RELEVANT_QUESTION", "ADDITIONAL_COMMENT", "CASUAL_CHAT"]]
    messages: Annotated[List[BaseMessage], add_messages]
    loop_count: int

async def classify_chat_topic(state: OverallState) -> OverallState:
    """
    分类聊天话题意图
    如果用户输入的对话历史小于3条，则使用用户输入作为上下文，如果用户输入的对话历史大于3条，则取三条对话历史作为上下文
    使用LLM意图识别器生成意图，判断用户在通用场景下的意图转变
    """
    print('开始意图识别')

    if len(state["messages"]) < 3:
        context = format_messages_for_llm(state["user_input"])
    else:
        context = format_messages_for_llm(state["user_input"],state["messages"][-2:])
    
    # 直接使用用户输入进行意图识别
    response = await llm_service.generate(intent_recognizer_prompt(context))
    
    intent = " "  # 默认值
    # 修复：按行分割字符串后遍历
    for line in response.split('\n'):
        if line.startswith("<utterance_intent>"):
            intent = line.split("<utterance_intent>")[1].split("</utterance_intent>")[0]
            break
    print(f'意图识别结果：{intent}')
    return {
        **state,  
        "messages": [HumanMessage(content=context)],
        "intent": intent
    }

#  rag返回的格式
# return {
#                 "answer": answer,
#                 "retrieved_docs": [
#                     {
#                         "source": doc.get('source', ''),
#                         "title": doc.get('title', ''),
#                         "article_number": doc.get('article_number', ''),
#                         "text": doc.get('text', ''),
#                         "score": doc.get('score', 0.0)
#                     } for doc in retrieved_docs
#                 ],
#                 "sources": self._extract_sources_from_answer(answer, retrieved_docs)
#             }

async def generate_response_rag_context(state: OverallState) -> OverallState:
    """使用RAG生成响应（有上下文）"""
    print('开始RAG生成响应')
    if len(state["messages"]) < 3:
        context = format_messages_for_llm(state["user_input"])
    else:
        context = format_messages_for_llm(state["user_input"],state["messages"][-2:])

    response = await rag_chain.rag_chain(context, rewrite_query=False)
    answer = response.get("answer", "")
    sources = response.get("sources", [])
    print(f'RAG生成响应结果：{answer}')
    return {
        **state,
        "messages": AIMessage(content=answer),
        "answer": answer,
        "sources": sources
    }

async def generate_response_rag_contextfree(state: OverallState) -> OverallState:
    """使用RAG生成响应（无上下文）"""
    print('开始RAG生成响应')
    user_input = format_messages_for_llm(state["messages"][-1].content)
    response = await rag_chain.rag_chain(user_input)
    answer = response.get("answer", "")
    sources = response.get("sources", [])
    print(f'RAG生成响应结果：{answer}')
    return {
        **state,
        "messages": AIMessage(content=response.get("answer", "")),
        "answer": answer,
        "sources": sources  # 修复：使用正确的字段名
    }

async def generate_response_llm_context(state: OverallState) -> OverallState:
    """使用LLM生成响应（有上下文）"""
    print('开始LLM生成响应')
    if len(state["messages"]) < 3:
        context = format_messages_for_llm(state["user_input"])
    else:
        context = format_messages_for_llm(state["user_input"],state["messages"][-2:])
    response = llm_service.generate(llm_response_prompt(context))
    print(f'LLM生成响应结果：{response}')
    return {
        **state,
        "messages": state["messages"] + [AIMessage(content=response)],
        "answer": response,
        "sources": []
    }

async def generate_response_llm_contextfree(state: OverallState) -> OverallState:
    """使用LLM生成响应（无上下文）"""
    print('开始LLM生成响应')
    user_input = format_messages_for_llm(state["messages"][-1].content)
    response = await llm_service.generate(llm_response_prompt(user_input))
    print(f'LLM生成响应结果：{response}')
    return {
        **state,
        "messages": AIMessage(content=response),
        "answer": response,
        "sources": []
    }


builder = StateGraph(OverallState)

builder.add_node("classify_chat_topic", classify_chat_topic)
builder.add_node("generate_response_rag_context", generate_response_rag_context)
builder.add_node("generate_response_llm_context", generate_response_llm_context)
builder.add_node("generate_response_rag_contextfree", generate_response_rag_contextfree)
builder.add_node("generate_response_llm_contextfree", generate_response_llm_contextfree)
builder.add_edge(START, "classify_chat_topic")
builder.add_conditional_edges("classify_chat_topic", lambda state: state["intent"],{
    "DIFFERENT_QUESTION": "generate_response_rag_contextfree",
    "RELEVANT_QUESTION": "generate_response_rag_context",
    "ADDITIONAL_COMMENT": "generate_response_llm_context",
    "CASUAL_CHAT": "generate_response_llm_contextfree"
})
builder.add_edge("generate_response_rag_context", END)
builder.add_edge("generate_response_llm_context", END)
builder.add_edge("generate_response_rag_contextfree", END)
builder.add_edge("generate_response_llm_contextfree", END)

chat_workflow_graph = builder.compile()

async def process_with_workflow(
    user_input: str,
) -> Dict[str, Any]:
    initial_state = {
        # InputState字段
        "user_input": user_input,
        # OutputState字段
        "answer": None,
        "intent": None,
        "sources": None,
        # 原有字段
        "messages": [],
        "loop_count": 0
    }
    try:
        result = await chat_workflow_graph.ainvoke(initial_state)
        return result
    except Exception as e:
        print(f'处理消息时发生错误: {str(e)}')
        return {
            "answer": "处理消息时发生错误",
        }
async def interactive_chat():
    while True:
        user_input = input('\n您：').strip()
        if user_input == 'exit':
            break
        try:
            result = await process_with_workflow(user_input)
            print(f'AI：{result["answer"]}')
        except Exception as e:
            print(f'处理消息时发生错误: {str(e)}')
    

if __name__ == "__main__":
    asyncio.run(interactive_chat())

