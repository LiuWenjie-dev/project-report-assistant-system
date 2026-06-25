"""
文本格式化工具
提供各种文本格式化功能
"""

import re
from typing import List, Dict, Any
from datetime import datetime


class TextFormatter:
    """文本格式化工具类"""
    
    @staticmethod
    def format_timestamp(timestamp: str = None, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化时间戳
        
        Args:
            timestamp: 时间戳字符串（ISO格式），如果为None则使用当前时间
            format_str: 输出格式
            
        Returns:
            格式化后的时间字符串
        """
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                return dt.strftime(format_str)
            except:
                pass
        
        return datetime.now().strftime(format_str)
    
    @staticmethod
    def truncate_text(text: str, max_length: int = 100, ellipsis: str = "...") -> str:
        """
        截断文本
        
        Args:
            text: 原始文本
            max_length: 最大长度
            ellipsis: 省略号
            
        Returns:
            截断后的文本
        """
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(ellipsis)] + ellipsis
    
    @staticmethod
    def clean_html_tags(html_text: str) -> str:
        """
        清理HTML标签
        
        Args:
            html_text: 包含HTML标签的文本
            
        Returns:
            清理后的纯文本
        """
        if not html_text:
            return ""
        
        # 移除HTML标签
        clean = re.sub(r'<[^>]+>', '', html_text)
        
        # 替换HTML实体
        clean = clean.replace('&nbsp;', ' ')
        clean = clean.replace('&', '&')
        clean = clean.replace('<', '<')
        clean = clean.replace('>', '>')
        clean = clean.replace('"', '"')
        clean = clean.replace('&#39;', "'")
        
        # 合并多个空格
        clean = re.sub(r'\s+', ' ', clean)
        
        return clean.strip()
    
    @staticmethod
    def format_list_items(items: List[str], bullet: str = "•") -> str:
        """
        格式化列表项
        
        Args:
            items: 列表项
            bullet: 项目符号
            
        Returns:
            格式化后的列表文本
        """
        if not items:
            return ""
        
        formatted = []
        for item in items:
            if item.strip():
                formatted.append(f"{bullet} {item.strip()}")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_table(data: List[Dict[str, Any]], headers: List[str] = None) -> str:
        """
        格式化表格数据
        
        Args:
            data: 表格数据
            headers: 表头（如果为None则使用字典键）
            
        Returns:
            格式化后的表格文本
        """
        if not data:
            return ""
        
        # 确定表头
        if headers is None:
            headers = list(data[0].keys())
        
        # 计算每列最大宽度
        col_widths = []
        for i, header in enumerate(headers):
            max_width = len(str(header))
            for row in data:
                if i < len(headers):
                    value = str(row.get(headers[i], ""))
                    max_width = max(max_width, len(value))
            col_widths.append(max_width)
        
        # 构建表格
        lines = []
        
        # 表头
        header_line = "|"
        separator_line = "|"
        for i, header in enumerate(headers):
            header_line += f" {header:<{col_widths[i]}} |"
            separator_line += f" {'-' * col_widths[i]} |"
        
        lines.append(header_line)
        lines.append(separator_line)
        
        # 数据行
        for row in data:
            row_line = "|"
            for i, header in enumerate(headers):
                value = str(row.get(header, ""))
                row_line += f" {value:<{col_widths[i]}} |"
            lines.append(row_line)
        
        return "\n".join(lines)
    
    @staticmethod
    def extract_links(text: str) -> List[Dict[str, str]]:
        """
        从文本中提取链接
        
        Args:
            text: 文本
            
        Returns:
            链接列表，每个链接包含url和text
        """
        if not text:
            return []
        
        # 查找URL
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        urls = re.findall(url_pattern, text)
        
        links = []
        for url in urls:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # 尝试提取链接文本
            text_match = re.search(rf'\[([^\]]+)\]\({re.escape(url)}\)', text)
            link_text = text_match.group(1) if text_match else url
            
            links.append({
                "url": url,
                "text": link_text
            })
        
        return links
    
    @staticmethod
    def word_count(text: str) -> Dict[str, int]:
        """
        统计文本字数
        
        Args:
            text: 文本
            
        Returns:
            字数统计
        """
        if not text:
            return {"characters": 0, "words": 0, "lines": 0}
        
        # 字符数（包括空格）
        char_count = len(text)
        
        # 单词数（按空格分割）
        words = text.split()
        word_count = len(words)
        
        # 行数
        line_count = text.count('\n') + 1
        
        return {
            "characters": char_count,
            "words": word_count,
            "lines": line_count
        }
    
    @staticmethod
    def format_duration(seconds: int) -> str:
        """
        格式化持续时间
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化的持续时间
        """
        if seconds < 60:
            return f"{seconds}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            seconds = seconds % 60
            return f"{minutes}分{seconds}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            return f"{hours}小时{minutes}分{seconds}秒"


# 工具函数
def format_text_for_display(text: str, max_lines: int = 10) -> str:
    """
    格式化文本用于显示（限制行数）
    
    Args:
        text: 原始文本
        max_lines: 最大行数
        
    Returns:
    格式化后的文本
    """
    if not text:
        return ""
    
    lines = text.split('\n')
    if len(lines) <= max_lines:
        return text
    
    return '\n'.join(lines[:max_lines]) + f"\n...（还有{len(lines) - max_lines}行）"