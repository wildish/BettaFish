"""
Taurus - BettaFish MVP 搜索引擎催化因子系统

目录结构：
├── engines/          # 核心引擎
│   ├── query_optimizer.py      # Query预处理
│   ├── query_engine_wrapper.py # QueryEngine包装器
│   └── catalyst_analyzer.py    # 催化分析引擎
├── models/           # 数据模型
│   ├── factor.py               # 因子基类和实现
│   └── schemas.py              # 数据结构定义
├── cache/            # 缓存层
│   ├── redis_cache.py          # Redis缓存
│   └── postgres_cache.py       # PostgreSQL缓存
├── tasks/            # 异步任务
│   ├── celery_app.py           # Celery应用
│   └── factor_tasks.py         # 因子计算任务
├── api/              # API接口
│   ├── routes.py               # Flask路由
│   └── schemas.py              # API数据结构
├── database/         # 数据库
│   ├── models.py               # SQLAlchemy模型
│   └── init_db.py              # 数据库初始化
├── utils/            # 工具函数
│   └── config.py               # MVP配置（从主config读取）
└── tests/            # 测试
"""

__version__ = "0.1.0"
__author__ = "BettaFish Team"
