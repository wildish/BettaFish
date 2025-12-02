"""
数据库初始化脚本

创建表结构并初始化因子元数据
"""

from loguru import logger
from .models import (
    Base, FactorMetadata, FactorResult,
    FactorCachedSearchResult, FactorCachedAnalysisResult,
    init_database, create_tables, get_db
)
from ..utils.config import get_database_url


def initialize_database():
    """
    初始化数据库
    1. 创建所有表
    2. 初始化因子元数据
    """
    try:
        # 获取数据库URL
        database_url = get_database_url()
        logger.info(f"连接数据库: {database_url.split('@')[1] if '@' in database_url else database_url}")
        
        # 初始化数据库连接
        engine = init_database(database_url)
        
        # 创建所有表
        logger.info("创建数据表...")
        create_tables(engine)
        logger.success("数据表创建成功")
        
        # 初始化因子元数据
        logger.info("初始化因子元数据...")
        _initialize_factor_metadata()
        logger.success("因子元数据初始化成功")
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise e


def _initialize_factor_metadata():
    """
    初始化因子元数据
    插入搜索引擎催化因子的元数据
    """
    from datetime import datetime
    
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查是否已存在
        existing = db.query(FactorMetadata).filter_by(
            factor_name='search_engine_catalyst_factor'
        ).first()
        
        if existing:
            logger.info("搜索引擎催化因子元数据已存在，跳过初始化")
            return
        
        # 创建搜索引擎催化因子元数据
        catalyst_factor = FactorMetadata(
            factor_name='search_engine_catalyst_factor',
            factor_category='catalyst',
            factor_version='1.0.0',
            description='基于搜索引擎新闻的催化因子，量化特定主题对股票的催化强度',
            output_range_min=-1.0,
            output_range_max=1.0,
            config={
                'default_days': 7,
                'min_news_count': 1,
                'relevance_threshold': 0.5,
                'catalyst_weights': {
                    'major': 1.0,
                    'normal': 0.7,
                    'minor': 0.4
                },
                'event_bonus': {
                    'rate': 0.05,
                    'max': 0.2
                }
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(catalyst_factor)
        db.commit()
        
        logger.success(f"搜索引擎催化因子元数据已创建，ID: {catalyst_factor.id}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"初始化因子元数据失败: {str(e)}")
        raise e
    finally:
        db.close()


def drop_all_tables():
    """
    删除所有表（谨慎使用！）
    """
    database_url = get_database_url()
    engine = init_database(database_url)
    
    logger.warning("正在删除所有表...")
    Base.metadata.drop_all(bind=engine)
    logger.warning("所有表已删除")


if __name__ == "__main__":
    # 直接运行此脚本进行数据库初始化
    logger.info("=" * 50)
    logger.info("开始初始化 Taurus MVP 数据库")
    logger.info("=" * 50)
    
    initialize_database()
    
    logger.info("=" * 50)
    logger.info("数据库初始化完成")
    logger.info("=" * 50)
