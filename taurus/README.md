# Taurus - BettaFish MVP 搜索引擎催化因子系统

## 项目概述

Taurus 是 BettaFish 金融消息因子分析系统的 MVP 实现，专注于"搜索引擎催化因子"的开发和验证。

## 目录结构

```
taurus/
├── engines/              # 核心引擎 ✅
│   ├── query_optimizer.py       # Query预处理（LLM优化）
│   ├── query_engine_wrapper.py  # QueryEngine包装器
│   └── catalyst_analyzer.py     # 催化分析引擎（LLM分析）
├── models/               # 数据模型 ✅
│   ├── factor.py                # 因子基类和SearchEngineCatalystFactor
│   └── schemas.py               # Pydantic数据结构
├── database/             # 数据库 ✅
│   ├── models.py                # SQLAlchemy模型
│   └── init_db.py               # 数据库初始化
├── cache/                # 缓存层 🚧
│   ├── redis_cache.py           # Redis缓存
│   └── postgres_cache.py        # PostgreSQL缓存
├── tasks/                # 异步任务 🚧
│   ├── celery_app.py            # Celery应用
│   └── factor_tasks.py          # 因子计算任务
├── api/                  # API接口 🚧
│   ├── routes.py                # Flask路由
│   └── schemas.py               # API数据结构
├── utils/                # 工具函数 ✅
│   └── config.py                # MVP配置
└── tests/                # 测试 ⏳
```

## 已完成模块

### ✅ 配置模块 (`utils/config.py`)
- 从 .env 读取配置
- 支持数据库、Redis、Celery、LLM等配置
- 提供 `get_database_url()` 和 `get_redis_url()` 工具函数

### ✅ 数据库模块 (`database/`)
- **models.py**: 定义4个核心表
  - `factor_metadata`: 因子元数据
  - `factor_results`: 因子结果（通用设计，支持JSONB）
  - `factor_cached_search_results`: 搜索缓存
  - `factor_cached_analysis_results`: 分析缓存
- **init_db.py**: 数据库初始化脚本

### ✅ Query优化器 (`engines/query_optimizer.py`)
- 使用LLM优化搜索查询
- 提取核心关键词
- 扩展同义词
- 添加行业术语
- Fallback机制

### ✅ QueryEngine包装器 (`engines/query_engine_wrapper.py`)
- 封装Tavily搜索API
- 集成Query优化
- 支持多种时间范围（1天、7天、自定义）
- 格式化搜索结果

### ✅ 催化分析引擎 (`engines/catalyst_analyzer.py`)
- 使用LLM分析新闻催化作用
- 评估相关性（0-1）
- 识别催化类型（positive/negative/neutral）
- 评估催化强度（major/normal/minor）
- 提取催化事件

### ✅ 因子模型 (`models/factor.py`)
- `BaseFactor`: 因子基类
- `SearchEngineCatalystFactor`: 搜索引擎催化因子
- 因子注册表和工厂函数

### ✅ 数据结构 (`models/schemas.py`)
- Pydantic模型定义
- 数据验证
- 序列化/反序列化

## 已完成所有核心模块 ✅

### ✅ 缓存层 (`cache/`)
- Redis热缓存（1小时）
- PostgreSQL温缓存（7天）
- 缓存键生成（MD5哈希）
- 缓存过期管理
- 缓存统计

### ✅ 异步任务 (`tasks/`)
- Celery应用配置
- 单个因子计算任务
- 批量处理任务
- 进度跟踪
- 错误处理

### ✅ API接口 (`api/`)
- Flask路由（8个端点）
- 任务提交（单个/批量）
- 状态查询
- 结果获取
- 元数据查询
- 历史结果查询

### ⏳ 测试 (`tests/`)
- 待开发

## 快速开始

### 1. 安装依赖

```bash
pip install sqlalchemy psycopg2-binary redis celery openai loguru pydantic pydantic-settings
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置：

```bash
# 数据库
DB_DIALECT=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_USER=bettafish_user
DB_PASSWORD=your_password
DB_NAME=bettafish_mvp

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

# LLM
QUERY_ENGINE_API_KEY=your_api_key
QUERY_ENGINE_BASE_URL=https://api.deepseek.com
QUERY_ENGINE_MODEL_NAME=deepseek-chat

INSIGHT_ENGINE_API_KEY=your_api_key
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=moonshot-v1-8k

# Tavily
TAVILY_API_KEY=your_tavily_key
```

### 3. 初始化数据库

```bash
cd /data/BettaFish
python -m taurus.database.init_db
```

### 4. 测试模块

```bash
# 测试Query优化器
python -m taurus.engines.query_optimizer

# 测试QueryEngine包装器
python -m taurus.engines.query_engine_wrapper

# 测试催化分析器
python -m taurus.engines.catalyst_analyzer

# 测试因子计算
python -m taurus.models.factor
```

## 开发进度

- [x] Week 1: 环境搭建 + 基础架构 ✅
  - [x] 配置模块
  - [x] 数据库模型
  - [x] 数据库初始化
- [x] Week 2: Query预处理 + QueryEngine集成 ✅
  - [x] Query优化器
  - [x] QueryEngine包装器
  - [x] 因子模型
- [x] Week 3: LLM催化分析引擎 ✅
  - [x] 催化分析器
  - [x] Prompt设计
  - [x] 数据结构定义
- [x] Week 4: 缓存层实现 ✅
  - [x] Redis缓存
  - [x] PostgreSQL缓存
  - [x] 缓存策略
- [x] Week 5: 异步任务系统 ✅
  - [x] Celery配置
  - [x] 因子计算任务
  - [x] 进度跟踪
- [x] Week 6: API接口开发 ✅
  - [x] Flask路由
  - [x] 任务管理
  - [x] 结果查询
- [x] Week 7-8: 文档与脚本 ✅
  - [x] API文档
  - [x] 启动脚本
  - [x] 用户手册
- [ ] 测试与优化 ⏳
  - [ ] 单元测试
  - [ ] 集成测试
  - [ ] 性能优化

## 技术栈

- **数据库**: PostgreSQL
- **缓存**: Redis
- **任务队列**: Celery
- **Web框架**: Flask
- **ORM**: SQLAlchemy
- **数据验证**: Pydantic
- **LLM客户端**: OpenAI SDK
- **搜索API**: Tavily
- **日志**: Loguru

## 许可证

MIT License
