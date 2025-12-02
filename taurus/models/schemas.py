"""
数据结构定义

使用 Pydantic 定义数据模型，用于数据验证和序列化
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class FactorRequest(BaseModel):
    """因子计算请求"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    search_topic: str = Field(..., description="搜索主题")
    sector: Optional[str] = Field(None, description="板块")
    days: int = Field(7, description="搜索天数", ge=1, le=30)
    
    @validator('stock_code')
    def validate_stock_code(cls, v):
        if not v or len(v) < 6:
            raise ValueError('股票代码格式无效')
        return v


class NewsItem(BaseModel):
    """新闻条目"""
    title: str = Field(..., description="新闻标题")
    content: str = Field(..., description="新闻内容")
    url: str = Field(..., description="新闻URL")
    source: str = Field("tavily", description="新闻来源")
    published_date: Optional[str] = Field(None, description="发布日期")
    score: float = Field(0.0, description="相关性评分")


class CatalystAnalysis(BaseModel):
    """催化分析结果"""
    relevance_score: float = Field(..., description="相关性评分", ge=0.0, le=1.0)
    catalyst_type: str = Field(..., description="催化类型")
    catalyst_strength: str = Field(..., description="催化强度")
    catalyst_events: List[str] = Field(default_factory=list, description="催化事件列表")
    reasoning: str = Field("", description="分析推理")
    news_summary: str = Field("", description="新闻摘要")
    
    @validator('catalyst_type')
    def validate_catalyst_type(cls, v):
        if v not in ['positive', 'negative', 'neutral']:
            raise ValueError('催化类型必须是 positive, negative 或 neutral')
        return v
    
    @validator('catalyst_strength')
    def validate_catalyst_strength(cls, v):
        if v not in ['major', 'normal', 'minor']:
            raise ValueError('催化强度必须是 major, normal 或 minor')
        return v


class FactorResult(BaseModel):
    """因子计算结果"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    factor_name: str = Field(..., description="因子名称")
    factor_value: float = Field(..., description="因子值")
    factor_date: datetime = Field(..., description="因子日期")
    factor_attributes: Dict[str, Any] = Field(default_factory=dict, description="因子特定属性")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")


class TaskStatus(BaseModel):
    """任务状态"""
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    progress: int = Field(0, description="进度百分比", ge=0, le=100)
    result: Optional[Dict[str, Any]] = Field(None, description="任务结果")
    error: Optional[str] = Field(None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class BatchFactorRequest(BaseModel):
    """批量因子计算请求"""
    requests: List[FactorRequest] = Field(..., description="因子请求列表")
    
    @validator('requests')
    def validate_requests(cls, v):
        if not v or len(v) == 0:
            raise ValueError('请求列表不能为空')
        if len(v) > 100:
            raise ValueError('单次批量请求不能超过100个')
        return v


class FactorMetadataInfo(BaseModel):
    """因子元数据信息"""
    id: int = Field(..., description="因子ID")
    factor_name: str = Field(..., description="因子名称")
    factor_category: str = Field(..., description="因子类别")
    factor_version: str = Field(..., description="因子版本")
    description: Optional[str] = Field(None, description="因子描述")
    output_range_min: Optional[float] = Field(None, description="输出范围最小值")
    output_range_max: Optional[float] = Field(None, description="输出范围最大值")
    config: Optional[Dict[str, Any]] = Field(None, description="因子配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True


class FactorResultInfo(BaseModel):
    """因子结果信息"""
    id: int = Field(..., description="结果ID")
    stock_code: str = Field(..., description="股票代码")
    stock_name: Optional[str] = Field(None, description="股票名称")
    factor_metadata_id: int = Field(..., description="因子元数据ID")
    factor_date: datetime = Field(..., description="因子日期")
    factor_value: float = Field(..., description="因子值")
    factor_attributes: Optional[Dict[str, Any]] = Field(None, description="因子特定属性")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    
    class Config:
        from_attributes = True
