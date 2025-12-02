"""
Taurus 数据库模型定义

使用 SQLAlchemy ORM 定义数据表结构
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Index,
    create_engine, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class FactorMetadata(Base):
    """
    因子元数据表
    存储因子的基本信息和配置
    """
    __tablename__ = 'factor_metadata'
    __table_args__ = (
        {'comment': '因子元数据表，存储因子定义和配置信息'},
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    factor_name = Column(String(100), nullable=False, unique=True, comment='因子名称')
    factor_category = Column(String(50), nullable=False, comment='因子类别')
    factor_version = Column(String(20), nullable=False, comment='因子版本')
    description = Column(Text, comment='因子描述')
    output_range_min = Column(Float, comment='输出范围最小值')
    output_range_max = Column(Float, comment='输出范围最大值')
    config = Column(JSON, comment='因子配置（JSON格式）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f"<FactorMetadata(id={self.id}, name='{self.factor_name}', version='{self.factor_version}')>"


class FactorResult(Base):
    """
    因子结果表
    存储因子计算结果，使用 JSONB 存储因子特定属性
    """
    __tablename__ = 'factor_results'
    __table_args__ = (
        Index('idx_factor_stock_date', 'stock_code', 'factor_metadata_id', 'factor_date', unique=True),
        Index('idx_factor_date', 'factor_date'),
        Index('idx_stock_code', 'stock_code'),
        Index('idx_factor_metadata', 'factor_metadata_id'),
        Index('idx_factor_attributes', 'factor_attributes', postgresql_using='gin'),
        {'comment': '因子结果表，存储所有类型因子的计算结果'},
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    stock_name = Column(String(100), comment='股票名称')
    factor_metadata_id = Column(Integer, nullable=False, comment='因子元数据ID（关联factor_metadata.id，无外键约束）')
    factor_date = Column(DateTime, nullable=False, comment='因子日期')
    factor_value = Column(Float, nullable=False, comment='因子值')
    factor_attributes = Column(JSON, comment='因子特定属性（JSON格式，不同因子存储不同字段）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f"<FactorResult(id={self.id}, stock='{self.stock_code}', value={self.factor_value})>"


class FactorCachedSearchResult(Base):
    """
    因子搜索结果缓存表
    缓存搜索引擎的搜索结果
    """
    __tablename__ = 'factor_cached_search_results'
    __table_args__ = (
        Index('idx_search_cache_key', 'cache_key', unique=True),
        Index('idx_search_created_at', 'created_at'),
        {'comment': '因子搜索结果缓存表，缓存Tavily等搜索引擎的结果'},
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cache_key = Column(String(255), nullable=False, unique=True, comment='缓存键（由查询参数生成）')
    search_query = Column(String(500), nullable=False, comment='搜索查询')
    search_results = Column(JSON, nullable=False, comment='搜索结果（JSON格式）')
    result_count = Column(Integer, comment='结果数量')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f"<FactorCachedSearchResult(id={self.id}, key='{self.cache_key}', count={self.result_count})>"


class FactorCachedAnalysisResult(Base):
    """
    因子分析结果缓存表
    缓存LLM分析结果
    """
    __tablename__ = 'factor_cached_analysis_results'
    __table_args__ = (
        Index('idx_analysis_cache_key', 'cache_key', unique=True),
        Index('idx_analysis_created_at', 'created_at'),
        {'comment': '因子分析结果缓存表，缓存LLM催化分析结果'},
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    cache_key = Column(String(255), nullable=False, unique=True, comment='缓存键（由分析参数生成）')
    stock_code = Column(String(20), nullable=False, comment='股票代码')
    search_query = Column(String(500), comment='搜索查询')
    analysis_result = Column(JSON, nullable=False, comment='分析结果（JSON格式）')
    created_at = Column(DateTime, default=datetime.utcnow, comment='创建时间')
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment='更新时间')
    
    def __repr__(self):
        return f"<FactorCachedAnalysisResult(id={self.id}, stock='{self.stock_code}', key='{self.cache_key}')>"


# 数据库会话工厂
SessionLocal = None
engine = None


def init_database(database_url: str):
    """
    初始化数据库连接
    
    Args:
        database_url: 数据库连接URL
    """
    global engine, SessionLocal
    
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return engine


def create_tables(engine):
    """
    创建所有表
    
    Args:
        engine: SQLAlchemy引擎
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话
    """
    if SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_database()")
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
