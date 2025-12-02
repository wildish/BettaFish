"""
催化分析引擎

使用 LLM 分析新闻对股票的催化作用
"""

import json
from typing import List, Dict, Any, Optional
from loguru import logger
from openai import OpenAI


# 催化分析Prompt
CATALYST_ANALYSIS_PROMPT = """
你是一个专业的金融分析师，擅长识别和评估市场催化事件。

任务：分析以下新闻是否对指定股票构成催化，并评估催化强度。

股票信息：
- 股票代码: {stock_code}
- 股票名称: {stock_name}
- 板块: {sector}
- 搜索主题: {search_topic}

新闻列表（共{news_count}条）：
{news_list}

分析要求：
1. **相关性评分**（0-1）：评估新闻与股票和主题的相关程度
   - 1.0: 高度相关，直接涉及该股票和主题
   - 0.5-0.9: 中度相关，涉及行业或板块
   - 0-0.4: 低度相关或无关

2. **催化类型**：
   - positive: 利好催化
   - negative: 利空催化
   - neutral: 中性或无催化

3. **催化强度**：
   - major: 重大催化（如重大政策、业绩超预期、重大合作等）
   - normal: 一般催化（如常规业务进展、行业动态等）
   - minor: 轻微催化（如市场传闻、分析师观点等）

4. **催化事件**：提取具体的催化事件（3-5个关键事件）

输出格式（必须严格遵守JSON格式）：
```json
{
    "relevance_score": 0.85,
    "catalyst_type": "positive",
    "catalyst_strength": "major",
    "catalyst_events": [
        "茅台宣布提价18%",
        "经销商确认新价格体系",
        "分析师上调目标价"
    ],
    "reasoning": "新闻高度相关，茅台提价是重大利好催化，预计带动板块估值提升",
    "news_summary": "贵州茅台宣布产品提价，幅度超市场预期，经销商积极响应"
}
```

注意事项：
- 必须返回有效的JSON格式，不要有其他文本
- relevance_score 必须在 0-1 之间
- catalyst_events 数量控制在 3-5 个
- 如果新闻与股票无关，relevance_score 应该很低（<0.3）
- 如果没有明确的催化事件，catalyst_type 应该是 neutral

现在请分析：
"""


class CatalystAnalyzer:
    """
    催化分析引擎（基于LLM）
    """
    
    def __init__(self, api_key: str, base_url: Optional[str] = None, model_name: str = "gpt-3.5-turbo"):
        """
        初始化催化分析引擎
        
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
        
        logger.info(f"CatalystAnalyzer 初始化完成 - 模型: {model_name}")
    
    def analyze_catalyst(self,
                        stock_code: str,
                        stock_name: str,
                        search_topic: str,
                        news_list: List[Dict[str, Any]],
                        sector: Optional[str] = None) -> Dict[str, Any]:
        """
        分析催化作用
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            news_list: 新闻列表
            sector: 板块（可选）
        
        Returns:
            {
                'relevance_score': float,
                'catalyst_type': str,
                'catalyst_strength': str,
                'catalyst_events': List[str],
                'reasoning': str,
                'news_summary': str
            }
        """
        logger.info(f"分析催化 - {stock_name}({stock_code}), 主题: {search_topic}, 新闻数: {len(news_list)}")
        
        # 检查新闻数量
        if not news_list or len(news_list) == 0:
            logger.warning("新闻列表为空，返回默认结果")
            return self._get_default_result()
        
        # 格式化新闻列表
        news_text = self._format_news_list(news_list)
        
        # 构造Prompt
        prompt = CATALYST_ANALYSIS_PROMPT.format(
            stock_code=stock_code,
            stock_name=stock_name,
            sector=sector or "未知",
            search_topic=search_topic,
            news_count=len(news_list),
            news_list=news_text
        )
        
        # 调用LLM
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # 解析响应
            result = self._parse_response(response.choices[0].message.content)
            
            logger.info(f"催化分析完成 - 类型: {result['catalyst_type']}, 强度: {result['catalyst_strength']}, 相关性: {result['relevance_score']}")
            
            return result
            
        except Exception as e:
            logger.error(f"催化分析失败: {str(e)}")
            return self._get_default_result()
    
    def _format_news_list(self, news_list: List[Dict[str, Any]]) -> str:
        """
        格式化新闻列表为文本
        
        Args:
            news_list: 新闻列表
        
        Returns:
            格式化后的文本
        """
        formatted = []
        
        for i, news in enumerate(news_list, 1):
            title = news.get('title', '无标题')
            content = news.get('content', '')
            published_date = news.get('published_date', '未知日期')
            
            # 截断过长的内容
            if len(content) > 500:
                content = content[:500] + "..."
            
            formatted.append(f"""
新闻 {i}:
标题: {title}
日期: {published_date}
内容: {content}
""")
        
        return "\n".join(formatted)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: LLM原始响应
        
        Returns:
            解析后的结果
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
            required_fields = ['relevance_score', 'catalyst_type', 'catalyst_strength', 'catalyst_events']
            if not all(field in result for field in required_fields):
                raise ValueError("缺少必需字段")
            
            # 验证数据类型和范围
            if not (0 <= result['relevance_score'] <= 1):
                logger.warning(f"相关性评分超出范围: {result['relevance_score']}, 修正为 0.5")
                result['relevance_score'] = 0.5
            
            if result['catalyst_type'] not in ['positive', 'negative', 'neutral']:
                logger.warning(f"催化类型无效: {result['catalyst_type']}, 修正为 neutral")
                result['catalyst_type'] = 'neutral'
            
            if result['catalyst_strength'] not in ['major', 'normal', 'minor']:
                logger.warning(f"催化强度无效: {result['catalyst_strength']}, 修正为 normal")
                result['catalyst_strength'] = 'normal'
            
            return result
            
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}, 原始响应: {response[:200]}")
            raise e
    
    def _get_default_result(self) -> Dict[str, Any]:
        """
        获取默认结果（当分析失败或无新闻时）
        
        Returns:
            默认结果
        """
        return {
            'relevance_score': 0.0,
            'catalyst_type': 'neutral',
            'catalyst_strength': 'minor',
            'catalyst_events': [],
            'reasoning': '无相关新闻或分析失败',
            'news_summary': '暂无新闻'
        }


if __name__ == "__main__":
    # 测试催化分析器
    from ..utils.config import settings
    
    analyzer = CatalystAnalyzer(
        api_key=settings.INSIGHT_ENGINE_API_KEY,
        base_url=settings.INSIGHT_ENGINE_BASE_URL,
        model_name=settings.INSIGHT_ENGINE_MODEL_NAME
    )
    
    # 模拟新闻数据
    test_news = [
        {
            'title': '贵州茅台宣布提价18%，超市场预期',
            'content': '贵州茅台今日宣布，飞天茅台出厂价上调18%，批发价相应调整。这是茅台近三年来最大幅度提价，超出市场预期。',
            'published_date': '2025-12-01',
            'score': 0.95
        },
        {
            'title': '经销商确认茅台新价格体系',
            'content': '多家经销商确认收到茅台新价格通知，新价格将于下月开始执行。业内人士认为此次提价将带动整个高端白酒板块估值提升。',
            'published_date': '2025-12-01',
            'score': 0.88
        }
    ]
    
    # 测试分析
    print("\n=== 测试催化分析 ===")
    result = analyzer.analyze_catalyst(
        stock_code="600519",
        stock_name="贵州茅台",
        search_topic="提价",
        news_list=test_news,
        sector="白酒"
    )
    
    print(f"\n相关性评分: {result['relevance_score']}")
    print(f"催化类型: {result['catalyst_type']}")
    print(f"催化强度: {result['catalyst_strength']}")
    print(f"催化事件: {result['catalyst_events']}")
    print(f"推理: {result['reasoning']}")
