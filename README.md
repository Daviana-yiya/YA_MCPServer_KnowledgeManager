## YA_MCPServer_KnowledgeManager

基于语义搜索与智能组织的个性化知识管理 MCP Server，支持笔记的增删改查、混合搜索、主题总结与网页内容抓取。

### 组员信息

| 姓名 | 学号 | 分工 | 备注 |
| :--: | :--: | :--: | :--: |
|      |      |      |      |
|      |      |      |      |
|      |      |      |      |

### Tool 列表

| 工具名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| add_note | 添加新笔记到知识库 | title, content, tags（可选） | 笔记对象（id,title,content,tags,created_at） | tags 为空时使用jieba.analyse自动提取关键词 |
| search_notes | 根据提取出的关键词来混合搜索笔记（语义+关键词+标签） | query, top_k（默认5） | 结果列表（含相关性得分） | RRF 融合排名; 传入的query是用llm根据用户输入总结出的|
| update_note | 更新已有笔记 | note_id, title/content/tags（可选） | 更新后的笔记对象 | 仅传入需要修改的字段；用户传入更新笔记的需求时，在调用update_note之前要调用search_notes |
| delete_note | 删除指定笔记 | note_id | {success, note_id} | 同步删除向量存储；用户传入删除笔记的需求时，在调用delete_note之前要调用search_notes |
| summarize_topic | 检索主题相关笔记并汇总 | topic, top_k（默认5） | {topic, note_count, notes, combined_content} | 传入的topic是用llm根据用户输入总结出的；输出的combined_content还需供 LLM 二次总结 |
| fetch_url | 抓取网页标题和正文 | url | {title, content} | 返回后可调用 add_note 存入知识库 |

### Resource 列表

| 资源名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| knowledge://notes | 获取所有笔记列表 | 无 | 笔记列表（id,title,tags,created_at,updated_at） | JSON 格式 |
| knowledge://tags | 获取所有标签列表 | 无 | 标签字符串列表 | 去重排序 |
| file:///README.md | 获取项目 README | 无 | README.md 文件内容 | 纯文本 |
| file:///logs/{path} | 获取指定日志文件内容 | path（日志文件名） | 日志文件内容 | 纯文本 |

### Prompts 列表

| 指令名称 | 功能描述 | 输入 | 输出 | 备注 |
| :------: | :------: | :--: | :--: | :--: |
| daily_review | 生成每日知识复习提示词 | days（默认7） | 近期笔记复习提示词文本 | 引导 LLM 对笔记进行要点总结和复习建议 |
| knowledge_gap | 分析指定主题的知识盲区 | topic, top_k（默认9999） | 知识盲区分析提示词文本 | topic 由 LLM 提炼后传入；引导 LLM 指出未覆盖的子主题并给出学习建议 |
| connect_ideas | 找出两个概念之间的联系 | concept_a, concept_b, top_k（默认3） | 概念关联分析提示词文本 | concept_a/b 由 LLM 提炼后传入；引导 LLM 分析相似点、区别和结合方式 |

### 项目结构

- `core/`: 核心业务逻辑层
  - `knowledge_manager.py`: 知识库管理器，整合 SQLite 与 ChromaDB，提供笔记增删改查与混合搜索
  - `db.py`: SQLite 数据库操作封装（aiosqlite 异步实现）
  - `vector_store.py`: ChromaDB 向量存储封装，支持语义搜索
  - `keyword_extractor.py`: 基于 jieba.analyse 的关键词自动提取
  - `web_fetcher.py`: 网页内容抓取（httpx + BeautifulSoup4）
  - `models.py`: 数据模型定义（Note、NoteCreate、NoteUpdate、SearchResult）
- `tools/`: MCP Tool 实现（add_note、search_notes、update_note、delete_note、summarize_topic、fetch_url）
- `resources/`: MCP Resource 实现（knowledge://notes、knowledge://tags、README、日志）
- `prompts/`: MCP Prompt 实现（daily_review、knowledge_gap、connect_ideas）
- `config.yaml`: 服务器配置，额外添加了 `knowledge` 配置项，包含 SQLite 数据库路径（`knowledge.database.path`）、ChromaDB 向量存储路径（`knowledge.vector_store.path`）和集合名称（`knowledge.vector_store.collection_name`）
- `setup.py`: 依赖检查安装与向量存储预热（新增）
- `tests/`: 测试用例目录（新增）
  - `test_knowledge_manager.py`: core 层单元测试
  - `test_tools.py`: tools 层集成测试
- `data/`: 运行时数据目录，启动服务器后自动生成，包含 SQLite 数据库与 ChromaDB 向量存储

### 其他需要说明的情况

- 未使用 `sops` 模块，项目无需密钥配置
- 使用了 PyTorch 深度学习框架：通过 `sentence-transformers` 库加载预训练模型 `paraphrase-multilingual-MiniLM-L12-v2`，用于笔记的语义向量化，模型首次运行时会自动从 HuggingFace 下载（约 400MB），后续从本地缓存加载
- 使用了机器学习模型：`paraphrase-multilingual-MiniLM-L12-v2` 为多语言句向量模型，支持中英文语义搜索；关键词提取使用 `jieba.analyse`（基于 TF-IDF，无需额外模型）
- 添加了tests文件用于对 `core` 与 `tools` 进行单元测试