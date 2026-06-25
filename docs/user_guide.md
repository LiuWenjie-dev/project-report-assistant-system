# 报告助手用户指南

## 概述

报告助手是一个桌面应用程序，帮助您一键生成周报邮件。它从Confluence页面提取项目状态信息，从Jira查询P0/P1问题，并自动创建Outlook邮件草稿。

## 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.10或更高版本
- **Outlook**: Microsoft Outlook桌面版（Office标准版/365）
- **网络**: 可访问Confluence和Jira服务器

## 安装步骤

### 1. 安装Python依赖

```bash
cd report_assistant
pip install -r requirements.txt
```

### 2. 配置环境变量

1. 复制 `.env.example` 为 `.env`
2. 编辑 `.env` 文件，填写您的配置：

```ini
# Confluence配置
CONFLUENCE_BASE_URL=https://your-confluence.atlassian.net
CONFLUENCE_API_TOKEN=your_api_token_here
CONFLUENCE_USERNAME=your_email@example.com

# Jira配置
JIRA_BASE_URL=https://your-jira.atlassian.net
JIRA_API_TOKEN=your_api_token_here
JIRA_USERNAME=your_email@example.com

# 邮件配置
DEFAULT_TO_EMAIL=recipient@example.com
DEFAULT_CC_EMAIL=cc@example.com
DEFAULT_EMAIL_SUBJECT_PREFIX=[Weekly Report]
```

### 3. 获取API Token

#### Confluence API Token
1. 登录Confluence
2. 点击右上角头像 → "个人设置"
3. 选择"安全" → "创建和管理API令牌"
4. 创建新令牌并复制

#### Jira API Token
1. 登录Jira
2. 点击右上角头像 → "个人设置"
3. 选择"安全" → "API令牌"
4. 创建新令牌并复制

## 使用指南

### 首次运行

1. 运行主程序：
   ```bash
   python src/main.py
   ```

2. 程序会自动检查依赖并创建默认配置文件

### 主界面说明

#### 左侧面板（配置区）

1. **项目配置**
   - Jira项目Key：输入或选择项目Key（如：PROJ）
   - Confluence URL：输入Confluence页面URL
   - 加载项目配置：从历史记录加载配置

2. **数据获取**
   - 本周测试进展：手动填写本周工作内容
   - 一键获取数据：从Confluence和Jira提取数据

3. **邮件配置**
   - 收件人：默认收件人邮箱
   - 抄送：抄送邮箱
   - 主题前缀：邮件主题前缀

4. **操作**
   - 预览完整报告：查看生成的完整报告
   - 一键生成Outlook邮件：创建邮件草稿
   - 保存当前配置：保存设置到本地

#### 右侧面板（编辑预览区）

6个标签页分别显示：
1. 项目整体状态（从Confluence提取）
2. Highlight（从Confluence提取）
3. 本周测试进展（手动填写）
4. 整体测试进展（从Confluence提取）
5. 当前严重问题（从Jira提取的P0/P1问题）
6. 下周测试计划（从Confluence提取）

### 工作流程

1. **配置项目**
   - 输入Jira项目Key
   - 输入Confluence页面URL
   - 点击"加载项目配置"（如有历史记录）

2. **填写本周工作**
   - 在"本周测试进展"区域填写本周工作内容

3. **获取数据**
   - 点击"一键获取数据"
   - 等待数据提取完成（显示进度条）

4. **编辑和验证**
   - 检查各个标签页的内容
   - 查看数据验证结果（底部显示）

5. **生成邮件**
   - 点击"预览完整报告"查看完整内容
   - 点击"一键生成Outlook邮件"
   - Outlook会自动弹出邮件草稿窗口

6. **发送邮件**
   - 在Outlook中检查邮件内容
   - 补充收件人/抄送人
   - 点击发送或保存为草稿

## 功能特性

### 数据提取
- **Confluence**: 自动提取Next Milestone、Highlight、Test Status、Next Action
- **Jira**: 查询P0/P1未关闭问题，统计问题数量
- **智能解析**: 使用关键词匹配提取相关内容

### 邮件生成
- **Outlook集成**: 直接调用本地Outlook创建邮件
- **HTML格式**: 自动生成美观的HTML邮件
- **模板化**: 标准6段式周报格式

### 用户体验
- **多线程**: 数据获取不阻塞UI
- **进度显示**: 实时显示数据获取进度
- **数据验证**: 自动验证数据完整性
- **配置保存**: 保存项目和邮件配置

## 常见问题

### Q1: 无法连接到Confluence/Jira
- 检查网络连接
- 验证API Token和用户名是否正确
- 确认服务器地址是否正确

### Q2: Outlook邮件没有弹出
- 确认Outlook已安装并运行
- 检查Windows服务中Outlook相关服务是否正常
- 尝试重新启动Outlook

### Q3: 数据提取不完整
- 检查Confluence页面结构
- 确认页面包含所需的关键词（如"Next Milestone"）
- 尝试手动在相应标签页中编辑内容

### Q4: 程序启动失败
- 检查Python版本（需要3.10+）
- 确认所有依赖已安装
- 查看错误信息并参考安装步骤

## 高级配置

### 自定义提取关键词
如需修改Confluence内容提取的关键词，可以编辑 `data_sources/confluence_client.py` 中的关键词列表。

### 修改邮件模板
邮件HTML模板位于 `data_sources/outlook_client.py` 中的 `_format_html_body` 方法。

### 添加项目缓存
项目配置自动保存到 `config/projects.json`，可以手动编辑该文件添加常用项目。

## 技术支持

如遇问题，请：
1. 查看错误日志
2. 检查配置文件
3. 参考本用户指南
4. 联系开发人员

## 版本历史

- v1.0.0 (2024-01-01): 初始版本发布
  - 基础Confluence/Jira数据提取
  - Outlook邮件生成
  - PyQt6图形界面

---

**注意**: 本工具仅用于个人工作效率提升，请遵守公司数据安全政策，妥善保管API Token等敏感信息。