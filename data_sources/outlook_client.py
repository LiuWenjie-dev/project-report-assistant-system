"""
Outlook邮件客户端
使用win32com调用本地Outlook创建邮件草稿
"""

import win32com.client
from typing import Dict, Any, List, Optional
import pythoncom
from datetime import datetime

from utils.config_manager import get_config_manager


class OutlookClient:
    """Outlook客户端类"""
    
    def __init__(self):
        """初始化Outlook客户端"""
        self.config_manager = get_config_manager()
        self.email_config = self.config_manager.get_email_config()
        
        self.outlook = None
        self._initialize_outlook()
    
    def _initialize_outlook(self) -> None:
        """初始化Outlook COM对象"""
        try:
            # 初始化COM
            pythoncom.CoInitialize()
            
            # 创建Outlook应用程序对象
            self.outlook = win32com.client.Dispatch("Outlook.Application")
            
        except Exception as e:
            print(f"错误：初始化Outlook失败: {e}")
            self.outlook = None
    
    def create_email_draft(self, subject: str, body: str, 
                          to_recipients: List[str] = None,
                          cc_recipients: List[str] = None,
                          bcc_recipients: List[str] = None) -> bool:
        """
        创建邮件草稿
        
        Args:
            subject: 邮件主题
            body: 邮件正文
            to_recipients: 收件人列表
            cc_recipients: 抄送人列表
            bcc_recipients: 密送人列表
            
        Returns:
            是否成功创建
        """
        if not self.outlook:
            print("错误：Outlook未初始化")
            return False
        
        try:
            # 创建新邮件
            mail = self.outlook.CreateItem(0)  # 0 = olMailItem
            
            # 设置邮件属性
            mail.Subject = subject
            
            # 设置收件人
            if to_recipients:
                mail.To = "; ".join(to_recipients)
            
            if cc_recipients:
                mail.CC = "; ".join(cc_recipients)
            
            if bcc_recipients:
                mail.BCC = "; ".join(bcc_recipients)
            
            # 设置邮件正文（HTML格式）
            mail.BodyFormat = 2  # 2 = olFormatHTML
            mail.HTMLBody = self._format_html_body(body)
            
            # 显示邮件窗口（草稿模式）
            mail.Display(False)  # False = 不立即发送
            
            print("成功：Outlook邮件草稿已创建")
            return True
            
        except Exception as e:
            print(f"错误：创建邮件草稿失败: {e}")
            return False
    
    def _format_html_body(self, plain_text: str) -> str:
        """
        将纯文本格式化为HTML邮件正文
        
        Args:
            plain_text: 纯文本内容
            
        Returns:
            HTML格式的邮件正文
        """
        # 基本HTML模板
        html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        h1 {{
            font-size: 24px;
        }}
        h2 {{
            font-size: 20px;
            margin-top: 30px;
        }}
        h3 {{
            font-size: 16px;
            margin-top: 20px;
        }}
        p {{
            margin: 10px 0;
        }}
        ul, ol {{
            margin: 10px 0 10px 20px;
        }}
        li {{
            margin: 5px 0;
        }}
        .section {{
            background-color: #f8f9fa;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .highlight {{
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .issue-list {{
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 15px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .link {{
            color: #3498db;
            text-decoration: none;
        }}
        .link:hover {{
            text-decoration: underline;
        }}
        .signature {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
        }}
        .timestamp {{
            color: #999;
            font-size: 12px;
            margin-top: 5px;
        }}
    </style>
</head>
<body>
    {content}
    
    <div class="signature">
        {signature}
        <div class="timestamp">
            邮件生成时间: {timestamp}
        </div>
    </div>
</body>
</html>"""
        
        # 将纯文本转换为HTML
        html_content = self._convert_text_to_html(plain_text)
        
        # 获取签名
        signature = self.email_config.get("signature", "Best regards,<br>[Your Name]")
        
        # 获取当前时间
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 填充模板
        return html_template.format(
            content=html_content,
            signature=signature,
            timestamp=timestamp
        )
    
    def _convert_text_to_html(self, text: str) -> str:
        """
        将纯文本转换为HTML
        
        Args:
            text: 纯文本
            
        Returns:
            HTML内容
        """
        if not text:
            return ""
        
        # 分割段落
        paragraphs = text.split('\n\n')
        html_paragraphs = []
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                continue
            
            # 检查是否是标题
            if paragraph.startswith('# '):
                html_paragraphs.append(f'<h1>{paragraph[2:]}</h1>')
            elif paragraph.startswith('## '):
                html_paragraphs.append(f'<h2>{paragraph[3:]}</h2>')
            elif paragraph.startswith('### '):
                html_paragraphs.append(f'<h3>{paragraph[4:]}</h3>')
            else:
                # 处理普通段落
                lines = paragraph.split('\n')
                processed_lines = []
                
                for line in lines:
                    # 处理项目符号
                    if line.strip().startswith('- ') or line.strip().startswith('• '):
                        line = f'<li>{line.strip()[2:]}</li>'
                    # 处理数字列表
                    elif line.strip() and line.strip()[0].isdigit() and '. ' in line:
                        parts = line.split('. ', 1)
                        if len(parts) == 2:
                            line = f'<li>{parts[1]}</li>'
                    
                    # 处理链接
                    if 'http://' in line or 'https://' in line:
                        import re
                        urls = re.findall(r'https?://[^\s]+', line)
                        for url in urls:
                            line = line.replace(url, f'<a href="{url}" class="link">{url}</a>')
                    
                    processed_lines.append(line)
                
                # 如果包含列表项，包装在ul/ol中
                if any('<li>' in line for line in processed_lines):
                    list_html = '<ul>' + '\n'.join(processed_lines) + '</ul>'
                    html_paragraphs.append(list_html)
                else:
                    html_paragraphs.append('<p>' + '<br>'.join(processed_lines) + '</p>')
        
        return '\n'.join(html_paragraphs)
    
    def create_weekly_report_email(self, report_data: Dict[str, Any], 
                                  project_name: str = None) -> bool:
        """
        创建周报邮件
        
        Args:
            report_data: 报告数据字典
            project_name: 项目名称
            
        Returns:
            是否成功创建
        """
        # 构建邮件主题
        subject_prefix = self.email_config.get("subject_prefix", "[Weekly Report]")
        if project_name:
            subject = f"{subject_prefix} {project_name} - {datetime.now().strftime('%Y-%m-%d')}"
        else:
            subject = f"{subject_prefix} {datetime.now().strftime('%Y-%m-%d')}"
        
        # 构建邮件正文
        body = self._format_weekly_report_body(report_data)
        
        # 获取默认收件人
        default_to = self.email_config.get("default_to", "")
        default_cc = self.email_config.get("default_cc", "")
        
        to_recipients = [email.strip() for email in default_to.split(';') if email.strip()]
        cc_recipients = [email.strip() for email in default_cc.split(';') if email.strip()]
        
        # 创建邮件
        return self.create_email_draft(
            subject=subject,
            body=body,
            to_recipients=to_recipients,
            cc_recipients=cc_recipients
        )
    
    def _format_weekly_report_body(self, report_data: Dict[str, Any]) -> str:
        """
        格式化周报正文
        
        Args:
            report_data: 报告数据
            
        Returns:
            格式化的邮件正文
        """
        sections = []
        
        # 1. 项目整体状态
        if "next_milestone" in report_data:
            sections.append(f"一、项目整体状态\n{report_data['next_milestone']}")
        
        # 2. Highlight
        if "highlight_blocked" in report_data:
            sections.append(f"二、Highlight\n{report_data['highlight_blocked']}")
        
        # 3. 本周测试进展
        if "weekly_test_progress" in report_data:
            sections.append(f"三、本周测试进展\n{report_data['weekly_test_progress']}")
        else:
            sections.append("三、本周测试进展\n[请在此处填写本周测试进展]")
        
        # 4. 整体测试进展
        if "test_status" in report_data:
            sections.append(f"四、整体测试进展\n{report_data['test_status']}")
        
        # 5. 当前严重问题
        if "priority_issues" in report_data:
            sections.append(f"五、当前严重问题\n{report_data['priority_issues']}")
        
        # 6. 下周测试计划
        if "next_action" in report_data:
            sections.append(f"六、下周测试计划\n{report_data['next_action']}")
        
        # 添加链接
        links_section = "\n\n相关链接：\n"
        if "confluence_url" in report_data:
            links_section += f"• Confluence页面: {report_data['confluence_url']}\n"
        if "jira_dashboard_url" in report_data:
            links_section += f"• Jira看板: {report_data['jira_dashboard_url']}\n"
        
        sections.append(links_section)
        
        return "\n\n".join(sections)
    
    def test_connection(self) -> bool:
        """测试Outlook连接"""
        try:
            if not self.outlook:
                self._initialize_outlook()
            
            return self.outlook is not None
        except:
            return False
    
    def cleanup(self) -> None:
        """清理COM资源"""
        try:
            if self.outlook:
                self.outlook = None
            pythoncom.CoUninitialize()
        except:
            pass


# 单例实例
_outlook_client: Optional[OutlookClient] = None

def get_outlook_client() -> OutlookClient:
    """获取Outlook客户端单例"""
    global _outlook_client
    if _outlook_client is None:
        _outlook_client = OutlookClient()
    return _outlook_client