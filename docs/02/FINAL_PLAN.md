# BettaFish 金融消息因子分析系统 - 最终实施方案

## 文档说明

**文档版本**: v4.0 Final  
**创建日期**: 2025-12-02  
**最后更新**: 2025-12-02  
**文档类型**: 设计 + 实施计划（一体化）  
**目标读者**: 开发工程师  
**实施策略**: 渐进式开发，MVP 优先（1-2个月上线）

**核心特性**:  
✅ 因子开发平台化（可扩展）  
✅ 异步任务处理（高并发）  
✅ 标准化因子接口（易维护）

---

## 一、系统核心定位 ⭐

### 1.1 系统定位

```
BettaFish = 金融消息因子开发平台 ⭐

核心能力：
├─ 多源消息获取（新闻、公告、舆情）
├─ 智能消息分析（LLM + Agent 协作）
├─ 标准化因子输出（量化信号）
└─ 因子快速开发（平台化能力）

输出产物：
└─ 消息因子（可直接用于量化策略）

平台特性：
├─ 因子标准化接口（BaseFactor）
├─ 因子注册机制（FactorRegistry）
├─ 因子计算引擎（FactorEngine）
└─ 异步任务处理（Celery + Redis）
```

**与现有系统的关系**：
- **读取**：股票基本信息、题材列表、股票-题材关联（只读，不写入）
- **输出**：消息因子数据（通过中间层，供量化系统使用）
- **独立**：行情分析、技术指标由现有量化系统负责

---

### 1.2 系统边界

```
BettaFish 负责：
✅ 消息获取（QueryEngine、MediaEngine、InsightEngine）
✅ 消息分析（ForumEngine、LLM 深度分析）
✅ 因子量化（MessageFactorGenerator）
✅ 因子存储（本地数据库）

现有量化系统负责：
✅ 行情数据管理
✅ 技术指标计算
✅ 因子分析与回测
✅ 策略生成与执行

不做：
❌ 不重复计算技术指标
❌ 不管理行情数据
❌ 不做策略回测
```

---

## 二、整体架构设计

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│              BettaFish 消息因子分析系统                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────── 消息获取层 ─────────────────────┐     │
│  │                                                    │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  │ QueryEngine  │  │ MediaEngine  │  │InsightEngine │  │
│  │  │ (Streamlit)  │  │ (Streamlit)  │  │ (Streamlit)  │  │
│  │  │              │  │              │  │              │  │
│  │  │ 新闻搜索     │  │ 多模态搜索   │  │ 私有数据库   │  │
│  │  │ Tavily API   │  │ Bocha API    │  │ MySQL        │  │
│  │  │ 8503端口     │  │ 8502端口     │  │ 8501端口     │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│  │         │                 │                 │          │
│  └─────────┼─────────────────┼─────────────────┼──────────┘
│            │                 │                 │            │
│            └─────────────────┼─────────────────┘            │
│                              ▼                              │
│  ┌────────────────── 消息分析层 ─────────────────────┐     │
│  │                                                    │     │
│  │  ┌──────────────────────────────────────────┐    │     │
│  │  │         ForumEngine (后台线程)            │    │     │
│  │  │  - 监控三个 Agent 的日志输出              │    │     │
│  │  │  - 协调 Agent 协作                        │    │     │
│  │  │  - 生成论坛讨论总结                       │    │     │
│  │  └──────────────────┬───────────────────────┘    │     │
│  │                     ▼                             │     │
│  │  ┌──────────────────────────────────────────┐    │     │
│  │  │         消息分析引擎 (LLM)                │    │     │
│  │  │  - 实体识别（股票、题材、事件）           │    │     │
│  │  │  - 情感分析（利好/利空/中性）             │    │     │
│  │  │  - 事件提取（业绩、重组、政策等）         │    │     │
│  │  │  - 影响评估（重大/一般/轻微）             │    │     │
│  │  └──────────────────┬───────────────────────┘    │     │
│  │                                                    │     │
│  └────────────────────────────────────────────────────┘     │
│                              ▼                              │
│  ┌────────────────── 因子量化层 ⭐ ──────────────────┐     │
│  │                                                    │     │
│  │  ┌──────────────────────────────────────────┐    │     │
│  │  │    MessageFactorGenerator (新增核心)     │    │     │
│  │  │                                           │    │     │
│  │  │  输入：LLM 分析结果（非结构化）          │    │     │
│  │  │  处理：量化计算                           │    │     │
│  │  │  输出：标准化因子（数值化）              │    │     │
│  │  │                                           │    │     │
│  │  │  因子类型：                               │    │     │
│  │  │  ├─ 情感因子 (sentiment_factor)          │    │     │
│  │  │  ├─ 事件因子 (event_impact_factor)       │    │     │
│  │  │  ├─ 题材因子 (concept_heat_factor)       │    │     │
│  │  │  ├─ 舆情因子 (public_opinion_factor)     │    │     │
│  │  │  └─ 时效因子 (timeliness_factor)         │    │     │
│  │  └──────────────────┬───────────────────────┘    │     │
│  │                                                    │     │
│  └────────────────────────────────────────────────────┘     │
│                              ▼                              │
│  ┌────────────────── 数据存储层 ─────────────────────┐     │
│  │                                                    │     │
│  │  BettaFish 本地数据库 (PostgreSQL)                │     │
│  │  ├─ raw_news (原始新闻)                           │     │
│  │  ├─ raw_announcements (原始公告)                  │     │
│  │  ├─ analyzed_messages (分析结果)                  │     │
│  │  └─ message_factors (标准化因子) ⭐               │     │
│  │                                                    │     │
│  └────────────────────────────────────────────────────┘     │
│                                                             │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          │ 数据同步（后期实现）
                          ▼
              ┌───────────────────────┐
              │  现有量化系统          │
              │  - 接收消息因子       │
              │  - 因子分析与回测     │
              │  - 策略生成           │
              └───────────────────────┘
```

---

### 2.2 异步任务架构 ⭐

**核心设计**：消息因子生成流程耗时较长（20-60秒/只股票），必须采用异步处理架构以支持高并发和批量处理。

```
┌─────────────────────────────────────────────────────────────┐
│                  异步任务处理架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐         ┌──────────────┐                 │
│  │  Flask API   │────────▶│ Task Queue   │                 │
│  │  (接收请求)   │  提交   │   (Redis)    │                 │
│  │              │  任务   │              │                 │
│  │  - POST /analyze       │  - 任务队列   │                 │
│  │  - GET /status         │  - 结果缓存   │                 │
│  │  - GET /result         │  - 进度跟踪   │                 │
│  └──────────────┘         └──────┬───────┘                 │
│         ▲                        │                         │
│         │ 查询状态                │ 分发任务                 │
│         │                        ▼                         │
│  ┌────────────────────────────────────────────┐            │
│  │         Celery Workers (多进程)             │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐ │            │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │ │            │
│  │  │          │  │          │  │          │ │            │
│  │  │ 处理中   │  │ 空闲     │  │ 处理中   │ │            │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘ │            │
│  └───────┼─────────────┼─────────────┼────────┘            │
│          │             │             │                     │
│          ▼             ▼             ▼                     │
│  ┌──────────────────────────────────────────┐              │
│  │  消息获取 → 分析 → 因子计算 → 存储       │              │
│  │  (20-60秒/只股票)                        │              │
│  └──────────────────┬───────────────────────┘              │
│                     ▼                                      │
│  ┌──────────────────────────────────────────┐              │
│  │      PostgreSQL (结果持久化)              │              │
│  └──────────────────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**核心组件**：
- **Celery**: 分布式任务队列框架
- **Redis**: 消息队列 + 结果缓存 + 进度跟踪
- **PostgreSQL**: 持久化存储
- **Flask API**: RESTful接口

**关键特性**：
```
✅ 异步提交：API立即返回task_id，不阻塞
✅ 进度跟踪：实时查询任务进度（0-100%）
✅ 并发处理：多Worker并行处理任务
✅ 批量分析：支持批量提交（100+股票）
✅ 失败重试：自动重试机制
✅ 超时控制：任务超时自动终止
```

---

### 2.3 因子平台架构 ⭐

**核心设计**：将因子开发平台化，支持快速开发和迭代新因子。

```
┌─────────────────────────────────────────────────────────────┐
│                    因子开发平台                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌────────────────── 因子基类 ──────────────────┐          │
│  │                                                │          │
│  │  class BaseFactor(ABC):                       │          │
│  │      name: str                                │          │
│  │      version: str                             │          │
│  │      category: str                            │          │
│  │      output_range: tuple                      │          │
│  │                                                │          │
│  │      @abstractmethod                          │          │
│  │      def calculate(analysis) -> float         │          │
│  │                                                │          │
│  └────────────────────┬───────────────────────────┘          │
│                       │ 继承                                 │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────┐         │
│  │              内置因子（MVP阶段）                │         │
│  │  ┌──────────────┐  ┌──────────────┐           │         │
│  │  │SentimentFactor│  │EventImpactFactor│        │         │
│  │  └──────────────┘  └──────────────┘           │         │
│  │  ┌──────────────┐  ┌──────────────┐           │         │
│  │  │ConceptHeatFactor│ │OpinionFactor│          │         │
│  │  └──────────────┘  └──────────────┘           │         │
│  │  ┌──────────────┐  ┌──────────────┐           │         │
│  │  │TimelinessFactor│ │CompositeFactor│         │         │
│  │  └──────────────┘  └──────────────┘           │         │
│  └────────────────────┬───────────────────────────┘         │
│                       │ 注册                                 │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────┐         │
│  │           FactorRegistry (注册中心)             │         │
│  │  - register(factor_class)                      │         │
│  │  - get_factor(name)                            │         │
│  │  - list_factors(category)                      │         │
│  │  - get_metadata()                              │         │
│  └────────────────────┬───────────────────────────┘         │
│                       │ 使用                                 │
│                       ▼                                      │
│  ┌────────────────────────────────────────────────┐         │
│  │           FactorEngine (计算引擎)               │         │
│  │  - calculate_all(analysis)                     │         │
│  │  - calculate_composite(factors, weights)       │         │
│  │  - parallel_calculate() [并发计算]             │         │
│  └────────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**平台价值**：
```
对开发者：
✅ 标准化接口 → 降低开发难度
✅ 即插即用 → 快速迭代（1-2天上线新因子）
✅ 自动测试 → 保证质量
✅ 版本管理 → 可追溯

对业务：
✅ 快速响应需求 → 新因子快速上线
✅ A/B测试 → 多版本因子对比
✅ 灵活组合 → 不同策略使用不同因子组合
✅ 持续优化 → 因子迭代不影响系统稳定性

对系统：
✅ 松耦合 → 因子独立，互不影响
✅ 可扩展 → 无限扩展因子数量
✅ 可维护 → 每个因子独立维护
✅ 可监控 → 每个因子独立监控性能
```

---

### 2.4 数据流向

```
1. 消息获取
   外部新闻源 → QueryEngine/MediaEngine
   私有数据库 → InsightEngine
   
2. 消息存储
   → raw_news / raw_announcements 表

3. 消息分析
   → ForumEngine 协调 → LLM 深度分析
   → analyzed_messages 表

4. 因子量化 ⭐
   → MessageFactorGenerator 计算
   → message_factors 表

5. 因子同步（后期）
   → 推送到现有量化系统
```

---

### 2.3 与现有系统的数据交互

```
从现有系统读取（只读）:
┌─────────────────────────────────┐
│ PostgreSQL                      │
│ ├─ stock_basic_info (股票列表)  │
│ └─ concept_list (题材列表)      │
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ NebulaGraph                     │
│ └─ stock_concept_relation       │
│    (股票-题材关联图谱)          │
└─────────────────────────────────┘

写入 BettaFish 本地数据库:
┌─────────────────────────────────┐
│ BettaFish PostgreSQL            │
│ ├─ raw_news                     │
│ ├─ raw_announcements            │
│ ├─ analyzed_messages            │
│ └─ message_factors ⭐           │
└─────────────────────────────────┘
```

---

## 三、核心模块设计

### 3.1 消息获取层（保留原有架构）

#### QueryEngine（新闻搜索引擎）
- **功能**: 使用 Tavily API 搜索国内外新闻
- **端口**: 8503
- **输出**: 新闻标题、内容、URL、发布时间
- **保留**: 完全保留原有实现

#### MediaEngine（多模态搜索引擎）
- **功能**: 使用 Bocha API 进行多模态搜索
- **端口**: 8502
- **输出**: 结构化搜索结果
- **保留**: 完全保留原有实现

#### InsightEngine（私有数据库挖掘）
- **功能**: 从 MySQL 私有舆情数据库挖掘历史数据
- **端口**: 8501
- **输出**: 历史舆情数据
- **保留**: 完全保留原有实现

---

### 3.2 消息分析层（保留 + 增强）

#### ForumEngine（Agent 协作引擎）
- **功能**: 监控三个 Agent 的日志，协调协作，生成论坛讨论
- **保留**: 完全保留原有实现
- **增强**: 增加金融领域的 Prompt 模板

#### 消息分析引擎（LLM）
- **功能**: 
  - 实体识别：识别股票代码、公司名称、题材、事件类型
  - 情感分析：判断消息的情感倾向（利好/利空/中性）
  - 事件提取：提取关键事件（业绩预告、重组并购、政策利好等）
  - 影响评估：评估事件的影响程度（重大/一般/轻微）

---

### 3.3 因子量化层（新增核心模块）⭐

#### MessageFactorGenerator（消息因子生成器）

**核心职责**: 将 LLM 的非结构化分析结果量化为标准化因子

**因子定义**:

| 因子名称 | 数值范围 | 说明 | 计算逻辑 |
|---------|---------|------|---------|
| **情感因子** | [-1, 1] | 消息的情感倾向 | 利好: 0.5~1.0<br>中性: -0.2~0.2<br>利空: -1.0~-0.5 |
| **事件因子** | [0, 1] | 事件的重要性 | 根据事件类型和影响级别计算<br>业绩/重组: 0.9~1.0<br>政策/技术: 0.7~0.9<br>其他: 0.3~0.7 |
| **题材因子** | [0, 1] | 题材的热度 | 根据题材提及频次和市场热度计算 |
| **舆情因子** | [0, 1] | 舆论关注度 | 根据消息来源数量和传播广度计算 |
| **时效因子** | [0, 1] | 消息的时效性 | 当天: 1.0<br>1天前: 0.8<br>3天前: 0.5<br>7天前: 0.2 |
| **综合因子** | [0, 1] | 加权平均 | 上述因子的加权平均 |

**计算公式**:

```python
# 情感因子
sentiment_factor = base_score × impact_multiplier × confidence
  其中:
  - base_score: 根据情感倾向确定 (利好=0.7, 中性=0, 利空=-0.7)
  - impact_multiplier: 根据影响程度调整 (重大=1.3, 一般=1.0, 轻微=0.7)
  - confidence: LLM 分析的置信度

# 事件因子
event_factor = type_weight × impact_weight
  其中:
  - type_weight: 事件类型权重 (业绩=0.9, 重组=0.95, 政策=0.85)
  - impact_weight: 影响级别权重 (重大=1.0, 一般=0.7, 轻微=0.4)

# 题材因子
concept_factor = max(concept_hot_scores)
  - 取相关题材中热度最高的

# 舆情因子
opinion_factor = (source_factor + spread_score) / 2
  其中:
  - source_factor: min(1.0, source_count / 10)
  - spread_score: 传播广度评分

# 时效因子
timeliness_factor = 根据发布时间计算衰减

# 综合因子
composite_factor = weighted_average(all_factors)
```

---

### 3.4 数据存储层

#### BettaFish 本地数据库设计

```sql
-- 创建数据库
CREATE DATABASE bettafish_finance;

-- 1. 原始新闻表
CREATE TABLE raw_news (
    id SERIAL PRIMARY KEY,
    source VARCHAR(50) COMMENT '来源（新浪财经、东方财富等）',
    title VARCHAR(500) NOT NULL,
    content TEXT,
    url VARCHAR(500),
    publish_time TIMESTAMP,
    stock_codes VARCHAR(200) COMMENT '相关股票代码（逗号分隔）',
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_analyzed BOOLEAN DEFAULT FALSE,
    
    INDEX idx_publish_time (publish_time),
    INDEX idx_stock_codes (stock_codes),
    INDEX idx_is_analyzed (is_analyzed)
);

-- 2. 原始公告表
CREATE TABLE raw_announcements (
    id SERIAL PRIMARY KEY,
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50),
    announcement_type VARCHAR(50) COMMENT '公告类型（定期报告、重大事项等）',
    title VARCHAR(500) NOT NULL,
    content TEXT,
    publish_date DATE,
    url VARCHAR(500),
    crawl_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_analyzed BOOLEAN DEFAULT FALSE,
    
    INDEX idx_stock_code (stock_code),
    INDEX idx_publish_date (publish_date),
    INDEX idx_is_analyzed (is_analyzed)
);

-- 3. 分析结果表
CREATE TABLE analyzed_messages (
    id SERIAL PRIMARY KEY,
    message_id INT COMMENT '关联 raw_news 或 raw_announcements 的 id',
    message_type VARCHAR(20) COMMENT 'news 或 announcement',
    stock_code VARCHAR(20),
    
    -- LLM 分析结果
    summary TEXT COMMENT 'LLM 生成的摘要',
    key_points JSONB COMMENT '关键要点（JSON 数组）',
    sentiment VARCHAR(20) COMMENT '情感倾向（positive/neutral/negative）',
    sentiment_score DECIMAL(3,2) COMMENT '情感分数 -1 到 1',
    impact_level VARCHAR(20) COMMENT '影响程度（major/normal/minor）',
    event_type VARCHAR(50) COMMENT '事件类型（earnings/restructure/policy等）',
    
    -- 提取的结构化信息
    keywords JSONB COMMENT '关键词列表',
    entities JSONB COMMENT '实体识别（公司、人物、地点等）',
    related_stocks JSONB COMMENT '相关股票列表',
    related_concepts JSONB COMMENT '相关题材列表',
    
    -- 元数据
    analyzed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    llm_model VARCHAR(50) COMMENT '使用的 LLM 模型',
    confidence_score DECIMAL(3,2) COMMENT '分析置信度',
    
    INDEX idx_stock_code (stock_code),
    INDEX idx_sentiment (sentiment),
    INDEX idx_analyzed_time (analyzed_time)
);

-- 4. 消息因子表 ⭐ 核心输出
CREATE TABLE message_factors (
    id SERIAL PRIMARY KEY,
    
    -- 关联信息
    message_id INT COMMENT '关联 analyzed_messages 的 id',
    stock_code VARCHAR(20) NOT NULL,
    stock_name VARCHAR(50),
    
    -- 标准化因子（核心输出）
    sentiment_factor DECIMAL(5,4) COMMENT '情感因子 [-1, 1]',
    event_impact_factor DECIMAL(5,4) COMMENT '事件因子 [0, 1]',
    concept_heat_factor DECIMAL(5,4) COMMENT '题材因子 [0, 1]',
    public_opinion_factor DECIMAL(5,4) COMMENT '舆情因子 [0, 1]',
    timeliness_factor DECIMAL(5,4) COMMENT '时效因子 [0, 1]',
    composite_factor DECIMAL(5,4) COMMENT '综合因子（加权平均）',
    
    -- 元数据
    factor_date DATE NOT NULL COMMENT '因子日期',
    generate_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 辅助信息（供回溯分析）
    event_type VARCHAR(50),
    related_concepts JSONB COMMENT '相关题材列表',
    source_count INT DEFAULT 1 COMMENT '消息来源数量',
    confidence_score DECIMAL(3,2),
    
    INDEX idx_stock_code (stock_code),
    INDEX idx_factor_date (factor_date),
    INDEX idx_composite_factor (composite_factor)
);

-- 5. 题材热度表（辅助计算题材因子）
CREATE TABLE concept_heat_scores (
    concept_id INT,
    concept_name VARCHAR(100) NOT NULL,
    hot_score DECIMAL(5,4) COMMENT '热度评分 [0, 1]',
    mention_count INT DEFAULT 0 COMMENT '最近提及次数',
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    PRIMARY KEY (concept_id),
    INDEX idx_hot_score (hot_score DESC),
    INDEX idx_update_time (update_time)
);
```

---

## 四、外部数据依赖

### 4.1 从现有系统读取的数据（只读）

#### 1. 股票基本信息列表

```python
# 从 PostgreSQL 读取
def get_stock_list() -> pd.DataFrame:
    """
    读取股票基本信息列表
    """
    query = """
    SELECT 
        stock_code,
        stock_name,
        industry,
        market,
        list_date,
        is_active
    FROM stock_basic_info
    WHERE is_active = TRUE
    """
    return pd.read_sql(query, postgres_conn)
```

**用途**:
- 识别新闻/公告中提到的股票
- 验证股票代码的有效性
- 关联行业信息

#### 2. 题材列表

```python
# 从 PostgreSQL 读取
def get_concept_list() -> pd.DataFrame:
    """
    读取题材列表
    """
    query = """
    SELECT 
        concept_id,
        concept_name,
        concept_type,
        is_active
    FROM concept_list
    WHERE is_active = TRUE
    """
    return pd.read_sql(query, postgres_conn)
```

**用途**:
- 识别新闻/公告中的题材
- 题材热度分析
- 题材轮动监控

#### 3. 股票-题材关联关系

```python
# 从 NebulaGraph 读取（推荐）
def get_stock_concept_relation(stock_code: str = None) -> pd.DataFrame:
    """
    读取股票-题材关联关系
    """
    if stock_code:
        query = f"""
        MATCH (s:Stock {{code: '{stock_code}'}})-[r:BELONG_TO]->(c:Concept)
        RETURN s.code AS stock_code, 
               s.name AS stock_name, 
               c.name AS concept_name, 
               r.weight AS weight
        """
    else:
        query = """
        MATCH (s:Stock)-[r:BELONG_TO]->(c:Concept)
        RETURN s.code AS stock_code, 
               s.name AS stock_name, 
               c.name AS concept_name, 
               r.weight AS weight
        """
    return nebula_client.execute_query(query)
```

**用途**:
- 题材股识别
- 题材传导分析
- 板块联动分析

---

### 4.2 数据访问适配器设计

```python
# data_access/external_data_adapter.py

class ExternalDataAdapter:
    """
    外部数据适配器
    统一访问现有系统的数据
    """
    
    def __init__(self, config: Dict):
        # PostgreSQL 连接
        self.pg_conn = psycopg2.connect(
            host=config['postgres']['host'],
            database=config['postgres']['database'],
            user=config['postgres']['user'],
            password=config['postgres']['password']
        )
        
        # NebulaGraph 连接
        self.nebula_client = NebulaGraphClient(
            host=config['nebula']['host'],
            port=config['nebula']['port'],
            username=config['nebula']['username'],
            password=config['nebula']['password']
        )
        
        # 缓存（避免频繁查询）
        self._stock_list_cache = None
        self._concept_list_cache = None
        self._cache_expire_time = None
    
    def get_stock_list(self, use_cache: bool = True) -> pd.DataFrame:
        """获取股票列表（带缓存）"""
        if use_cache and self._is_cache_valid():
            return self._stock_list_cache
        
        # 从数据库读取
        df = pd.read_sql("""
            SELECT stock_code, stock_name, industry, market, is_active
            FROM stock_basic_info
            WHERE is_active = TRUE
        """, self.pg_conn)
        
        # 更新缓存
        self._stock_list_cache = df
        self._cache_expire_time = datetime.now() + timedelta(hours=24)
        
        return df
    
    def get_concept_list(self, use_cache: bool = True) -> pd.DataFrame:
        """获取题材列表（带缓存）"""
        # 类似实现
        pass
    
    def get_stock_concepts(self, stock_code: str) -> List[str]:
        """获取指定股票的题材列表"""
        query = f"""
        MATCH (s:Stock {{code: '{stock_code}'}})-[:BELONG_TO]->(c:Concept)
        RETURN c.name AS concept_name
        """
        result = self.nebula_client.execute_query(query)
        return [row['concept_name'] for row in result]
    
    def _is_cache_valid(self) -> bool:
        """检查缓存是否有效"""
        if self._cache_expire_time is None:
            return False
        return datetime.now() < self._cache_expire_time
```

---

## 五、MVP 实施计划（8周）

### 5.1 开发环境准备（Day 1-2）

**任务清单**:
- [ ] 创建 BettaFish 本地数据库 `bettafish_finance`
- [ ] 执行建表 SQL
- [ ] 配置外部数据源连接（PostgreSQL + NebulaGraph）
- [ ] 测试数据访问（确保能读取股票列表、题材列表）
- [ ] 准备开发环境（Python 3.9+, 依赖库）

**验收标准**:
- ✅ 能够成功连接所有数据库
- ✅ 能够读取股票基本信息列表
- ✅ 能够读取题材列表和关联关系

---

### 5.2 Week 1: 外部数据适配层（3-5天）

**任务清单**:
- [ ] 实现 `ExternalDataAdapter` 类
  - [ ] PostgreSQL 连接和查询
  - [ ] NebulaGraph 连接和查询
  - [ ] 数据缓存机制
- [ ] 实现数据访问接口
  - [ ] `get_stock_list()`
  - [ ] `get_concept_list()`
  - [ ] `get_stock_concepts(stock_code)`
- [ ] 单元测试
  - [ ] 测试数据读取
  - [ ] 测试缓存机制
  - [ ] 测试异常处理

**验收标准**:
- ✅ 能够正确读取所有外部数据
- ✅ 缓存机制工作正常
- ✅ 单元测试覆盖率 > 80%

---

### 5.3 Week 2: 消息获取层改造（5-7天）

**任务清单**:
- [ ] 保留原有 QueryEngine、MediaEngine、InsightEngine
- [ ] 调整数据存储逻辑
  - [ ] 将爬取的新闻保存到 `raw_news` 表
  - [ ] 将爬取的公告保存到 `raw_announcements` 表
- [ ] 增强实体识别
  - [ ] 使用 `ExternalDataAdapter` 验证股票代码
  - [ ] 识别题材关键词
- [ ] 测试消息获取流程

**验收标准**:
- ✅ 能够正常爬取新闻和公告
- ✅ 数据正确保存到本地数据库
- ✅ 实体识别准确率 > 80%

---

### 5.4 Week 3: 消息分析层改造（5-7天）

**任务清单**:
- [ ] 保留原有 ForumEngine 架构
- [ ] 设计金融分析 Prompt 模板
  - [ ] 实体识别 Prompt
  - [ ] 情感分析 Prompt
  - [ ] 事件提取 Prompt
  - [ ] 影响评估 Prompt
- [ ] 实现消息分析引擎
  - [ ] 调用 LLM 进行分析
  - [ ] 解析 LLM 输出
  - [ ] 保存分析结果到 `analyzed_messages` 表
- [ ] 测试分析准确性

**Prompt 模板示例**:

```python
FINANCIAL_ANALYSIS_PROMPT = """
你是一个专业的金融分析师，请分析以下消息：

【消息内容】
标题：{title}
内容：{content}
发布时间：{publish_time}

【分析任务】
1. 识别相关股票代码和公司名称
2. 识别相关题材（从以下列表中选择）：
   {concept_list}
3. 判断情感倾向：利好(positive) / 中性(neutral) / 利空(negative)
4. 评估影响程度：重大(major) / 一般(normal) / 轻微(minor)
5. 识别事件类型：业绩(earnings) / 重组(restructure) / 政策(policy) / 技术(technology) / 其他(other)
6. 提取关键要点（3-5条）
7. 生成摘要（100字以内）

【输出格式】（JSON）
{{
    "related_stocks": ["股票代码1", "股票代码2"],
    "related_concepts": ["题材1", "题材2"],
    "sentiment": "positive/neutral/negative",
    "impact_level": "major/normal/minor",
    "event_type": "earnings/restructure/policy/technology/other",
    "key_points": ["要点1", "要点2", "要点3"],
    "summary": "摘要内容",
    "confidence": 0.85
}}
"""
```

**验收标准**:
- ✅ LLM 分析结果格式正确
- ✅ 情感分析准确率 > 75%
- ✅ 实体识别准确率 > 80%
- ✅ 分析结果正确保存到数据库

---

### 5.5 Week 4: 因子量化层实现（5-7天）⭐ 核心

**任务清单**:
- [ ] 实现 `MessageFactorGenerator` 类
  - [ ] `calculate_sentiment_factor()` - 情感因子
  - [ ] `calculate_event_factor()` - 事件因子
  - [ ] `calculate_concept_factor()` - 题材因子
  - [ ] `calculate_opinion_factor()` - 舆情因子
  - [ ] `calculate_timeliness_factor()` - 时效因子
  - [ ] `calculate_composite_factor()` - 综合因子
- [ ] 实现因子存储逻辑
  - [ ] 保存到 `message_factors` 表
- [ ] 实现题材热度计算
  - [ ] 统计题材提及频次
  - [ ] 更新 `concept_heat_scores` 表
- [ ] 单元测试
  - [ ] 测试每个因子的计算逻辑
  - [ ] 测试边界情况

**代码框架**:

```python
# factor_engine/message_factor_generator.py

class MessageFactorGenerator:
    """
    消息因子生成器
    """
    
    def __init__(self, external_adapter: ExternalDataAdapter):
        self.external_adapter = external_adapter
    
    def generate_factors(self, analysis: Dict) -> Dict:
        """
        从分析结果生成标准化因子
        """
        factors = {
            'message_id': analysis['id'],
            'stock_code': analysis['stock_code'],
            'stock_name': self._get_stock_name(analysis['stock_code']),
            'factor_date': analysis['analyzed_time'].date(),
            
            # 计算各类因子
            'sentiment_factor': self._calculate_sentiment_factor(analysis),
            'event_impact_factor': self._calculate_event_factor(analysis),
            'concept_heat_factor': self._calculate_concept_factor(analysis),
            'public_opinion_factor': self._calculate_opinion_factor(analysis),
            'timeliness_factor': self._calculate_timeliness_factor(analysis),
            
            # 元数据
            'event_type': analysis.get('event_type'),
            'related_concepts': analysis.get('related_concepts'),
            'source_count': analysis.get('source_count', 1),
            'confidence_score': analysis.get('confidence_score', 0.8),
            'generate_time': datetime.now()
        }
        
        # 计算综合因子
        factors['composite_factor'] = self._calculate_composite_factor(factors)
        
        return factors
    
    def _calculate_sentiment_factor(self, analysis: Dict) -> float:
        """情感因子计算"""
        sentiment = analysis.get('sentiment', 'neutral')
        impact_level = analysis.get('impact_level', 'normal')
        confidence = analysis.get('confidence_score', 0.8)
        
        # 基础分数
        base_score = {
            'positive': 0.7,
            'neutral': 0.0,
            'negative': -0.7
        }.get(sentiment, 0.0)
        
        # 影响程度调整
        impact_multiplier = {
            'major': 1.3,
            'normal': 1.0,
            'minor': 0.7
        }.get(impact_level, 1.0)
        
        # 最终分数
        final_score = base_score * impact_multiplier * confidence
        
        # 限制范围 [-1, 1]
        return max(-1.0, min(1.0, final_score))
    
    def _calculate_event_factor(self, analysis: Dict) -> float:
        """事件因子计算"""
        event_type = analysis.get('event_type', 'other')
        impact_level = analysis.get('impact_level', 'normal')
        
        # 事件类型权重
        type_weight = {
            'earnings': 0.9,
            'restructure': 0.95,
            'policy': 0.85,
            'technology': 0.8,
            'management': 0.7,
            'other': 0.5
        }.get(event_type, 0.5)
        
        # 影响级别权重
        impact_weight = {
            'major': 1.0,
            'normal': 0.7,
            'minor': 0.4
        }.get(impact_level, 0.7)
        
        return type_weight * impact_weight
    
    def _calculate_concept_factor(self, analysis: Dict) -> float:
        """题材因子计算"""
        concepts = analysis.get('related_concepts', [])
        
        if not concepts:
            return 0.0
        
        # 查询题材热度
        concept_scores = []
        for concept in concepts:
            hot_score = self._get_concept_hot_score(concept)
            concept_scores.append(hot_score)
        
        # 取最高热度
        return max(concept_scores) if concept_scores else 0.0
    
    def _calculate_opinion_factor(self, analysis: Dict) -> float:
        """舆情因子计算"""
        source_count = analysis.get('source_count', 1)
        spread_score = analysis.get('spread_score', 0.5)
        
        # 来源越多，可信度越高
        source_factor = min(1.0, source_count / 10.0)
        
        # 综合评分
        return (source_factor + spread_score) / 2.0
    
    def _calculate_timeliness_factor(self, analysis: Dict) -> float:
        """时效因子计算"""
        publish_time = analysis.get('publish_time')
        
        if not publish_time:
            return 0.5
        
        days_ago = (datetime.now() - publish_time).days
        
        if days_ago == 0:
            return 1.0
        elif days_ago <= 1:
            return 0.8
        elif days_ago <= 3:
            return 0.5
        elif days_ago <= 7:
            return 0.2
        else:
            return 0.0
    
    def _calculate_composite_factor(self, factors: Dict) -> float:
        """综合因子计算（加权平均）"""
        weights = {
            'sentiment_factor': 0.3,
            'event_impact_factor': 0.3,
            'concept_heat_factor': 0.2,
            'public_opinion_factor': 0.1,
            'timeliness_factor': 0.1
        }
        
        # 情感因子需要转换到 [0, 1] 范围
        sentiment_normalized = (factors['sentiment_factor'] + 1) / 2
        
        composite = (
            sentiment_normalized * weights['sentiment_factor'] +
            factors['event_impact_factor'] * weights['event_impact_factor'] +
            factors['concept_heat_factor'] * weights['concept_heat_factor'] +
            factors['public_opinion_factor'] * weights['public_opinion_factor'] +
            factors['timeliness_factor'] * weights['timeliness_factor']
        )
        
        return round(composite, 4)
    
    def _get_concept_hot_score(self, concept_name: str) -> float:
        """获取题材热度评分"""
        # 从 concept_heat_scores 表查询
        # 如果不存在，返回默认值 0.5
        pass
    
    def save_factors(self, factors: Dict):
        """保存因子到数据库"""
        query = """
        INSERT INTO message_factors (
            message_id, stock_code, stock_name, factor_date,
            sentiment_factor, event_impact_factor, concept_heat_factor,
            public_opinion_factor, timeliness_factor, composite_factor,
            event_type, related_concepts, source_count, confidence_score,
            generate_time
        ) VALUES (
            %(message_id)s, %(stock_code)s, %(stock_name)s, %(factor_date)s,
            %(sentiment_factor)s, %(event_impact_factor)s, %(concept_heat_factor)s,
            %(public_opinion_factor)s, %(timeliness_factor)s, %(composite_factor)s,
            %(event_type)s, %(related_concepts)s, %(source_count)s, %(confidence_score)s,
            %(generate_time)s
        )
        """
        # 执行插入
        pass
```

**验收标准**:
- ✅ 所有因子计算逻辑正确
- ✅ 因子数值在合理范围内
- ✅ 因子正确保存到数据库
- ✅ 单元测试覆盖率 > 90%

---

### 5.6 Week 5: 异步架构实现 ⭐（5-7天）

**任务清单**:
- [ ] 环境搭建
  - [ ] 安装 Redis
  - [ ] 安装 Celery
  - [ ] 配置 Celery Worker
- [ ] 核心任务定义
  - [ ] `analyze_stock_async()` - 异步分析单只股票
  - [ ] `batch_analyze_stocks()` - 批量分析
  - [ ] `scheduled_factor_update()` - 定时更新
- [ ] API接口实现
  - [ ] `POST /api/factor/analyze` - 提交任务
  - [ ] `GET /api/factor/status/<task_id>` - 查询状态
  - [ ] `GET /api/factor/result/<task_id>` - 获取结果
  - [ ] `POST /api/factor/batch` - 批量提交
  - [ ] `POST /api/factor/cancel/<task_id>` - 取消任务
- [ ] 进度跟踪机制
  - [ ] 实现 `FactorTask` 基类
  - [ ] 实现 `update_progress()` 方法
  - [ ] 状态管理（PENDING/PROGRESS/SUCCESS/FAILURE）
- [ ] 测试
  - [ ] 单任务测试
  - [ ] 批量任务测试
  - [ ] 并发测试（10+任务）
  - [ ] 失败重试测试

**代码框架**:

```python
# tasks/factor_tasks.py

from celery import Celery, Task
from celery.result import AsyncResult

# 初始化Celery
celery_app = Celery(
    'bettafish',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/1'
)

# 配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    task_track_started=True,
    task_time_limit=300,  # 5分钟超时
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=50
)


class FactorTask(Task):
    """因子任务基类 - 支持进度跟踪"""
    
    def update_progress(self, current, total, message=''):
        """更新任务进度"""
        self.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'message': message,
                'percent': int(current / total * 100)
            }
        )


@celery_app.task(base=FactorTask, bind=True, name='tasks.analyze_stock')
def analyze_stock_async(self, stock_code: str, days: int = 30):
    """
    异步分析股票消息并生成因子
    """
    try:
        # Step 1: 消息获取 (0-30%)
        self.update_progress(0, 100, f'开始获取 {stock_code} 的消息...')
        messages = fetch_messages(stock_code, days)
        self.update_progress(30, 100, f'获取到 {len(messages)} 条消息')
        
        # Step 2: 消息分析 (30-80%)
        self.update_progress(30, 100, '开始分析消息...')
        analyzed_results = []
        for i, msg in enumerate(messages):
            analysis = analyze_message(msg)
            analyzed_results.append(analysis)
            progress = 30 + int((i + 1) / len(messages) * 50)
            self.update_progress(progress, 100, f'分析进度: {i+1}/{len(messages)}')
        
        # Step 3: 因子计算 (80-95%)
        self.update_progress(80, 100, '开始生成因子...')
        factors_list = []
        for i, analysis in enumerate(analyzed_results):
            factors = engine.calculate_all(analysis)
            save_factors_to_db(stock_code, factors)
            factors_list.append(factors)
            progress = 80 + int((i + 1) / len(analyzed_results) * 15)
            self.update_progress(progress, 100, f'因子生成: {i+1}/{len(analyzed_results)}')
        
        # Step 4: 生成汇总 (95-100%)
        self.update_progress(95, 100, '生成分析报告...')
        summary = generate_summary(stock_code, analyzed_results, factors_list)
        self.update_progress(100, 100, '分析完成')
        
        return {
            'stock_code': stock_code,
            'message_count': len(messages),
            'factor_count': len(factors_list),
            'summary': summary,
            'status': 'success'
        }
        
    except Exception as e:
        self.update_state(state='FAILURE', meta={'error': str(e)})
        raise


@celery_app.task(name='tasks.batch_analyze')
def batch_analyze_stocks(stock_codes: list, days: int = 30):
    """批量分析股票（并发执行）"""
    from celery import group
    
    job = group(analyze_stock_async.s(code, days) for code in stock_codes)
    result = job.apply_async()
    
    return {
        'task_ids': [r.id for r in result.results],
        'total': len(stock_codes)
    }
```

```python
# api/factor_api.py

from flask import Blueprint, request, jsonify
from celery.result import AsyncResult
from tasks.factor_tasks import analyze_stock_async, batch_analyze_stocks

factor_bp = Blueprint('factor', __name__, url_prefix='/api/factor')


@factor_bp.route('/analyze', methods=['POST'])
def submit_analysis():
    """提交分析任务"""
    data = request.json
    stock_code = data.get('stock_code')
    days = data.get('days', 30)
    
    if not stock_code:
        return jsonify({'error': 'stock_code is required'}), 400
    
    # 提交异步任务
    task = analyze_stock_async.apply_async(args=[stock_code, days])
    
    return jsonify({
        'task_id': task.id,
        'status': 'pending',
        'message': f'任务已提交: {stock_code}'
    }), 202


@factor_bp.route('/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """查询任务状态"""
    task = AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {'task_id': task_id, 'state': 'PENDING', 'message': '任务等待中...'}
    elif task.state == 'PROGRESS':
        response = {'task_id': task_id, 'state': 'PROGRESS', **task.info}
    elif task.state == 'SUCCESS':
        response = {'task_id': task_id, 'state': 'SUCCESS', 'result': task.result}
    elif task.state == 'FAILURE':
        response = {'task_id': task_id, 'state': 'FAILURE', 'error': str(task.info)}
    else:
        response = {'task_id': task_id, 'state': task.state}
    
    return jsonify(response)


@factor_bp.route('/batch', methods=['POST'])
def submit_batch_analysis():
    """批量分析"""
    data = request.json
    stock_codes = data.get('stock_codes', [])
    days = data.get('days', 30)
    
    if not stock_codes:
        return jsonify({'error': 'stock_codes is required'}), 400
    
    result = batch_analyze_stocks.apply_async(args=[stock_codes, days])
    
    return jsonify({
        'batch_task_id': result.id,
        'total': len(stock_codes),
        'message': f'批量任务已提交: {len(stock_codes)}只股票'
    }), 202
```

**验收标准**:
- ✅ 异步任务提交成功，API立即返回（< 100ms）
- ✅ 进度跟踪准确（0-100%）
- ✅ 支持并发处理（10+任务同时运行）
- ✅ 批量分析功能正常
- ✅ 任务失败自动重试
- ✅ 超时任务自动终止

---

### 5.7 Week 6: 因子平台实现 ⭐（5-7天）

**任务清单**:
- [ ] 因子基类实现
  - [ ] `BaseFactor` 抽象类
  - [ ] 元数据管理（name, version, category, output_range）
  - [ ] `calculate()` 抽象方法
  - [ ] `validate()` 验证方法
- [ ] 因子注册中心
  - [ ] `FactorRegistry` 类
  - [ ] `register()` 注册方法
  - [ ] `get_factor()` 获取方法
  - [ ] `list_factors()` 列表方法
- [ ] 因子计算引擎
  - [ ] `FactorEngine` 类
  - [ ] `calculate_all()` 批量计算
  - [ ] `calculate_composite()` 综合因子
  - [ ] 并发计算支持
- [ ] 内置因子实现
  - [ ] `SentimentFactor` - 情感因子
  - [ ] `EventImpactFactor` - 事件因子
  - [ ] `ConceptHeatFactor` - 题材因子
  - [ ] `PublicOpinionFactor` - 舆情因子
  - [ ] `TimelinessFactor` - 时效因子
  - [ ] `CompositeFactor` - 综合因子
- [ ] 因子测试框架
  - [ ] `FactorTester` 类
  - [ ] 基础测试（元数据、接口）
  - [ ] 边界测试
  - [ ] 性能测试（< 1ms/次）

**代码框架**:

```python
# factor_engine/base_factor.py

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseFactor(ABC):
    """
    因子基类 - 所有因子必须继承此类
    """
    
    # 因子元数据
    name: str = ""
    version: str = "1.0.0"
    category: str = ""
    output_range: tuple = (0, 1)
    
    @abstractmethod
    def calculate(self, analysis: Dict[str, Any]) -> float:
        """
        因子计算逻辑
        
        Args:
            analysis: 消息分析结果
            
        Returns:
            float: 因子值
        """
        pass
    
    def validate(self, value: float) -> bool:
        """验证因子值是否在合理范围内"""
        min_val, max_val = self.output_range
        return min_val <= value <= max_val
    
    def get_metadata(self) -> Dict:
        """获取因子元数据"""
        return {
            'name': self.name,
            'version': self.version,
            'category': self.category,
            'output_range': self.output_range,
            'description': self.__doc__
        }
```

```python
# factor_engine/factors/sentiment_factor.py

from factor_engine.base_factor import BaseFactor

class SentimentFactor(BaseFactor):
    """
    情感因子：量化消息的情感倾向
    """
    
    name = "sentiment_factor"
    version = "1.0.0"
    category = "sentiment"
    output_range = (-1, 1)
    
    def calculate(self, analysis: Dict[str, Any]) -> float:
        sentiment = analysis.get('sentiment', 'neutral')
        impact_level = analysis.get('impact_level', 'normal')
        confidence = analysis.get('confidence_score', 0.8)
        
        # 基础分数
        base_score = {
            'positive': 0.7,
            'neutral': 0.0,
            'negative': -0.7
        }.get(sentiment, 0.0)
        
        # 影响程度调整
        impact_multiplier = {
            'major': 1.3,
            'normal': 1.0,
            'minor': 0.7
        }.get(impact_level, 1.0)
        
        # 最终分数
        final_score = base_score * impact_multiplier * confidence
        
        # 限制范围
        return max(-1.0, min(1.0, final_score))
```

```python
# factor_engine/factor_registry.py

class FactorRegistry:
    """因子注册中心"""
    
    def __init__(self):
        self.factors = {}
        self.factor_groups = {}
    
    def register(self, factor_class: type):
        """注册因子"""
        factor = factor_class()
        
        if not isinstance(factor, BaseFactor):
            raise ValueError(f"{factor_class} must inherit from BaseFactor")
        
        if factor.name in self.factors:
            raise ValueError(f"Factor {factor.name} already registered")
        
        self.factors[factor.name] = factor
        
        # 分组管理
        category = factor.category
        if category not in self.factor_groups:
            self.factor_groups[category] = []
        self.factor_groups[category].append(factor.name)
        
        print(f"✅ Registered factor: {factor.name} v{factor.version}")
    
    def get_factor(self, name: str) -> BaseFactor:
        """获取因子"""
        return self.factors.get(name)
    
    def list_factors(self, category: str = None) -> list:
        """列出因子"""
        if category:
            return self.factor_groups.get(category, [])
        return list(self.factors.keys())


# 全局注册中心
_global_registry = FactorRegistry()

def get_registry() -> FactorRegistry:
    """获取全局注册中心"""
    return _global_registry
```

```python
# factor_engine/factor_engine.py

class FactorEngine:
    """因子计算引擎"""
    
    def __init__(self, registry: FactorRegistry):
        self.registry = registry
    
    def calculate_all(self, analysis: Dict[str, Any], 
                     enabled_factors: list = None) -> Dict[str, float]:
        """计算所有因子"""
        factors = {}
        
        if enabled_factors is None:
            enabled_factors = self.registry.list_factors()
        
        for factor_name in enabled_factors:
            factor = self.registry.get_factor(factor_name)
            
            if factor is None:
                continue
            
            try:
                value = factor.calculate(analysis)
                
                if not factor.validate(value):
                    logger.warning(f"Factor {factor_name} value {value} out of range")
                
                factors[factor_name] = value
                
            except Exception as e:
                logger.error(f"Error calculating {factor_name}: {e}")
                factors[factor_name] = None
        
        return factors
```

**验收标准**:
- ✅ 因子基类接口完整
- ✅ 6个内置因子实现正确
- ✅ 因子注册机制正常工作
- ✅ 因子计算引擎性能达标（< 1ms/因子）
- ✅ 新增因子只需3步（定义、注册、生效）
- ✅ 单元测试覆盖率 > 90%

---

### 5.8 Week 7: 完整流程集成（5-7天）

**任务清单**:
- [ ] 实现完整的消息处理流程
  - [ ] 消息获取 → 消息分析 → 因子量化 → 数据存储
- [ ] 实现 Flask 主应用调度逻辑
- [ ] 实现 ReportEngine 报告生成
  - [ ] 集成因子数据
  - [ ] 生成 HTML 报告
- [ ] 端到端测试
  - [ ] 输入股票代码
  - [ ] 验证完整流程
  - [ ] 检查输出结果

**完整流程代码**:

```python
# main_processor.py

class MessageProcessor:
    """
    消息处理器：完整流程编排
    """
    
    def __init__(self):
        self.external_adapter = ExternalDataAdapter(config)
        self.factor_generator = MessageFactorGenerator(self.external_adapter)
    
    def process_stock_messages(self, stock_code: str, days: int = 30):
        """
        处理指定股票的消息
        """
        # Step 1: 获取消息
        logger.info(f"开始获取 {stock_code} 的消息...")
        messages = self._fetch_messages(stock_code, days)
        logger.info(f"获取到 {len(messages)} 条消息")
        
        # Step 2: 分析消息
        logger.info("开始分析消息...")
        analyzed_results = []
        for msg in messages:
            analysis = self._analyze_message(msg)
            analyzed_results.append(analysis)
        logger.info(f"分析完成，共 {len(analyzed_results)} 条")
        
        # Step 3: 生成因子
        logger.info("开始生成因子...")
        factors_list = []
        for analysis in analyzed_results:
            factors = self.factor_generator.generate_factors(analysis)
            self.factor_generator.save_factors(factors)
            factors_list.append(factors)
        logger.info(f"因子生成完成，共 {len(factors_list)} 条")
        
        # Step 4: 生成报告
        logger.info("开始生成报告...")
        report = self._generate_report(stock_code, analyzed_results, factors_list)
        logger.info("报告生成完成")
        
        return report
    
    def _fetch_messages(self, stock_code: str, days: int) -> List[Dict]:
        """获取消息"""
        # 调用 QueryEngine、MediaEngine、InsightEngine
        pass
    
    def _analyze_message(self, message: Dict) -> Dict:
        """分析消息"""
        # 调用 ForumEngine 和 LLM
        pass
    
    def _generate_report(self, stock_code: str, 
                        analyzed_results: List[Dict], 
                        factors_list: List[Dict]) -> str:
        """生成报告"""
        # 调用 ReportEngine
        pass
```

**验收标准**:
- ✅ 完整流程能够正常运行
- ✅ 响应时间 < 60秒（单只股票）
- ✅ 生成的报告包含因子数据
- ✅ 无重大 Bug

---

### 5.7 Week 6: 题材热度统计（3-5天）

**任务清单**:
- [ ] 实现题材提及频次统计
- [ ] 实现题材热度评分计算
- [ ] 实现定时更新机制
  - [ ] 每小时更新一次
- [ ] 测试题材热度准确性

**代码框架**:

```python
# factor_engine/concept_heat_calculator.py

class ConceptHeatCalculator:
    """
    题材热度计算器
    """
    
    def calculate_concept_heat(self, time_window: int = 24):
        """
        计算题材热度
        
        Args:
            time_window: 时间窗口（小时）
        """
        # 统计最近 N 小时内每个题材的提及次数
        query = f"""
        SELECT 
            concept_name,
            COUNT(*) as mention_count
        FROM (
            SELECT jsonb_array_elements_text(related_concepts) as concept_name
            FROM analyzed_messages
            WHERE analyzed_time >= NOW() - INTERVAL '{time_window} hours'
        ) t
        GROUP BY concept_name
        ORDER BY mention_count DESC
        """
        
        results = self.db.query(query)
        
        # 计算热度评分（归一化）
        max_count = results[0]['mention_count'] if results else 1
        
        for row in results:
            hot_score = min(1.0, row['mention_count'] / max_count)
            
            # 更新或插入
            self.db.execute("""
                INSERT INTO concept_heat_scores (concept_name, hot_score, mention_count, update_time)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (concept_name) 
                DO UPDATE SET 
                    hot_score = EXCLUDED.hot_score,
                    mention_count = EXCLUDED.mention_count,
                    update_time = EXCLUDED.update_time
            """, (row['concept_name'], hot_score, row['mention_count']))
```

**验收标准**:
- ✅ 题材热度评分合理
- ✅ 定时更新机制正常工作
- ✅ 热度数据正确保存到数据库

---

### 5.8 Week 7: 性能优化与测试（5-7天）

**任务清单**:
- [ ] 性能优化
  - [ ] 数据库查询优化（添加索引）
  - [ ] 缓存机制优化
  - [ ] 并发处理优化
- [ ] 集成测试
  - [ ] 测试多只股票分析
  - [ ] 测试大量消息处理
  - [ ] 测试异常情况
- [ ] 压力测试
  - [ ] 测试并发请求
  - [ ] 测试响应时间
- [ ] Bug 修复

**性能指标**:
- ✅ 单只股票分析 < 60秒
- ✅ 并发支持 > 3 个请求
- ✅ 数据库查询 < 500ms
- ✅ 因子计算 < 100ms

---

### 5.9 Week 8: 文档与部署（3-5天）

**任务清单**:
- [ ] 完善代码文档
  - [ ] 添加 Docstring
  - [ ] 添加注释
- [ ] 编写用户文档
  - [ ] 系统使用说明
  - [ ] API 文档
  - [ ] 因子说明文档
- [ ] 部署准备
  - [ ] 配置文件模板
  - [ ] 启动脚本
  - [ ] 监控脚本
- [ ] 部署测试
  - [ ] 测试环境部署
  - [ ] 功能验证

**交付物**:
- ✅ 完整的代码库
- ✅ 用户使用文档
- ✅ API 文档
- ✅ 部署脚本
- ✅ 测试报告

---

## 六、技术栈

### 6.1 保留的技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 后端框架 | Flask | 2.0+ | Web 服务 |
| Agent UI | Streamlit | 1.28+ | Agent 界面 |
| LLM | DeepSeek | - | 消息分析 |
| 数据库 | MySQL | 8.0+ | 私有舆情数据 |
| 日志 | Loguru | 0.7+ | 日志记录 |
| API | Tavily API | - | 新闻搜索 |
| API | Bocha API | - | 多模态搜索 |

### 6.2 新增的技术栈 ⭐

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **本地数据库** | PostgreSQL | 14+ | BettaFish 数据存储 |
| **图数据库客户端** | nebula3-python | 3.0+ | 访问 NebulaGraph |
| **数据处理** | Pandas | 1.5+ | 数据处理 |
| **数据库连接** | psycopg2 | 2.9+ | PostgreSQL 连接 |
| **任务队列** | Celery | 5.3+ | 异步任务处理 |
| **消息队列** | Redis | 7.0+ | 任务队列 + 结果缓存 |
| **Redis客户端** | redis-py | 5.0+ | Redis 连接 |

### 6.3 Python 依赖

```txt
# requirements.txt

# 原有依赖（保留）
flask==2.3.0
streamlit==1.28.0
loguru==0.7.0
requests==2.31.0
beautifulsoup4==4.12.0

# 新增依赖 - 数据层
psycopg2-binary==2.9.9
nebula3-python==3.4.0
pandas==2.1.0
numpy==1.24.0

# 新增依赖 - 异步任务 ⭐
celery==5.3.4
redis==5.0.1
flower==2.0.1  # Celery 监控工具

# 新增依赖 - 因子平台
typing-extensions==4.8.0  # 类型注解支持
```

---

## 七、配置文件

### 7.1 数据库配置

```yaml
# config/database.yaml

# BettaFish 本地数据库
bettafish_db:
  type: postgresql
  host: localhost
  port: 5432
  database: bettafish_finance
  user: bettafish
  password: your_password

# 现有系统数据库（只读）
external_db:
  postgres:
    host: your_postgres_host
    port: 5432
    database: your_database
    user: readonly_user
    password: readonly_password
  
  nebula:
    host: your_nebula_host
    port: 9669
    username: readonly_user
    password: readonly_password
    space: your_space_name

# 原有私有舆情数据库
insight_db:
  type: mysql
  host: localhost
  port: 3306
  database: your_insight_db
  user: your_user
  password: your_password
```

---

## 八、MVP 验收标准

### 8.1 功能验收

- ✅ **消息获取**: 能够正常获取新闻和公告
- ✅ **消息分析**: LLM 分析结果格式正确，准确率 > 75%
- ✅ **因子生成**: 所有因子计算正确，数值在合理范围内
- ✅ **数据存储**: 数据正确保存到本地数据库
- ✅ **报告生成**: 生成包含因子数据的 HTML 报告

### 8.2 性能验收

- ✅ **响应时间**: 单只股票分析 < 60秒
- ✅ **并发能力**: 支持 3+ 并发请求
- ✅ **数据库性能**: 查询响应 < 500ms
- ✅ **因子计算**: 单条消息因子计算 < 100ms

### 8.3 质量验收

- ✅ **代码质量**: 符合 PEP 8 规范
- ✅ **测试覆盖**: 单元测试覆盖率 > 70%
- ✅ **文档完整**: 关键函数有 Docstring
- ✅ **无重大 Bug**: 核心流程稳定运行

---

## 九、后续优化方向（MVP 之后）

### 9.1 数据同步层（优先级 P1）

**目标**: 将消息因子同步到现有量化系统

**实现方式**（三选一）:
1. **定时批量同步**: 每小时同步一次（简单，推荐 MVP 后第一步）
2. **实时推送**: 通过 Kafka/RabbitMQ 推送（适合生产环境）
3. **API 查询**: 提供 REST API 供量化系统拉取（最灵活）

**预计时间**: 1-2周

---

### 9.2 向量检索（优先级 P1）

**目标**: 提升消息召回率从 75% 到 90%+

**实现方式**:
- 部署 ChromaDB 或 Milvus
- 向量化新闻和公告内容
- 实现混合检索（SQL + 向量）

**预计时间**: 4-6周

---

### 9.3 LangGraph 重构（优先级 P2）

**目标**: 提升系统可维护性和性能

**实现方式**:
- 定义 FinancialAnalysisState
- 改造所有节点为 LangGraph 格式
- 构建可视化工作流图

**预计时间**: 6-10周

---

## 十、风险与应对

### 10.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| LLM 分析准确率不足 | 高 | 中 | 优化 Prompt，增加示例，调整模型 |
| 外部数据源不稳定 | 中 | 低 | 添加重试机制，缓存数据 |
| 性能不达标 | 中 | 中 | 优化数据库查询，增加缓存 |
| 因子计算逻辑不合理 | 高 | 中 | 回测验证，调整权重 |

### 10.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| 消息召回率不足 | 高 | 中 | 引入向量检索，优化关键词 |
| 题材识别不准确 | 中 | 中 | 完善题材词典，增加人工校验 |
| 因子时效性不足 | 中 | 低 | 增加实时爬取，缩短更新周期 |

---

## 十一、总结

### 11.1 核心价值

```
BettaFish 金融消息因子开发平台的核心价值：

1. 平台化能力 ⭐
   - 因子标准化接口（BaseFactor）
   - 因子注册机制（FactorRegistry）
   - 快速开发新因子（1-2天上线）
   - 因子版本管理与迭代

2. 工程化能力 ⭐
   - 异步任务处理（Celery + Redis）
   - 高并发支持（10+任务并行）
   - 进度实时跟踪（0-100%）
   - 失败自动重试

3. 多源消息整合
   - 国内外新闻（QueryEngine）
   - 多模态内容（MediaEngine）
   - 私有舆情数据（InsightEngine）

4. 智能深度分析
   - Agent 协作（ForumEngine）
   - LLM 深度分析
   - 结构化信息提取

5. 标准化因子输出
   - 情感因子、事件因子、题材因子、舆情因子、时效因子
   - 数值化、可量化
   - 可直接用于量化策略

6. 与现有系统协同
   - 复用基础数据（股票列表、题材列表）
   - 输出标准化因子（供量化系统使用）
   - 职责清晰，松耦合
```

### 11.2 实施路径

```
MVP 阶段（8周）:
├─ Week 1: 环境搭建 + 外部数据适配层
├─ Week 2: 消息获取层改造
├─ Week 3: 消息分析层改造
├─ Week 4: 因子量化层实现（传统方式）
├─ Week 5: 异步架构实现 ⭐
│   ├─ Celery + Redis 环境搭建
│   ├─ 异步任务定义
│   ├─ API 接口实现
│   └─ 进度跟踪机制
├─ Week 6: 因子平台实现 ⭐
│   ├─ BaseFactor 基类
│   ├─ FactorRegistry 注册中心
│   ├─ FactorEngine 计算引擎
│   └─ 6个内置因子
├─ Week 7: 完整流程集成 + 题材热度统计
└─ Week 8: 性能优化 + 测试 + 文档 + 部署

优化阶段（2-4个月）:
├─ 数据同步层（1-2周）
├─ 向量检索（4-6周）
└─ 性能优化

生产阶段（4-6个月）:
└─ LangGraph 重构（6-10周）
```

### 11.3 成功标准

**MVP 成功标准（核心）**:
- ✅ **业务流程验证**：
  - 能够完成单只股票的消息分析
  - 生成标准化的消息因子
  - 因子数据可用于量化分析
  
- ✅ **工程化能力验证**：
  - 支持异步任务提交（API响应 < 100ms）
  - 支持并发处理（10+任务同时运行）
  - 支持批量分析（100+股票）
  - 进度实时跟踪准确
  
- ✅ **平台化能力验证**：
  - 新增因子只需3步（定义、注册、生效）
  - 因子计算性能达标（< 1ms/因子）
  - 因子独立可测试

**长期成功标准**:
- ✅ 消息召回率 > 90%
- ✅ 分析准确率 > 90%
- ✅ 因子有效性（通过回测验证）
- ✅ 与量化系统无缝集成
- ✅ 因子库持续扩展（20+因子）

---

**文档版本**: v4.0 Final  
**最后更新**: 2025-12-02  
**状态**: 已补充异步架构和因子平台设计，待用户确认后开始编码实施

**核心特性**:
- ✅ 因子开发平台化（可扩展）
- ✅ 异步任务处理（高并发）
- ✅ 标准化因子接口（易维护）
- ✅ 完整的MVP实施路径（8周）
