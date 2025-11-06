# 金融智能分析系统 - 技术实施方案

## 文档说明

**文档类型**: 技术实施方案（Implementation Plan）  
**前置文档**: [DESIGN.md](./DESIGN.md) - 请先阅读设计方案  
**适用阶段**: 开发实施阶段  
**目标读者**: 开发工程师、技术架构师  
**侧重点**: 技术细节、代码实现、开发规范

---

## 一、技术栈与工具选型

### 1.1 保留的技术栈

| 组件 | 技术 | 版本要求 | 用途 |
|------|------|---------|------|
| 后端框架 | Flask | 2.0+ | Web服务、API接口 |
| WebSocket | Flask-SocketIO | 5.0+ | 实时通信 |
| Agent框架 | 自研 | - | 多Agent协作 |
| 配置管理 | Pydantic Settings | 2.0+ | 环境变量管理 |
| 日志系统 | Loguru | 0.7+ | 日志记录 |
| 前端框架 | Streamlit | 1.28+ | 单Agent调试界面 |

### 1.2 新增的技术栈

| 组件 | 技术 | 版本要求 | 用途 |
|------|------|---------|------|
| 数据分析 | Pandas | 2.0+ | 数据处理 |
| 数值计算 | NumPy | 1.24+ | 技术指标计算 |
| 技术分析库 | TA-Lib | 0.4+ | 技术指标（可选） |
| 数据可视化 | Plotly | 5.17+ | K线图表生成 |
| 数据库连接 | PyMySQL | 1.1+ | MySQL连接 |
| 异步任务 | Celery | 5.3+ | 后台任务（可选） |

### 1.3 外部数据接口

| 数据源 | 接口方式 | 成本 | 备注 |
|--------|---------|------|------|
| 交易所公告 | 爬虫（Playwright） | 免费 | 需要反爬虫处理 |
| 财经新闻 | RSS/爬虫 | 免费 | 新浪财经、东方财富 |
| 实时行情 | WebSocket/HTTP | 按需 | 用户自有或购买 |
| 财务数据 | Tushare/AKShare | 免费/付费 | 开源财经数据库 |

---

## 二、目录结构重组

### 2.1 调整后的目录结构

```
FinanceAI/
├── app.py                          # Flask主应用（保留）
├── config.py                       # 全局配置（保留）
├── requirements.txt                # 依赖清单（更新）
│
├── MessageEngine/                  # 消息分析引擎（原QueryEngine）
│   ├── agent.py                    # Agent主逻辑
│   ├── tools/                      # 工具集
│   │   ├── announcement_parser.py  # 公告解析器 [新增]
│   │   ├── news_crawler.py         # 财经新闻爬虫 [新增]
│   │   ├── research_aggregator.py  # 研报聚合器 [新增]
│   │   └── event_analyzer.py       # 事件驱动分析 [新增]
│   ├── prompts/                    # Prompt模板
│   │   └── prompts.py              # 金融消息分析Prompt [改造]
│   └── ...
│
├── MarketEngine/                   # 市场数据引擎（原MediaEngine）
│   ├── agent.py                    # Agent主逻辑
│   ├── tools/                      # 工具集
│   │   ├── realtime_data.py        # 实时行情 [新增]
│   │   ├── technical_calculator.py # 技术指标计算 [新增]
│   │   ├── capital_flow.py         # 资金流向分析 [新增]
│   │   └── market_sentiment.py     # 市场情绪监控 [新增]
│   ├── prompts/                    # Prompt模板
│   │   └── prompts.py              # 技术分析Prompt [改造]
│   └── ...
│
├── StrategyEngine/                 # 策略分析引擎（原InsightEngine）
│   ├── agent.py                    # Agent主逻辑
│   ├── tools/                      # 工具集
│   │   ├── historical_analyzer.py  # 历史数据分析 [新增]
│   │   ├── backtest_engine.py      # 回测引擎 [新增]
│   │   ├── quantitative_scorer.py  # 量化评分器 [新增]
│   │   ├── risk_assessor.py        # 风险评估器 [新增]
│   │   ├── factor_analyzer.py      # 因子分析器 [改造]
│   │   └── sentiment_analyzer.py   # 情感分析（保留）
│   ├── prompts/                    # Prompt模板
│   │   └── prompts.py              # 量化分析Prompt [改造]
│   └── ...
│
├── ForumEngine/                    # 论坛协作引擎（保留）
│   ├── monitor.py                  # 日志监控
│   ├── llm_host.py                 # 论坛主持人
│   └── prompts/                    # Prompt模板
│       └── host_prompts.py         # 金融主持人Prompt [改造]
│
├── ReportEngine/                   # 报告生成引擎（保留）
│   ├── agent.py                    # Agent主逻辑
│   ├── report_template/            # 报告模板
│   │   ├── 个股深度分析.md          # 新模板 [新增]
│   │   ├── 题材分析.md              # 新模板 [新增]
│   │   └── 市场分析.md              # 新模板 [新增]
│   └── ...
│
├── data_access/                    # 数据访问层 [新增]
│   ├── __init__.py
│   ├── data_manager.py             # 数据管理器基类
│   ├── market_data_source.py       # 行情数据源
│   ├── financial_data_source.py    # 财务数据源
│   ├── alternative_data_source.py  # 另类数据源
│   └── data_integrator.py          # 数据整合器
│
├── utils/                          # 工具函数（保留）
│   ├── forum_reader.py             # 论坛读取（保留）
│   ├── retry_helper.py             # 重试机制（保留）
│   └── technical_indicators.py     # 技术指标工具 [新增]
│
└── database/                       # 数据库相关 [新增]
    ├── schema/                     # 数据库Schema
    │   ├── create_tables.sql       # 建表SQL
    │   └── migrations/             # 数据库迁移
    └── seeds/                      # 测试数据
```

### 2.2 需要删除/重构的模块

**删除**:
- `MindSpider/` - 舆情爬虫系统（不再需要）
- `SentimentAnalysisModel/WeiboSentiment*` - 微博专用情感分析（改为通用金融情感分析）

**保留但需重构**:
- `InsightEngine/tools/keyword_optimizer.py` - 可用于股票关键词优化
- `InsightEngine/tools/sentiment_analyzer.py` - 可用于财经新闻情感分析

---

## 三、数据访问层实现

### 3.1 数据库Schema设计

```sql
-- database/schema/create_tables.sql

-- ==================== 行情数据表 ====================
-- 用户已有的表结构（示例，需根据实际调整）

CREATE TABLE IF NOT EXISTS trading_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL COMMENT '股票代码',
    trade_date DATE NOT NULL COMMENT '交易日期',
    open_price DECIMAL(10,2) NOT NULL COMMENT '开盘价',
    high_price DECIMAL(10,2) NOT NULL COMMENT '最高价',
    low_price DECIMAL(10,2) NOT NULL COMMENT '最低价',
    close_price DECIMAL(10,2) NOT NULL COMMENT '收盘价',
    pre_close_price DECIMAL(10,2) COMMENT '前收盘价',
    volume BIGINT COMMENT '成交量（手）',
    amount DECIMAL(20,2) COMMENT '成交额（元）',
    change_pct DECIMAL(10,4) COMMENT '涨跌幅（%）',
    turnover_rate DECIMAL(10,4) COMMENT '换手率（%）',
    INDEX idx_stock_date (stock_code, trade_date),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='日K线数据表';

-- ==================== 技术指标表（预计算缓存） ====================
CREATE TABLE IF NOT EXISTS technical_indicators (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    ma5 DECIMAL(10,2) COMMENT '5日均线',
    ma10 DECIMAL(10,2) COMMENT '10日均线',
    ma20 DECIMAL(10,2) COMMENT '20日均线',
    ma60 DECIMAL(10,2) COMMENT '60日均线',
    macd_dif DECIMAL(10,4) COMMENT 'MACD DIF',
    macd_dea DECIMAL(10,4) COMMENT 'MACD DEA',
    macd_bar DECIMAL(10,4) COMMENT 'MACD柱',
    kdj_k DECIMAL(10,4) COMMENT 'KDJ K值',
    kdj_d DECIMAL(10,4) COMMENT 'KDJ D值',
    kdj_j DECIMAL(10,4) COMMENT 'KDJ J值',
    rsi_6 DECIMAL(10,4) COMMENT 'RSI(6)',
    rsi_14 DECIMAL(10,4) COMMENT 'RSI(14)',
    boll_upper DECIMAL(10,2) COMMENT '布林上轨',
    boll_mid DECIMAL(10,2) COMMENT '布林中轨',
    boll_lower DECIMAL(10,2) COMMENT '布林下轨',
    volume_ratio DECIMAL(10,4) COMMENT '量比',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_date (stock_code, trade_date),
    INDEX idx_date (trade_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='技术指标表（预计算缓存）';

-- ==================== 财务数据表 ====================
CREATE TABLE IF NOT EXISTS financial_data (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL,
    report_date DATE NOT NULL COMMENT '报告期',
    report_type VARCHAR(10) NOT NULL COMMENT '报告类型：Q1/Q2/Q3/annual',
    revenue DECIMAL(20,2) COMMENT '营业收入（万元）',
    revenue_yoy DECIMAL(10,4) COMMENT '营收同比增长率（%）',
    net_profit DECIMAL(20,2) COMMENT '净利润（万元）',
    net_profit_yoy DECIMAL(10,4) COMMENT '净利润同比增长率（%）',
    roe DECIMAL(10,4) COMMENT '净资产收益率（%）',
    gross_margin DECIMAL(10,4) COMMENT '毛利率（%）',
    net_margin DECIMAL(10,4) COMMENT '净利率（%）',
    asset_liability_ratio DECIMAL(10,4) COMMENT '资产负债率（%）',
    current_ratio DECIMAL(10,4) COMMENT '流动比率',
    quick_ratio DECIMAL(10,4) COMMENT '速动比率',
    operating_cash_flow DECIMAL(20,2) COMMENT '经营现金流（万元）',
    total_assets DECIMAL(20,2) COMMENT '总资产（万元）',
    total_equity DECIMAL(20,2) COMMENT '股东权益（万元）',
    eps DECIMAL(10,4) COMMENT '每股收益（元）',
    bvps DECIMAL(10,4) COMMENT '每股净资产（元）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_stock_report (stock_code, report_date, report_type),
    INDEX idx_stock_code (stock_code),
    INDEX idx_report_date (report_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财务数据表';

-- ==================== 股票基本信息表 ====================
CREATE TABLE IF NOT EXISTS stock_basic_info (
    stock_code VARCHAR(10) PRIMARY KEY COMMENT '股票代码',
    stock_name VARCHAR(50) NOT NULL COMMENT '股票名称',
    stock_abbr VARCHAR(20) COMMENT '股票简称',
    market VARCHAR(10) COMMENT '市场：SH/SZ',
    industry VARCHAR(50) COMMENT '所属行业',
    sector VARCHAR(50) COMMENT '所属板块',
    list_date DATE COMMENT '上市日期',
    total_shares DECIMAL(20,2) COMMENT '总股本（万股）',
    float_shares DECIMAL(20,2) COMMENT '流通股本（万股）',
    is_st BOOLEAN DEFAULT FALSE COMMENT '是否ST',
    is_delisted BOOLEAN DEFAULT FALSE COMMENT '是否退市',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_industry (industry),
    INDEX idx_sector (sector)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='股票基本信息表';

-- ==================== 公司公告表 ====================
CREATE TABLE IF NOT EXISTS company_announcements (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    stock_code VARCHAR(10) NOT NULL,
    announcement_id VARCHAR(50) UNIQUE COMMENT '公告唯一ID',
    title VARCHAR(200) NOT NULL COMMENT '公告标题',
    announcement_type VARCHAR(50) COMMENT '公告类型：财报/重组/分红等',
    publish_date DATETIME NOT NULL COMMENT '发布时间',
    content TEXT COMMENT '公告内容',
    url VARCHAR(500) COMMENT '公告链接',
    importance INT DEFAULT 5 COMMENT '重要性评分1-10',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_code (stock_code),
    INDEX idx_publish_date (publish_date),
    INDEX idx_type (announcement_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公司公告表';

-- ==================== 财经新闻表 ====================
CREATE TABLE IF NOT EXISTS financial_news (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    news_id VARCHAR(50) UNIQUE COMMENT '新闻唯一ID',
    title VARCHAR(200) NOT NULL COMMENT '新闻标题',
    source VARCHAR(50) COMMENT '新闻来源',
    publish_time DATETIME NOT NULL COMMENT '发布时间',
    content TEXT COMMENT '新闻内容',
    url VARCHAR(500) COMMENT '新闻链接',
    related_stocks VARCHAR(500) COMMENT '相关股票代码（逗号分隔）',
    sentiment_score DECIMAL(10,4) COMMENT '情感得分 -1到1',
    tags VARCHAR(200) COMMENT '标签（逗号分隔）',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_publish_time (publish_time),
    INDEX idx_related_stocks (related_stocks),
    FULLTEXT idx_content (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='财经新闻表';

-- ==================== 分析报告缓存表 ====================
CREATE TABLE IF NOT EXISTS analysis_reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    report_id VARCHAR(50) UNIQUE COMMENT '报告唯一ID',
    stock_code VARCHAR(10) NOT NULL,
    report_type VARCHAR(50) COMMENT '报告类型：个股分析/题材分析',
    query TEXT COMMENT '用户查询',
    report_content LONGTEXT COMMENT '报告内容（HTML）',
    analysis_date DATE COMMENT '分析基准日期',
    comprehensive_score INT COMMENT '综合评分 0-100',
    rating VARCHAR(20) COMMENT '投资评级',
    target_price DECIMAL(10,2) COMMENT '目标价',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stock_code (stock_code),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='分析报告缓存表';
```

### 3.2 数据访问层代码实现

```python
# data_access/data_manager.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd
import pymysql
from datetime import datetime, timedelta
from loguru import logger

class BaseDataSource(ABC):
    """数据源基类"""
    
    @abstractmethod
    def get_data(self, **kwargs) -> pd.DataFrame:
        """获取数据的抽象方法"""
        pass
    
    @abstractmethod
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据完整性"""
        pass


class MarketDataSource(BaseDataSource):
    """
    行情数据源
    负责从用户数据库获取行情数据
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection = self._create_connection()
    
    def _create_connection(self):
        """创建数据库连接"""
        return pymysql.connect(
            host=self.db_config['host'],
            port=self.db_config['port'],
            user=self.db_config['user'],
            password=self.db_config['password'],
            database=self.db_config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def get_kline_data(self, stock_code: str, start_date: str, 
                      end_date: str, period: str = 'D') -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            stock_code: 股票代码，如'600519'
            start_date: 开始日期，格式'YYYY-MM-DD'
            end_date: 结束日期
            period: 周期，'D'日线（默认），'W'周线，'M'月线
        
        Returns:
            DataFrame包含列: [date, open, high, low, close, volume, amount, change_pct]
        """
        query = """
        SELECT 
            trade_date as date,
            open_price as open,
            high_price as high,
            low_price as low,
            close_price as close,
            volume,
            amount,
            change_pct
        FROM trading_data
        WHERE stock_code = %s
          AND trade_date BETWEEN %s AND %s
        ORDER BY trade_date ASC
        """
        
        try:
            df = pd.read_sql(query, self.connection, 
                           params=(stock_code, start_date, end_date))
            
            if not self.validate_data(df):
                raise ValueError(f"数据验证失败: {stock_code}")
            
            logger.info(f"获取K线数据: {stock_code}, {len(df)}条")
            return df
            
        except Exception as e:
            logger.error(f"获取K线数据失败: {e}")
            raise
    
    def get_realtime_quote(self, stock_code: str) -> Dict:
        """
        获取实时行情
        
        Returns:
            {
                'stock_code': '600519',
                'current_price': 1850.00,
                'change_pct': 2.35,
                'volume': 12345678,
                'turnover_rate': 0.56,
                'timestamp': '2024-11-06 14:30:00'
            }
        """
        # TODO: 实现实时行情获取
        # 这里需要根据用户的实时行情接口进行适配
        pass
    
    def get_data(self, **kwargs) -> pd.DataFrame:
        """实现基类抽象方法"""
        return self.get_kline_data(**kwargs)
    
    def validate_data(self, data: pd.DataFrame) -> bool:
        """验证数据完整性"""
        if data.empty:
            return False
        
        required_columns = ['date', 'open', 'high', 'low', 'close']
        if not all(col in data.columns for col in required_columns):
            logger.error("缺少必要字段")
            return False
        
        # 检查数据合理性
        if (data['high'] < data['low']).any():
            logger.error("发现高价<低价的异常数据")
            return False
        
        if (data['close'] <= 0).any():
            logger.error("发现价格<=0的异常数据")
            return False
        
        return True


class TechnicalIndicatorCalculator:
    """
    技术指标计算器
    预计算并缓存常用技术指标
    """
    
    def __init__(self, db_config: Dict):
        self.db_config = db_config
        self.connection = pymysql.connect(**db_config)
    
    def calculate_ma(self, df: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> Dict:
        """计算移动平均线"""
        result = {}
        for period in periods:
            if len(df) >= period:
                result[f'ma{period}'] = df['close'].rolling(window=period).mean().iloc[-1]
            else:
                result[f'ma{period}'] = None
        return result
    
    def calculate_macd(self, df: pd.DataFrame, 
                      fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算MACD"""
        close = df['close']
        
        # 计算EMA
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        
        # DIF
        dif = ema_fast - ema_slow
        
        # DEA
        dea = dif.ewm(span=signal, adjust=False).mean()
        
        # MACD柱
        macd_bar = (dif - dea) * 2
        
        return {
            'dif': round(dif.iloc[-1], 4),
            'dea': round(dea.iloc[-1], 4),
            'macd_bar': round(macd_bar.iloc[-1], 4)
        }
    
    def calculate_kdj(self, df: pd.DataFrame, n: int = 9) -> Dict:
        """计算KDJ"""
        low_list = df['low'].rolling(window=n).min()
        high_list = df['high'].rolling(window=n).max()
        
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        
        k = rsv.ewm(com=2, adjust=False).mean()
        d = k.ewm(com=2, adjust=False).mean()
        j = 3 * k - 2 * d
        
        return {
            'k': round(k.iloc[-1], 2),
            'd': round(d.iloc[-1], 2),
            'j': round(j.iloc[-1], 2)
        }
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14) -> float:
        """计算RSI"""
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return round(rsi.iloc[-1], 2)
    
    def calculate_all_indicators(self, stock_code: str, trade_date: str) -> Dict:
        """
        计算指定日期的所有技术指标
        
        Args:
            stock_code: 股票代码
            trade_date: 交易日期
        
        Returns:
            包含所有技术指标的字典
        """
        # 获取历史数据（需要足够的数据来计算指标）
        start_date = (datetime.strptime(trade_date, '%Y-%m-%d') - timedelta(days=200)).strftime('%Y-%m-%d')
        
        market_data = MarketDataSource(self.db_config)
        df = market_data.get_kline_data(stock_code, start_date, trade_date)
        
        if df.empty:
            return {}
        
        indicators = {}
        
        # 计算各类指标
        indicators.update(self.calculate_ma(df))
        indicators.update(self.calculate_macd(df))
        indicators.update(self.calculate_kdj(df))
        indicators['rsi_14'] = self.calculate_rsi(df, 14)
        
        return indicators
    
    def cache_indicators(self, stock_code: str, trade_date: str):
        """将计算的指标缓存到数据库"""
        indicators = self.calculate_all_indicators(stock_code, trade_date)
        
        if not indicators:
            return
        
        query = """
        INSERT INTO technical_indicators 
        (stock_code, trade_date, ma5, ma10, ma20, ma60, 
         macd_dif, macd_dea, macd_bar, kdj_k, kdj_d, kdj_j, rsi_14)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        ma5=%s, ma10=%s, ma20=%s, ma60=%s,
        macd_dif=%s, macd_dea=%s, macd_bar=%s,
        kdj_k=%s, kdj_d=%s, kdj_j=%s, rsi_14=%s
        """
        
        params = (
            stock_code, trade_date,
            indicators.get('ma5'), indicators.get('ma10'), 
            indicators.get('ma20'), indicators.get('ma60'),
            indicators['dif'], indicators['dea'], indicators['macd_bar'],
            indicators['k'], indicators['d'], indicators['j'],
            indicators['rsi_14'],
            # 重复参数用于UPDATE
            indicators.get('ma5'), indicators.get('ma10'), 
            indicators.get('ma20'), indicators.get('ma60'),
            indicators['dif'], indicators['dea'], indicators['macd_bar'],
            indicators['k'], indicators['d'], indicators['j'],
            indicators['rsi_14']
        )
        
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)
            self.connection.commit()
        
        logger.info(f"技术指标已缓存: {stock_code} {trade_date}")
```

---

## 四、Agent工具集实现

### 4.1 MessageEngine工具集

```python
# MessageEngine/tools/announcement_parser.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger

class AnnouncementParser:
    """
    公司公告解析器
    从交易所官网爬取上市公司公告
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # 交易所公告查询接口
        self.szse_url = 'http://www.szse.cn/api/disc/announcement/annList'  # 深交所
        self.sse_url = 'http://query.sse.com.cn/security/stock/getStockAnnouncementList'  # 上交所
    
    def fetch_announcements(self, stock_code: str, days: int = 30) -> List[Dict]:
        """
        获取指定股票的公告
        
        Args:
            stock_code: 股票代码
            days: 获取最近多少天的公告
        
        Returns:
            [
                {
                    'title': '2024年三季度报告',
                    'type': '定期报告',
                    'publish_date': '2024-10-30',
                    'url': 'http://...',
                    'summary': '...'
                },
                ...
            ]
        """
        market = 'SZ' if stock_code.startswith('0') or stock_code.startswith('3') else 'SH'
        
        if market == 'SZ':
            return self._fetch_szse_announcements(stock_code, days)
        else:
            return self._fetch_sse_announcements(stock_code, days)
    
    def _fetch_szse_announcements(self, stock_code: str, days: int) -> List[Dict]:
        """获取深交所公告"""
        start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        params = {
            'stock': stock_code,
            'startDate': start_date,
            'endDate': end_date,
            'pageSize': 50
        }
        
        try:
            response = requests.get(self.szse_url, params=params, headers=self.headers, timeout=10)
            data = response.json()
            
            announcements = []
            for item in data.get('data', []):
                announcements.append({
                    'title': item['title'],
                    'type': item.get('category', '其他'),
                    'publish_date': item['publishTime'][:10],
                    'url': f"http://disc.szse.cn/download/{item['attachPath']}",
                    'summary': item.get('summary', '')
                })
            
            logger.info(f"获取深交所公告: {stock_code}, 共{len(announcements)}条")
            return announcements
            
        except Exception as e:
            logger.error(f"获取深交所公告失败: {e}")
            return []
    
    def _fetch_sse_announcements(self, stock_code: str, days: int) -> List[Dict]:
        """获取上交所公告"""
        # 实现类似逻辑
        pass
    
    def parse_financial_report(self, announcement_url: str) -> Dict:
        """
        解析财报公告，提取关键财务指标
        
        Returns:
            {
                'revenue': 1234567.89,  # 营业收入（万元）
                'revenue_yoy': 15.6,    # 同比增长率
                'net_profit': 234567.89,
                'net_profit_yoy': 20.3,
                'roe': 18.5,
                ...
            }
        """
        # TODO: 实现财报解析逻辑
        # 可以使用PyPDF2解析PDF，或者调用第三方财报解析API
        pass
```

```python
# MessageEngine/tools/news_crawler.py

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict
from loguru import logger

class FinancialNewsCrawler:
    """
    财经新闻爬虫
    从主流财经网站爬取相关新闻
    """
    
    def __init__(self):
        self.sources = {
            '新浪财经': 'https://finance.sina.com.cn',
            '东方财富': 'https://www.eastmoney.com',
            '证券时报': 'http://www.stcn.com'
        }
    
    def fetch_news(self, keywords: List[str], days: int = 7) -> List[Dict]:
        """
        搜索相关新闻
        
        Args:
            keywords: 关键词列表，如['贵州茅台', '白酒']
            days: 获取最近多少天的新闻
        
        Returns:
            [
                {
                    'title': '茅台三季报业绩超预期',
                    'source': '新浪财经',
                    'publish_time': '2024-11-06 14:30:00',
                    'content': '...',
                    'url': 'https://...',
                    'sentiment': 'positive'  # positive/neutral/negative
                },
                ...
            ]
        """
        all_news = []
        
        for keyword in keywords:
            # 从各个源爬取新闻
            all_news.extend(self._fetch_sina_news(keyword, days))
            all_news.extend(self._fetch_eastmoney_news(keyword, days))
        
        # 去重
        unique_news = self._deduplicate_news(all_news)
        
        logger.info(f"爬取新闻: 关键词{keywords}, 共{len(unique_news)}条")
        return unique_news
    
    def _fetch_sina_news(self, keyword: str, days: int) -> List[Dict]:
        """从新浪财经爬取新闻"""
        # TODO: 实现具体的爬虫逻辑
        # 注意：需要处理反爬虫、JS渲染等问题
        pass
    
    def _deduplicate_news(self, news_list: List[Dict]) -> List[Dict]:
        """新闻去重"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            if news['title'] not in seen_titles:
                seen_titles.add(news['title'])
                unique_news.append(news)
        
        return unique_news
```

### 4.2 MarketEngine工具集

```python
# MarketEngine/tools/technical_calculator.py

import pandas as pd
import numpy as np
from typing import Dict, List
from loguru import logger

class TechnicalCalculator:
    """
    技术指标计算器（完整版）
    提供更多专业技术指标的计算
    """
    
    def __init__(self, kline_data: pd.DataFrame):
        """
        Args:
            kline_data: K线数据，必须包含列[date, open, high, low, close, volume]
        """
        self.df = kline_data.copy()
        self._validate_data()
    
    def _validate_data(self):
        """验证数据完整性"""
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing = [col for col in required_columns if col not in self.df.columns]
        if missing:
            raise ValueError(f"缺少必要字段: {missing}")
    
    def calculate_bollinger_bands(self, period: int = 20, std_dev: int = 2) -> Dict:
        """
        计算布林带
        
        Returns:
            {
                'upper': 上轨价格,
                'middle': 中轨价格,
                'lower': 下轨价格,
                'bandwidth': 带宽
            }
        """
        close = self.df['close']
        
        middle = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        
        upper = middle + (std_dev * std)
        lower = middle - (std_dev * std)
        bandwidth = (upper - lower) / middle
        
        return {
            'upper': round(upper.iloc[-1], 2),
            'middle': round(middle.iloc[-1], 2),
            'lower': round(lower.iloc[-1], 2),
            'bandwidth': round(bandwidth.iloc[-1], 4)
        }
    
    def identify_chart_patterns(self) -> List[str]:
        """
        识别K线形态
        
        Returns:
            识别到的形态列表，如['morning_star', 'hammer']
        """
        patterns = []
        
        # 获取最近3根K线
        if len(self.df) < 3:
            return patterns
        
        recent_3 = self.df.tail(3)
        
        # 早晨之星
        if self._is_morning_star(recent_3):
            patterns.append('morning_star')
        
        # 黄昏之星
        if self._is_evening_star(recent_3):
            patterns.append('evening_star')
        
        # 锤子线
        if self._is_hammer(self.df.tail(1).iloc[0]):
            patterns.append('hammer')
        
        # 吊颈线
        if self._is_hanging_man(self.df.tail(1).iloc[0]):
            patterns.append('hanging_man')
        
        return patterns
    
    def _is_morning_star(self, df: pd.DataFrame) -> bool:
        """判断是否为早晨之星（看涨）"""
        if len(df) != 3:
            return False
        
        first = df.iloc[0]
        second = df.iloc[1]
        third = df.iloc[2]
        
        # 第一根：阴线
        first_is_bearish = first['close'] < first['open']
        
        # 第二根：小实体（阳线或阴线）
        second_body = abs(second['close'] - second['open'])
        second_is_small = second_body < (first['open'] - first['close']) * 0.3
        
        # 第三根：阳线，收盘价超过第一根实体中部
        third_is_bullish = third['close'] > third['open']
        third_closes_high = third['close'] > (first['open'] + first['close']) / 2
        
        return first_is_bearish and second_is_small and third_is_bullish and third_closes_high
    
    def _is_hammer(self, candle: pd.Series) -> bool:
        """判断是否为锤子线（看涨）"""
        body = abs(candle['close'] - candle['open'])
        lower_shadow = min(candle['open'], candle['close']) - candle['low']
        upper_shadow = candle['high'] - max(candle['open'], candle['close'])
        
        # 下影线至少是实体的2倍，上影线很小
        return (lower_shadow >= body * 2 and 
                upper_shadow < body * 0.3)
```

---

## 五、Prompt模板改造

### 5.1 Prompt改造规范

**改造原则**:
1. 所有Prompt必须包含金融专业术语和分析框架
2. 强制要求输出JSON格式，便于解析
3. 包含风险提示和免责声明
4. 强调数据支撑，避免主观臆断

### 5.2 核心Prompt模板

```python
# MessageEngine/prompts/prompts.py

MESSAGE_ANALYSIS_PROMPT = """
你是一位资深的金融信息分析师，专注于解读上市公司公告和财经新闻。

【分析任务】
股票代码: {stock_code}
股票名称: {stock_name}
分析主题: {analysis_topic}

【可用信息】
{information_sources}

【分析框架】
请按以下结构进行分析:

1. 信息摘要 (20%)
   - 核心要点提取
   - 关键数据罗列
   
2. 影响评估 (40%)
   - 对公司基本面的影响
   - 对股价的预期影响
   - 影响持续时间预估
   
3. 历史对比 (20%)
   - 类似事件的历史表现
   - 市场反应规律
   
4. 投资建议 (20%)
   - 操作方向（买入/观望/规避）
   - 目标价位和止损位
   - 风险提示

【输出要求】
1. 必须基于提供的信息，不可杜撰
2. 所有结论都要有数据支撑
3. 保持客观中立，避免过度乐观或悲观
4. 以JSON格式输出

【输出格式】
{{
    "summary": "核心要点摘要（100字以内）",
    "impact_analysis": {{
        "fundamental_impact": "对基本面的影响分析",
        "price_impact_score": 7.5,  // 0-10分，10分最利好
        "duration": "短期/中期/长期"
    }},
    "historical_reference": "历史类似事件的表现",
    "investment_advice": {{
        "direction": "积极关注",  // 积极关注/谨慎观望/规避风险
        "target_price": null,  // 如有明确目标
        "stop_loss": null,  // 如有明确止损
        "reasoning": "建议理由"
    }},
    "risk_warning": ["风险点1", "风险点2"]
}}

【免责声明】
本分析仅供参考，不构成投资建议。投资者据此操作，风险自担。
"""

# MarketEngine/prompts/prompts.py

TECHNICAL_ANALYSIS_PROMPT = """
你是一位经验丰富的技术分析师，擅长解读K线图表和技术指标。

【分析标的】
股票代码: {stock_code}
股票名称: {stock_name}
分析日期: {analysis_date}

【当前行情】
最新价: {current_price}元 ({change_pct}%)
成交量: {volume}万手 (量比: {volume_ratio})
换手率: {turnover_rate}%
振幅: {amplitude}%

【技术指标】
移动平均线:
- MA5: {ma5}
- MA10: {ma10}
- MA20: {ma20}
- MA60: {ma60}

MACD:
- DIF: {macd_dif}
- DEA: {macd_dea}
- MACD柱: {macd_bar}

KDJ:
- K: {kdj_k}
- D: {kdj_d}
- J: {kdj_j}

其他指标:
- RSI(14): {rsi}
- 布林带: 上轨{boll_upper}, 中轨{boll_mid}, 下轨{boll_lower}

【K线形态】
{chart_patterns}

【分析要求】
1. 趋势判断: 识别当前趋势（上升/下降/震荡），给出关键支撑位和压力位
2. 技术信号: 解读各指标的买卖信号（金叉/死叉/超买/超卖）
3. 形态分析: 解释K线形态的意义和后续预期
4. 量价关系: 分析成交量与价格的配合情况
5. 操作建议: 给出具体的操作方向和点位

【输出格式】
{{
    "trend_analysis": {{
        "direction": "上升趋势",  // 上升/下降/震荡
        "strength": "强势",  // 强势/中性/弱势
        "support_level": 45.20,
        "resistance_level": 52.80
    }},
    "technical_signals": {{
        "ma_signal": "MA5上穿MA10，短期金叉",
        "macd_signal": "MACD柱由绿转红，多头强势",
        "kdj_signal": "KDJ高位钝化，注意回调风险",
        "综合信号": "买入"  // 买入/卖出/观望
    }},
    "chart_pattern_interpretation": "识别到早晨之星形态，通常预示反转...",
    "volume_analysis": "放量突破，资金积极入场，短期看涨",
    "technical_score": 75,  // 技术面综合得分 0-100
    "operation_suggestion": {{
        "action": "逢低买入",
        "entry_price": "47-48元区间",
        "target_price": 55.00,
        "stop_loss": 44.50,
        "position_size": "30%"  // 建议仓位
    }},
    "risk_warning": ["短期技术指标超买，注意回调风险"]
}}

【重要提示】
1. 技术分析存在滞后性，需结合基本面和消息面
2. 严格执行止损纪律
3. 本分析仅供参考，不构成投资建议
"""

# StrategyEngine/prompts/prompts.py

QUANTITATIVE_ANALYSIS_PROMPT = """
你是一位量化分析师，擅长从历史数据中挖掘规律并进行量化评分。

【分析任务】
股票代码: {stock_code}
股票名称: {stock_name}

【结构化数据】
财务数据:
{financial_data}

历史表现:
{historical_performance}

因子得分:
{factor_scores}

【分析框架】
1. 基本面评分 (40%)
   - 盈利能力: ROE, 净利率
   - 成长性: 营收增速, 利润增速
   - 财务健康: 负债率, 现金流
   
2. 估值评分 (30%)
   - 估值水平: PE, PB历史分位
   - 估值合理性: 与行业对比
   
3. 动量评分 (20%)
   - 价格动量: 近期涨跌幅
   - 资金动量: 主力资金流向
   
4. 质量评分 (10%)
   - 公司治理
   - 行业地位

【输出格式】
{{
    "fundamental_score": 85,  // 基本面得分 0-100
    "valuation_score": 65,    // 估值得分
    "momentum_score": 72,     // 动量得分
    "quality_score": 80,      // 质量得分
    "composite_score": 76,    // 综合得分（加权平均）
    "rating": "增持",  // 买入/增持/中性/减持/卖出
    "score_reasoning": {{
        "strengths": ["ROE高达25%，盈利能力强", "营收增速30%，成长性突出"],
        "weaknesses": ["PE估值处于历史80%分位，偏高", "短期资金有流出迹象"],
        "opportunities": ["行业政策利好，市场空间扩大"],
        "threats": ["行业竞争加剧，毛利率承压"]
    }},
    "investment_horizon": "中长期持有",  // 短期/中期/中长期
    "risk_level": "中等",  // 低/中等/高
    "expected_return": "15-20%",  // 预期年化收益率
    "confidence_level": 0.75  // 置信度 0-1
}}
"""

# ForumEngine/prompts/host_prompts.py

FORUM_HOST_SYSTEM_PROMPT = """
你是一个多Agent金融分析系统的论坛主持人。

【Agent角色】
- 消息分析师 (MESSAGE): 解读公告、新闻、研报
- 市场分析师 (MARKET): 分析行情、技术、资金
- 策略分析师 (STRATEGY): 量化评分、回测、风险评估

【你的职责】
1. 信息整合: 综合三位分析师的观点
2. 矛盾识别: 发现不同维度之间的矛盾（如消息利好但资金流出）
3. 逻辑推理: 分析矛盾背后的原因
4. 引导协作: 为分析师布置下一步研究任务
5. 风险提示: 指出潜在的风险点

【发言原则】
- 保持客观中立
- 用量化数据支撑观点
- 明确指出确定性和不确定性
- 控制在800字以内
"""

FORUM_HOST_USER_PROMPT = """
【最近的分析师发言】
{recent_speeches}

【主持人任务】
请按以下结构组织你的发言:

一、核心观点整合（30%）
- MESSAGE分析师的核心观点
- MARKET分析师的核心观点
- STRATEGY分析师的核心观点

二、数据交叉验证（40%）
- 哪些数据相互印证？
- 哪些数据相互矛盾？
- 矛盾背后的可能原因

三、多空力量对比（20%）
- 当前多空力量对比
- 市场所处阶段判断
- 风险收益比评估

四、下一步研究方向（10%）
- MESSAGE分析师应重点关注: ...
- MARKET分析师应重点关注: ...
- STRATEGY分析师应重点关注: ...
"""
```

---

## 六、开发实施路线

### 6.1 阶段划分

**第一阶段: 数据基础搭建（1周）**
- 数据库Schema设计与建表
- 数据访问层(DAL)实现
- 技术指标计算器实现
- 数据质量验证机制

**第二阶段: Agent改造（2周）**
- 改造InsightEngine → StrategyEngine
- 改造QueryEngine → MessageEngine
- 改造MediaEngine → MarketEngine
- 实现新的工具集

**第三阶段: Prompt改造（1周）**
- 重写所有Prompt模板
- 创建金融分析报告模板
- 测试Prompt效果

**第四阶段: ForumEngine适配（3天）**
- 更新主持人Prompt
- 测试Agent协作效果

**第五阶段: 测试与优化（1周）**
- 单元测试
- 集成测试
- 性能优化
- Bug修复

### 6.2 开发规范

**代码风格**:
- 遵循PEP 8规范
- 使用Type Hints
- 添加详细的Docstring

**测试规范**:
- 单元测试覆盖率 > 80%
- 集成测试覆盖核心流程
- 性能测试确保响应时间 < 30秒

**文档规范**:
- API文档使用Swagger
- 代码注释覆盖关键逻辑
- README包含快速开始指南

---

## 七、待补充的技术细节

### 7.1 需要进一步讨论的问题

1. **实时行情接口对接**
   - 用户是否有实时行情API？
   - 数据格式和更新频率
   - 需要哪些字段

2. **财务数据获取方式**
   - 使用第三方API（Tushare/AKShare）？
   - 自行爬取交易所？
   - 数据更新策略

3. **情感分析模型选择**
   - 复用原有的多语言BERT？
   - 需要微调吗？
   - 准确率要求

4. **性能优化方案**
   - 数据缓存策略
   - 技术指标预计算
   - 并发处理机制

5. **部署方式**
   - 本地部署还是云端？
   - 需要GPU吗？
   - 如何扩展

---

**文档版本**: v1.0  
**最后更新**: 2024-11-06  
**状态**: 待完善
