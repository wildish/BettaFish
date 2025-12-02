# Taurus MVP 快速开始

5分钟快速启动 Taurus 搜索引擎催化因子系统。

---

## 📋 前置要求

- Python 3.8+
- PostgreSQL 12+
- Redis 5.0+

---

## 🚀 快速启动（5步）

### Step 1: 安装依赖

```bash
cd /data/BettaFish
pip install -r taurus/requirements.txt
```

### Step 2: 配置环境变量

```bash
# 编辑 .env 文件，配置以下必需项：

# 数据库
DB_HOST=localhost
DB_PORT=5432
DB_USER=bettafish_user
DB_PASSWORD=your_password
DB_NAME=bettafish_mvp

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# LLM API Keys
QUERY_ENGINE_API_KEY=your_deepseek_key
QUERY_ENGINE_BASE_URL=https://api.deepseek.com
QUERY_ENGINE_MODEL_NAME=deepseek-chat

INSIGHT_ENGINE_API_KEY=your_moonshot_key
INSIGHT_ENGINE_BASE_URL=https://api.moonshot.cn/v1
INSIGHT_ENGINE_MODEL_NAME=moonshot-v1-8k

# Tavily API
TAVILY_API_KEY=your_tavily_key
```

### Step 3: 初始化数据库

```bash
bash taurus/scripts/init_database.sh
```

### Step 4: 启动服务

```bash
# 终端1：启动 Redis
redis-server

# 终端2：启动 Celery Worker
bash taurus/scripts/start_worker.sh

# 终端3：启动 API 服务
bash taurus/scripts/start_api.sh
```

### Step 5: 测试

```bash
# 健康检查
curl http://localhost:5001/api/taurus/health

# 提交任务
curl -X POST http://localhost:5001/api/taurus/factors/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "search_topic": "提价",
    "sector": "白酒",
    "days": 7
  }'

# 查询任务状态（替换 <task_id>）
curl http://localhost:5001/api/taurus/tasks/<task_id>
```

---

## 📖 详细文档

- **API使用指南**: `taurus/API_GUIDE.md`
- **项目文档**: `taurus/README.md`
- **完成报告**: `docs/02/MVP_COMPLETION_REPORT.md`

---

## 🎯 核心功能

1. **Query优化**: LLM优化搜索查询
2. **新闻搜索**: Tavily API搜索相关新闻
3. **催化分析**: LLM分析新闻催化作用
4. **因子计算**: 量化催化强度（-1到1）
5. **三层缓存**: Redis + PostgreSQL
6. **异步处理**: Celery任务队列
7. **REST API**: 8个API端点

---

## 💡 使用示例

### Python

```python
import requests

# 提交任务
response = requests.post('http://localhost:5001/api/taurus/factors/calculate', json={
    'stock_code': '600519',
    'stock_name': '贵州茅台',
    'search_topic': '提价',
    'sector': '白酒',
    'days': 7
})

task_id = response.json()['task_id']
print(f"任务ID: {task_id}")

# 查询状态
status = requests.get(f'http://localhost:5001/api/taurus/tasks/{task_id}').json()
print(f"状态: {status['status']}")
```

---

## ⚠️ 常见问题

### Q: 数据库连接失败？
A: 检查 PostgreSQL 是否启动，配置是否正确。

### Q: Redis 连接失败？
A: 检查 Redis 是否启动：`redis-cli ping`

### Q: Celery Worker 无法启动？
A: 检查 Redis 连接，确保在项目根目录运行。

### Q: API 返回 500 错误？
A: 检查日志，确认 LLM API Key 是否正确。

---

## 📞 技术支持

- 项目文档：`/data/BettaFish/taurus/README.md`
- API文档：`/data/BettaFish/taurus/API_GUIDE.md`
- 完成报告：`/data/BettaFish/docs/02/MVP_COMPLETION_REPORT.md`

---

**祝你使用愉快！** 🎉
