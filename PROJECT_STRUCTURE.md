# 报告助手项目结构

## 四层架构设计

### 1. 数据源采集层 (data_sources/)
- **confluence_client.py**: Confluence REST API客户端，提取页面数据
- **jira_client.py**: Jira REST API客户端，查询P0/P1问题
- **outlook_client.py**: Outlook COM接口客户端，生成邮件草稿

### 2. 业务模板组装层 (business/)
- **template_assembler.py**: 邮件模板组装器，格式化6段式报告
- **report_generator.py**: 报告生成器，协调数据采集和模板组装

### 3. GUI交互界面层 (gui/)
- **dashboard_window.py**: 主窗口PyQt6界面
- **login_dialog.py**: 登录配置对话框
- **multi_select_combo.py**: 多选组合框组件

### 4. 公共工具底层层 (utils/)
- **config_manager.py**: 配置管理（.env, config.json）
- **text_formatter.py**: 文本格式化工具
- **cache_manager.py**: 缓存管理
- **exception_handler.py**: 异常处理

### 5. 主程序入口 (src/)
- **main.py**: 应用程序入口点

### 6. 配置文件 (config/)
- **config.json**: 应用程序配置
- **projects.json**: 项目配置缓存

### 7. 资源文件 (resources/)
- **icons/**: 图标资源
- **templates/**: 邮件模板

### 8. 测试文件 (tests/)
- **test_confluence_client.py**
- **test_jira_client.py**
- **test_template_assembler.py**
- **test_gui.py**

### 9. 文档 (docs/)
- **user_guide.md**: 用户指南
- **api_reference.md**: API参考

## 数据流
1. 用户输入项目配置 → config_manager
2. 点击拉取数据 → confluence_client + jira_client
3. 数据返回 → template_assembler
4. 用户编辑 → report_editor_widget
5. 点击生成邮件 → outlook_client
6. Outlook弹出邮件草稿

## 依赖管理
- requirements.txt: Python包依赖
- .env.example: 环境变量示例