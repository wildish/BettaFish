# BettaFish MVP实施计划 - 搜索引擎催化因子

## 文档说明

**文档版本**: v1.0  
**创建日期**: 2025-12-02  
**文档类型**: MVP实施计划  
**目标**: 实现"搜索引擎催化因子"作为平台首个因子

---

## 一、MVP核心定位

### 1.1 什么是"搜索引擎催化因子"？

```
定义：
基于用户指定的搜索主题，量化该主题对股票的催化强度

输入：
├─ 特定股票（如：600519 贵州茅台）
├─ 特定板块（如：白酒、消费）
└─ 用户自定义搜索内容（如："提价"、"销售数据"、"渠道变化"）

处理流程：
└─ QueryEngine定向搜索 → LLM催化分析 → 因子量化

输出：
└─ 催化因子值（-1到1，表示催化强度和方向）
    ├─ 1.0: 强烈利好催化
    ├─ 0.0: 无催化或中性
    └─ -1.0: 强烈利空催化
```

### 1.2 为什么选择这个因子作为MVP？

**业务价值明确**：
- ✅ 催化剂是量化交易的关键信号
- ✅ 可配置、可监控、可量化
- ✅ 用户可自定义关注主题

**技术实现可控**：
- ✅ 只用QueryEngine（已有）
- ✅ 单一因子类型，范围清晰
- ✅ 易于验证效果

**平台化能力体现**：
- ✅ 从单一因子到因子家族的路径清晰
- ✅ 验证因子平台架构的可行性

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│              搜索引擎催化因子系统（MVP）                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户输入                                                    │
│  ├─ 股票代码: 600519                                        │
│  ├─ 板块: 白酒                                              │
│  ├─ 搜索主题: ["提价", "销售数据"]                          │
│  └─ 天数: 7                                                 │
│                                                             │
│  ┌────────────────── 异步任务层 ──────────────────┐        │
│  │                                                  │        │
│  │  Flask API → Redis Queue → Celery Workers       │        │
│  │  (提交任务)   (任务队列)    (并发处理)          │        │
│  │                                                  │        │
│  └──────────────────────┬───────────────────────────┘        │
│                         ▼                                    │
│  ┌────────────────── 缓存层 ⭐ ─────────────────────┐       │
│  │                                                    │       │
│  │  检查缓存 → 命中？→ 是 → 直接返回                │       │
│  │      ↓                                             │       │
│  │     否                                             │       │
│  │      ↓                                             │       │
│  └──────┼──────────────────────────────────────────────┘       │
│         ▼                                                    │
│  ┌────────────────── Query预处理层 ⭐ ──────────────┐       │
│  │                                                    │       │
│  │  QueryOptimizer (LLM)                             │       │
│  │  - 输入: "贵州茅台" + "提价策略"                 │       │
│  │  - 优化: "贵州茅台 提价 价格调整 出厂价"         │       │
│  │  - 关键词提取 + 同义词扩展 + 行业术语            │       │
│  │                                                    │       │
│  └──────────────────────┬───────────────────────────┘       │
│         ▼                                                    │
│  ┌────────────────── 搜索层 ──────────────────────┐        │
│  │                                                  │        │
│  │  QueryEngine (Tavily API)                       │        │
│  │  - 搜索: 优化后的查询                           │        │
│  │  - 返回: 最近7天新闻                            │        │
│  │                                                  │        │
│  └──────────────────────┬───────────────────────────┘        │
│                         ▼                                    │
│  ┌────────────────── 分析层 ──────────────────────┐        │
│  │                                                  │        │
│  │  LLM催化分析引擎                                │        │
│  │  - 相关性评分                                   │        │
│  │  - 催化类型识别（利好/利空/中性）               │        │
│  │  - 催化强度评估（重大/一般/轻微）               │        │
│  │  - 催化事件提取                                 │        │
│  │                                                  │        │
│  └──────────────────────┬───────────────────────────┘        │
│                         ▼                                    │
│  ┌────────────────── 因子层 ⭐ ────────────────────┐        │
│  │                                                  │        │
│  │  SearchEngineCatalystFactor                     │        │
│  │  - calculate(analysis) → 催化因子值             │        │
│  │  - 范围: -1 到 1                                │        │
│  │                                                  │        │
│  └──────────────────────┬───────────────────────────┘        │
│                         ▼                                    │
│  ┌────────────────── 存储层 ──────────────────────┐        │
│  │                                                  │        │
│  │  PostgreSQL                                     │        │
│  │  ├─ cached_search_results (搜索缓存)           │        │
│  │  ├─ cached_analysis_results (分析缓存)         │        │
│  │  └─ message_factors (因子结果) ⭐              │        │
│  │                                                  │        │
│  └──────────────────────────────────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Query预处理架构 ⭐

```
Query优化流程：

输入：
├─ stock_name: "贵州茅台"
├─ search_topic: "提价策略"
└─ sector: "白酒" (可选)

LLM优化（QueryOptimizer）：
├─ 核心关键词提取
│   └─ "贵州茅台", "提价"
├─ 同义词扩展
│   └─ "价格调整", "涨价", "出厂价"
├─ 行业术语补充
│   └─ "飞天茅台", "高端白酒"
└─ 查询组合优化

输出：
├─ optimized_query: "贵州茅台 提价 价格调整 出厂价"
├─ keywords: ["贵州茅台", "提价", "价格调整", ...]
└─ reasoning: "优化思路说明"

优势：
✅ 提升搜索相关性
✅ 扩展搜索覆盖面
✅ 减少无效结果
✅ 适应不同表述方式
```

### 2.3 缓存架构 ⭐

```
三层缓存策略：

Layer 1: Redis热缓存（1小时）
├─ 搜索结果缓存
├─ 分析结果缓存
└─ 任务状态缓存

Layer 2: PostgreSQL温缓存（7天）
├─ cached_search_results
└─ cached_analysis_results

Layer 3: 外部API（缓存未命中时）
└─ Tavily API

优势：
✅ API调用节省 > 90%
✅ 响应时间提升 > 95%
✅ 成本降低显著
```

---

## 三、核心因子设计

### 3.1 SearchEngineCatalystFactor

```python
class SearchEngineCatalystFactor(BaseFactor):
    """
    搜索引擎催化因子
    
    计算逻辑：
    1. 相关性评分（0-1）
    2. 催化类型（positive/negative/neutral）
    3. 催化强度（major/normal/minor）
    4. 事件数量加成
    5. 综合计算
    """
    
    name = "search_engine_catalyst_factor"
    version = "1.0.0"
    category = "catalyst"
    output_range = (-1, 1)
    
    def calculate(self, analysis: Dict[str, Any]) -> float:
        llm = analysis.get('llm_analysis', {})
        
        # 1. 相关性评分
        relevance = llm.get('relevance_score', 0.0)
        
        # 2. 催化类型
        catalyst_type = llm.get('catalyst_type', 'neutral')
        type_score = {
            'positive': 1.0,
            'neutral': 0.0,
            'negative': -1.0
        }.get(catalyst_type, 0.0)
        
        # 3. 催化强度
        catalyst_strength = llm.get('catalyst_strength', 'normal')
        strength_multiplier = {
            'major': 1.0,
            'normal': 0.7,
            'minor': 0.4
        }.get(catalyst_strength, 0.7)
        
        # 4. 事件数量加成
        events = llm.get('catalyst_events', [])
        event_count_bonus = min(0.2, len(events) * 0.05)
        
        # 5. 综合计算
        base_score = type_score * strength_multiplier
        final_score = base_score * relevance + event_count_bonus * type_score
        
        return max(-1.0, min(1.0, final_score))
```

### 3.2 使用场景示例

#### 场景1：白酒板块提价监控

```python
输入：
{
    'stock_code': '600519',
    'stock_name': '贵州茅台',
    'sector': '白酒',
    'search_query': '提价',
    'days': 7
}

输出：
{
    'stock_code': '600519',
    'factor_name': 'search_engine_catalyst_factor',
    'factor_value': 0.85,  # 强烈利好
    'catalyst_type': 'positive',
    'catalyst_strength': 'major',
    'catalyst_events': [
        '茅台宣布提价18%',
        '经销商确认新价格体系',
        '分析师上调目标价'
    ],
    'news_count': 5,
    'update_time': '2025-12-02 11:00:00'
}
```

#### 场景2：新能源板块政策监控

```python
输入：
{
    'stock_code': '300750',
    'stock_name': '宁德时代',
    'sector': '新能源',
    'search_query': '补贴政策',
    'days': 7
}

输出：
{
    'factor_value': -0.3,  # 轻微利空
    'catalyst_type': 'negative',
    'catalyst_strength': 'minor',
    'catalyst_events': [
        '补贴退坡政策延续'
    ]
}
```

---

## 四、8周实施计划

### Week 1: 环境搭建 + 基础架构（5天）

**任务清单**：
- [ ] PostgreSQL数据库安装配置
- [ ] Redis安装配置
- [ ] 创建数据库表结构
  - [ ] cached_search_results
  - [ ] cached_analysis_results
  - [ ] message_factors
- [ ] 外部数据适配层（简化版）
  - [ ] 读取股票列表
  - [ ] 读取板块信息

**验收标准**：
- ✅ 数据库连接正常
- ✅ Redis连接正常
- ✅ 表结构创建完成

---

### Week 2: Query预处理 + QueryEngine集成（5天）

**任务清单**：
- [ ] 实现Query预处理模块 ⭐
  - [ ] 设计Query优化Prompt
  - [ ] 实现LLM查询优化
  - [ ] 添加查询验证逻辑
- [ ] 保留原有QueryEngine
- [ ] 实现定向搜索接口
  ```python
  def search_by_topic(stock_code, stock_name, query, days=7):
      """定向搜索指定主题的新闻"""
      pass
  ```
- [ ] 新闻结果存储
- [ ] 测试搜索功能

**代码框架**：

#### 2.1 Query预处理模块

```python
# engines/query_optimizer.py

from typing import Dict, Any
import json
from loguru import logger

class QueryOptimizer:
    """搜索查询优化器（基于LLM）"""
    
    def __init__(self, llm_client):
        """
        初始化查询优化器
        
        Args:
            llm_client: LLM客户端
        """
        self.llm_client = llm_client
    
    def optimize_query(self, stock_name: str, search_topic: str, 
                      sector: str = None) -> Dict[str, Any]:
        """
        优化搜索查询
        
        Args:
            stock_name: 股票名称（如"贵州茅台"）
            search_topic: 搜索主题（如"提价"）
            sector: 板块（如"白酒"，可选）
        
        Returns:
            {
                'optimized_query': '贵州茅台 提价',
                'keywords': ['贵州茅台', '提价', '价格调整'],
                'reasoning': '提取核心关键词，添加同义词'
            }
        """
        logger.info(f"优化查询 - 股票: {stock_name}, 主题: {search_topic}")
        
        # 构造Prompt
        prompt = self._build_optimization_prompt(
            stock_name, search_topic, sector
        )
        
        # 调用LLM
        try:
            response = self.llm_client.invoke(
                system_prompt=QUERY_OPTIMIZATION_PROMPT,
                user_message=prompt
            )
            
            # 解析响应
            result = self._parse_response(response)
            
            logger.info(f"优化后查询: {result['optimized_query']}")
            logger.info(f"关键词: {result['keywords']}")
            
            return result
            
        except Exception as e:
            logger.error(f"查询优化失败: {str(e)}")
            # 返回默认查询
            return self._get_fallback_query(stock_name, search_topic)
    
    def _build_optimization_prompt(self, stock_name: str, 
                                  search_topic: str, 
                                  sector: str = None) -> str:
        """
        构造优化Prompt
        
        Returns:
            JSON格式的输入数据
        """
        data = {
            'stock_name': stock_name,
            'search_topic': search_topic
        }
        
        if sector:
            data['sector'] = sector
        
        return json.dumps(data, ensure_ascii=False)
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
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
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # 解析JSON
            result = json.loads(cleaned)
            
            # 验证必需字段
            required_fields = ['optimized_query', 'keywords', 'reasoning']
            if not all(field in result for field in required_fields):
                raise ValueError("缺少必需字段")
            
            return result
            
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}")
            raise e
    
    def _get_fallback_query(self, stock_name: str, 
                           search_topic: str) -> Dict[str, Any]:
        """
        获取默认查询（当LLM失败时）
        
        Returns:
            默认的查询结果
        """
        optimized_query = f"{stock_name} {search_topic}"
        
        return {
            'optimized_query': optimized_query,
            'keywords': [stock_name, search_topic],
            'reasoning': '使用默认查询（LLM优化失败）'
        }


# Prompt定义
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
```

#### 2.2 QueryEngine包装器

```python
# engines/query_engine_wrapper.py

from QueryEngine.tools import TavilyNewsAgency
from .query_optimizer import QueryOptimizer
from loguru import logger

class QueryEngineWrapper:
    """QueryEngine包装器（集成Query优化）"""
    
    def __init__(self, llm_client, tavily_api_key: str):
        """
        初始化包装器
        
        Args:
            llm_client: LLM客户端
            tavily_api_key: Tavily API密钥
        """
        self.search_agency = TavilyNewsAgency(api_key=tavily_api_key)
        self.query_optimizer = QueryOptimizer(llm_client)
    
    def search_catalyst_news(self, stock_code: str, stock_name: str,
                            search_topic: str, sector: str = None,
                            days: int = 7) -> list:
        """
        搜索催化相关新闻（带Query优化）
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            search_topic: 搜索主题
            sector: 板块（可选）
            days: 搜索天数
        
        Returns:
            list: 新闻列表
            [
                {
                    'title': '...',
                    'content': '...',
                    'url': '...',
                    'source': 'tavily',
                    'publish_time': '...',
                    'score': 0.95
                }
            ]
        """
        logger.info(f"搜索催化新闻 - {stock_name}({stock_code}), 主题: {search_topic}")
        
        # Step 1: 优化查询
        optimization_result = self.query_optimizer.optimize_query(
            stock_name=stock_name,
            search_topic=search_topic,
            sector=sector
        )
        
        optimized_query = optimization_result['optimized_query']
        logger.info(f"原始主题: {search_topic}")
        logger.info(f"优化查询: {optimized_query}")
        
        # Step 2: 选择搜索工具
        if days == 1:
            response = self.search_agency.search_news_last_24_hours(optimized_query)
        elif days == 7:
            response = self.search_agency.search_news_last_week(optimized_query)
        else:
            response = self.search_agency.basic_search_news(
                optimized_query, 
                max_results=10
            )
        
        # Step 3: 格式化结果
        news_list = []
        for result in response.results:
            news_list.append({
                'title': result.title,
                'content': result.content,
                'url': result.url,
                'source': 'tavily',
                'publish_time': result.published_date,
                'score': result.score
            })
        
        logger.info(f"搜索完成，找到 {len(news_list)} 条新闻")
        
        return news_list
```

**验收标准**：
- ✅ Query优化功能正常
  - LLM能够生成优化后的查询
  - 关键词提取合理（3-8个）
  - 有Fallback机制（LLM失败时）
- ✅ 能够搜索指定主题的新闻
- ✅ 返回结果格式正确
- ✅ 搜索结果保存到数据库
- ✅ 测试案例通过
  - 输入："贵州茅台" + "提价策略"
  - 优化查询示例："贵州茅台 提价 价格调整"
  - 搜索结果数量 > 0

---

### Week 3: LLM催化分析引擎（7天）

**任务清单**：
- [ ] 催化事件识别Prompt设计 ⭐
- [ ] 相关性评分逻辑
- [ ] 催化类型判断（利好/利空/中性）
- [ ] 催化强度评估（重大/一般/轻微）
- [ ] 结构化输出解析
- [ ] 测试与优化

**Prompt设计**：
```python
CATALYST_ANALYSIS_PROMPT = """
你是一个专业的金融分析师，擅长识别和评估市场催化事件。

任务：分析以下新闻是否对指定股票构成催化，并评估催化强度。

股票信息：
- 股票代码：{stock_code}
- 股票名称：{stock_name}
- 所属板块：{sector}
- 关注主题：{search_query}

新闻内容：
{news_content}

请按照以下格式输出分析结果：

{{
    "relevance_score": 0.0-1.0,  // 新闻与股票的相关性评分
    "catalyst_type": "positive/negative/neutral",  // 催化类型
    "catalyst_strength": "major/normal/minor",  // 催化强度
    "catalyst_events": [  // 识别的催化事件列表
        "事件1描述",
        "事件2描述"
    ],
    "reasoning": "分析理由",  // 简要说明判断依据
    "confidence_score": 0.0-1.0  // 分析置信度
}}

评分标准：
- relevance_score: 新闻内容与股票/主题的相关程度
- catalyst_type: 
  * positive: 利好催化（如提价、业绩超预期、政策利好）
  * negative: 利空催化（如降价、业绩不及预期、政策利空）
  * neutral: 中性或无明显催化
- catalyst_strength:
  * major: 重大催化（可能引起股价显著波动）
  * normal: 一般催化（可能引起股价小幅波动）
  * minor: 轻微催化（影响有限）
"""
```

**验收标准**：
- ✅ LLM能够准确识别催化事件（准确率 > 80%）
- ✅ 催化类型判断合理
- ✅ 催化强度评估合理
- ✅ 输出格式稳定

---

### Week 4: 催化因子实现（5天）

**任务清单**：
- [ ] 实现BaseFactor基类
- [ ] 实现SearchEngineCatalystFactor
- [ ] 因子计算逻辑
- [ ] 单元测试
- [ ] 因子验证（人工对比）

**代码框架**：
```python
# factor_engine/base_factor.py
# (已在FINAL_PLAN.md中定义)

# factor_engine/factors/catalyst_factor.py
# (已在本文档3.1节中定义)
```

**验收标准**：
- ✅ 因子计算逻辑正确
- ✅ 因子值在合理范围内（-1到1）
- ✅ 与人工判断一致性 > 75%
- ✅ 单元测试覆盖率 > 90%

---

### Week 5: 异步架构 + 缓存机制（7天）

**任务清单**：
- [ ] Celery + Redis环境搭建
- [ ] 核心任务定义
  - [ ] `analyze_catalyst_async()`
  - [ ] `batch_analyze_catalysts()`
- [ ] 缓存机制实现 ⭐
  - [ ] CacheManager类
  - [ ] 搜索结果缓存
  - [ ] 分析结果缓存
- [ ] API接口实现
  - [ ] `POST /api/catalyst/analyze`
  - [ ] `GET /api/catalyst/status/<task_id>`
  - [ ] `GET /api/catalyst/result/<task_id>`
  - [ ] `POST /api/catalyst/batch`
- [ ] 进度跟踪机制

**缓存实现**：
```python
# cache/cache_manager.py
# (已在前面讨论中详细定义)
```

**验收标准**：
- ✅ 异步任务提交成功（API响应 < 100ms）
- ✅ 进度跟踪准确（0-100%）
- ✅ 缓存命中率 > 80%（重复查询）
- ✅ API调用节省 > 90%
- ✅ 支持并发处理（5+任务）

---

### Week 6: 因子平台基础（5天）

**任务清单**：
- [ ] FactorRegistry注册中心
- [ ] FactorEngine计算引擎
- [ ] 注册SearchEngineCatalystFactor
- [ ] 因子测试框架
- [ ] 性能优化

**代码框架**：
```python
# factor_engine/factor_registry.py
# factor_engine/factor_engine.py
# (已在FINAL_PLAN.md中定义)

# 注册因子
from factor_engine.factor_registry import get_registry
from factor_engine.factors.catalyst_factor import SearchEngineCatalystFactor

registry = get_registry()
registry.register(SearchEngineCatalystFactor)
```

**验收标准**：
- ✅ 因子注册机制正常
- ✅ 因子计算引擎性能达标（< 1ms/因子）
- ✅ 新增因子只需3步（定义、注册、生效）

---

### Week 7: 用户界面 + 完整流程（7天）

**任务清单**：
- [ ] Streamlit用户界面
  - [ ] 输入：股票代码、板块、搜索主题
  - [ ] 输出：催化因子、催化事件列表
  - [ ] 历史因子查询
- [ ] 批量监控功能
  - [ ] 监控多只股票的同一主题
  - [ ] 批量结果展示
- [ ] 完整流程集成测试
- [ ] 端到端测试

**界面设计**：
```python
# ui/catalyst_monitor.py

import streamlit as st

st.title("🔍 搜索引擎催化因子监控")

# 输入区
col1, col2 = st.columns(2)
with col1:
    stock_code = st.text_input("股票代码", "600519")
    stock_name = st.text_input("股票名称", "贵州茅台")
with col2:
    sector = st.text_input("所属板块", "白酒")
    days = st.slider("搜索天数", 1, 30, 7)

# 搜索主题
search_queries = st.text_area(
    "搜索主题（每行一个）",
    "提价\n销售数据\n渠道变化"
).split('\n')

if st.button("🚀 开始分析"):
    # 提交任务并显示结果
    pass
```

**验收标准**：
- ✅ 界面友好易用
- ✅ 完整流程能够正常运行
- ✅ 响应时间 < 30秒（单只股票）
- ✅ 结果展示清晰

---

### Week 8: 测试 + 文档 + 部署（5天）

**任务清单**：
- [ ] 性能测试
  - [ ] 单任务性能
  - [ ] 并发性能
  - [ ] 缓存性能
- [ ] 集成测试
  - [ ] 多只股票测试
  - [ ] 多主题测试
  - [ ] 异常情况测试
- [ ] 文档编写
  - [ ] 用户使用文档
  - [ ] API文档
  - [ ] 因子说明文档
- [ ] 部署准备
  - [ ] 配置文件模板
  - [ ] 启动脚本
  - [ ] 监控脚本

**验收标准**：
- ✅ 所有测试通过
- ✅ 文档完整
- ✅ 部署脚本可用

---

## 五、技术栈

### 5.1 核心组件

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | Flask | 2.0+ | Web服务 |
| 任务队列 | Celery | 5.3+ | 异步任务 |
| 消息队列 | Redis | 7.0+ | 任务队列+缓存 |
| 数据库 | PostgreSQL | 14+ | 数据存储 |
| LLM | DeepSeek | - | 催化分析 |
| 搜索API | Tavily | - | 新闻搜索 |
| UI框架 | Streamlit | 1.28+ | 用户界面 |

### 5.2 Python依赖

```txt
# requirements.txt

# 原有依赖
flask==2.3.0
streamlit==1.28.0
loguru==0.7.0
requests==2.31.0

# 新增依赖
celery==5.3.4
redis==5.0.1
psycopg2-binary==2.9.9
pandas==2.1.0
flower==2.0.1  # Celery监控
```

---

## 六、数据库设计（PostgreSQL）

### 6.1 搜索结果缓存表

```sql
-- 搜索结果缓存表
CREATE TABLE factor_cached_search_results (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    search_query TEXT NOT NULL,
    search_days INTEGER NOT NULL,
    news_results JSONB NOT NULL,
    news_count INTEGER NOT NULL,
    search_time TIMESTAMP NOT NULL,
    expire_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_factor_search_cache_key ON factor_cached_search_results(cache_key);
CREATE INDEX idx_factor_search_expire ON factor_cached_search_results(expire_time);
CREATE INDEX idx_factor_search_stock ON factor_cached_search_results(stock_code, search_query);

-- 注释
COMMENT ON TABLE factor_cached_search_results IS '因子搜索结果缓存表';
COMMENT ON COLUMN factor_cached_search_results.cache_key IS '缓存Key，格式：search:{stock_code}:{query_hash}:{days}:{date}';
COMMENT ON COLUMN factor_cached_search_results.news_results IS '新闻结果JSON数组';
COMMENT ON COLUMN factor_cached_search_results.expire_time IS '过期时间，默认7天';
```

### 6.2 分析结果缓存表

```sql
-- 分析结果缓存表
CREATE TABLE factor_cached_analysis_results (
    id SERIAL PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE NOT NULL,
    stock_code VARCHAR(20) NOT NULL,
    search_query TEXT NOT NULL,
    news_hash VARCHAR(64) NOT NULL,
    llm_analysis JSONB NOT NULL,
    analysis_time TIMESTAMP NOT NULL,
    expire_time TIMESTAMP NOT NULL,
    llm_model VARCHAR(50) DEFAULT 'deepseek',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_factor_analysis_cache_key ON factor_cached_analysis_results(cache_key);
CREATE INDEX idx_factor_analysis_news_hash ON factor_cached_analysis_results(news_hash);
CREATE INDEX idx_factor_analysis_expire ON factor_cached_analysis_results(expire_time);

-- 注释
COMMENT ON TABLE factor_cached_analysis_results IS '因子分析结果缓存表';
COMMENT ON COLUMN factor_cached_analysis_results.cache_key IS '缓存Key，格式：analysis:{stock_code}:{query_hash}:{news_hash}';
COMMENT ON COLUMN factor_cached_analysis_results.news_hash IS '新闻内容的MD5哈希，用于去重';
COMMENT ON COLUMN factor_cached_analysis_results.llm_analysis IS 'LLM分析结果JSON';
COMMENT ON COLUMN factor_cached_analysis_results.expire_time IS '过期时间，默认24小时';
```

### 6.3 因子元数据表（先定义）

```sql
-- 因子元数据表
CREATE TABLE factor_metadata (
    id SERIAL PRIMARY KEY,
    factor_name VARCHAR(100) UNIQUE NOT NULL,
    factor_version VARCHAR(20) NOT NULL,
    factor_category VARCHAR(50) NOT NULL,  -- catalyst/sentiment/event等
    output_range_min DECIMAL(10, 4),
    output_range_max DECIMAL(10, 4),
    description TEXT,
    calculation_logic TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引
CREATE INDEX idx_factor_metadata_name ON factor_metadata(factor_name);
CREATE INDEX idx_factor_metadata_category ON factor_metadata(factor_category);

-- 注释
COMMENT ON TABLE factor_metadata IS '因子元数据表，记录因子定义信息';
COMMENT ON COLUMN factor_metadata.factor_name IS '因子名称，如：search_engine_catalyst_factor';
COMMENT ON COLUMN factor_metadata.factor_category IS '因子类别';
COMMENT ON COLUMN factor_metadata.output_range_min IS '因子输出最小值';
COMMENT ON COLUMN factor_metadata.output_range_max IS '因子输出最大值';
COMMENT ON COLUMN factor_metadata.calculation_logic IS '因子计算逻辑说明';
COMMENT ON COLUMN factor_metadata.is_active IS '因子是否启用';

-- 初始化催化因子元数据
INSERT INTO factor_metadata 
(factor_name, factor_version, factor_category, output_range_min, output_range_max, description, calculation_logic)
VALUES 
('search_engine_catalyst_factor', '1.0.0', 'catalyst', -1.0, 1.0, 
 '搜索引擎催化因子：基于用户指定搜索主题量化催化强度',
 '相关性评分 × (催化类型分数 × 催化强度系数) + 事件数量加成');
```

### 6.4 因子结果表（通用设计）

```sql
-- 因子结果表（主表）- 通用设计
CREATE TABLE factor_results (
    id SERIAL PRIMARY KEY,
    
    -- 股票信息
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(100),
    sector VARCHAR(100),
    
    -- 因子信息（关联factor_metadata，但不设置外键）⭐
    factor_metadata_id INTEGER NOT NULL,
    factor_value DECIMAL(10, 4) NOT NULL,
    
    -- 因子扩展属性（JSONB存储，灵活扩展）⭐
    factor_attributes JSONB,
    
    -- 时间信息
    factor_date DATE NOT NULL,
    calculated_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- 唯一约束
    UNIQUE(stock_code, factor_metadata_id, factor_date)
);

-- 索引
CREATE INDEX idx_factor_results_stock_date ON factor_results(stock_code, factor_date);
CREATE INDEX idx_factor_results_metadata_date ON factor_results(factor_metadata_id, factor_date);
CREATE INDEX idx_factor_results_stock_metadata ON factor_results(stock_code, factor_metadata_id, factor_date);
-- JSONB字段索引（用于查询特定属性）
CREATE INDEX idx_factor_results_attributes ON factor_results USING GIN(factor_attributes);

-- 注释
COMMENT ON TABLE factor_results IS '因子结果表（通用设计，永久存储）';
COMMENT ON COLUMN factor_results.factor_metadata_id IS '关联factor_metadata.id（无外键约束）';
COMMENT ON COLUMN factor_results.factor_value IS '因子主值，范围根据因子类型定义';
COMMENT ON COLUMN factor_results.factor_attributes IS '因子扩展属性JSON，不同因子类型存储不同字段';
COMMENT ON COLUMN factor_results.factor_date IS '因子所属日期';

-- 示例数据结构：

-- 1. 催化因子的 factor_attributes
-- {
--   "catalyst_type": "positive",
--   "catalyst_strength": "major",
--   "catalyst_events": ["茅台宣布提价18%", "经销商确认新价格体系"],
--   "search_query": "提价",
--   "news_count": 5,
--   "relevance_score": 0.95
-- }

-- 2. 情感因子的 factor_attributes
-- {
--   "sentiment": "positive",
--   "sentiment_score": 0.8,
--   "confidence": 0.9,
--   "source": "news_analysis"
-- }

-- 3. 事件因子的 factor_attributes
-- {
--   "event_type": "earnings",
--   "event_impact": "major",
--   "event_description": "业绩超预期",
--   "event_date": "2025-12-01"
-- }
```

---

## 七、MVP验收标准

### 7.1 功能验收

- ✅ **搜索功能**: 能够根据用户指定主题搜索相关新闻
- ✅ **分析功能**: LLM能够准确识别催化事件（准确率 > 80%）
- ✅ **因子计算**: 催化因子计算合理（与人工判断一致性 > 75%）
- ✅ **批量处理**: 支持批量监控（10+股票 x 5+主题）
- ✅ **结果展示**: 用户界面友好，结果展示清晰

### 7.2 工程化验收

- ✅ **异步处理**: API响应 < 100ms
- ✅ **处理速度**: 单只股票分析 < 30秒
- ✅ **并发能力**: 支持5+任务并发
- ✅ **缓存效果**: 缓存命中率 > 80%
- ✅ **API节省**: API调用节省 > 90%

### 7.3 平台化验收

- ✅ **可配置**: 新增催化主题无需修改代码
- ✅ **可测试**: 因子计算逻辑可独立测试
- ✅ **可扩展**: 易于扩展到其他因子类型

---

## 八、后续扩展路径

### 8.1 扩展1: 多引擎催化因子（+2周）

```
增强搜索能力：
├─ 加入MediaEngine（视频、社交媒体）
├─ 加入InsightEngine（历史对比）
└─ 多源催化信号融合
```

### 8.2 扩展2: 催化因子家族（+4周）

```
新增因子类型：
├─ 政策催化因子
├─ 业绩催化因子
├─ 行业催化因子
└─ 技术催化因子
```

### 8.3 扩展3: 催化预测模型（+6周）

```
预测能力：
├─ 催化强度预测
├─ 催化持续时间预测
└─ 催化传导路径分析
```

---

## 九、风险与应对

### 9.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| LLM催化识别准确率不足 | 高 | 中 | 优化Prompt，增加示例，人工校验 |
| Tavily API不稳定 | 中 | 低 | 添加重试机制，缓存数据 |
| 缓存策略不合理 | 中 | 低 | 监控缓存命中率，动态调整 |

### 9.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| 催化主题定义不清晰 | 中 | 中 | 提供典型场景示例，用户培训 |
| 因子有效性待验证 | 高 | 中 | 回测验证，持续优化 |

---

## 十、总结

### 10.1 MVP核心价值

```
1. 业务价值
   ✅ 自动化监控催化事件
   ✅ 量化催化强度
   ✅ 可配置、可扩展

2. 技术价值
   ✅ 验证因子平台架构
   ✅ 验证异步处理能力
   ✅ 验证缓存策略

3. 平台价值
   ✅ 首个因子成功落地
   ✅ 为后续因子开发铺路
   ✅ 积累催化事件库
```

### 10.2 成功标准

**MVP成功 = 功能验收 + 工程化验收 + 平台化验收**

- ✅ 能够准确识别和量化催化事件
- ✅ 支持高并发、低延迟处理
- ✅ 易于扩展新因子

---

**文档版本**: v1.0  
**最后更新**: 2025-12-02  
**状态**: 待开始实施
