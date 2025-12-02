"""
Query 优化器

使用 LLM 优化搜索查询，提取关键词、扩展同义词、添加行业术语
"""

import json
from typing import Dict, Any, Optional
from loguru import logger
from openai import OpenAI


# Query优化Prompt
QUERY_OPTIMIZATION_PROMPT = """
你是一个专业的金融信息检索专家，擅长优化搜索查询以获得最相关的新闻结果。

任务：
根据给定的股票名称和搜索主题，生成优化的搜索查询。

优化原则：
1. **核心关键词提取**：提取最核心的关键词，去除冗余词汇
2. **同义词扩展**：添加相关的同义词或近义词（如"提价"→"价格调整"、"涨价"）
3. **行业术语**：根据板块添加行业特定术语（如白酒板块→"高端白酒"、"飞天茅台"）
4. **简洁性**：保持查询简洁，避免过长的句子
5. **相关性**：确保所有关键词都与股票和主题高度相关

输入格式：
```json
{
    "stock_name": "贵州茅台",
    "search_topic": "提价策略",
    "sector": "白酒"  // 可选
}
```

输出格式（必须严格遵守JSON格式）：
```json
{
    "optimized_query": "贵州茅台 提价",
    "keywords": [
        "贵州茅台",
        "提价",
        "价格调整",
        "飞天茅台",
        "出厂价"
    ],
    "reasoning": "提取核心词'贵州茅台'和'提价'，添加同义词'价格调整'，补充产品名'飞天茅台'和相关术语'出厂价'，提升搜索相关性"
}
```

注意事项：
- optimized_query应该是最终用于搜索的查询字符串，简洁且高度相关
- keywords是提取和扩展的关键词列表，用于理解查询意图
- reasoning解释优化的思路和依据
- 必须返回有效的JSON格式，不要有其他文本
- 关键词数量控制在3-8个之间

现在请优化以下查询：
"""


class QueryOptimizer:
    """
    搜索查询优化器（基于LLM）
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """
        初始化查询优化器
        
        Args:
            api_key: LLM API密钥
            base_url: LLM API基础URL（可选）
            model_name: LLM模型名称
        """
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        
        # 初始化OpenAI客户端
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
        
        self.client = OpenAI(**client_kwargs)
        
        logger.info(f"QueryOptimizer 初始化完成 - 模型: {model_name}")
    
    def optimize_query(self, stock_name: str, search_topic: str, 
                      sector: Optional[str] = None) -> Dict[str, Any]:
        """
        优化搜索查询
        
        Args:
            stock_name: 股票名称（如"贵州茅台"）
            search_topic: 搜索主题（如"提价"）
            sector: 板块（如"白酒"，可选）
        
        Returns:
            {
                'optimized_query': str,
                'keywords': List[str],
                'reasoning': str
            }
        """
        logger.info(f"优化查询 - 股票: {stock_name}, 主题: {search_topic}, 板块: {sector}")
        
        # 构造输入数据
        input_data = {
            'stock_name': stock_name,
            'search_topic': search_topic
        }
        
        if sector:
            input_data['sector'] = sector
        
        user_message = json.dumps(input_data, ensure_ascii=False)
        
        # 调用LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": QUERY_OPTIMIZATION_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # 解析响应
            result = self._parse_response(response.choices[0].message.content)
            
            logger.info(f"优化后查询: {result['optimized_query']}")
            logger.debug(f"关键词: {result['keywords']}")
            
            return result
            
        except Exception as e:
            logger.error(f"查询优化失败: {str(e)}")
            # 返回默认查询
            return self._get_fallback_query(stock_name, search_topic)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: LLM原始响应
        
        Returns:
            {
                'optimized_query': str,
                'keywords': List[str],
                'reasoning': str
            }
        """
        try:
            # 清理JSON标签
            cleaned = response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # 解析JSON
            result = json.loads(cleaned)
            
            # 验证必需字段
            required_fields = ['optimized_query', 'keywords', 'reasoning']
            if not all(field in result for field in required_fields):
                raise ValueError("缺少必需字段")
            
            # 验证关键词数量
            if not isinstance(result['keywords'], list) or len(result['keywords']) < 1:
                raise ValueError("关键词列表无效")
            
            return result
            
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}, 原始响应: {response[:200]}")
            raise e
    
    def _get_fallback_query(self, stock_name: str, search_topic: str) -> Dict[str, Any]:
        """
        获取默认查询（当LLM失败时）
        
        Args:
            stock_name: 股票名称
            search_topic: 搜索主题
        
        Returns:
            默认的查询结果
        """
        optimized_query = f"{stock_name} {search_topic}"
        
        logger.warning(f"使用默认查询: {optimized_query}")
        
        return {
            'optimized_query': optimized_query,
            'keywords': [stock_name, search_topic],
            'reasoning': '使用默认查询（LLM优化失败）'
        }


if __name__ == "__main__":
    # 测试Query优化器
    from ..utils.config import settings
    
    optimizer = QueryOptimizer(
        api_key=settings.QUERY_ENGINE_API_KEY,
        base_url=settings.QUERY_ENGINE_BASE_URL,
        model_name=settings.QUERY_ENGINE_MODEL_NAME
    )
    
    # 测试案例1
    result1 = optimizer.optimize_query(
        stock_name="贵州茅台",
        search_topic="提价策略",
        sector="白酒"
    )
    print("\n=== 测试案例1 ===")
    print(f"优化查询: {result1['optimized_query']}")
    print(f"关键词: {result1['keywords']}")
    print(f"推理: {result1['reasoning']}")
    
    # 测试案例2
    result2 = optimizer.optimize_query(
        stock_name="宁德时代",
        search_topic="补贴政策",
        sector="新能源"
    )
    print("\n=== 测试案例2 ===")
    print(f"优化查询: {result2['optimized_query']}")
    print(f"关键词: {result2['keywords']}")
    print(f"推理: {result2['reasoning']}")
