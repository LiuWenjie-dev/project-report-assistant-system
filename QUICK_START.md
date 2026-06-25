# 快速开始指南

## 1. 环境配置

### 1.1 复制配置文件
```bash
cd report_assistant
copy .env.example .env
```

### 1.2 编辑配置文件
打开 `.env` 文件，填写以下配置：

```ini
# Confluence配置
CONFLUENCE_URL=https://your-confluence.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token

# Jira配置  
JIRA_URL=https://your-jira.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token

# 项目配置
DEFAULT_PROJECT_KEY=SWPL
DEFAULT_CONFLUENCE_PAGE_ID=123456
```

### 1.3 获取API Token
- **Confluence**: 访问 https://id.atlassian.com/manage-profile/security/api-tokens
- **Jira**: 同上，使用相同的API Token

## 2. 运行应用程序

### 2.1 启动主程序
```bash
python src/main.py
```

### 2.2 主界面说明
主界面包含6个部分：

1. **项目整体情况** - 从Confluence Next Milestone提取
2. **本周测试进展** - 手动输入
3. **Highlight** - 从Confluence Highlight & Blocked提取
4. **整体测试进展** - 从Confluence Test Status提取
5. **当前严重问题** - 从Jira P0/P1问题提取
6. **下周测试计划** - 从Confluence Next Action提取

### 2.3 基本操作流程

1. **选择项目**: 从下拉菜单中选择项目
2. **获取数据**: 点击"获取数据"按钮
3. **编辑内容**: 在文本框中编辑内容
4. **预览报告**: 点击"预览报告"按钮
5. **Jira筛选**: 点击"Jira筛选器"按钮查看问题

## 3. 高级功能

### 3.1 Jira筛选器
- 支持按项目、状态、优先级筛选
- 支持自定义JQL查询
- 实时查看问题详情

### 3.2 数据提取
- 自动从Confluence页面提取结构化数据
- 支持多个项目配置
- 缓存机制提高性能

## 4. 故障排除

### 4.1 常见问题

**Q: 无法连接到Confluence/Jira**
A: 检查 `.env` 文件中的URL和API Token

**Q: 数据提取失败**
A: 检查Confluence页面ID是否正确

**Q: Jira查询无结果**
A: 检查项目Key和权限

### 4.2 日志查看
```bash
# 查看详细日志
python src/main.py --debug
```

## 5. 项目结构

```
report_assistant/
├── src/main.py              # 主程序入口
├── gui/                     # 界面文件
│   ├── dashboard_window.py  # 主界面
│   └── jira_filter_window.py # Jira筛选器
├── data_sources/           # 数据源
│   ├── confluence_client.py
│   └── jira_client.py
├── business/               # 业务逻辑
│   └── template_assembler.py
├── utils/                  # 工具类
│   ├── config_manager.py
│   └── text_formatter.py
└── tests/                  # 测试文件
```

## 6. 扩展开发

### 6.1 添加新数据源
1. 在 `data_sources/` 创建新客户端
2. 在 `template_assembler.py` 中添加提取逻辑
3. 在 `dashboard_window.py` 中添加显示区域

### 6.2 修改界面布局
编辑 `dashboard_window.py` 中的布局代码

### 6.3 添加新功能
遵循现有代码结构，保持简约风格

---

**注意**: 本工具设计为简约、高可读性、方便修改。所有代码都遵循这一原则，便于团队协作和功能扩展。