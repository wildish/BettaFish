"""
Redis 缓存层

实现 Layer 1 热缓存（短期缓存，快速访问）
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime
import redis
from loguru import logger


class RedisCache:
    """
    Redis 缓存管理器
    
    用于缓存：
    - 搜索结果（TTL: 1小时）
    - 分析结果（TTL: 24小时）
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 6379,
                 db: int = 0,
                 password: Optional[str] = None,
                 search_ttl: int = 3600,
                 analysis_ttl: int = 86400,
                 search_prefix: str = 'taurus:search:',
                 analysis_prefix: str = 'taurus:analysis:'):
        """
        初始化 Redis 缓存
        
        Args:
            host: Redis主机
            port: Redis端口
            db: Redis数据库编号
            password: Redis密码（可选）
            search_ttl: 搜索结果缓存时间（秒）
            analysis_ttl: 分析结果缓存时间（秒）
            search_prefix: 搜索缓存键前缀
            analysis_prefix: 分析缓存键前缀
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        
        self.search_ttl = search_ttl
        self.analysis_ttl = analysis_ttl
        self.search_prefix = search_prefix
        self.analysis_prefix = analysis_prefix
        
        # 初始化 Redis 客户端
        try:
            self.client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # 测试连接
            self.client.ping()
            logger.info(f"Redis 缓存初始化成功 - {host}:{port}/{db}")
            
        except Exception as e:
            logger.error(f"Redis 连接失败: {str(e)}")
            self.client = None
    
    def _generate_cache_key(self, prefix: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            prefix: 键前缀
            **kwargs: 用于生成键的参数
        
        Returns:
            str: 缓存键
        """
        # 将参数排序并序列化
        sorted_params = sorted(kwargs.items())
        param_str = json.dumps(sorted_params, ensure_ascii=False, sort_keys=True)
        
        # 生成哈希
        hash_obj = hashlib.md5(param_str.encode('utf-8'))
        hash_key = hash_obj.hexdigest()
        
        return f"{prefix}{hash_key}"
    
    def get_search_cache(self, 
                        stock_code: str,
                        stock_name: str,
                        search_topic: str,
                        days: int) -> Optional[List[Dict[str, Any]]]:
        """
        获取搜索结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            days: 搜索天数
        
        Returns:
            Optional[List[Dict]]: 缓存的搜索结果，如果不存在返回None
        """
        if not self.client:
            return None
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                self.search_prefix,
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                days=days
            )
            
            # 获取缓存
            cached_data = self.client.get(cache_key)
            
            if cached_data:
                logger.info(f"Redis 搜索缓存命中 - {cache_key[:50]}...")
                return json.loads(cached_data)
            else:
                logger.debug(f"Redis 搜索缓存未命中 - {cache_key[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"获取搜索缓存失败: {str(e)}")
            return None
    
    def set_search_cache(self,
                        stock_code: str,
                        stock_name: str,
                        search_topic: str,
                        days: int,
                        search_results: List[Dict[str, Any]]) -> bool:
        """
        设置搜索结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            days: 搜索天数
            search_results: 搜索结果列表
        
        Returns:
            bool: 是否成功
        """
        if not self.client:
            return False
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                self.search_prefix,
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                days=days
            )
            
            # 序列化数据
            cache_data = json.dumps(search_results, ensure_ascii=False)
            
            # 设置缓存（带过期时间）
            self.client.setex(cache_key, self.search_ttl, cache_data)
            
            logger.info(f"Redis 搜索缓存已设置 - {cache_key[:50]}..., TTL: {self.search_ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"设置搜索缓存失败: {str(e)}")
            return False
    
    def get_analysis_cache(self,
                          stock_code: str,
                          stock_name: str,
                          search_topic: str,
                          news_count: int) -> Optional[Dict[str, Any]]:
        """
        获取分析结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            news_count: 新闻数量
        
        Returns:
            Optional[Dict]: 缓存的分析结果，如果不存在返回None
        """
        if not self.client:
            return None
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                self.analysis_prefix,
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                news_count=news_count
            )
            
            # 获取缓存
            cached_data = self.client.get(cache_key)
            
            if cached_data:
                logger.info(f"Redis 分析缓存命中 - {cache_key[:50]}...")
                return json.loads(cached_data)
            else:
                logger.debug(f"Redis 分析缓存未命中 - {cache_key[:50]}...")
                return None
                
        except Exception as e:
            logger.error(f"获取分析缓存失败: {str(e)}")
            return None
    
    def set_analysis_cache(self,
                          stock_code: str,
                          stock_name: str,
                          search_topic: str,
                          news_count: int,
                          analysis_result: Dict[str, Any]) -> bool:
        """
        设置分析结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            news_count: 新闻数量
            analysis_result: 分析结果
        
        Returns:
            bool: 是否成功
        """
        if not self.client:
            return False
        
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                self.analysis_prefix,
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                news_count=news_count
            )
            
            # 序列化数据
            cache_data = json.dumps(analysis_result, ensure_ascii=False)
            
            # 设置缓存（带过期时间）
            self.client.setex(cache_key, self.analysis_ttl, cache_data)
            
            logger.info(f"Redis 分析缓存已设置 - {cache_key[:50]}..., TTL: {self.analysis_ttl}s")
            return True
            
        except Exception as e:
            logger.error(f"设置分析缓存失败: {str(e)}")
            return False
    
    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        清除缓存
        
        Args:
            pattern: 键模式（如 "taurus:search:*"），如果为None则清除所有taurus缓存
        
        Returns:
            int: 删除的键数量
        """
        if not self.client:
            return 0
        
        try:
            if pattern is None:
                pattern = "taurus:*"
            
            # 查找匹配的键
            keys = self.client.keys(pattern)
            
            if keys:
                # 删除键
                deleted = self.client.delete(*keys)
                logger.info(f"清除缓存 - 模式: {pattern}, 删除: {deleted} 个键")
                return deleted
            else:
                logger.info(f"清除缓存 - 模式: {pattern}, 未找到匹配的键")
                return 0
                
        except Exception as e:
            logger.error(f"清除缓存失败: {str(e)}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.client:
            return {'error': 'Redis未连接'}
        
        try:
            # 统计搜索缓存
            search_keys = self.client.keys(f"{self.search_prefix}*")
            search_count = len(search_keys)
            
            # 统计分析缓存
            analysis_keys = self.client.keys(f"{self.analysis_prefix}*")
            analysis_count = len(analysis_keys)
            
            # Redis 信息
            info = self.client.info('memory')
            
            stats = {
                'search_cache_count': search_count,
                'analysis_cache_count': analysis_count,
                'total_cache_count': search_count + analysis_count,
                'memory_used': info.get('used_memory_human', 'N/A'),
                'memory_peak': info.get('used_memory_peak_human', 'N/A')
            }
            
            logger.debug(f"缓存统计: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {'error': str(e)}
    
    def close(self):
        """关闭 Redis 连接"""
        if self.client:
            self.client.close()
            logger.info("Redis 连接已关闭")


if __name__ == "__main__":
    # 测试 Redis 缓存
    from ..utils.config import settings
    
    cache = RedisCache(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD,
        search_ttl=settings.REDIS_CACHE_TTL_SEARCH,
        analysis_ttl=settings.REDIS_CACHE_TTL_ANALYSIS,
        search_prefix=settings.CACHE_KEY_PREFIX_SEARCH,
        analysis_prefix=settings.CACHE_KEY_PREFIX_ANALYSIS
    )
    
    # 测试搜索缓存
    print("\n=== 测试搜索缓存 ===")
    test_search_results = [
        {'title': '测试新闻1', 'content': '内容1', 'url': 'http://example.com/1'},
        {'title': '测试新闻2', 'content': '内容2', 'url': 'http://example.com/2'}
    ]
    
    # 设置缓存
    cache.set_search_cache(
        stock_code='600519',
        stock_name='贵州茅台',
        search_topic='提价',
        days=7,
        search_results=test_search_results
    )
    
    # 获取缓存
    cached = cache.get_search_cache(
        stock_code='600519',
        stock_name='贵州茅台',
        search_topic='提价',
        days=7
    )
    print(f"缓存结果: {cached}")
    
    # 测试分析缓存
    print("\n=== 测试分析缓存 ===")
    test_analysis = {
        'relevance_score': 0.85,
        'catalyst_type': 'positive',
        'catalyst_strength': 'major',
        'catalyst_events': ['提价18%']
    }
    
    cache.set_analysis_cache(
        stock_code='600519',
        stock_name='贵州茅台',
        search_topic='提价',
        news_count=5,
        analysis_result=test_analysis
    )
    
    cached_analysis = cache.get_analysis_cache(
        stock_code='600519',
        stock_name='贵州茅台',
        search_topic='提价',
        news_count=5
    )
    print(f"分析缓存: {cached_analysis}")
    
    # 统计信息
    print("\n=== 缓存统计 ===")
    stats = cache.get_cache_stats()
    print(f"统计: {stats}")
    
    cache.close()
