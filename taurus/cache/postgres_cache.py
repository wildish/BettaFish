"""
PostgreSQL 缓存层

实现 Layer 2 温缓存（长期缓存，持久化存储）
"""

import json
import hashlib
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from loguru import logger
from sqlalchemy.orm import Session

from ..database.models import (
    FactorCachedSearchResult,
    FactorCachedAnalysisResult,
    get_db
)


class PostgresCache:
    """
    PostgreSQL 缓存管理器
    
    用于缓存：
    - 搜索结果（TTL: 7天）
    - 分析结果（永久保存）
    """
    
    def __init__(self,
                 search_ttl: int = 604800,  # 7天
                 analysis_ttl: int = 0):     # 0表示永久
        """
        初始化 PostgreSQL 缓存
        
        Args:
            search_ttl: 搜索结果缓存时间（秒），0表示永久
            analysis_ttl: 分析结果缓存时间（秒），0表示永久
        """
        self.search_ttl = search_ttl
        self.analysis_ttl = analysis_ttl
        
        logger.info(f"PostgreSQL 缓存初始化 - 搜索TTL: {search_ttl}s, 分析TTL: {analysis_ttl}s")
    
    def _generate_cache_key(self, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
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
        
        return hash_key
    
    def _is_cache_expired(self, created_at: datetime, ttl: int) -> bool:
        """
        检查缓存是否过期
        
        Args:
            created_at: 创建时间
            ttl: 过期时间（秒），0表示永不过期
        
        Returns:
            bool: 是否过期
        """
        if ttl == 0:
            return False
        
        expiry_time = created_at + timedelta(seconds=ttl)
        return datetime.utcnow() > expiry_time
    
    def get_search_cache(self,
                        stock_code: str,
                        stock_name: str,
                        search_topic: str,
                        days: int,
                        db: Session) -> Optional[List[Dict[str, Any]]]:
        """
        获取搜索结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            days: 搜索天数
            db: 数据库会话
        
        Returns:
            Optional[List[Dict]]: 缓存的搜索结果，如果不存在或过期返回None
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                days=days
            )
            
            # 查询缓存
            cached = db.query(FactorCachedSearchResult).filter_by(
                cache_key=cache_key
            ).first()
            
            if not cached:
                logger.debug(f"PostgreSQL 搜索缓存未命中 - {cache_key[:20]}...")
                return None
            
            # 检查是否过期
            if self._is_cache_expired(cached.created_at, self.search_ttl):
                logger.info(f"PostgreSQL 搜索缓存已过期 - {cache_key[:20]}...")
                # 删除过期缓存
                db.delete(cached)
                db.commit()
                return None
            
            logger.info(f"PostgreSQL 搜索缓存命中 - {cache_key[:20]}...")
            return cached.search_results
            
        except Exception as e:
            logger.error(f"获取搜索缓存失败: {str(e)}")
            db.rollback()
            return None
    
    def set_search_cache(self,
                        stock_code: str,
                        stock_name: str,
                        search_topic: str,
                        days: int,
                        search_results: List[Dict[str, Any]],
                        db: Session) -> bool:
        """
        设置搜索结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            days: 搜索天数
            search_results: 搜索结果列表
            db: 数据库会话
        
        Returns:
            bool: 是否成功
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                days=days
            )
            
            # 构造搜索查询字符串
            search_query = f"{stock_name} {search_topic}"
            
            # 检查是否已存在
            existing = db.query(FactorCachedSearchResult).filter_by(
                cache_key=cache_key
            ).first()
            
            if existing:
                # 更新现有缓存
                existing.search_results = search_results
                existing.result_count = len(search_results)
                existing.updated_at = datetime.utcnow()
                logger.info(f"PostgreSQL 搜索缓存已更新 - {cache_key[:20]}...")
            else:
                # 创建新缓存
                new_cache = FactorCachedSearchResult(
                    cache_key=cache_key,
                    search_query=search_query,
                    search_results=search_results,
                    result_count=len(search_results),
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_cache)
                logger.info(f"PostgreSQL 搜索缓存已创建 - {cache_key[:20]}...")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"设置搜索缓存失败: {str(e)}")
            db.rollback()
            return False
    
    def get_analysis_cache(self,
                          stock_code: str,
                          stock_name: str,
                          search_topic: str,
                          news_count: int,
                          db: Session) -> Optional[Dict[str, Any]]:
        """
        获取分析结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            news_count: 新闻数量
            db: 数据库会话
        
        Returns:
            Optional[Dict]: 缓存的分析结果，如果不存在或过期返回None
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                news_count=news_count
            )
            
            # 查询缓存
            cached = db.query(FactorCachedAnalysisResult).filter_by(
                cache_key=cache_key
            ).first()
            
            if not cached:
                logger.debug(f"PostgreSQL 分析缓存未命中 - {cache_key[:20]}...")
                return None
            
            # 检查是否过期
            if self._is_cache_expired(cached.created_at, self.analysis_ttl):
                logger.info(f"PostgreSQL 分析缓存已过期 - {cache_key[:20]}...")
                # 删除过期缓存
                db.delete(cached)
                db.commit()
                return None
            
            logger.info(f"PostgreSQL 分析缓存命中 - {cache_key[:20]}...")
            return cached.analysis_result
            
        except Exception as e:
            logger.error(f"获取分析缓存失败: {str(e)}")
            db.rollback()
            return None
    
    def set_analysis_cache(self,
                          stock_code: str,
                          stock_name: str,
                          search_topic: str,
                          news_count: int,
                          analysis_result: Dict[str, Any],
                          db: Session) -> bool:
        """
        设置分析结果缓存
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            news_count: 新闻数量
            analysis_result: 分析结果
            db: 数据库会话
        
        Returns:
            bool: 是否成功
        """
        try:
            # 生成缓存键
            cache_key = self._generate_cache_key(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                news_count=news_count
            )
            
            # 构造搜索查询字符串
            search_query = f"{stock_name} {search_topic}"
            
            # 检查是否已存在
            existing = db.query(FactorCachedAnalysisResult).filter_by(
                cache_key=cache_key
            ).first()
            
            if existing:
                # 更新现有缓存
                existing.analysis_result = analysis_result
                existing.updated_at = datetime.utcnow()
                logger.info(f"PostgreSQL 分析缓存已更新 - {cache_key[:20]}...")
            else:
                # 创建新缓存
                new_cache = FactorCachedAnalysisResult(
                    cache_key=cache_key,
                    stock_code=stock_code,
                    search_query=search_query,
                    analysis_result=analysis_result,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_cache)
                logger.info(f"PostgreSQL 分析缓存已创建 - {cache_key[:20]}...")
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"设置分析缓存失败: {str(e)}")
            db.rollback()
            return False
    
    def clear_expired_cache(self, db: Session) -> Dict[str, int]:
        """
        清除过期缓存
        
        Args:
            db: 数据库会话
        
        Returns:
            Dict: 清除统计 {'search': count, 'analysis': count}
        """
        try:
            stats = {'search': 0, 'analysis': 0}
            
            # 清除过期搜索缓存
            if self.search_ttl > 0:
                expiry_time = datetime.utcnow() - timedelta(seconds=self.search_ttl)
                deleted_search = db.query(FactorCachedSearchResult).filter(
                    FactorCachedSearchResult.created_at < expiry_time
                ).delete()
                stats['search'] = deleted_search
                logger.info(f"清除过期搜索缓存: {deleted_search} 条")
            
            # 清除过期分析缓存
            if self.analysis_ttl > 0:
                expiry_time = datetime.utcnow() - timedelta(seconds=self.analysis_ttl)
                deleted_analysis = db.query(FactorCachedAnalysisResult).filter(
                    FactorCachedAnalysisResult.created_at < expiry_time
                ).delete()
                stats['analysis'] = deleted_analysis
                logger.info(f"清除过期分析缓存: {deleted_analysis} 条")
            
            db.commit()
            return stats
            
        except Exception as e:
            logger.error(f"清除过期缓存失败: {str(e)}")
            db.rollback()
            return {'search': 0, 'analysis': 0}
    
    def get_cache_stats(self, db: Session) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Args:
            db: 数据库会话
        
        Returns:
            Dict: 统计信息
        """
        try:
            # 统计搜索缓存
            search_count = db.query(FactorCachedSearchResult).count()
            
            # 统计分析缓存
            analysis_count = db.query(FactorCachedAnalysisResult).count()
            
            stats = {
                'search_cache_count': search_count,
                'analysis_cache_count': analysis_count,
                'total_cache_count': search_count + analysis_count,
                'search_ttl': self.search_ttl,
                'analysis_ttl': self.analysis_ttl
            }
            
            logger.debug(f"PostgreSQL 缓存统计: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"获取缓存统计失败: {str(e)}")
            return {'error': str(e)}


if __name__ == "__main__":
    # 测试 PostgreSQL 缓存
    from ..utils.config import settings, get_database_url
    from ..database.models import init_database
    
    # 初始化数据库
    database_url = get_database_url()
    init_database(database_url)
    
    cache = PostgresCache(
        search_ttl=settings.POSTGRES_CACHE_TTL_SEARCH,
        analysis_ttl=settings.POSTGRES_CACHE_TTL_ANALYSIS
    )
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
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
            search_results=test_search_results,
            db=db
        )
        
        # 获取缓存
        cached = cache.get_search_cache(
            stock_code='600519',
            stock_name='贵州茅台',
            search_topic='提价',
            days=7,
            db=db
        )
        print(f"缓存结果: {cached}")
        
        # 统计信息
        print("\n=== 缓存统计 ===")
        stats = cache.get_cache_stats(db)
        print(f"统计: {stats}")
        
    finally:
        db.close()
