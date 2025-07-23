# '''
# 意图识别组件，用于识别用户对话的意图，初始化槽位并填槽
# '''
# import logging
# from typing import Dict, List, Any, Optional, Tuple
# import os
# from app.core.config import settings
# from backend.app.models.llm import get_llm_service, LLMService

# logger = logging.getLogger(__name__)

# class IntentRecognizer:
#     """
#     意图识别组件，用于识别用户对话的意图并收集必要信息
#     """
    
#     # 法律相关主题列表
#     LEGAL_TOPICS = [
#         "1.设立登记和行业准入：指企业成立时需要完成的工商注册、税务登记等法定手续，以及进入特定行业所需的许可证、资质认证等准入要求，确保企业合法经营",
#         "2.股权架构和公司治理：涉及公司股东结构设计、股权分配、董事会构成、决策机制等治理框架，旨在明确权责关系，保护股东权益，提高企业运营效率",
#         "3.劳动关系和员工激励：包括劳动合同签订、薪酬福利设计、绩效考核、股权激励等人力资源管理制度，旨在建立和谐劳动关系，激发员工积极性",
#         "4.知识产权和商业机密：涉及专利、商标、著作权等知识产权的申请保护，以及商业秘密、技术秘密的保密措施，维护企业核心竞争优势和无形资产",
#         "5.财务融资：包括企业财务管理、资金筹集、投融资决策、财务报告等，涉及银行贷款、股权融资、债券发行等多种融资方式和财务规范",
#         "6.税务管理：涉及企业各类税种的申报缴纳、税务筹划、税收优惠政策运用、税务风险防控等，确保合规纳税并优化税负成本",
#         "7.合同管理：包括合同起草、审查、谈判、履行、变更等全生命周期管理，涉及销售、采购、服务等各类商业合同的法律风险控制",
#         "8.纠纷解决：指企业面临商业争议时的处理机制，包括协商、调解、仲裁、诉讼等解决途径，以及预防纠纷的合规管理和风险控制措施。"
#     ]
    
#     # 各主题需要收集的信息
#     TOPIC_INFO_REQUIREMENTS = {
#         "设立登记和行业准入": ["公司类型/行业", "公司经营范围", "注册地区"],
#         "股权架构和公司治理": ["创始人结构", "融资阶段", "公司治理结构"],
#         "劳动关系和员工激励": ["员工规模", "用工类型", "员工激励需求"],
#         "知识产权和商业机密": ["技术或产品类型", "保护需求", "商业竞争程度"],
#         "财务融资": ["融资阶段", "资金使用需求", "商业模式"],
#         "税务管理": ["税种类型", "经营情况", "公司类型/行业"],
#         "合同管理": ["合同类型和数量", "合同审批方式", "履约监控情况"],
#         "纠纷解决": ["纠纷类型", "争议焦点", "解决方式偏好"]
#     }
    
#     def __init__(self, llm_service: LLMService = None):
#         """
#         初始化意图识别器
        
#         Args:
#             llm_service: 大语言模型服务，如果为None则使用默认服务
#         """
#         self.llm_service = llm_service or get_llm_service(
#             model= settings.VOLCENGINE_MODEL
#             # temperature=0.1  # 意图识别需要更确定性的回答
#         )
#         logger.info("意图识别组件初始化完成")
    
#     async def analyze_intent(
#         self, 
#         query: str, 
#         chat_history: Optional[List[Dict[str, str]]] = None,
#         user_context: Optional[Dict[str, Any]] = None
#     ) -> Dict[str, Any]:
#         """
#         分析用户意图，判断是否相关、是否继续上一轮对话，以及需要收集的信息
        
#         Args:
#             query: 用户查询
#             chat_history: 聊天历史
#             user_context: 用户上下文信息
            
#         Returns:
#             包含意图分析结果的字典
#         """
#         # 默认结果
#         result = {
#             "is_related_to_previous": False,
#             "is_legal_topic": False,
#             "identified_topic": None,
#             "missing_info": [],
#             "should_collect_info": False,
#             "next_question": None,
#             "enhanced_query": query
#         }
        
#         try:
#             # 1. 判断是否与上一轮对话相关
#             if chat_history and len(chat_history) > 0:
#                 is_related = await self._check_conversation_continuity(query, chat_history)
#                 result["is_related_to_previous"] = is_related
            
#             # 2. 判断是否与法律主题相关
#             topic_result = await self._identify_legal_topic(query)
#             result["is_legal_topic"] = topic_result["is_legal"]
#             result["identified_topic"] = topic_result["topic"]
            
#             # 3. 如果相关，检查是否需要收集额外信息
#             if result["is_legal_topic"] and result["identified_topic"]:
#                 info_result = await self._check_missing_information(
#                     query, 
#                     result["identified_topic"], 
#                     user_context
#                 )
#                 result["missing_info"] = info_result["missing_info"]
#                 result["should_collect_info"] = len(info_result["missing_info"]) > 0
                
#                 # 如果需要收集信息，生成下一个问题
#                 if result["should_collect_info"]:
#                     result["next_question"] = await self._generate_info_collection_question(
#                         result["identified_topic"],
#                         info_result["missing_info"][0]
#                     )
#                 else:
#                     # 如果不需要收集信息，生成增强查询
#                     result["enhanced_query"] = await self._generate_enhanced_query(
#                         query, 
#                         result["identified_topic"], 
#                         user_context
#                     )
#             else:
#                 # 如果不相关，直接使用原始查询
#                 result["enhanced_query"] = query
                
#             return result
            
#         except Exception as e:
#             logger.error(f"意图分析过程中发生错误: {str(e)}")
#             # 发生错误时返回默认结果
#             return result
    
#     async def _check_conversation_continuity(
#         self, 
#         query: str, 
#         chat_history: List[Dict[str, str]]
#     ) -> bool:
#         """
#         判断当前查询是否与之前的对话相关
        
#         Args:
#             query: 当前用户查询
#             chat_history: 聊天历史
            
#         Returns:
#             是否相关的布尔值
#         """
#         # 获取最近的对话
#         recent_history = chat_history[-1:] if len(chat_history) > 1 else chat_history
        
#         # 构建提示词
#         prompt = f"""
#         请分析以下当前用户查询与之前对话的关系，判断当前查询是否与之前的对话主题相关，或者是开启了一个全新的对话主题。
        
#         之前的对话:
#         {self._format_chat_history(recent_history)}
        
#         当前用户查询:
#         {query}
        
#         请回答"是"或"否":
#         - "是": 如果当前查询与之前对话相关或是对之前对话的延续
#         - "否": 如果当前查询开启了一个全新的对话主题
#         """
        
#         # 调用LLM
#         response = await self.llm_service.generate(prompt)
        
#         # 解析结果
#         return "是" in response.lower()
    
#     async def _identify_legal_topic(self, query: str) -> Dict[str, Any]:
#         """
#         识别查询是否与法律主题相关，如果相关，识别具体主题
        
#         Args:
#             query: 用户查询
            
#         Returns:
#             包含是否相关和具体主题的字典
#         """
#         # 简化的主题关键词映射
#         topic_keywords = {
#             "设立登记和行业准入": ["注册", "登记", "成立", "设立", "营业执照", "许可证", "资质", "准入", "工商", "行业"],
#             "股权架构和公司治理": ["股权", "股份", "股东", "董事", "治理", "决策", "投票", "控制权", "分配"],
#             "劳动关系和员工激励": ["员工", "劳动", "合同", "试用期", "工资", "薪酬", "激励", "股权激励", "福利", "社保"],
#             "知识产权和商业机密": ["专利", "商标", "著作权", "版权", "知识产权", "商业秘密", "保密", "侵权"],
#             "财务融资": ["融资", "投资", "资金", "贷款", "股权融资", "债权", "天使轮", "A轮", "B轮", "IPO"],
#             "税务管理": ["税", "税务", "纳税", "税收", "优惠", "减免", "申报", "发票", "增值税", "所得税"],
#             "合同管理": ["合同", "协议", "条款", "违约", "履行", "签订", "审查", "风险"],
#             "纠纷解决": ["纠纷", "争议", "仲裁", "诉讼", "调解", "违约", "赔偿", "法律责任"]
#         }
        
#         prompt = f"""
#         请分析以下用户查询，判断是否与公司运营的法律问题相关。

#         用户查询: {query}

#         如果相关，请从以下8个法律主题中选择最匹配的一个：
#         1. 设立登记和行业准入
#         2. 股权架构和公司治理  
#         3. 劳动关系和员工激励
#         4. 知识产权和商业机密
#         5. 财务融资
#         6. 税务管理
#         7. 合同管理
#         8. 纠纷解决

#         请严格按照以下格式回答：
#         相关: 是/否
#         主题编号: [如果相关，请填写1-8中的数字；如果不相关，请填写0]
#         主题名称: [如果相关，请填写对应的主题名称；如果不相关，请填写"无"]
#         """
        
#         # 调用LLM
#         response = await self.llm_service.generate(prompt)
        
#         # 解析结果
#         is_legal = False
#         identified_topic = None
#         topic_number = 0
        
#         lines = response.strip().split('\n')
#         for line in lines:
#             line = line.strip()
#             if line.startswith("相关:"):
#                 is_legal = "是" in line
#             elif line.startswith("主题编号:"):
#                 try:
#                     topic_number = int(line.replace("主题编号:", "").strip())
#                 except:
#                     topic_number = 0
#             elif line.startswith("主题名称:"):
#                 topic_name = line.replace("主题名称:", "").strip()
#                 if topic_name != "无":
#                     # 根据编号直接映射到完整主题
#                     topic_mapping = {
#                         1: "设立登记和行业准入：指企业成立时需要完成的工商注册、税务登记等法定手续，以及进入特定行业所需的许可证、资质认证等准入要求，确保企业合法经营",
#                         2: "股权架构和公司治理：涉及公司股东结构设计、股权分配、董事会构成、决策机制等治理框架，旨在明确权责关系，保护股东权益，提高企业运营效率",
#                         3: "劳动关系和员工激励：包括劳动合同签订、薪酬福利设计、绩效考核、股权激励等人力资源管理制度，旨在建立和谐劳动关系，激发员工积极性",
#                         4: "知识产权和商业机密：涉及专利、商标、著作权等知识产权的申请保护，以及商业秘密、技术秘密的保密措施，维护企业核心竞争优势和无形资产",
#                         5: "财务融资：包括企业财务管理、资金筹集、投融资决策、财务报告等，涉及银行贷款、股权融资、债券发行等多种融资方式和财务规范",
#                         6: "税务管理：涉及企业各类税种的申报缴纳、税务筹划、税收优惠政策运用、税务风险防控等，确保合规纳税并优化税负成本",
#                         7: "合同管理：包括合同起草、审查、谈判、履行、变更等全生命周期管理，涉及销售、采购、服务等各类商业合同的法律风险控制",
#                         8: "纠纷解决：指企业面临商业争议时的处理机制，包括协商、调解、仲裁、诉讼等解决途径，以及预防纠纷的合规管理和风险控制措施。"
#                     }
#                     identified_topic = topic_mapping.get(topic_number)
        
#         # 如果LLM没有正确识别，尝试关键词匹配作为备选方案
#         if is_legal and not identified_topic:
#             query_lower = query.lower()
#             best_match = None
#             max_matches = 0
            
#             for topic_name, keywords in topic_keywords.items():
#                 matches = sum(1 for keyword in keywords if keyword in query_lower)
#                 if matches > max_matches:
#                     max_matches = matches
#                     best_match = topic_name
            
#             if best_match and max_matches > 0:
#                 # 找到对应的完整主题描述
#                 for full_topic in self.LEGAL_TOPICS:
#                     if best_match in full_topic:
#                         identified_topic = full_topic
#                         break
        
#         return {
#             "is_legal": is_legal,
#             "topic": identified_topic
#         }
    
#     async def _check_missing_information(
#         self, 
#         query: str, 
#         topic: str, 
#         user_context: Optional[Dict[str, Any]] = None
#     ) -> Dict[str, Any]:
#         """
#         检查对于特定主题是否缺少必要信息
        
#         Args:
#             query: 用户查询
#             topic: 识别出的法律主题
#             user_context: 用户上下文信息
            
#         Returns:
#             包含缺失信息的字典
#         """
#         # 从完整主题描述中提取主题名称
#         topic_name = topic.split("：")[0] if "：" in topic else topic
        
#         # 获取该主题需要的信息
#         required_info = self.TOPIC_INFO_REQUIREMENTS.get(topic_name, [])
        
#         # 如果该主题不需要特定信息，直接返回空
#         if not required_info:
#             return {"missing_info": []}
        
#         # 首先进行基于规则的检查
#         missing_info = self._rule_based_info_check(query, topic_name, required_info, user_context)
        
#         # 如果基于规则的检查发现所有信息都已提供，直接返回
#         if not missing_info:
#             return {"missing_info": []}
        
#         # 如果仍有缺失信息，使用LLM进行二次确认
#         llm_missing_info = await self._llm_based_info_check(query, topic_name, missing_info, user_context)
        
#         return {"missing_info": llm_missing_info}
    
#     def _rule_based_info_check(
#         self, 
#         query: str, 
#         topic_name: str, 
#         required_info: List[str], 
#         user_context: Optional[Dict[str, Any]] = None
#     ) -> List[str]:
#         """
#         基于规则的信息完整性检查
        
#         Args:
#             query: 用户查询
#             topic_name: 主题名称
#             required_info: 需要的信息列表
#             user_context: 用户上下文
            
#         Returns:
#             缺失的信息列表
#         """
#         missing_info = []
#         query_lower = query.lower()
        
#         # 构建上下文信息字符串用于检查
#         context_str = ""
#         if user_context:
#             context_str = self._format_user_context(user_context).lower()
        
#         # 定义信息项的关键词映射
#         info_keywords = {
#             "公司类型/行业": ["行业", "类型", "科技", "软件", "互联网", "制造", "服务", "贸易", "金融", "教育", "医疗", "有限责任", "股份有限"],
#             "公司经营范围": ["经营范围", "业务范围", "经营", "业务", "开发", "咨询", "销售", "服务", "生产", "制造"],
#             "注册地区": ["地区", "地址", "北京", "上海", "深圳", "广州", "杭州", "成都", "武汉", "西安", "南京", "苏州", "省", "市", "区"],
#             "创始人结构": ["创始人", "股东", "合伙人", "团队", "人员", "成员"],
#             "融资阶段": ["融资", "轮次", "天使", "pre-a", "a轮", "b轮", "c轮", "ipo", "种子", "战略投资"],
#             "公司治理结构": ["治理", "董事会", "监事会", "股东会", "决策", "管理层"],
#             "员工规模": ["员工", "人数", "规模", "团队大小", "人员数量", "多少人"],
#             "用工类型": ["用工", "全职", "兼职", "实习", "劳务", "派遣", "外包"],
#             "员工激励需求": ["激励", "股权激励", "期权", "奖金", "提成", "福利"],
#             "技术或产品类型": ["技术", "产品", "软件", "硬件", "算法", "专利", "商标"],
#             "保护需求": ["保护", "专利", "商标", "版权", "商业秘密", "知识产权"],
#             "商业竞争程度": ["竞争", "市场", "对手", "同行", "垄断", "竞争激烈"],
#             "资金使用需求": ["资金", "用途", "投资", "运营", "扩张", "研发"],
#             "商业模式": ["模式", "盈利", "收入", "b2b", "b2c", "saas", "平台"],
#             "税种类型": ["税种", "增值税", "所得税", "印花税", "个税", "社保"],
#             "经营情况": ["经营", "收入", "利润", "亏损", "营业额", "业绩"],
#             "优惠政策": ["优惠", "减免", "政策", "补贴", "扶持"],
#             "合同类型和数量": ["合同", "协议", "数量", "类型", "销售合同", "采购合同", "服务合同"],
#             "合同审批方式": ["审批", "流程", "签署", "审查", "批准"],
#             "履约监控情况": ["履约", "监控", "执行", "违约", "风险"],
#             "纠纷类型": ["纠纷", "争议", "冲突", "违约", "侵权", "劳动纠纷", "合同纠纷"],
#             "争议焦点": ["焦点", "争议点", "分歧", "问题", "核心"],
#             "解决方式偏好": ["解决", "方式", "协商", "调解", "仲裁", "诉讼", "偏好"]
#         }
        
#         for info_item in required_info:
#             found = False
#             keywords = info_keywords.get(info_item, [])
            
#             # 检查查询中是否包含相关关键词
#             for keyword in keywords:
#                 if keyword in query_lower:
#                     found = True
#                     break
            
#             # 检查用户上下文中是否包含相关信息
#             if not found and context_str:
#                 for keyword in keywords:
#                     if keyword in context_str:
#                         found = True
#                         break
            
#             # 特殊处理：检查用户上下文中的具体字段
#             if not found and user_context and "company" in user_context:
#                 company = user_context["company"]
#                 if info_item == "公司类型/行业" and company.get("industry"):
#                     found = True
#                 elif info_item == "公司经营范围" and company.get("business_scope"):
#                     found = True
#                 elif info_item == "注册地区" and company.get("address"):
#                     found = True
#                 elif info_item == "融资阶段" and company.get("financing_stage"):
#                     found = True
            
#             if not found:
#                 missing_info.append(info_item)
        
#         return missing_info
    
#     async def _llm_based_info_check(
#         self, 
#         query: str, 
#         topic_name: str, 
#         potential_missing_info: List[str], 
#         user_context: Optional[Dict[str, Any]] = None
#     ) -> List[str]:
#         """
#         基于LLM的信息完整性检查（二次确认）
        
#         Args:
#             query: 用户查询
#             topic_name: 主题名称
#             potential_missing_info: 可能缺失的信息列表
#             user_context: 用户上下文
            
#         Returns:
#             确认缺失的信息列表
#         """
#         if not potential_missing_info:
#             return []
        
#         # 构建提示词，检查哪些信息已经在查询或上下文中提供
#         context_str = self._format_user_context(user_context) if user_context else "无"
#         info_str = "\n".join([f"- {info}" for info in potential_missing_info])
        
#         prompt = f"""
#         请仔细分析用户查询和已有上下文，判断对于主题"{topic_name}"，以下哪些信息确实缺失。
        
#         用户查询:
#         {query}
        
#         已有上下文:
#         {context_str}
        
#         可能缺失的信息:
#         {info_str}
        
#         分析规则：
#         1. 如果用户查询中明确提到了某项信息，则认为该信息已提供
#         2. 如果上下文中明确包含了某项信息，则认为该信息已提供
#         3. 对于一般性咨询问题（如"劳动合同包含哪些条款"），通常不需要收集具体信息
#         4. 只有当用户明确表达需要具体建议或方案时，才需要收集详细信息
#         5. 如果用户查询是询问"怎么做"、"如何设计"、"需要什么"等具体操作问题，才需要收集信息
        
#         请严格按照以下格式回答:
#         缺失信息: [确实缺失的信息项，用逗号分隔；如果所有信息都已提供或不需要收集，请回答"无"]
#         """
        
#         # 调用LLM
#         response = await self.llm_service.generate(prompt)
        
#         # 解析结果
#         missing_info = []
#         for line in response.split('\n'):
#             line = line.strip()
#             if line.startswith("缺失信息:"):
#                 info_str = line.replace("缺失信息:", "").strip()
#                 if info_str != "无":
#                     # 解析缺失的信息项
#                     for info in info_str.split('，'):
#                         info = info.strip()
#                         # 检查是否是有效的必需信息项
#                         if info and info in potential_missing_info:
#                             missing_info.append(info)
        
#         return missing_info
    
#     async def _generate_info_collection_question(self, topic: str, missing_info: str) -> str:
#         """
#         生成收集缺失信息的问题
        
#         Args:
#             topic: 法律主题
#             missing_info: 缺失的信息项
            
#         Returns:
#             收集信息的问题
#         """
#         prompt = f"""
#         请为主题"{topic}"生成一个友好、专业的问题，用于收集关于"{missing_info}"的信息。
#         问题应当简洁明了，直接询问用户相关信息，不需要过多解释。
#         """
        
#         # 调用LLM
#         response = await self.llm_service.generate(prompt)
        
#         return response.strip()
    
#     async def _generate_enhanced_query(
#         self, 
#         query: str, 
#         topic: str, 
#         user_context: Optional[Dict[str, Any]] = None
#     ) -> str:
#         """
#         根据主题和上下文生成增强查询
        
#         Args:
#             query: 原始查询
#             topic: 法律主题
#             user_context: 用户上下文
            
#         Returns:
#             增强后的查询
#         """
#         context_str = self._format_user_context(user_context) if user_context else "无"
        
#         prompt = f"""
#         请根据用户的原始查询、识别出的法律主题和上下文信息，生成一个更详细的查询，以便更准确地检索相关法律信息。
#         增强查询应当包含原始查询的核心意图，并融入主题和上下文的关键信息。
        
#         原始查询: {query}
#         法律主题: {topic}
#         上下文信息: {context_str}
        
#         请直接给出增强后的查询，不需要任何前缀或解释。
#         """
        
#         # 调用LLM
#         response = await self.llm_service.generate(prompt)
        
#         return response.strip()
    
#     def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
#         """格式化聊天历史"""
#         formatted_history = ""
#         for msg in chat_history:
#             role_prefix = "用户: " if msg["role"] == "user" else "助手: "
#             formatted_history += f"{role_prefix}{msg['content']}\n\n"
        
#         return formatted_history
    
#     def _format_user_context(self, user_context: Dict[str, Any]) -> str:
#         """格式化用户上下文信息"""
#         context_text = ""
        
#         # 处理公司信息
#         if "company" in user_context:
#             company = user_context["company"]
#             if company.get('company_name'):
#                 context_text += f"公司名称: {company.get('company_name')}\n"
#             if company.get('industry'):
#                 context_text += f"行业: {company.get('industry')}\n"
#             if company.get('address'):
#                 context_text += f"地址: {company.get('address')}\n"
#             if company.get('financing_stage'):
#                 context_text += f"融资阶段: {company.get('financing_stage')}\n"
#             if company.get('business_scope'):
#                 context_text += f"经营范围: {company.get('business_scope')}\n"
#             if company.get('additional_info'):
#                 context_text += f"其他信息: {company.get('additional_info')}\n"
            
#             # 处理可能的其他公司字段
#             for key, value in company.items():
#                 if key not in ['company_name', 'industry', 'address', 'financing_stage', 'business_scope', 'additional_info'] and value:
#                     context_text += f"{key}: {value}\n"
        
#         # 处理其他可能的上下文信息
#         for key, value in user_context.items():
#             if key != "company" and isinstance(value, (str, int, float, bool)) and value:
#                 context_text += f"{key}: {value}\n"
        
#         return context_text