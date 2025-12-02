#!/bin/bash

# Taurus Celery Worker 启动脚本

echo "=========================================="
echo "启动 Taurus Celery Worker"
echo "=========================================="

# 设置工作目录
cd /data/BettaFish

# 启动 Worker
celery -A taurus.tasks.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --queues=factor,batch \
    --max-tasks-per-child=100 \
    --time-limit=600 \
    --soft-time-limit=540

echo "Worker 已停止"
