"""
Taurus Flask 应用

主应用入口，提供 API 服务
"""

from flask import Flask, jsonify
from flask_cors import CORS
from loguru import logger

from .api import api_bp
from .utils.config import settings
from .database import initialize_database


def create_app():
    """
    创建 Flask 应用
    
    Returns:
        Flask: Flask 应用实例
    """
    app = Flask(__name__)
    
    # CORS 配置
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 配置
    app.config['JSON_AS_ASCII'] = False
    app.config['JSON_SORT_KEYS'] = False
    
    # 注册 Blueprint
    app.register_blueprint(api_bp)
    
    # 根路由
    @app.route('/')
    def index():
        return jsonify({
            'service': 'Taurus MVP',
            'version': '0.1.0',
            'description': 'BettaFish 搜索引擎催化因子系统',
            'endpoints': {
                'health': '/api/taurus/health',
                'calculate_factor': 'POST /api/taurus/factors/calculate',
                'batch_calculate': 'POST /api/taurus/factors/batch',
                'task_status': 'GET /api/taurus/tasks/<task_id>',
                'task_result': 'GET /api/taurus/tasks/<task_id>/result',
                'factor_metadata': 'GET /api/taurus/factors/metadata',
                'factor_results': 'GET /api/taurus/factors/results'
            }
        })
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'not_found',
            'message': '资源不存在'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"服务器错误: {str(error)}")
        return jsonify({
            'error': 'internal_error',
            'message': '服务器内部错误'
        }), 500
    
    logger.info("Taurus Flask 应用创建成功")
    
    return app


def init_app():
    """
    初始化应用
    - 初始化数据库
    - 创建 Flask 应用
    """
    logger.info("=" * 50)
    logger.info("初始化 Taurus MVP 应用")
    logger.info("=" * 50)
    
    # 初始化数据库
    try:
        logger.info("初始化数据库...")
        initialize_database()
        logger.success("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        logger.warning("应用将继续运行，但数据库功能可能不可用")
    
    # 创建 Flask 应用
    app = create_app()
    
    logger.info("=" * 50)
    logger.info("Taurus MVP 应用初始化完成")
    logger.info(f"API 地址: http://{settings.API_HOST}:{settings.API_PORT}")
    logger.info("=" * 50)
    
    return app


if __name__ == '__main__':
    # 初始化并运行应用
    app = init_app()
    
    # 运行 Flask 应用
    app.run(
        host=settings.API_HOST,
        port=settings.API_PORT,
        debug=settings.API_DEBUG
    )
