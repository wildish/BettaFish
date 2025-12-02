#!/bin/bash

# Taurus API 服务启动脚本

echo "=========================================="
echo "启动 Taurus API 服务"
echo "=========================================="

# 设置工作目录
cd /data/BettaFish

# 启动 Flask 应用
python -m taurus.app

echo "API 服务已停止"
