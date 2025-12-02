"""
Celery 应用配置

用于异步任务处理
"""

from celery import Celery
from loguru import logger

from ..utils.config import settings


# 创建 Celery 应用
app = Celery(
    'taurus_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['taurus.tasks.factor_tasks']
)

# Celery 配置
app.conf.update(
    # 任务配置
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    
    # 任务时间限制
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    
    # Worker 配置
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    
    # 结果配置
    result_expires=3600,  # 结果保留1小时
    result_backend_transport_options={'master_name': 'mymaster'},
    
    # 任务路由
    task_routes={
        'taurus.tasks.factor_tasks.calculate_factor_task': {'queue': 'factor'},
        'taurus.tasks.factor_tasks.batch_calculate_factors_task': {'queue': 'batch'},
    },
    
    # 任务优先级
    task_default_priority=5,
    task_queue_max_priority=10,
    
    # 重试配置
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

logger.info("Celery 应用初始化完成")


if __name__ == '__main__':
    # 启动 Worker
    # celery -A taurus.tasks.celery_app worker --loglevel=info
    app.start()
