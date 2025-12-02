# QueryEngine 深度分析文档

**文档版本**: v1.0  
**创建日期**: 2025-12-02  
**分析范围**: QueryEngine 完整工作流程  
**代码版本**: 基于当前代码库

---

## 目录

- [一、系统概述](#一系统概述)
- [二、核心架构](#二核心架构)
- [三、完整工作流程](#三完整工作流程)
- [四、关键组件详解](#四关键组件详解)
- [五、数据流转与状态管理](#五数据流转与状态管理)
- [六、搜索工具集](#六搜索工具集)
- [七、Prompt设计](#七prompt设计)
- [八、技术特点与限制](#八技术特点与限制)

---

## 一、系统概述

### 1.1 系统定位

QueryEngine 是 BettaFish 系统中的**深度研究引擎**，专门用于：
- 对复杂主题进行深度网络搜索
- 生成结构化的研究报告
- 通过反思机制持续优化内容质量

### 1.2 核心能力

```
输入：用户查询（如："分析贵州茅台最近的提价策略"）
      ↓
处理：深度搜索 + LLM分析 + 反思优化
      ↓
输出：结构化的深度研究报告（Markdown格式，万字级）
```

### 1.3 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| 搜索后端 | Tavily API | 网络新闻搜索 |
| LLM | OpenAI兼容API | 内容生成与分析 |
| 状态管理 | Dataclass | 研究过程状态追踪 |
| 配置管理 | Pydantic Settings | 环境变量管理 |
| 日志 | Loguru | 日志记录 |

---

## 二、核心架构

### 2.1 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    QueryEngine 架构                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  用户查询                                                    │
│  └─ "分析贵州茅台最近的提价策略"                            │
│                                                             │
│  ┌────────────────── DeepSearchAgent ─────────────────┐    │
│  │                                                      │    │
│  │  1. 报告结构生成                                     │    │
│  │     ├─ ReportStructureNode                          │    │
│  │     └─ LLM生成段落大纲（最多5个段落）               │    │
│  │                                                      │    │
│  │  2. 段落处理循环（针对每个段落）                     │    │
│  │     ├─ 初始搜索与总结                               │    │
│  │     │   ├─ FirstSearchNode（生成搜索查询）          │    │
│  │     │   ├─ TavilyNewsAgency（执行搜索）             │    │
│  │     │   └─ FirstSummaryNode（生成初始总结）         │    │
│  │     │                                                │    │
│  │     └─ 反思循环（最多2次）                          │    │
│  │         ├─ ReflectionNode（生成反思查询）           │    │
│  │         ├─ TavilyNewsAgency（补充搜索）             │    │
│  │         └─ ReflectionSummaryNode（更新总结）        │    │
│  │                                                      │    │
│  │  3. 最终报告生成                                     │    │
│  │     └─ ReportFormattingNode（整合所有段落）         │    │
│  │                                                      │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌────────────────── 状态管理 (State) ─────────────────┐   │
│  │                                                       │   │
│  │  State                                                │   │
│  │  ├─ query: 原始查询                                  │   │
│  │  ├─ report_title: 报告标题                           │   │
│  │  ├─ paragraphs: List[Paragraph]                      │   │
│  │  │   └─ Paragraph                                    │   │
│  │  │       ├─ title: 段落标题                          │   │
│  │  │       ├─ content: 预期内容                        │   │
│  │  │       └─ research: Research                       │   │
│  │  │           ├─ search_history: List[Search]         │   │
│  │  │           ├─ latest_summary: 最新总结             │   │
│  │  │           └─ reflection_iteration: 反思次数       │   │
│  │  └─ final_report: 最终报告                           │   │
│  │                                                       │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 目录结构

```
QueryEngine/
├── agent.py                    # 主Agent类
├── llms/                       # LLM客户端
│   ├── __init__.py
│   └── base.py                 # LLMClient实现
├── nodes/                      # 处理节点
│   ├── base_node.py            # 节点基类
│   ├── report_structure_node.py  # 报告结构生成
│   ├── search_node.py          # 搜索查询生成
│   ├── summary_node.py         # 总结生成
│   └── formatting_node.py      # 报告格式化
├── state/                      # 状态管理
│   └── state.py                # State数据类
├── tools/                      # 工具集
│   └── search.py               # Tavily搜索工具
├── prompts/                    # Prompt定义
│   └── prompts.py              # 所有Prompt
└── utils/                      # 工具函数
    ├── config.py               # 配置管理
    └── text_processing.py      # 文本处理
```

---

## 三、完整工作流程

### 3.1 流程概览

```
Step 1: 生成报告结构
  └─ 输入：用户查询
  └─ 输出：报告标题 + 段落大纲（最多5个）

Step 2: 处理每个段落（循环）
  ├─ 2.1 初始搜索与总结
  │   ├─ 生成搜索查询（FirstSearchNode）
  │   ├─ 执行网络搜索（TavilyNewsAgency）
  │   └─ 生成初始总结（FirstSummaryNode）
  │
  └─ 2.2 反思循环（最多2次）
      ├─ 生成反思查询（ReflectionNode）
      ├─ 执行补充搜索（TavilyNewsAgency）
      └─ 更新总结（ReflectionSummaryNode）

Step 3: 生成最终报告
  └─ 整合所有段落（ReportFormattingNode）
  └─ 输出：完整的Markdown报告
```

### 3.2 详细执行流程

#### Step 1: 生成报告结构

```python
# 代码位置：agent.py -> _generate_report_structure()

def _generate_report_structure(self, query: str):
    """
    生成报告结构
    
    流程：
    1. 创建 ReportStructureNode
    2. LLM根据query生成报告大纲
    3. 更新State（包含段落列表）
    
    输出示例：
    {
        "report_title": "贵州茅台提价策略深度分析",
        "paragraphs": [
            {
                "title": "提价历史回顾",
                "content": "梳理茅台近年来的提价历史..."
            },
            {
                "title": "市场反应分析",
                "content": "分析市场对提价的反应..."
            },
            ...
        ]
    }
    """
    report_structure_node = ReportStructureNode(self.llm_client, query)
    self.state = report_structure_node.mutate_state(state=self.state)
```

**关键Prompt**: `SYSTEM_PROMPT_REPORT_STRUCTURE`
- 要求：规划报告结构，最多5个段落
- 输出：JSON格式的段落列表

---

#### Step 2.1: 初始搜索与总结

```python
# 代码位置：agent.py -> _initial_search_and_summary()

def _initial_search_and_summary(self, paragraph_index: int):
    """
    为单个段落执行初始搜索和总结
    
    流程：
    1. FirstSearchNode生成搜索查询
       - 输入：段落标题 + 预期内容
       - 输出：search_query + search_tool + reasoning
    
    2. 执行搜索（TavilyNewsAgency）
       - 根据选择的工具执行搜索
       - 支持6种搜索工具（见下文）
    
    3. FirstSummaryNode生成初始总结
       - 输入：段落信息 + 搜索结果
       - 输出：paragraph_latest_state（800-1200字）
    
    4. 更新State
    """
    # 1. 生成搜索查询
    search_output = self.first_search_node.run(search_input)
    search_query = search_output["search_query"]
    search_tool = search_output.get("search_tool", "basic_search_news")
    
    # 2. 执行搜索
    search_response = self.execute_search_tool(search_tool, search_query)
    
    # 3. 生成总结
    self.state = self.first_summary_node.mutate_state(
        summary_input, self.state, paragraph_index
    )
```

**关键Prompt**:
- `SYSTEM_PROMPT_FIRST_SEARCH`: 生成搜索查询，选择搜索工具
- `SYSTEM_PROMPT_FIRST_SUMMARY`: 生成800-1200字的初始总结

---

#### Step 2.2: 反思循环

```python
# 代码位置：agent.py -> _reflection_loop()

def _reflection_loop(self, paragraph_index: int):
    """
    执行反思循环（最多2次）
    
    目的：
    - 发现初始总结中的遗漏
    - 补充关键信息
    - 提升内容质量
    
    流程：
    for i in range(MAX_REFLECTIONS):  # 默认2次
        1. ReflectionNode生成反思查询
           - 输入：段落信息 + 当前总结
           - 输出：补充搜索查询
        
        2. 执行补充搜索
        
        3. ReflectionSummaryNode更新总结
           - 输入：原总结 + 新搜索结果
           - 输出：更新后的总结
    """
    for reflection_i in range(self.config.MAX_REFLECTIONS):
        # 1. 生成反思查询
        reflection_output = self.reflection_node.run(reflection_input)
        
        # 2. 执行搜索
        search_response = self.execute_search_tool(search_tool, search_query)
        
        # 3. 更新总结
        self.state = self.reflection_summary_node.mutate_state(
            reflection_summary_input, self.state, paragraph_index
        )
```

**关键Prompt**:
- `SYSTEM_PROMPT_REFLECTION`: 反思当前内容，生成补充查询
- `SYSTEM_PROMPT_REFLECTION_SUMMARY`: 基于新信息更新总结

---

#### Step 3: 生成最终报告

```python
# 代码位置：agent.py -> _generate_final_report()

def _generate_final_report(self) -> str:
    """
    整合所有段落，生成最终报告
    
    流程：
    1. 收集所有段落的最终总结
    2. ReportFormattingNode整合成完整报告
       - 添加报告标题
       - 格式化段落结构
       - 添加目录、摘要等
    3. 保存报告到文件
    
    输出：
    - Markdown格式的完整报告（万字级）
    - 包含：标题、摘要、各段落、结论等
    """
    # 准备报告数据
    report_data = []
    for paragraph in self.state.paragraphs:
        report_data.append({
            "title": paragraph.title,
            "paragraph_latest_state": paragraph.research.latest_summary
        })
    
    # 格式化报告
    final_report = self.report_formatting_node.run(report_data)
    
    return final_report
```

**关键Prompt**: `SYSTEM_PROMPT_REPORT_FORMATTING`
- 要求：生成专业的新闻分析报告（万字级）
- 包含：事实核查、多源验证、时间线、数据分析等

---

## 四、关键组件详解

### 4.1 DeepSearchAgent（主Agent）

**职责**：
- 协调整个研究流程
- 管理状态
- 调用各个节点和工具

**核心方法**：

```python
class DeepSearchAgent:
    def __init__(self, config):
        """初始化Agent"""
        self.llm_client = LLMClient(...)
        self.search_agency = TavilyNewsAgency(...)
        self.state = State()
        self._initialize_nodes()
    
    def research(self, query: str) -> str:
        """执行深度研究（主入口）"""
        self._generate_report_structure(query)
        self._process_paragraphs()
        return self._generate_final_report()
    
    def execute_search_tool(self, tool_name, query, **kwargs):
        """执行指定的搜索工具"""
        # 支持6种搜索工具
        pass
```

---

### 4.2 State（状态管理）

**数据结构**：

```python
@dataclass
class State:
    """整个报告的状态"""
    query: str                          # 原始查询
    report_title: str                   # 报告标题
    paragraphs: List[Paragraph]         # 段落列表
    final_report: str                   # 最终报告
    is_completed: bool                  # 是否完成
    created_at: str
    updated_at: str

@dataclass
class Paragraph:
    """单个段落的状态"""
    title: str                          # 段落标题
    content: str                        # 预期内容
    research: Research                  # 研究进度
    order: int                          # 段落顺序

@dataclass
class Research:
    """段落研究过程的状态"""
    search_history: List[Search]        # 搜索记录
    latest_summary: str                 # 最新总结
    reflection_iteration: int           # 反思次数
    is_completed: bool                  # 是否完成

@dataclass
class Search:
    """单个搜索结果的状态"""
    query: str                          # 搜索查询
    url: str                            # 结果URL
    title: str                          # 结果标题
    content: str                        # 结果内容
    score: Optional[float]              # 相关度评分
    timestamp: str                      # 时间戳
```

**状态持久化**：
- 支持保存到JSON文件
- 支持从JSON文件加载
- 用于断点续传和调试

---

### 4.3 Nodes（处理节点）

#### 4.3.1 ReportStructureNode

```python
class ReportStructureNode(BaseNode):
    """生成报告结构的节点"""
    
    def run(self, query: str) -> Dict:
        """
        根据查询生成报告大纲
        
        输入：用户查询
        输出：{
            "report_title": "...",
            "paragraphs": [
                {"title": "...", "content": "..."},
                ...
            ]
        }
        """
        # 调用LLM生成结构
        response = self.llm_client.invoke(
            SYSTEM_PROMPT_REPORT_STRUCTURE, 
            query
        )
        return self.process_output(response)
```

#### 4.3.2 FirstSearchNode

```python
class FirstSearchNode(BaseNode):
    """生成首次搜索查询的节点"""
    
    def run(self, input_data: Dict) -> Dict:
        """
        为段落生成搜索查询
        
        输入：{
            "title": "段落标题",
            "content": "预期内容"
        }
        
        输出：{
            "search_query": "搜索查询",
            "search_tool": "basic_search_news",
            "reasoning": "选择理由",
            "start_date": "2025-01-01",  # 可选
            "end_date": "2025-03-31"     # 可选
        }
        """
        response = self.llm_client.invoke(
            SYSTEM_PROMPT_FIRST_SEARCH,
            json.dumps(input_data)
        )
        return self.process_output(response)
```

#### 4.3.3 FirstSummaryNode

```python
class FirstSummaryNode(BaseNode):
    """生成初始总结的节点"""
    
    def run(self, input_data: Dict) -> Dict:
        """
        基于搜索结果生成总结
        
        输入：{
            "title": "段落标题",
            "content": "预期内容",
            "search_query": "搜索查询",
            "search_results": [...]
        }
        
        输出：{
            "paragraph_latest_state": "800-1200字的总结"
        }
        """
        response = self.llm_client.invoke(
            SYSTEM_PROMPT_FIRST_SUMMARY,
            json.dumps(input_data)
        )
        return self.process_output(response)
```

#### 4.3.4 ReflectionNode

```python
class ReflectionNode(BaseNode):
    """生成反思查询的节点"""
    
    def run(self, input_data: Dict) -> Dict:
        """
        反思当前总结，生成补充查询
        
        输入：{
            "title": "段落标题",
            "content": "预期内容",
            "paragraph_latest_state": "当前总结"
        }
        
        输出：{
            "search_query": "补充查询",
            "search_tool": "...",
            "reasoning": "反思理由"
        }
        """
        response = self.llm_client.invoke(
            SYSTEM_PROMPT_REFLECTION,
            json.dumps(input_data)
        )
        return self.process_output(response)
```

#### 4.3.5 ReflectionSummaryNode

```python
class ReflectionSummaryNode(BaseNode):
    """更新反思总结的节点"""
    
    def run(self, input_data: Dict) -> Dict:
        """
        基于新搜索结果更新总结
        
        输入：{
            "title": "段落标题",
            "content": "预期内容",
            "search_query": "补充查询",
            "search_results": [...],
            "paragraph_latest_state": "当前总结"
        }
        
        输出：{
            "updated_paragraph_latest_state": "更新后的总结"
        }
        """
        response = self.llm_client.invoke(
            SYSTEM_PROMPT_REFLECTION_SUMMARY,
            json.dumps(input_data)
        )
        return self.process_output(response)
```

#### 4.3.6 ReportFormattingNode

```python
class ReportFormattingNode(BaseNode):
    """格式化最终报告的节点"""
    
    def run(self, report_data: List[Dict]) -> str:
        """
        整合所有段落，生成最终报告
        
        输入：[
            {
                "title": "段落1标题",
                "paragraph_latest_state": "段落1内容"
            },
            ...
        ]
        
        输出：完整的Markdown报告
        """
        response = self.llm_client.invoke(
            SYSTEM_PROMPT_REPORT_FORMATTING,
            json.dumps(report_data)
        )
        return response
```

---

## 五、数据流转与状态管理

### 5.1 数据流转图

```
用户查询
    ↓
[Step 1] 生成报告结构
    ↓
State.query = "..."
State.report_title = "..."
State.paragraphs = [
    Paragraph(title="...", content="...", research=Research()),
    ...
]
    ↓
[Step 2] 处理段落1
    ↓
    ├─ [2.1] 初始搜索
    │   ├─ FirstSearchNode → search_query
    │   ├─ TavilyNewsAgency → search_results
    │   └─ FirstSummaryNode → latest_summary
    │       ↓
    │   State.paragraphs[0].research.search_history.append(...)
    │   State.paragraphs[0].research.latest_summary = "..."
    │
    └─ [2.2] 反思循环（2次）
        ├─ Reflection 1
        │   ├─ ReflectionNode → search_query
        │   ├─ TavilyNewsAgency → search_results
        │   └─ ReflectionSummaryNode → updated_summary
        │       ↓
        │   State.paragraphs[0].research.search_history.append(...)
        │   State.paragraphs[0].research.latest_summary = "..."
        │   State.paragraphs[0].research.reflection_iteration = 1
        │
        └─ Reflection 2
            └─ （同上）
    ↓
State.paragraphs[0].research.is_completed = True
    ↓
[Step 2] 处理段落2...
    ↓
[Step 3] 生成最终报告
    ↓
State.final_report = "..."
State.is_completed = True
    ↓
保存报告文件
```

### 5.2 状态更新时机

| 时机 | 更新内容 | 代码位置 |
|------|---------|---------|
| 生成报告结构后 | `State.query`, `State.report_title`, `State.paragraphs` | `ReportStructureNode.mutate_state()` |
| 初始搜索后 | `Paragraph.research.search_history` | `agent._initial_search_and_summary()` |
| 初始总结后 | `Paragraph.research.latest_summary` | `FirstSummaryNode.mutate_state()` |
| 反思搜索后 | `Paragraph.research.search_history` | `agent._reflection_loop()` |
| 反思总结后 | `Paragraph.research.latest_summary`, `reflection_iteration` | `ReflectionSummaryNode.mutate_state()` |
| 段落完成后 | `Paragraph.research.is_completed` | `agent._process_paragraphs()` |
| 最终报告生成后 | `State.final_report`, `State.is_completed` | `agent._generate_final_report()` |

---

## 六、搜索工具集

### 6.1 TavilyNewsAgency

**核心类**：封装了6种专业的新闻搜索工具

```python
class TavilyNewsAgency:
    """Tavily新闻搜索工具集"""
    
    def __init__(self, api_key: str):
        self._client = TavilyClient(api_key=api_key)
    
    # 6种搜索工具
    def basic_search_news(self, query, max_results=7)
    def deep_search_news(self, query)
    def search_news_last_24_hours(self, query)
    def search_news_last_week(self, query)
    def search_images_for_news(self, query)
    def search_news_by_date(self, query, start_date, end_date)
```

### 6.2 搜索工具详解

#### 1. basic_search_news（基础搜索）

```python
def basic_search_news(self, query: str, max_results: int = 7):
    """
    基础新闻搜索工具
    
    适用场景：
    - 一般性的新闻搜索
    - 不确定需要何种特定搜索时
    
    特点：
    - 快速、标准的通用搜索
    - 最常用的基础工具
    
    参数：
    - query: 搜索查询
    - max_results: 最大结果数（默认7）
    
    返回：TavilyResponse
    - results: 搜索结果列表
    - 每个结果包含：title, url, content, score, published_date
    """
    return self._search_internal(
        query=query,
        max_results=max_results,
        search_depth="basic",
        include_answer=False
    )
```

#### 2. deep_search_news（深度搜索）

```python
def deep_search_news(self, query: str):
    """
    深度新闻分析工具
    
    适用场景：
    - 需要全面深入了解某个主题时
    
    特点：
    - 提供最详细的分析结果
    - 包含AI生成的高级摘要
    - 返回最多20条最相关结果
    
    返回：TavilyResponse
    - answer: AI生成的详细摘要
    - results: 最多20条结果
    """
    return self._search_internal(
        query=query,
        search_depth="advanced",
        max_results=20,
        include_answer="advanced"
    )
```

#### 3. search_news_last_24_hours（24小时新闻）

```python
def search_news_last_24_hours(self, query: str):
    """
    24小时最新新闻工具
    
    适用场景：
    - 追踪突发事件
    - 了解最新动态
    
    特点：
    - 只搜索过去24小时的新闻
    - 适合实时性要求高的场景
    
    返回：最多10条最新新闻
    """
    return self._search_internal(
        query=query,
        time_range='d',  # day
        max_results=10
    )
```

#### 4. search_news_last_week（本周新闻）

```python
def search_news_last_week(self, query: str):
    """
    本周新闻工具
    
    适用场景：
    - 周度舆情总结
    - 了解近期发展趋势
    
    特点：
    - 搜索过去一周的新闻
    
    返回：最多10条本周新闻
    """
    return self._search_internal(
        query=query,
        time_range='w',  # week
        max_results=10
    )
```

#### 5. search_images_for_news（图片搜索）

```python
def search_images_for_news(self, query: str):
    """
    新闻图片搜索工具
    
    适用场景：
    - 需要为报告配图
    - 需要可视化信息
    
    特点：
    - 返回图片链接及描述
    
    返回：TavilyResponse
    - images: 图片列表
    - 每个图片包含：url, description
    """
    return self._search_internal(
        query=query,
        include_images=True,
        include_image_descriptions=True,
        max_results=5
    )
```

#### 6. search_news_by_date（按日期搜索）

```python
def search_news_by_date(self, query: str, start_date: str, end_date: str):
    """
    按日期范围搜索工具
    
    适用场景：
    - 研究特定历史时期
    - 分析历史事件
    
    特点：
    - 可指定精确的时间范围
    - 唯一需要额外参数的工具
    
    参数：
    - start_date: 开始日期（格式：YYYY-MM-DD）
    - end_date: 结束日期（格式：YYYY-MM-DD）
    
    返回：最多15条指定时间范围内的新闻
    """
    return self._search_internal(
        query=query,
        start_date=start_date,
        end_date=end_date,
        max_results=15
    )
```

### 6.3 搜索结果数据结构

```python
@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str                      # 新闻标题
    url: str                        # 新闻链接
    content: str                    # 新闻内容摘要
    score: Optional[float]          # 相关度评分
    raw_content: Optional[str]      # 原始内容
    published_date: Optional[str]   # 发布日期

@dataclass
class TavilyResponse:
    """Tavily API返回结果"""
    query: str                      # 搜索查询
    answer: Optional[str]           # AI摘要（仅deep_search）
    results: List[SearchResult]     # 搜索结果列表
    images: List[ImageResult]       # 图片列表（仅image_search）
    response_time: Optional[float]  # 响应时间
```

---

## 七、Prompt设计

### 7.1 Prompt体系

QueryEngine 使用了**5个核心Prompt**，每个Prompt都有明确的职责：

| Prompt | 用途 | 输入 | 输出 |
|--------|------|------|------|
| `SYSTEM_PROMPT_REPORT_STRUCTURE` | 生成报告大纲 | 用户查询 | 段落列表（JSON） |
| `SYSTEM_PROMPT_FIRST_SEARCH` | 生成首次搜索查询 | 段落标题+内容 | 搜索查询+工具选择（JSON） |
| `SYSTEM_PROMPT_FIRST_SUMMARY` | 生成初始总结 | 段落信息+搜索结果 | 800-1200字总结（JSON） |
| `SYSTEM_PROMPT_REFLECTION` | 生成反思查询 | 段落信息+当前总结 | 补充查询+工具选择（JSON） |
| `SYSTEM_PROMPT_REFLECTION_SUMMARY` | 更新反思总结 | 原总结+新搜索结果 | 更新后的总结（JSON） |
| `SYSTEM_PROMPT_REPORT_FORMATTING` | 格式化最终报告 | 所有段落总结 | 完整报告（Markdown） |

### 7.2 Prompt设计特点

#### 1. 结构化输出（JSON Schema）

所有Prompt都要求LLM输出**严格的JSON格式**：

```python
# 示例：首次搜索的输出Schema
output_schema_first_search = {
    "type": "object",
    "properties": {
        "search_query": {"type": "string"},
        "search_tool": {"type": "string"},
        "reasoning": {"type": "string"},
        "start_date": {"type": "string"},  # 可选
        "end_date": {"type": "string"}     # 可选
    },
    "required": ["search_query", "search_tool", "reasoning"]
}
```

#### 2. 工具选择指导

Prompt中详细说明了6种搜索工具的使用场景：

```
SYSTEM_PROMPT_FIRST_SEARCH:

你可以使用以下6种专业的新闻搜索工具：

1. **basic_search_news** - 基础新闻搜索工具
   - 适用于：一般性的新闻搜索
   - 特点：快速、标准的通用搜索

2. **deep_search_news** - 深度新闻分析工具
   - 适用于：需要全面深入了解某个主题时
   - 特点：提供最详细的分析结果

3. **search_news_last_24_hours** - 24小时最新新闻工具
   - 适用于：需要了解最新动态、突发事件时
   - 特点：只搜索过去24小时的新闻

...
```

#### 3. 内容质量要求

**FirstSummary Prompt** 对内容质量有严格要求：

```
**你的核心任务：创建信息密集、结构完整的新闻分析段落（每段不少于800-1200字）**

**撰写标准和要求：**

1. **开篇框架**：
   - 用2-3句话概括本段要分析的核心问题
   - 明确分析的角度和重点方向

2. **丰富的信息层次**：
   - **事实陈述层**：详细引用新闻报道的具体内容、数据、事件细节
   - **多源验证层**：对比不同新闻源的报道角度和信息差异
   - **数据分析层**：提取并分析相关的数量、时间、地点等关键数据
   - **深度解读层**：分析事件背后的原因、影响和意义

3. **信息密度要求**：
   - 每100字至少包含2-3个具体信息点（数据、引用、事实）
   - 每个分析点都要有新闻源支撑
   - 避免空洞的理论分析，重点关注实证信息
```

#### 4. 专业报告格式

**ReportFormatting Prompt** 要求生成专业的新闻分析报告：

```
**新闻分析报告的专业架构：**

# 【深度调查】[主题]全面新闻分析报告

## 核心要点摘要
### 关键事实发现
- 核心事件梳理
- 重要数据指标
- 主要结论要点

### 信息来源概览
- 主流媒体报道统计
- 官方信息发布
- 权威数据来源

## 一、[段落1标题]
### 1.1 事件脉络梳理
| 时间 | 事件 | 信息来源 | 可信度 | 影响程度 |
|------|------|----------|--------|----------|
| XX月XX日 | XX事件 | XX媒体 | 高 | 重大 |

### 1.2 多方报道对比
**主流媒体观点**：
- 《XX日报》："具体报道内容..."

**官方声明**：
- XX部门："官方表态内容..."

...
```

---

## 八、技术特点与限制

### 8.1 技术特点

#### 1. 反思机制（Reflection）

```
优势：
✅ 通过多轮反思提升内容质量
✅ 发现并补充遗漏的关键信息
✅ 类似人类的"二次审查"过程

实现：
- 最多2轮反思（可配置）
- 每轮反思都会生成新的搜索查询
- 基于新信息更新总结
```

#### 2. 状态持久化

```
优势：
✅ 支持断点续传
✅ 便于调试和分析
✅ 可追溯研究过程

实现：
- State对象可序列化为JSON
- 保存所有搜索历史
- 记录每个段落的演化过程
```

#### 3. 模块化设计

```
优势：
✅ 各节点职责清晰
✅ 易于测试和维护
✅ 可独立优化各个环节

实现：
- 基于BaseNode的节点体系
- 统一的输入输出接口
- 标准化的Prompt设计
```

#### 4. 工具选择智能化

```
优势：
✅ LLM自动选择最合适的搜索工具
✅ 根据任务需求动态调整
✅ 支持6种不同场景的搜索

实现：
- Prompt中详细说明工具特性
- LLM输出工具名称和理由
- Agent根据工具名称执行搜索
```

---

### 8.2 技术限制

#### 1. 搜索后端单一

```
❌ 问题：
- 只支持Tavily API
- 无法更换其他搜索后端
- 存在单点依赖风险

影响：
- 如果Tavily服务不可用，整个搜索功能失效
- API成本较高
- 无法利用其他搜索源

解决方案（未来）：
- 设计搜索后端抽象层
- 支持多种搜索后端（Serper, Google, 自建等）
- 配置化切换
```

#### 2. LLM依赖性强

```
❌ 问题：
- 整个流程高度依赖LLM质量
- LLM输出不稳定可能导致流程失败
- JSON解析失败会中断流程

影响：
- 内容质量受LLM能力限制
- 可能出现格式错误
- 成本较高（多次LLM调用）

缓解措施：
- 严格的JSON Schema定义
- 输出清理和修复机制
- 重试机制（retry_helper）
```

#### 3. 并发能力有限

```
❌ 问题：
- 段落处理是串行的
- 无法并行处理多个段落
- 大型报告耗时较长

影响：
- 5个段落 × (1次初始搜索 + 2次反思) = 15次搜索
- 每次搜索 + LLM处理 ≈ 10-30秒
- 总耗时：5-15分钟

优化方向：
- 段落并行处理
- 搜索结果缓存
- 异步任务处理
```

#### 4. 缺少缓存机制

```
❌ 问题：
- 相同查询会重复搜索
- 浪费API调用额度
- 增加响应时间

影响：
- 成本增加
- 效率降低

解决方案（建议）：
- 实现搜索结果缓存（Redis）
- 实现LLM分析结果缓存
- 设置合理的过期时间
```

#### 5. 配置灵活性不足

```
❌ 问题：
- 段落数量固定（最多5个）
- 反思次数固定（2次）
- 总结长度固定（800-1200字）

影响：
- 无法根据任务复杂度调整
- 简单任务可能过度处理
- 复杂任务可能处理不足

优化方向：
- 动态调整段落数量
- 根据内容质量决定是否继续反思
- 支持自定义Prompt模板
```

---

### 8.3 性能指标

#### 典型场景性能

```
场景：分析"贵州茅台提价策略"

报告结构：
- 5个段落
- 每个段落：1次初始搜索 + 2次反思搜索

API调用统计：
- Tavily API: 15次搜索（5 × 3）
- LLM API: 
  - 报告结构生成：1次
  - 搜索查询生成：15次（5 × 3）
  - 总结生成：15次（5 × 3）
  - 最终报告格式化：1次
  - 总计：32次

时间消耗：
- Tavily搜索：15 × 3秒 = 45秒
- LLM处理：32 × 10秒 = 320秒
- 总计：约6-7分钟

成本估算（假设）：
- Tavily API：15次 × $0.01 = $0.15
- LLM API（DeepSeek）：32次 × $0.002 = $0.064
- 总计：约$0.21/报告
```

---

## 九、与MVP的关系

### 9.1 QueryEngine在MVP中的角色

```
MVP目标：搜索引擎催化因子

QueryEngine的作用：
✅ 提供新闻搜索能力（TavilyNewsAgency）
✅ 支持多种搜索工具（6种）
✅ 返回结构化的搜索结果

不需要的部分：
❌ 报告结构生成（ReportStructureNode）
❌ 反思机制（ReflectionNode）
❌ 报告格式化（ReportFormattingNode）
```

### 9.2 MVP需要的改造

#### 方案1：直接使用TavilyNewsAgency

```python
# MVP中的使用方式

from QueryEngine.tools import TavilyNewsAgency

# 初始化搜索工具
search_agency = TavilyNewsAgency(api_key=TAVILY_API_KEY)

# 搜索新闻
response = search_agency.basic_search_news(
    query="贵州茅台 提价",
    max_results=10
)

# 获取搜索结果
news_list = []
for result in response.results:
    news_list.append({
        'title': result.title,
        'url': result.url,
        'content': result.content,
        'published_date': result.published_date
    })
```

#### 方案2：创建简化的Wrapper

```python
# engines/query_engine_wrapper.py

class QueryEngineWrapper:
    """QueryEngine包装器（用于MVP）"""
    
    def __init__(self, api_key: str):
        self.search_agency = TavilyNewsAgency(api_key=api_key)
    
    def search_catalyst_news(self, stock_code: str, stock_name: str,
                            query: str, days: int = 7) -> list:
        """
        搜索催化相关新闻
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            query: 搜索主题（如"提价"）
            days: 搜索天数
        
        Returns:
            list: 新闻列表
        """
        # 构造搜索查询
        search_query = f"{stock_name} {query}"
        
        # 选择搜索工具
        if days == 1:
            response = self.search_agency.search_news_last_24_hours(search_query)
        elif days == 7:
            response = self.search_agency.search_news_last_week(search_query)
        else:
            response = self.search_agency.basic_search_news(
                search_query, 
                max_results=10
            )
        
        # 转换为标准格式
        news_list = []
        for result in response.results:
            news_list.append({
                'title': result.title,
                'url': result.url,
                'content': result.content,
                'source': 'tavily',
                'publish_time': result.published_date,
                'score': result.score
            })
        
        return news_list
```

---

## 十、总结

### 10.1 核心优势

```
1. 深度研究能力
   ✅ 多轮搜索 + 反思机制
   ✅ 生成高质量的深度报告
   ✅ 适合复杂主题的分析

2. 模块化设计
   ✅ 各节点职责清晰
   ✅ 易于维护和扩展
   ✅ 可复用的组件

3. 状态管理完善
   ✅ 完整的状态追踪
   ✅ 支持断点续传
   ✅ 便于调试分析

4. 工具选择智能化
   ✅ 6种专业搜索工具
   ✅ LLM自动选择
   ✅ 覆盖多种场景
```

### 10.2 主要限制

```
1. 搜索后端单一
   ❌ 只支持Tavily API
   ❌ 存在单点依赖

2. 并发能力有限
   ❌ 段落串行处理
   ❌ 耗时较长

3. 缺少缓存机制
   ❌ 重复搜索浪费资源
   ❌ 成本较高

4. 配置灵活性不足
   ❌ 参数固定
   ❌ 难以动态调整
```

### 10.3 MVP适配建议

```
对于"搜索引擎催化因子"MVP：

✅ 可以直接使用：
- TavilyNewsAgency（搜索工具集）
- 6种搜索工具
- 搜索结果数据结构

❌ 不需要使用：
- DeepSearchAgent（完整流程）
- 报告结构生成
- 反思机制
- 报告格式化

建议：
1. 创建简化的Wrapper类
2. 只使用搜索功能
3. 自行实现LLM催化分析
4. 实现搜索结果缓存
```

---

**文档版本**: v1.0  
**最后更新**: 2025-12-02  
**状态**: 分析完成，可用于MVP设计参考
