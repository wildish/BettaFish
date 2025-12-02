"""
Taurus API 路由

提供因子计算的 REST API 接口
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from loguru import logger
from celery.result import AsyncResult

from ..tasks import app as celery_app, calculate_factor_task, batch_calculate_factors_task
from ..models.schemas import FactorRequest, BatchFactorRequest, FactorMetadataInfo, FactorResultInfo
from ..database import get_db, FactorMetadata, FactorResult
from pydantic import ValidationError


# 创建 Blueprint
api_bp = Blueprint('taurus_api', __name__, url_prefix='/api/taurus')


@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    健康检查
    
    Returns:
        JSON: 服务状态
    """
    return jsonify({
        'status': 'healthy',
        'service': 'Taurus MVP',
        'timestamp': datetime.utcnow().isoformat()
    })


@api_bp.route('/factors/calculate', methods=['POST'])
def calculate_factor():
    """
    提交因子计算任务
    
    Request Body:
        {
            "stock_code": "600519",
            "stock_name": "贵州茅台",
            "search_topic": "提价",
            "sector": "白酒",  // optional
            "days": 7  // optional
        }
    
    Returns:
        JSON: 任务信息
        {
            "task_id": "xxx",
            "status": "PENDING",
            "message": "任务已提交"
        }
    """
    try:
        # 验证请求数据
        data = request.get_json()
        factor_request = FactorRequest(**data)
        
        # 提交异步任务
        task = calculate_factor_task.delay(
            stock_code=factor_request.stock_code,
            stock_name=factor_request.stock_name,
            search_topic=factor_request.search_topic,
            sector=factor_request.sector,
            days=factor_request.days,
            use_cache=True
        )
        
        logger.info(f"因子计算任务已提交 - Task ID: {task.id}, 股票: {factor_request.stock_name}")
        
        return jsonify({
            'task_id': task.id,
            'status': task.status,
            'message': '任务已提交',
            'request': {
                'stock_code': factor_request.stock_code,
                'stock_name': factor_request.stock_name,
                'search_topic': factor_request.search_topic
            }
        }), 202
        
    except ValidationError as e:
        logger.warning(f"请求数据验证失败: {e.errors()}")
        return jsonify({
            'error': 'validation_error',
            'message': '请求数据格式错误',
            'details': e.errors()
        }), 400
        
    except Exception as e:
        logger.error(f"提交任务失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@api_bp.route('/factors/batch', methods=['POST'])
def batch_calculate_factors():
    """
    批量提交因子计算任务
    
    Request Body:
        {
            "requests": [
                {
                    "stock_code": "600519",
                    "stock_name": "贵州茅台",
                    "search_topic": "提价",
                    "sector": "白酒",
                    "days": 7
                },
                ...
            ]
        }
    
    Returns:
        JSON: 批量任务信息
    """
    try:
        # 验证请求数据
        data = request.get_json()
        batch_request = BatchFactorRequest(**data)
        
        # 转换为字典列表
        requests_data = [
            {
                'stock_code': req.stock_code,
                'stock_name': req.stock_name,
                'search_topic': req.search_topic,
                'sector': req.sector,
                'days': req.days
            }
            for req in batch_request.requests
        ]
        
        # 提交批量任务
        task = batch_calculate_factors_task.delay(requests_data)
        
        logger.info(f"批量因子计算任务已提交 - Task ID: {task.id}, 数量: {len(requests_data)}")
        
        return jsonify({
            'task_id': task.id,
            'status': task.status,
            'message': '批量任务已提交',
            'total': len(requests_data)
        }), 202
        
    except ValidationError as e:
        logger.warning(f"批量请求数据验证失败: {e.errors()}")
        return jsonify({
            'error': 'validation_error',
            'message': '请求数据格式错误',
            'details': e.errors()
        }), 400
        
    except Exception as e:
        logger.error(f"提交批量任务失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@api_bp.route('/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    查询任务状态
    
    Args:
        task_id: 任务ID
    
    Returns:
        JSON: 任务状态
        {
            "task_id": "xxx",
            "status": "SUCCESS",
            "progress": 100,
            "result": {...}
        }
    """
    try:
        # 获取任务结果
        task_result = AsyncResult(task_id, app=celery_app)
        
        response = {
            'task_id': task_id,
            'status': task_result.status
        }
        
        # 根据状态返回不同信息
        if task_result.status == 'PENDING':
            response['message'] = '任务等待中'
            
        elif task_result.status == 'PROGRESS':
            response['progress'] = task_result.info.get('progress', 0)
            response['message'] = task_result.info.get('status', '处理中')
            
        elif task_result.status == 'SUCCESS':
            response['progress'] = 100
            response['result'] = task_result.result
            response['message'] = '任务完成'
            
        elif task_result.status == 'FAILURE':
            response['error'] = str(task_result.info)
            response['message'] = '任务失败'
            
        else:
            response['message'] = task_result.status
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"查询任务状态失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@api_bp.route('/tasks/<task_id>/result', methods=['GET'])
def get_task_result(task_id):
    """
    获取任务结果
    
    Args:
        task_id: 任务ID
    
    Returns:
        JSON: 任务结果
    """
    try:
        # 获取任务结果
        task_result = AsyncResult(task_id, app=celery_app)
        
        if task_result.status == 'SUCCESS':
            return jsonify({
                'task_id': task_id,
                'status': 'SUCCESS',
                'result': task_result.result
            }), 200
            
        elif task_result.status == 'FAILURE':
            return jsonify({
                'task_id': task_id,
                'status': 'FAILURE',
                'error': str(task_result.info)
            }), 200
            
        else:
            return jsonify({
                'task_id': task_id,
                'status': task_result.status,
                'message': '任务未完成'
            }), 200
            
    except Exception as e:
        logger.error(f"获取任务结果失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@api_bp.route('/factors/metadata', methods=['GET'])
def get_factor_metadata():
    """
    获取因子元数据列表
    
    Returns:
        JSON: 因子元数据列表
    """
    try:
        db = next(get_db())
        
        try:
            # 查询所有因子元数据
            metadata_list = db.query(FactorMetadata).all()
            
            # 转换为 Pydantic 模型
            result = [
                FactorMetadataInfo.from_orm(metadata).dict()
                for metadata in metadata_list
            ]
            
            return jsonify({
                'total': len(result),
                'factors': result
            }), 200
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"获取因子元数据失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@api_bp.route('/factors/results', methods=['GET'])
def get_factor_results():
    """
    查询因子结果
    
    Query Parameters:
        - stock_code: 股票代码（可选）
        - factor_name: 因子名称（可选）
        - start_date: 开始日期（可选，格式：YYYY-MM-DD）
        - end_date: 结束日期（可选，格式：YYYY-MM-DD）
        - limit: 返回数量限制（默认100）
        - offset: 偏移量（默认0）
    
    Returns:
        JSON: 因子结果列表
    """
    try:
        # 获取查询参数
        stock_code = request.args.get('stock_code')
        factor_name = request.args.get('factor_name', 'search_engine_catalyst_factor')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        
        db = next(get_db())
        
        try:
            # 构建查询
            query = db.query(FactorResult)
            
            # 根据因子名称过滤
            if factor_name:
                factor_metadata = db.query(FactorMetadata).filter_by(
                    factor_name=factor_name
                ).first()
                
                if factor_metadata:
                    query = query.filter(
                        FactorResult.factor_metadata_id == factor_metadata.id
                    )
            
            # 根据股票代码过滤
            if stock_code:
                query = query.filter(FactorResult.stock_code == stock_code)
            
            # 根据日期范围过滤
            if start_date:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(FactorResult.factor_date >= start_dt)
            
            if end_date:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                query = query.filter(FactorResult.factor_date <= end_dt)
            
            # 排序
            query = query.order_by(FactorResult.factor_date.desc())
            
            # 分页
            total = query.count()
            results = query.limit(limit).offset(offset).all()
            
            # 转换为 Pydantic 模型
            result_list = [
                FactorResultInfo.from_orm(result).dict()
                for result in results
            ]
            
            return jsonify({
                'total': total,
                'limit': limit,
                'offset': offset,
                'results': result_list
            }), 200
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"查询因子结果失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


@api_bp.route('/factors/results/<int:result_id>', methods=['GET'])
def get_factor_result_detail(result_id):
    """
    获取因子结果详情
    
    Args:
        result_id: 结果ID
    
    Returns:
        JSON: 因子结果详情
    """
    try:
        db = next(get_db())
        
        try:
            # 查询结果
            result = db.query(FactorResult).filter_by(id=result_id).first()
            
            if not result:
                return jsonify({
                    'error': 'not_found',
                    'message': f'结果ID {result_id} 不存在'
                }), 404
            
            # 转换为 Pydantic 模型
            result_info = FactorResultInfo.from_orm(result).dict()
            
            return jsonify(result_info), 200
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"获取因子结果详情失败: {str(e)}")
        return jsonify({
            'error': 'internal_error',
            'message': str(e)
        }), 500


# 错误处理
@api_bp.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'not_found',
        'message': '资源不存在'
    }), 404


@api_bp.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'internal_error',
        'message': '服务器内部错误'
    }), 500
