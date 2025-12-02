# MVP 配置需求分析与管理方案

**文档版本**: v1.0  
**创建日期**: 2025-12-02  
**文档类型**: 配置管理分析  
**目标**: 明确MVP配置需求，统一配置管理

---

## 一、当前配置管理现状

### 1.1 配置文件分布

```
BettaFish/
├─ config.py                          # ✅ 主配置文件（统一管理）
├─ .env                               # ✅ 环境变量文件
├─ .env.example                       # ✅ 配置模板
│
├─ QueryEngine/utils/config.py        # ⚠️ 独立配置（部分重复）
├─ InsightEngine/utils/config.py      # ⚠️ 独立配置（部分重复）
├─ MediaEngine/utils/config.py        # ⚠️ 独立配置（部分重复）
├─ ReportEngine/utils/config.py       # ⚠️ 独立配置（部分重复）
└─ MindSpider/config.py               # ⚠️ 独立配置
```

### 1.2 配置管理方式

#### 主配置文件 (`/data/BettaFish/config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 使用 pydantic-settings 统一管理
    # 支持 .env 文件和环境变量
    # 类型安全 + 自动验证
    
    model_config = ConfigDict(
        env_file=ENV_FILE,
        env_prefix="",
        case_sensitive=False,
        extra="allow"
    )

settings = Settings()  # 全局单例
```

**优势**：
- ✅ 统一入口
- ✅ 类型安全
- ✅ 自动从 .env 加载
- ✅ 环境变量覆盖

#### 各Engine独立配置

```python
# QueryEngine/utils/config.py
# InsightEngine/utils/config.py
# MediaEngine/utils/config.py
# ReportEngine/utils/config.py

class Settings(BaseSettings):
    # 每个Engine都有自己的Settings类
    # 从同一个 .env 文件读取
    # 但配置字段有重复
    pass

settings = Settings()  # 各自的单例
```

**问题**：
- ⚠️ 配置字段重复定义
- ⚠️ 多个 Settings 实例
- ⚠️ 维护成本高
- ⚠️ 容易不一致

---

## 二、MVP 配置需求清单

### 2.1 核心配置项

#### A. 数据库配置（PostgreSQL）⭐

```python
# MVP 需要新的 PostgreSQL 数据库
DB_DIALECT: str = "postgresql"
DB_HOST: str = "localhost"
DB_PORT: int = 5432
DB_USER: str = "bettafish_user"
DB_PASSWORD: str = "your_password"
DB_NAME: str = "bettafish_mvp"
DB_CHARSET: str = "utf8mb4"
```

**用途**：
- factor_metadata（因子元数据）
- factor_results（因子结果）
- factor_cached_search_results（搜索缓存）
- factor_cached_analysis_results（分析缓存）

**状态**：✅ 已在主配置文件中定义

---

#### B. Redis 配置 ⭐

```python
# MVP 新增需求：Redis 用于缓存和任务队列
REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379
REDIS_DB: int = 0
REDIS_PASSWORD: Optional[str] = None

# Celery 相关
CELERY_BROKER_URL: str = "redis://localhost:6379/0"
CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
```

**用途**：
- Layer 1 热缓存（搜索结果、分析结果）
- Celery 任务队列
- 任务状态跟踪

**状态**：❌ 未在主配置文件中定义

---

#### C. LLM 配置（Query优化 + 催化分析）⭐

```python
# Query Optimizer LLM（用于搜索查询优化）
QUERY_OPTIMIZER_API_KEY: str
QUERY_OPTIMIZER_BASE_URL: str
QUERY_OPTIMIZER_MODEL_NAME: str

# Catalyst Analyzer LLM（用于催化事件分析）
CATALYST_ANALYZER_API_KEY: str
CATALYST_ANALYZER_BASE_URL: str
CATALYST_ANALYZER_MODEL_NAME: str
```

**用途**：
- Query预处理（关键词提取、同义词扩展）
- 催化事件识别和评分

**状态**：❌ 未在主配置文件中定义（可复用现有LLM配置）

---

#### D. QueryEngine 配置（搜索后端）

```python
# Tavily API（搜索后端）
TAVILY_API_KEY: str

# QueryEngine LLM（如果需要完整QueryEngine）
QUERY_ENGINE_API_KEY: str
QUERY_ENGINE_BASE_URL: str
QUERY_ENGINE_MODEL_NAME: str
```

**用途**：
- 新闻搜索（Tavily API）
- 深度搜索（如果使用完整QueryEngine）

**状态**：✅ 已在主配置文件中定义

---

#### E. 缓存策略配置

```python
# 缓存过期时间
REDIS_CACHE_TTL_SEARCH: int = 3600        # 搜索结果：1小时
REDIS_CACHE_TTL_ANALYSIS: int = 86400     # 分析结果：24小时
POSTGRES_CACHE_TTL_SEARCH: int = 604800   # 搜索结果：7天
POSTGRES_CACHE_TTL_ANALYSIS: int = 0      # 分析结果：永久

# 缓存键前缀
CACHE_KEY_PREFIX_SEARCH: str = "mvp:search:"
CACHE_KEY_PREFIX_ANALYSIS: str = "mvp:analysis:"
```

**用途**：
- 三层缓存策略控制
- 缓存键命名规范

**状态**：❌ 未在主配置文件中定义

---

#### F. 因子计算配置

```python
# 因子计算参数
FACTOR_DEFAULT_DAYS: int = 7              # 默认搜索天数
FACTOR_MIN_NEWS_COUNT: int = 1            # 最小新闻数量
FACTOR_RELEVANCE_THRESHOLD: float = 0.5   # 相关性阈值

# 催化强度权重
CATALYST_WEIGHT_MAJOR: float = 1.0
CATALYST_WEIGHT_NORMAL: float = 0.7
CATALYST_WEIGHT_MINOR: float = 0.4

# 事件数量加成
CATALYST_EVENT_BONUS_RATE: float = 0.05
CATALYST_EVENT_BONUS_MAX: float = 0.2
```

**用途**：
- 因子计算逻辑参数
- 催化强度评估权重

**状态**：❌ 未在主配置文件中定义

---

#### G. Celery 任务配置

```python
# Celery Worker 配置
CELERY_WORKER_CONCURRENCY: int = 4        # 并发数
CELERY_TASK_TIME_LIMIT: int = 600         # 任务超时（秒）
CELERY_TASK_SOFT_TIME_LIMIT: int = 540    # 软超时（秒）

# 任务优先级
CELERY_TASK_DEFAULT_PRIORITY: int = 5
CELERY_TASK_HIGH_PRIORITY: int = 9
CELERY_TASK_LOW_PRIORITY: int = 1
```

**用途**：
- Celery Worker 行为控制
- 任务超时和优先级管理

**状态**：❌ 未在主配置文件中定义

---

### 2.2 配置需求汇总表

| 配置类别 | 配置项数量 | 主配置文件状态 | 优先级 |
|---------|-----------|--------------|--------|
| 数据库配置（PostgreSQL） | 7 | ✅ 已定义 | P0 |
| Redis配置 | 4 | ❌ 缺失 | P0 |
| LLM配置（Query优化） | 3 | ⚠️ 可复用 | P0 |
| LLM配置（催化分析） | 3 | ⚠️ 可复用 | P0 |
| Tavily API | 1 | ✅ 已定义 | P0 |
| 缓存策略配置 | 6 | ❌ 缺失 | P1 |
| 因子计算配置 | 8 | ❌ 缺失 | P1 |
| Celery配置 | 6 | ❌ 缺失 | P0 |
| **总计** | **38** | **8已定义** | - |

---

## 三、配置统一管理方案

### 3.1 推荐方案：扩展主配置文件 ⭐

#### 方案描述

```
在 /data/BettaFish/config.py 中添加 MVP 所需的所有配置项
├─ 保留现有配置（向后兼容）
├─ 添加 Redis 配置
├─ 添加 Celery 配置
├─ 添加 MVP 因子配置
└─ 添加缓存策略配置
```

#### 优势

```
✅ 统一入口：所有配置在一个文件
✅ 类型安全：pydantic 自动验证
✅ 易于维护：修改一处即可
✅ 向后兼容：不影响现有系统
✅ 环境隔离：通过 .env 区分环境
```

#### 实施步骤

**Step 1: 更新 config.py**

```python
# config.py

class Settings(BaseSettings):
    # ========== 现有配置（保留） ==========
    HOST: str = Field("0.0.0.0", ...)
    PORT: int = Field(5000, ...)
    DB_HOST: str = Field("your_db_host", ...)
    # ... 其他现有配置 ...
    
    # ========== MVP 新增配置 ⭐ ==========
    
    # Redis 配置
    REDIS_HOST: str = Field("localhost", description="Redis主机地址")
    REDIS_PORT: int = Field(6379, description="Redis端口")
    REDIS_DB: int = Field(0, description="Redis数据库编号")
    REDIS_PASSWORD: Optional[str] = Field(None, description="Redis密码（可选）")
    
    # Celery 配置
    CELERY_BROKER_URL: str = Field(
        "redis://localhost:6379/0", 
        description="Celery消息代理URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        "redis://localhost:6379/1", 
        description="Celery结果后端URL"
    )
    CELERY_WORKER_CONCURRENCY: int = Field(4, description="Celery并发数")
    CELERY_TASK_TIME_LIMIT: int = Field(600, description="任务超时（秒）")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(540, description="软超时（秒）")
    
    # 缓存策略配置
    REDIS_CACHE_TTL_SEARCH: int = Field(3600, description="搜索结果缓存时间（秒）")
    REDIS_CACHE_TTL_ANALYSIS: int = Field(86400, description="分析结果缓存时间（秒）")
    POSTGRES_CACHE_TTL_SEARCH: int = Field(604800, description="PostgreSQL搜索缓存（秒）")
    CACHE_KEY_PREFIX_SEARCH: str = Field("mvp:search:", description="搜索缓存键前缀")
    CACHE_KEY_PREFIX_ANALYSIS: str = Field("mvp:analysis:", description="分析缓存键前缀")
    
    # 因子计算配置
    FACTOR_DEFAULT_DAYS: int = Field(7, description="默认搜索天数")
    FACTOR_MIN_NEWS_COUNT: int = Field(1, description="最小新闻数量")
    FACTOR_RELEVANCE_THRESHOLD: float = Field(0.5, description="相关性阈值")
    CATALYST_WEIGHT_MAJOR: float = Field(1.0, description="重大催化权重")
    CATALYST_WEIGHT_NORMAL: float = Field(0.7, description="一般催化权重")
    CATALYST_WEIGHT_MINOR: float = Field(0.4, description="轻微催化权重")
    CATALYST_EVENT_BONUS_RATE: float = Field(0.05, description="事件数量加成率")
    CATALYST_EVENT_BONUS_MAX: float = Field(0.2, description="事件加成上限")
    
    # MVP LLM 配置（可复用现有配置，也可单独定义）
    # 选项1：复用 QUERY_ENGINE_* 用于Query优化
    # 选项2：复用 INSIGHT_ENGINE_* 用于催化分析
    # 选项3：新增独立配置
    MVP_QUERY_OPTIMIZER_API_KEY: Optional[str] = Field(
        None, 
        description="MVP Query优化LLM API Key（为空则使用QUERY_ENGINE_API_KEY）"
    )
    MVP_CATALYST_ANALYZER_API_KEY: Optional[str] = Field(
        None, 
        description="MVP 催化分析LLM API Key（为空则使用INSIGHT_ENGINE_API_KEY）"
    )
```

**Step 2: 更新 .env.example**

```bash
# .env.example

# ========== MVP 配置 ⭐ ==========

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Celery 配置
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
CELERY_WORKER_CONCURRENCY=4
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_SOFT_TIME_LIMIT=540

# 缓存策略
REDIS_CACHE_TTL_SEARCH=3600
REDIS_CACHE_TTL_ANALYSIS=86400
POSTGRES_CACHE_TTL_SEARCH=604800

# 因子计算参数
FACTOR_DEFAULT_DAYS=7
FACTOR_MIN_NEWS_COUNT=1
FACTOR_RELEVANCE_THRESHOLD=0.5
CATALYST_WEIGHT_MAJOR=1.0
CATALYST_WEIGHT_NORMAL=0.7
CATALYST_WEIGHT_MINOR=0.4
CATALYST_EVENT_BONUS_RATE=0.05
CATALYST_EVENT_BONUS_MAX=0.2

# MVP LLM（可选，为空则复用现有配置）
MVP_QUERY_OPTIMIZER_API_KEY=
MVP_CATALYST_ANALYZER_API_KEY=
```

**Step 3: MVP 代码中使用统一配置**

```python
# mvp/engines/query_optimizer.py

from config import settings  # 导入主配置

class QueryOptimizer:
    def __init__(self):
        # 优先使用 MVP 专用配置，否则回退到 QUERY_ENGINE 配置
        api_key = settings.MVP_QUERY_OPTIMIZER_API_KEY or settings.QUERY_ENGINE_API_KEY
        base_url = settings.QUERY_ENGINE_BASE_URL
        model_name = settings.QUERY_ENGINE_MODEL_NAME
        
        self.llm_client = LLMClient(
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
```

```python
# mvp/cache/redis_cache.py

from config import settings

class RedisCache:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
        
        self.search_ttl = settings.REDIS_CACHE_TTL_SEARCH
        self.analysis_ttl = settings.REDIS_CACHE_TTL_ANALYSIS
```

```python
# mvp/celery_app.py

from config import settings
from celery import Celery

app = Celery(
    'mvp_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

app.conf.update(
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY
)
```

---

### 3.2 Engine 独立配置的处理

#### 问题

```
各Engine有独立的 config.py，导致：
- 配置重复定义
- 维护成本高
- 容易不一致
```

#### 解决方案

**选项A：保持现状（推荐）⭐**

```
理由：
- 各Engine可以独立运行
- 不影响现有架构
- MVP 使用主配置即可

实施：
- MVP 只使用主配置文件
- Engine 配置保持不变
- 逐步迁移（可选）
```

**选项B：统一配置（长期目标）**

```
理由：
- 彻底消除重复
- 统一维护入口
- 降低复杂度

实施：
- 各Engine从主配置导入
- 移除独立 config.py
- 需要大量重构
```

**推荐**：选项A（保持现状），MVP 使用主配置即可。

---

## 四、配置管理最佳实践

### 4.1 配置分层

```
Layer 1: 默认配置（config.py 中的 Field 默认值）
Layer 2: .env 文件配置（开发环境）
Layer 3: 环境变量配置（生产环境）

优先级：环境变量 > .env 文件 > 默认值
```

### 4.2 敏感信息管理

```
✅ 使用 .env 文件存储敏感信息
✅ .env 文件加入 .gitignore
✅ 提供 .env.example 作为模板
❌ 不要在代码中硬编码密钥
❌ 不要提交 .env 到版本控制
```

### 4.3 配置验证

```python
# config.py

from pydantic import validator

class Settings(BaseSettings):
    REDIS_PORT: int = Field(6379, description="Redis端口")
    
    @validator('REDIS_PORT')
    def validate_redis_port(cls, v):
        if not (1 <= v <= 65535):
            raise ValueError('Redis端口必须在1-65535之间')
        return v
    
    @validator('FACTOR_RELEVANCE_THRESHOLD')
    def validate_threshold(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError('相关性阈值必须在0-1之间')
        return v
```

### 4.4 配置文档化

```python
# 每个配置项都应该有清晰的 description

REDIS_HOST: str = Field(
    "localhost", 
    description="Redis主机地址，用于缓存和任务队列"
)

FACTOR_DEFAULT_DAYS: int = Field(
    7, 
    description="默认搜索天数，用于催化因子计算时的新闻搜索范围"
)
```

---

## 五、MVP 配置检查清单

### 5.1 必需配置（P0）

- [ ] PostgreSQL 数据库连接信息
  - [ ] DB_HOST
  - [ ] DB_PORT
  - [ ] DB_USER
  - [ ] DB_PASSWORD
  - [ ] DB_NAME
  - [ ] DB_DIALECT=postgresql

- [ ] Redis 连接信息
  - [ ] REDIS_HOST
  - [ ] REDIS_PORT
  - [ ] REDIS_DB
  - [ ] REDIS_PASSWORD（可选）

- [ ] Celery 配置
  - [ ] CELERY_BROKER_URL
  - [ ] CELERY_RESULT_BACKEND
  - [ ] CELERY_WORKER_CONCURRENCY

- [ ] Tavily API
  - [ ] TAVILY_API_KEY

- [ ] LLM 配置（至少一个）
  - [ ] QUERY_ENGINE_API_KEY（用于Query优化）
  - [ ] INSIGHT_ENGINE_API_KEY（用于催化分析）

### 5.2 推荐配置（P1）

- [ ] 缓存策略
  - [ ] REDIS_CACHE_TTL_SEARCH
  - [ ] REDIS_CACHE_TTL_ANALYSIS
  - [ ] POSTGRES_CACHE_TTL_SEARCH

- [ ] 因子计算参数
  - [ ] FACTOR_DEFAULT_DAYS
  - [ ] FACTOR_RELEVANCE_THRESHOLD
  - [ ] CATALYST_WEIGHT_*

### 5.3 可选配置（P2）

- [ ] Celery 高级配置
  - [ ] CELERY_TASK_TIME_LIMIT
  - [ ] CELERY_TASK_SOFT_TIME_LIMIT

- [ ] 缓存键前缀
  - [ ] CACHE_KEY_PREFIX_SEARCH
  - [ ] CACHE_KEY_PREFIX_ANALYSIS

---

## 六、总结与建议

### 6.1 当前状态

```
✅ 主配置文件已建立（config.py）
✅ 支持 .env 文件和环境变量
✅ 类型安全（pydantic-settings）
⚠️ MVP 所需配置部分缺失
⚠️ Engine 配置存在重复
```

### 6.2 MVP 实施建议

**短期（Week 1）**：
1. ✅ 在主配置文件中添加 MVP 所需配置
2. ✅ 更新 .env.example
3. ✅ MVP 代码统一使用主配置

**中期（Week 2-4）**：
1. ✅ 验证配置完整性
2. ✅ 添加配置验证逻辑
3. ✅ 完善配置文档

**长期（可选）**：
1. ⚠️ 考虑统一 Engine 配置
2. ⚠️ 配置中心化管理
3. ⚠️ 配置热更新支持

### 6.3 配置管理原则

```
1. 统一入口：所有配置通过主配置文件
2. 类型安全：使用 pydantic 验证
3. 环境隔离：开发/测试/生产环境分离
4. 敏感保护：密钥不进版本控制
5. 文档完善：每个配置项有清晰说明
```

---

**配置统一管理是 MVP 成功的基础！** 🔧
