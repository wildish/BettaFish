# Taurus API 使用指南

## 目录

1. [快速开始](#快速开始)
2. [API 端点](#api-端点)
3. [使用示例](#使用示例)
4. [错误处理](#错误处理)

---

## 快速开始

### 1. 启动服务

```bash
# 1. 初始化数据库
bash taurus/scripts/init_database.sh

# 2. 启动 Redis
redis-server

# 3. 启动 Celery Worker
bash taurus/scripts/start_worker.sh

# 4. 启动 API 服务
bash taurus/scripts/start_api.sh
```

### 2. 测试连接

```bash
curl http://localhost:5001/
```

---

## API 端点

### 1. 健康检查

**GET** `/api/taurus/health`

检查服务是否正常运行。

**响应示例**：
```json
{
    "status": "healthy",
    "service": "Taurus MVP",
    "timestamp": "2025-12-02T10:00:00"
}
```

---

### 2. 提交因子计算任务

**POST** `/api/taurus/factors/calculate`

提交单个因子计算任务。

**请求体**：
```json
{
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "search_topic": "提价",
    "sector": "白酒",
    "days": 7
}
```

**参数说明**：
- `stock_code` (必需): 股票代码
- `stock_name` (必需): 股票名称
- `search_topic` (必需): 搜索主题
- `sector` (可选): 板块
- `days` (可选): 搜索天数，默认7

**响应示例**：
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "PENDING",
    "message": "任务已提交",
    "request": {
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "search_topic": "提价"
    }
}
```

---

### 3. 批量提交任务

**POST** `/api/taurus/factors/batch`

批量提交因子计算任务。

**请求体**：
```json
{
    "requests": [
        {
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "search_topic": "提价",
            "sector": "白酒",
            "days": 7
        },
        {
            "stock_code": "300750",
            "stock_name": "宁德时代",
            "search_topic": "补贴政策",
            "sector": "新能源",
            "days": 7
        }
    ]
}
```

**响应示例**：
```json
{
    "task_id": "batch-abc123",
    "status": "PENDING",
    "message": "批量任务已提交",
    "total": 2
}
```

---

### 4. 查询任务状态

**GET** `/api/taurus/tasks/<task_id>`

查询任务执行状态。

**响应示例（进行中）**：
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "PROGRESS",
    "progress": 50,
    "message": "分析催化"
}
```

**响应示例（完成）**：
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "SUCCESS",
    "progress": 100,
    "result": {
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "search_topic": "提价",
        "factor_value": 0.756,
        "news_count": 5,
        "analysis": {
            "relevance_score": 0.9,
            "catalyst_type": "positive",
            "catalyst_strength": "major",
            "catalyst_events": ["提价18%", "经销商确认", "分析师上调目标价"]
        },
        "completed_at": "2025-12-02T10:05:00"
    },
    "message": "任务完成"
}
```

**响应示例（失败）**：
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "FAILURE",
    "error": "API key invalid",
    "message": "任务失败"
}
```

---

### 5. 获取任务结果

**GET** `/api/taurus/tasks/<task_id>/result`

获取已完成任务的结果。

**响应示例**：
```json
{
    "task_id": "abc123-def456-ghi789",
    "status": "SUCCESS",
    "result": {
        "stock_code": "600519",
        "stock_name": "贵州茅台",
        "factor_value": 0.756,
        "news_count": 5,
        "analysis": {...}
    }
}
```

---

### 6. 获取因子元数据

**GET** `/api/taurus/factors/metadata`

获取所有因子的元数据信息。

**响应示例**：
```json
{
    "total": 1,
    "factors": [
        {
            "id": 1,
            "factor_name": "search_engine_catalyst_factor",
            "factor_category": "catalyst",
            "factor_version": "1.0.0",
            "description": "基于搜索引擎新闻的催化因子",
            "output_range_min": -1.0,
            "output_range_max": 1.0,
            "config": {
                "default_days": 7,
                "catalyst_weights": {...}
            },
            "created_at": "2025-12-02T10:00:00",
            "updated_at": "2025-12-02T10:00:00"
        }
    ]
}
```

---

### 7. 查询因子结果

**GET** `/api/taurus/factors/results`

查询历史因子结果。

**查询参数**：
- `stock_code` (可选): 股票代码
- `factor_name` (可选): 因子名称，默认 "search_engine_catalyst_factor"
- `start_date` (可选): 开始日期，格式 YYYY-MM-DD
- `end_date` (可选): 结束日期，格式 YYYY-MM-DD
- `limit` (可选): 返回数量限制，默认100
- `offset` (可选): 偏移量，默认0

**请求示例**：
```bash
GET /api/taurus/factors/results?stock_code=600519&limit=10
```

**响应示例**：
```json
{
    "total": 25,
    "limit": 10,
    "offset": 0,
    "results": [
        {
            "id": 1,
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "factor_metadata_id": 1,
            "factor_date": "2025-12-02T00:00:00",
            "factor_value": 0.756,
            "factor_attributes": {
                "search_topic": "提价",
                "sector": "白酒",
                "news_count": 5,
                "catalyst_type": "positive",
                "catalyst_strength": "major",
                "catalyst_events": ["提价18%", "..."]
            },
            "created_at": "2025-12-02T10:05:00",
            "updated_at": "2025-12-02T10:05:00"
        }
    ]
}
```

---

### 8. 获取因子结果详情

**GET** `/api/taurus/factors/results/<result_id>`

获取单个因子结果的详细信息。

**响应示例**：
```json
{
    "id": 1,
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "factor_metadata_id": 1,
    "factor_date": "2025-12-02T00:00:00",
    "factor_value": 0.756,
    "factor_attributes": {
        "search_topic": "提价",
        "sector": "白酒",
        "days": 7,
        "news_count": 5,
        "relevance_score": 0.9,
        "catalyst_type": "positive",
        "catalyst_strength": "major",
        "catalyst_events": ["提价18%", "经销商确认", "分析师上调目标价"],
        "reasoning": "新闻高度相关，茅台提价是重大利好催化",
        "news_summary": "贵州茅台宣布产品提价，幅度超市场预期"
    },
    "created_at": "2025-12-02T10:05:00",
    "updated_at": "2025-12-02T10:05:00"
}
```

---

## 使用示例

### Python 示例

```python
import requests
import time

# 1. 提交任务
response = requests.post('http://localhost:5001/api/taurus/factors/calculate', json={
    'stock_code': '600519',
    'stock_name': '贵州茅台',
    'search_topic': '提价',
    'sector': '白酒',
    'days': 7
})

task_id = response.json()['task_id']
print(f"任务ID: {task_id}")

# 2. 轮询任务状态
while True:
    status_response = requests.get(f'http://localhost:5001/api/taurus/tasks/{task_id}')
    status_data = status_response.json()
    
    print(f"状态: {status_data['status']}")
    
    if status_data['status'] == 'SUCCESS':
        print(f"因子值: {status_data['result']['factor_value']}")
        break
    elif status_data['status'] == 'FAILURE':
        print(f"失败: {status_data['error']}")
        break
    
    time.sleep(5)

# 3. 查询历史结果
results_response = requests.get('http://localhost:5001/api/taurus/factors/results', params={
    'stock_code': '600519',
    'limit': 10
})

results = results_response.json()
print(f"找到 {results['total']} 条历史记录")
```

### cURL 示例

```bash
# 1. 提交任务
curl -X POST http://localhost:5001/api/taurus/factors/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "600519",
    "stock_name": "贵州茅台",
    "search_topic": "提价",
    "sector": "白酒",
    "days": 7
  }'

# 2. 查询任务状态
curl http://localhost:5001/api/taurus/tasks/<task_id>

# 3. 查询历史结果
curl "http://localhost:5001/api/taurus/factors/results?stock_code=600519&limit=10"
```

---

## 错误处理

### 错误响应格式

```json
{
    "error": "error_code",
    "message": "错误描述",
    "details": {...}  // 可选
}
```

### 常见错误码

| 错误码 | HTTP状态码 | 说明 |
|--------|-----------|------|
| `validation_error` | 400 | 请求数据格式错误 |
| `not_found` | 404 | 资源不存在 |
| `internal_error` | 500 | 服务器内部错误 |

### 错误示例

**验证错误**：
```json
{
    "error": "validation_error",
    "message": "请求数据格式错误",
    "details": [
        {
            "loc": ["stock_code"],
            "msg": "field required",
            "type": "value_error.missing"
        }
    ]
}
```

**资源不存在**：
```json
{
    "error": "not_found",
    "message": "结果ID 999 不存在"
}
```

---

## 最佳实践

1. **异步处理**：因子计算是异步的，提交任务后应轮询状态
2. **批量处理**：大量任务使用批量接口，提高效率
3. **缓存利用**：相同参数的请求会使用缓存，加快响应
4. **错误重试**：任务失败时可以重新提交
5. **结果持久化**：所有结果都保存在数据库中，可随时查询

---

## 技术支持

如有问题，请查看：
- 项目文档：`/data/BettaFish/taurus/README.md`
- MVP计划：`/data/BettaFish/docs/02/MVP_PLAN.md`
- 配置分析：`/data/BettaFish/docs/02/MVP_CONFIG_ANALYSIS.md`
