"""
因子模型定义

包含因子基类和具体因子实现
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from loguru import logger


class BaseFactor(ABC):
    """
    因子基类
    
    所有因子必须继承此类并实现 calculate 方法
    """
    
    # 因子元数据（子类必须定义）
    name: str = "base_factor"
    version: str = "1.0.0"
    category: str = "unknown"
    output_range: Tuple[float, float] = (-1.0, 1.0)
    description: str = "因子基类"
    
    @abstractmethod
    def calculate(self, analysis: Dict[str, Any]) -> float:
        """
        计算因子值
        
        Args:
            analysis: 分析结果字典
        
        Returns:
            float: 因子值
        """
        pass
    
    def validate(self, value: float) -> float:
        """
        验证并修正因子值到有效范围
        
        Args:
            value: 原始因子值
        
        Returns:
            float: 修正后的因子值
        """
        min_val, max_val = self.output_range
        
        if value < min_val:
            logger.warning(f"因子值 {value} 小于最小值 {min_val}，修正为 {min_val}")
            return min_val
        elif value > max_val:
            logger.warning(f"因子值 {value} 大于最大值 {max_val}，修正为 {max_val}")
            return max_val
        else:
            return value
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        获取因子元数据
        
        Returns:
            Dict: 因子元数据
        """
        return {
            'name': self.name,
            'version': self.version,
            'category': self.category,
            'output_range': self.output_range,
            'description': self.description
        }


class SearchEngineCatalystFactor(BaseFactor):
    """
    搜索引擎催化因子
    
    基于搜索引擎新闻分析，量化特定主题对股票的催化强度
    """
    
    name = "search_engine_catalyst_factor"
    version = "1.0.0"
    category = "catalyst"
    output_range = (-1.0, 1.0)
    description = "基于搜索引擎新闻的催化因子，量化特定主题对股票的催化强度"
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化因子
        
        Args:
            config: 因子配置
        """
        self.config = config or {}
        
        # 从配置读取权重参数
        self.catalyst_weights = self.config.get('catalyst_weights', {
            'major': 1.0,
            'normal': 0.7,
            'minor': 0.4
        })
        
        self.event_bonus = self.config.get('event_bonus', {
            'rate': 0.05,
            'max': 0.2
        })
        
        logger.debug(f"SearchEngineCatalystFactor 初始化完成 - 权重: {self.catalyst_weights}")
    
    def calculate(self, analysis: Dict[str, Any]) -> float:
        """
        计算催化因子值
        
        计算逻辑：
        1. 相关性评分（0-1）
        2. 催化类型（positive/negative/neutral）
        3. 催化强度（major/normal/minor）
        4. 事件数量加成
        5. 综合计算
        
        Args:
            analysis: 催化分析结果
            {
                'relevance_score': float,
                'catalyst_type': str,
                'catalyst_strength': str,
                'catalyst_events': List[str],
                'news_count': int
            }
        
        Returns:
            float: 因子值（-1到1）
        """
        # 1. 相关性评分
        relevance = analysis.get('relevance_score', 0.0)
        
        # 2. 催化类型
        catalyst_type = analysis.get('catalyst_type', 'neutral')
        type_score = {
            'positive': 1.0,
            'neutral': 0.0,
            'negative': -1.0
        }.get(catalyst_type, 0.0)
        
        # 3. 催化强度
        catalyst_strength = analysis.get('catalyst_strength', 'normal')
        strength_multiplier = self.catalyst_weights.get(catalyst_strength, 0.7)
        
        # 4. 事件数量加成
        events = analysis.get('catalyst_events', [])
        event_count = len(events)
        event_bonus = min(
            event_count * self.event_bonus['rate'],
            self.event_bonus['max']
        )
        
        # 5. 综合计算
        # 基础分数 = 相关性 * 类型 * 强度
        base_score = relevance * type_score * strength_multiplier
        
        # 最终分数 = 基础分数 * (1 + 事件加成)
        final_score = base_score * (1 + event_bonus)
        
        # 验证并修正到有效范围
        final_score = self.validate(final_score)
        
        logger.debug(
            f"因子计算 - 相关性:{relevance:.2f}, 类型:{catalyst_type}, "
            f"强度:{catalyst_strength}, 事件数:{event_count}, 最终值:{final_score:.3f}"
        )
        
        return final_score


# 因子注册表
FACTOR_REGISTRY = {
    'search_engine_catalyst_factor': SearchEngineCatalystFactor
}


def get_factor(factor_name: str, config: Dict[str, Any] = None) -> BaseFactor:
    """
    获取因子实例
    
    Args:
        factor_name: 因子名称
        config: 因子配置
    
    Returns:
        BaseFactor: 因子实例
    """
    if factor_name not in FACTOR_REGISTRY:
        raise ValueError(f"未知的因子: {factor_name}")
    
    factor_class = FACTOR_REGISTRY[factor_name]
    return factor_class(config=config)


if __name__ == "__main__":
    # 测试因子计算
    factor = SearchEngineCatalystFactor()
    
    # 测试案例1：强烈利好
    analysis1 = {
        'relevance_score': 0.9,
        'catalyst_type': 'positive',
        'catalyst_strength': 'major',
        'catalyst_events': ['提价18%', '经销商确认', '分析师上调目标价'],
        'news_count': 5
    }
    
    value1 = factor.calculate(analysis1)
    print(f"\n测试案例1（强烈利好）: {value1:.3f}")
    
    # 测试案例2：轻微利空
    analysis2 = {
        'relevance_score': 0.6,
        'catalyst_type': 'negative',
        'catalyst_strength': 'minor',
        'catalyst_events': ['补贴退坡'],
        'news_count': 2
    }
    
    value2 = factor.calculate(analysis2)
    print(f"测试案例2（轻微利空）: {value2:.3f}")
    
    # 测试案例3：中性
    analysis3 = {
        'relevance_score': 0.3,
        'catalyst_type': 'neutral',
        'catalyst_strength': 'normal',
        'catalyst_events': [],
        'news_count': 1
    }
    
    value3 = factor.calculate(analysis3)
    print(f"测试案例3（中性）: {value3:.3f}")
