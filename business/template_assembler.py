"""
模板组装器
负责将各个数据源的数据组装成完整的周报模板
"""

from typing import Dict, Any, Optional
from datetime import datetime

from data_sources.confluence_client import get_confluence_client
from data_sources.jira_client import get_jira_client
from utils.config_manager import get_config_manager


class TemplateAssembler:
    """模板组装器类"""
    
    def __init__(self):
        """初始化模板组装器"""
        self.config_manager = get_config_manager()
        self.confluence_client = get_confluence_client()
        self.jira_client = get_jira_client()
    
    def assemble_weekly_report(self, project_key: str, confluence_url: str, 
                              weekly_test_progress: str = None) -> Dict[str, Any]:
        """
        组装周报
        
        Args:
            project_key: Jira项目Key
            confluence_url: Confluence页面URL
            weekly_test_progress: 本周测试进展（可选）
            
        Returns:
            完整的周报数据
        """
        report_data = {
            "project_key": project_key,
            "confluence_url": confluence_url,
            "generated_time": datetime.now().isoformat(),
            "sections": {}
        }
        
        try:
            # 1. 从Confluence提取数据
            print("正在从Confluence提取数据...")
            confluence_data = self.confluence_client.extract_all_sections(confluence_url)
            
            report_data["sections"]["next_milestone"] = confluence_data.get("next_milestone", "")
            report_data["sections"]["highlight_blocked"] = confluence_data.get("highlight_blocked", "")
            report_data["sections"]["test_status"] = confluence_data.get("test_status", "")
            report_data["sections"]["next_action"] = confluence_data.get("next_action", "")
            report_data["page_title"] = confluence_data.get("page_title", "")
            
            # 2. 从Jira提取P0/P1问题
            print("正在从Jira提取P0/P1问题...")
            jira_data = self.jira_client.get_priority_issues(project_key)
            
            report_data["sections"]["priority_issues"] = self.jira_client.format_issues_for_email(jira_data)
            report_data["jira_dashboard_url"] = jira_data.get("dashboard_url", "")
            report_data["jira_issue_count"] = jira_data.get("total", 0)
            
            # 3. 本周测试进展
            if weekly_test_progress:
                report_data["sections"]["weekly_test_progress"] = weekly_test_progress
            else:
                report_data["sections"]["weekly_test_progress"] = "[请在此处填写本周测试进展]"
            
            # 4. 组装完整报告
            report_data["complete_report"] = self._assemble_complete_report(report_data)
            
            print("周报组装完成")
            return report_data
            
        except Exception as e:
            print(f"错误：组装周报失败: {e}")
            # 返回错误状态
            report_data["error"] = str(e)
            report_data["complete_report"] = f"组装周报时出错: {e}"
            return report_data
    
    def _assemble_complete_report(self, report_data: Dict[str, Any]) -> str:
        """
        组装完整报告文本
        
        Args:
            report_data: 报告数据
            
        Returns:
            完整的报告文本
        """
        sections = report_data["sections"]
        project_key = report_data.get("project_key", "")
        page_title = report_data.get("page_title", "")
        
        # 构建报告标题
        report_lines = []
        report_lines.append(f"{page_title if page_title else '项目周报'}")
        report_lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"项目: {project_key}")
        report_lines.append("")
        
        # 1. 项目整体状态
        if sections.get("next_milestone"):
            report_lines.append("一、项目整体状态")
            report_lines.append(sections["next_milestone"])
            report_lines.append("")
        
        # 2. Highlight
        if sections.get("highlight_blocked"):
            report_lines.append("二、Highlight")
            report_lines.append(sections["highlight_blocked"])
            report_lines.append("")
        
        # 3. 本周测试进展
        if sections.get("weekly_test_progress"):
            report_lines.append("三、本周测试进展")
            report_lines.append(sections["weekly_test_progress"])
            report_lines.append("")
        
        # 4. 整体测试进展
        if sections.get("test_status"):
            report_lines.append("四、整体测试进展")
            report_lines.append(sections["test_status"])
            report_lines.append("")
        
        # 5. 当前严重问题
        if sections.get("priority_issues"):
            report_lines.append("五、当前严重问题")
            report_lines.append(sections["priority_issues"])
            report_lines.append("")
        
        # 6. 下周测试计划
        if sections.get("next_action"):
            report_lines.append("六、下周测试计划")
            report_lines.append(sections["next_action"])
            report_lines.append("")
        
        # 添加相关链接
        report_lines.append("相关链接")
        if report_data.get("confluence_url"):
            report_lines.append(f"• Confluence页面: {report_data['confluence_url']}")
        
        if report_data.get("jira_dashboard_url"):
            report_lines.append(f"• Jira看板: {report_data['jira_dashboard_url']}")
        
        return "\n".join(report_lines)
    
    def format_report_for_email(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化报告用于邮件发送
        
        Args:
            report_data: 原始报告数据
            
        Returns:
            格式化后的邮件数据
        """
        sections = report_data.get("sections", {})
        
        email_data = {
            "next_milestone": sections.get("next_milestone", ""),
            "highlight_blocked": sections.get("highlight_blocked", ""),
            "weekly_test_progress": sections.get("weekly_test_progress", "[请在此处填写本周测试进展]"),
            "test_status": sections.get("test_status", ""),
            "priority_issues": sections.get("priority_issues", "当前无P0/P1未关闭问题。"),
            "next_action": sections.get("next_action", ""),
            "confluence_url": report_data.get("confluence_url", ""),
            "jira_dashboard_url": report_data.get("jira_dashboard_url", ""),
            "project_key": report_data.get("project_key", ""),
            "page_title": report_data.get("page_title", "")
        }
        
        return email_data
    
    def validate_report_data(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证报告数据完整性
        
        Args:
            report_data: 报告数据
            
        Returns:
            验证结果
        """
        validation_result = {
            "is_valid": True,
            "missing_sections": [],
            "warnings": [],
            "suggestions": []
        }
        
        sections = report_data.get("sections", {})
        
        # 检查必要部分
        required_sections = ["next_milestone", "highlight_blocked", "test_status", "next_action"]
        for section in required_sections:
            if not sections.get(section) or sections[section].endswith("未找到相关内容"):
                validation_result["missing_sections"].append(section)
                validation_result["is_valid"] = False
        
        # 检查本周测试进展
        weekly_progress = sections.get("weekly_test_progress", "")
        if not weekly_progress or weekly_progress == "[请在此处填写本周测试进展]":
            validation_result["warnings"].append("本周测试进展需要手动填写")
        
        # 检查Jira问题
        if report_data.get("jira_issue_count", 0) == 0:
            validation_result["suggestions"].append("未发现P0/P1问题，请确认查询条件是否正确")
        
        # 提供建议
        if len(validation_result["missing_sections"]) > 0:
            validation_result["suggestions"].append(
                f"以下部分未找到：{', '.join(validation_result['missing_sections'])}，请检查Confluence页面结构"
            )
        
        return validation_result


# 单例实例
_template_assembler: Optional[TemplateAssembler] = None

def get_template_assembler() -> TemplateAssembler:
    """获取模板组装器单例"""
    global _template_assembler
    if _template_assembler is None:
        _template_assembler = TemplateAssembler()
    return _template_assembler