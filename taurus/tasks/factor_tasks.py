"""
因子计算异步任务

使用 Celery 实现异步因子计算
"""

from typing import Dict, Any, List
from datetime import datetime
from loguru import logger
from celery import group

from .celery_app import app
from ..engines import QueryOptimizer, QueryEngineWrapper, CatalystAnalyzer
from ..models import get_factor
from ..cache import RedisCache, PostgresCache
from ..database import get_db, FactorMetadata, FactorResult
from ..utils.config import settings


@app.task(bind=True, name='taurus.tasks.factor_tasks.calculate_factor_task')
def calculate_factor_task(self,
                          stock_code: str,
                          stock_name: str,
                          search_topic: str,
                          sector: str = None,
                          days: int = 7,
                          use_cache: bool = True) -> Dict[str, Any]:
    """
    计算单个因子（异步任务）
    
    Args:
        self: Celery task 实例
        stock_code: 股票代码
        stock_name: 股票名称
        search_topic: 搜索主题
        sector: 板块
        days: 搜索天数
        use_cache: 是否使用缓存
    
    Returns:
        Dict: 计算结果
    """
    task_id = self.request.id
    logger.info(f"[Task {task_id}] 开始计算因子 - {stock_name}({stock_code}), 主题: {search_topic}")
    
    try:
        # 更新任务状态
        self.update_state(state='PROGRESS', meta={'progress': 10, 'status': '初始化组件'})
        
        # 1. 初始化组件
        redis_cache = RedisCache(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            search_ttl=settings.REDIS_CACHE_TTL_SEARCH,
            analysis_ttl=settings.REDIS_CACHE_TTL_ANALYSIS,
            search_prefix=settings.CACHE_KEY_PREFIX_SEARCH,
            analysis_prefix=settings.CACHE_KEY_PREFIX_ANALYSIS
        )
        
        postgres_cache = PostgresCache(
            search_ttl=settings.POSTGRES_CACHE_TTL_SEARCH,
            analysis_ttl=settings.POSTGRES_CACHE_TTL_ANALYSIS
        )
        
        query_optimizer = QueryOptimizer(
            api_key=settings.QUERY_ENGINE_API_KEY,
            base_url=settings.QUERY_ENGINE_BASE_URL,
            model_name=settings.QUERY_ENGINE_MODEL_NAME
        )
        
        query_wrapper = QueryEngineWrapper(
            tavily_api_key=settings.TAVILY_API_KEY,
            optimizer=query_optimizer
        )
        
        catalyst_analyzer = CatalystAnalyzer(
            api_key=settings.INSIGHT_ENGINE_API_KEY,
            base_url=settings.INSIGHT_ENGINE_BASE_URL,
            model_name=settings.INSIGHT_ENGINE_MODEL_NAME
        )
        
        # 2. 搜索新闻（带缓存）
        self.update_state(state='PROGRESS', meta={'progress': 20, 'status': '搜索新闻'})
        
        news_list = None
        
        # 尝试从 Redis 获取
        if use_cache:
            news_list = redis_cache.get_search_cache(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                days=days
            )
        
        # 尝试从 PostgreSQL 获取
        if news_list is None and use_cache:
            db = next(get_db())
            try:
                news_list = postgres_cache.get_search_cache(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    search_topic=search_topic,
                    days=days,
                    db=db
                )
            finally:
                db.close()
        
        # 如果缓存未命中，执行搜索
        if news_list is None:
            logger.info(f"[Task {task_id}] 缓存未命中，执行搜索")
            news_list = query_wrapper.search_catalyst_news(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                sector=sector,
                days=days,
                use_optimizer=True
            )
            
            # 保存到缓存
            if use_cache and news_list:
                redis_cache.set_search_cache(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    search_topic=search_topic,
                    days=days,
                    search_results=news_list
                )
                
                db = next(get_db())
                try:
                    postgres_cache.set_search_cache(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        search_topic=search_topic,
                        days=days,
                        search_results=news_list,
                        db=db
                    )
                finally:
                    db.close()
        
        logger.info(f"[Task {task_id}] 找到 {len(news_list)} 条新闻")
        
        # 3. 分析催化（带缓存）
        self.update_state(state='PROGRESS', meta={'progress': 50, 'status': '分析催化'})
        
        analysis_result = None
        news_count = len(news_list)
        
        # 尝试从 Redis 获取
        if use_cache:
            analysis_result = redis_cache.get_analysis_cache(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                news_count=news_count
            )
        
        # 尝试从 PostgreSQL 获取
        if analysis_result is None and use_cache:
            db = next(get_db())
            try:
                analysis_result = postgres_cache.get_analysis_cache(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    search_topic=search_topic,
                    news_count=news_count,
                    db=db
                )
            finally:
                db.close()
        
        # 如果缓存未命中，执行分析
        if analysis_result is None:
            logger.info(f"[Task {task_id}] 分析缓存未命中，执行分析")
            analysis_result = catalyst_analyzer.analyze_catalyst(
                stock_code=stock_code,
                stock_name=stock_name,
                search_topic=search_topic,
                news_list=news_list,
                sector=sector
            )
            
            # 保存到缓存
            if use_cache and analysis_result:
                redis_cache.set_analysis_cache(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    search_topic=search_topic,
                    news_count=news_count,
                    analysis_result=analysis_result
                )
                
                db = next(get_db())
                try:
                    postgres_cache.set_analysis_cache(
                        stock_code=stock_code,
                        stock_name=stock_name,
                        search_topic=search_topic,
                        news_count=news_count,
                        analysis_result=analysis_result,
                        db=db
                    )
                finally:
                    db.close()
        
        # 4. 计算因子值
        self.update_state(state='PROGRESS', meta={'progress': 70, 'status': '计算因子'})
        
        factor = get_factor('search_engine_catalyst_factor', config={
            'catalyst_weights': {
                'major': settings.CATALYST_WEIGHT_MAJOR,
                'normal': settings.CATALYST_WEIGHT_NORMAL,
                'minor': settings.CATALYST_WEIGHT_MINOR
            },
            'event_bonus': {
                'rate': settings.CATALYST_EVENT_BONUS_RATE,
                'max': settings.CATALYST_EVENT_BONUS_MAX
            }
        })
        
        # 添加新闻数量到分析结果
        analysis_with_count = {**analysis_result, 'news_count': news_count}
        factor_value = factor.calculate(analysis_with_count)
        
        logger.info(f"[Task {task_id}] 因子值: {factor_value:.3f}")
        
        # 5. 保存到数据库
        self.update_state(state='PROGRESS', meta={'progress': 90, 'status': '保存结果'})
        
        db = next(get_db())
        try:
            # 获取因子元数据
            factor_metadata = db.query(FactorMetadata).filter_by(
                factor_name='search_engine_catalyst_factor'
            ).first()
            
            if not factor_metadata:
                raise ValueError("因子元数据不存在，请先初始化数据库")
            
            # 检查是否已存在
            factor_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            existing = db.query(FactorResult).filter_by(
                stock_code=stock_code,
                factor_metadata_id=factor_metadata.id,
                factor_date=factor_date
            ).first()
            
            # 构造因子特定属性
            factor_attributes = {
                'search_topic': search_topic,
                'sector': sector,
                'days': days,
                'news_count': news_count,
                'relevance_score': analysis_result.get('relevance_score', 0.0),
                'catalyst_type': analysis_result.get('catalyst_type', 'neutral'),
                'catalyst_strength': analysis_result.get('catalyst_strength', 'normal'),
                'catalyst_events': analysis_result.get('catalyst_events', []),
                'reasoning': analysis_result.get('reasoning', ''),
                'news_summary': analysis_result.get('news_summary', '')
            }
            
            if existing:
                # 更新现有结果
                existing.factor_value = factor_value
                existing.factor_attributes = factor_attributes
                existing.updated_at = datetime.utcnow()
                logger.info(f"[Task {task_id}] 更新因子结果 - ID: {existing.id}")
            else:
                # 创建新结果
                new_result = FactorResult(
                    stock_code=stock_code,
                    stock_name=stock_name,
                    factor_metadata_id=factor_metadata.id,
                    factor_date=factor_date,
                    factor_value=factor_value,
                    factor_attributes=factor_attributes,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                db.add(new_result)
                logger.info(f"[Task {task_id}] 创建因子结果")
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"[Task {task_id}] 保存结果失败: {str(e)}")
            raise e
        finally:
            db.close()
        
        # 6. 返回结果
        result = {
            'task_id': task_id,
            'stock_code': stock_code,
            'stock_name': stock_name,
            'search_topic': search_topic,
            'factor_value': factor_value,
            'news_count': news_count,
            'analysis': analysis_result,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Task {task_id}] 因子计算完成")
        redis_cache.close()
        
        return result
        
    except Exception as e:
        logger.error(f"[Task {task_id}] 因子计算失败: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e


@app.task(bind=True, name='taurus.tasks.factor_tasks.batch_calculate_factors_task')
def batch_calculate_factors_task(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    批量计算因子（异步任务）
    
    Args:
        self: Celery task 实例
        requests: 因子请求列表
            [
                {
                    'stock_code': str,
                    'stock_name': str,
                    'search_topic': str,
                    'sector': str (optional),
                    'days': int (optional)
                },
                ...
            ]
    
    Returns:
        Dict: 批量计算结果
    """
    task_id = self.request.id
    total = len(requests)
    logger.info(f"[Batch Task {task_id}] 开始批量计算 - 共 {total} 个任务")
    
    try:
        # 创建任务组
        job = group(
            calculate_factor_task.s(
                stock_code=req['stock_code'],
                stock_name=req['stock_name'],
                search_topic=req['search_topic'],
                sector=req.get('sector'),
                days=req.get('days', 7),
                use_cache=True
            )
            for req in requests
        )
        
        # 执行任务组
        result = job.apply_async()
        
        # 等待所有任务完成
        results = result.get(timeout=3600)  # 最多等待1小时
        
        # 统计结果
        success_count = sum(1 for r in results if r is not None)
        
        batch_result = {
            'batch_task_id': task_id,
            'total': total,
            'success': success_count,
            'failed': total - success_count,
            'results': results,
            'completed_at': datetime.utcnow().isoformat()
        }
        
        logger.info(f"[Batch Task {task_id}] 批量计算完成 - 成功: {success_count}/{total}")
        
        return batch_result
        
    except Exception as e:
        logger.error(f"[Batch Task {task_id}] 批量计算失败: {str(e)}")
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise e


if __name__ == "__main__":
    # 测试任务
    result = calculate_factor_task.delay(
        stock_code='600519',
        stock_name='贵州茅台',
        search_topic='提价',
        sector='白酒',
        days=7
    )
    
    print(f"任务ID: {result.id}")
    print(f"任务状态: {result.status}")
    
    # 等待结果
    try:
        task_result = result.get(timeout=300)
        print(f"任务结果: {task_result}")
    except Exception as e:
        print(f"任务失败: {str(e)}")
