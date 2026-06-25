# 报告助手 - 周报生成工具

一个简约、高可读性的工具，用于从Confluence和Jira自动提取数据生成周报。

## 功能特点

1. **数据自动提取**
   - 从Confluence页面提取Next Milestone信息
   - 从Confluence页面提取Highlight & Blocked Issues信息
   - 从Confluence页面提取Test Status信息
   - 从Confluence页面提取Next Action信息
   - 从Jira提取P0/P1严重问题

2. **Jira问题筛选**
   - 支持按项目、状态、优先级筛选
   - 支持自定义JQL查询
   - 实时查看问题详情

3. **简约界面**
   - 直观的操作界面
   - 实时状态反馈
   - 一键数据获取

## 快速开始

### 1. 安装依赖
```bash
cd report_assistant
pip install -r requirements.txt
```

### 2. 配置环境
复制 `.env.example` 为 `.env` 并填写您的配置：
```bash
cp .env.example .env
```

编辑 `.env` 文件：
```env
# Jira配置
JIRA_BASE_URL=https://your-jira-instance.atlassian.net
JIRA_USERNAME=your-email@example.com
JIRA_API_TOKEN=your-api-token

# Confluence配置
CONFLUENCE_BASE_URL=https://your-confluence.atlassian.net
CONFLUENCE_USERNAME=your-email@example.com
CONFLUENCE_API_TOKEN=your-api-token
```

### 3. 运行应用
```bash
python src/main.py
```

## 使用说明

### 主界面
1. **项目设置**
   - 选择项目（SWPL, A113X, A311D等）
   - 输入Confluence页面URL
   - 点击"获取数据"按钮

2. **报告内容**
   - 项目整体情况：自动从Confluence Next Milestone提取
   - 本周测试进展：手动填写
   - Highlight：自动从Confluence Highlight & Blocked提取
   - 下周测试计划：自动从Confluence Next Action提取

3. **Jira筛选器**
   - 点击"Jira筛选器"按钮打开筛选窗口
   - 按项目、状态、优先级筛选问题
   - 查看问题详情

### 数据提取流程
1. 选择项目和输入Confluence URL
2. 点击"获取数据"按钮
3. 工具自动：
   - 连接到Confluence提取页面信息
   - 连接到Jira查询P0/P1问题
   - 填充到对应的编辑区域

## 项目结构

```
report_assistant/
├── src/main.py              # 主程序入口
├── gui/
│   ├── dashboard_window.py  # 主界面
│   ├── jira_filter_window.py # Jira筛选器
│   └── login_dialog.py      # 登录配置
├── data_sources/
│   ├── confluence_client.py # Confluence客户端
│   └── jira_client.py       # Jira客户端
├── business/
│   └── template_assembler.py # 模板组装器
├── utils/
│   ├── config_manager.py    # 配置管理
│   └── text_formatter.py    # 文本格式化
└── tests/                   # 测试文件
```

## 配置说明

### Jira API Token
1. 登录到您的Jira实例
2. 点击右上角头像 → "个人设置"
3. 选择"安全" → "创建和管理API令牌"
4. 创建新令牌并复制

### Confluence API Token
1. 登录到您的Confluence实例
2. 点击右上角头像 → "个人设置"
3. 选择"安全" → "创建和管理API令牌"
4. 创建新令牌并复制

## 常见问题

### 1. 连接失败
- 检查网络连接
- 验证API令牌是否正确
- 确认URL格式正确

### 2. 数据提取失败
- 检查Confluence页面结构
- 确认有访问权限
- 验证页面包含所需信息

### 3. Jira筛选器无数据
- 检查Jira配置
- 确认项目存在
- 验证筛选条件

## 开发说明

### 代码风格
- 简约、高可读性
- 避免重复代码
- 方便随时修改和添加新功能

### 扩展功能
1. 添加新的数据源
2. 自定义报告模板
3. 导出功能（PDF、Word等）
4. 邮件发送功能（后续考虑）

## 许可证

MIT License