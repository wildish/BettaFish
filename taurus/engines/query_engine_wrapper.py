"""
QueryEngine 包装器

封装 QueryEngine 的搜索功能，集成 Query 优化
"""

from typing import List, Dict, Any, Optional
from loguru import logger
import sys
from pathlib import Path

# 添加QueryEngine到路径
query_engine_path = Path(__file__).resolve().parents[2] / "QueryEngine"
if str(query_engine_path) not in sys.path:
    sys.path.insert(0, str(query_engine_path))

from QueryEngine.tools.search import TavilyNewsAgency
from .query_optimizer import QueryOptimizer


class QueryEngineWrapper:
    """
    QueryEngine包装器（集成Query优化）
    """
    
    def __init__(self, 
                 tavily_api_key: str,
                 optimizer: Optional[QueryOptimizer] = None):
        """
        初始化包装器
        
        Args:
            tavily_api_key: Tavily API密钥
            optimizer: Query优化器实例（可选）
        """
        self.search_agency = TavilyNewsAgency(api_key=tavily_api_key)
        self.optimizer = optimizer
        
        logger.info("QueryEngineWrapper 初始化完成")
    
    def search_catalyst_news(self, 
                            stock_code: str, 
                            stock_name: str,
                            search_topic: str, 
                            sector: Optional[str] = None,
                            days: int = 7,
                            use_optimizer: bool = True) -> List[Dict[str, Any]]:
        """
        搜索催化相关新闻（带Query优化）
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            sector: 板块（可选）
            days: 搜索天数（1, 7, 或其他）
            use_optimizer: 是否使用Query优化器
        
        Returns:
            list: 新闻列表
            [
                {
                    'title': str,
                    'content': str,
                    'url': str,
                    'source': 'tavily',
                    'published_date': str,
                    'score': float
                },
                ...
            ]
        """
        logger.info(f"搜索催化新闻 - {stock_name}({stock_code}), 主题: {search_topic}, 天数: {days}")
        
        # Step 1: 优化查询（如果启用）
        if use_optimizer and self.optimizer:
            try:
                optimization_result = self.optimizer.optimize_query(
                    stock_name=stock_name,
                    search_topic=search_topic,
                    sector=sector
                )
                optimized_query = optimization_result['optimized_query']
                logger.info(f"原始主题: {search_topic}")
                logger.info(f"优化查询: {optimized_query}")
            except Exception as e:
                logger.warning(f"Query优化失败，使用原始查询: {str(e)}")
                optimized_query = f"{stock_name} {search_topic}"
        else:
            # 不使用优化器，直接拼接
            optimized_query = f"{stock_name} {search_topic}"
            logger.info(f"搜索查询（未优化）: {optimized_query}")
        
        # Step 2: 选择搜索工具
        try:
            if days == 1:
                logger.debug("使用 search_news_last_24_hours")
                response = self.search_agency.search_news_last_24_hours(optimized_query)
            elif days == 7:
                logger.debug("使用 search_news_last_week")
                response = self.search_agency.search_news_last_week(optimized_query)
            else:
                logger.debug(f"使用 basic_search_news (max_results=10)")
                response = self.search_agency.basic_search_news(
                    optimized_query, 
                    max_results=10
                )
        except Exception as e:
            logger.error(f"搜索失败: {str(e)}")
            return []
        
        # Step 3: 格式化结果
        news_list = self._format_results(response)
        
        logger.info(f"搜索完成，找到 {len(news_list)} 条新闻")
        
        return news_list
    
    def _format_results(self, response) -> List[Dict[str, Any]]:
        """
        格式化搜索结果
        
        Args:
            response: TavilyResponse对象
        
        Returns:
            格式化后的新闻列表
        """
        news_list = []
        
        if not hasattr(response, 'results') or not response.results:
            logger.warning("搜索结果为空")
            return news_list
        
        for result in response.results:
            try:
                news_item = {
                    'title': result.title if hasattr(result, 'title') else '',
                    'content': result.content if hasattr(result, 'content') else '',
                    'url': result.url if hasattr(result, 'url') else '',
                    'source': 'tavily',
                    'published_date': result.published_date if hasattr(result, 'published_date') else None,
                    'score': result.score if hasattr(result, 'score') else 0.0
                }
                news_list.append(news_item)
            except Exception as e:
                logger.warning(f"格式化单条结果失败: {str(e)}")
                continue
        
        return news_list


if __name__ == "__main__":
    # 测试QueryEngineWrapper
    from ..utils.config import settings
    
    # 创建优化器
    optimizer = QueryOptimizer(
        api_key=settings.QUERY_ENGINE_API_KEY,
        base_url=settings.QUERY_ENGINE_BASE_URL,
        model_name=settings.QUERY_ENGINE_MODEL_NAME
    )
    
    # 创建包装器
    wrapper = QueryEngineWrapper(
        tavily_api_key=settings.TAVILY_API_KEY,
        optimizer=optimizer
    )
    
    # 测试搜索
    print("\n=== 测试搜索 ===")
    results = wrapper.search_catalyst_news(
        stock_code="600519",
        stock_name="贵州茅台",
        search_topic="提价",
        sector="白酒",
        days=7,
        use_optimizer=True
    )
    
    print(f"\n找到 {len(results)} 条新闻")
    for i, news in enumerate(results[:3], 1):
        print(f"\n新闻 {i}:")
        print(f"  标题: {news['title']}")
        print(f"  URL: {news['url']}")
        print(f"  评分: {news['score']}")
