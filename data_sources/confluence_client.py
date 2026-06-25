"""
Confluence REST API客户端
用于从Confluence页面提取项目状态信息
"""

import requests
from typing import Dict, Any, Optional
import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote_plus

from utils.config_manager import get_config_manager


class ConfluenceClient:
    """Confluence客户端类"""
    
    def __init__(self):
        """初始化Confluence客户端"""
        self.config_manager = get_config_manager()
        self.config = self.config_manager.get_confluence_config()
        self.api_config = self.config_manager.get_api_config()
        
        self.base_url = self.config["base_url"]
        self.api_token = self.config["api_token"]
        self.username = self.config["username"]
        
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建HTTP会话"""
        session = requests.Session()
        session.timeout = self.api_config["request_timeout"]
        
        if self.api_token and self.username:
            session.auth = (self.username, self.api_token)
        
        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        
        return session
    
    def _extract_page_id_from_url(self, url: str) -> Optional[str]:
        """从Confluence URL中提取页面ID"""
        try:
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)

            if "pageId" in query_params:
                return query_params["pageId"][0]

            path_parts = parsed.path.split('/')
            for part in path_parts:
                if part.isdigit() and len(part) > 4:
                    return part

            if parsed.fragment:
                fragment_parts = parsed.fragment.split('/')
                for part in fragment_parts:
                    if part.isdigit() and len(part) > 4:
                        return part
        except Exception as e:
            print(f"警告：无法从URL提取页面ID: {e}")

        return None

    def _extract_display_page_ref(self, url: str) -> Optional[Dict[str, str]]:
        """从/display/SPACE/Page+Title形式URL中提取space和标题。"""
        try:
            parsed = urlparse(url)
            path_parts = [part for part in parsed.path.split('/') if part]
            if len(path_parts) < 3 or path_parts[0].lower() != "display":
                return None

            space_key = unquote_plus(path_parts[1])
            raw_title = "/".join(path_parts[2:])
            title = unquote_plus(raw_title).replace("+", " ")
            if not space_key or not title:
                return None

            return {"space_key": space_key, "title": title}
        except Exception as e:
            print(f"警告：无法从display URL提取页面信息: {e}")
            return None

    def get_page_content(self, page_url: str) -> Optional[Dict[str, Any]]:
        """
        获取Confluence页面内容
        
        Args:
            page_url: Confluence页面URL
            
        Returns:
            页面内容字典，包含HTML和解析后的数据
        """
        page_id = self._extract_page_id_from_url(page_url)
        display_ref = None
        if not page_id:
            display_ref = self._extract_display_page_ref(page_url)
            if not display_ref:
                print(f"错误：无法从URL提取页面ID或display页面信息: {page_url}")
                return None
        
        try:
            if page_id:
                response = self.session.get(
                    f"{self.base_url}/rest/api/content/{page_id}",
                    params={"expand": "body.storage,version"}
                )
            else:
                response = self.session.get(
                    f"{self.base_url}/rest/api/content",
                    params={
                        "spaceKey": display_ref["space_key"],
                        "title": display_ref["title"],
                        "expand": "body.storage,version"
                    }
                )
            response.raise_for_status()
            
            data = response.json()
            if not page_id:
                results = data.get("results", [])
                if not results:
                    print(f"错误：Confluence中未找到页面: space={display_ref['space_key']}, title={display_ref['title']}")
                    return None
                data = results[0]
                page_id = data.get("id", "")
            
            return {
                "page_id": page_id,
                "title": data.get("title", ""),
                "version": data.get("version", {}).get("number", 1),
                "html_content": data.get("body", {}).get("storage", {}).get("value", ""),
                "raw_data": data
            }
        except requests.exceptions.RequestException as e:
            print(f"错误：获取Confluence页面失败: {e}")
            return None
    def extract_next_milestone(self, html_content: str) -> str:
        """
        提取Next Milestone信息
        
        Args:
            html_content: Confluence页面HTML内容
            
        Returns:
            Next Milestone文本
        """
        return self._extract_section_by_keywords(
            html_content,
            keywords=["next milestone", "next milestones", "upcoming milestone", "里程碑"],
            section_name="Next Milestone"
        )
    
    def extract_highlight_blocked_issues(self, html_content: str) -> str:
        """
        提取Highlight & Blocked Issues信息
        
        Args:
            html_content: Confluence页面HTML内容
            
        Returns:
            Highlight & Blocked Issues文本
        """
        return self._extract_section_by_keywords(
            html_content,
            keywords=["highlight", "blocked", "blocking", "highlights", "阻塞", "阻碍"],
            section_name="Highlight & Blocked Issues"
        )
    
    def extract_test_status(self, html_content: str) -> str:
        """
        提取Test Status信息
        
        Args:
            html_content: Confluence页面HTML内容
            
        Returns:
            Test Status文本
        """
        return self._extract_section_by_keywords(
            html_content,
            keywords=["test status", "testing status", "测试状态", "测试进展"],
            section_name="Test Status"
        )
    
    def extract_next_action(self, html_content: str) -> str:
        """
        提取Next Action信息
        
        Args:
            html_content: Confluence页面HTML内容
            
        Returns:
            Next Action文本
        """
        return self._extract_section_by_keywords(
            html_content,
            keywords=["next action", "next actions", "下一步", "下周计划", "下周测试计划"],
            section_name="Next Action"
        )
    
    def _extract_section_by_keywords(self, html_content: str, keywords: list, 
                                    section_name: str = "Section") -> str:
        """
        根据关键词提取页面部分内容
        
        Args:
            html_content: HTML内容
            keywords: 关键词列表
            section_name: 部分名称（用于调试）
            
        Returns:
            提取的文本内容
        """
        if not html_content:
            return f"{section_name}: 未找到相关内容"
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 查找包含关键词的标题
            for keyword in keywords:
                # 查找标题元素（h1-h6）
                for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                    if keyword.lower() in heading.get_text().lower():
                        # 获取标题后的内容
                        content = []
                        current = heading.next_sibling
                        
                        # 收集直到下一个同级标题的内容
                        while current and not (hasattr(current, 'name') and 
                                             current.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                            if hasattr(current, 'get_text'):
                                text = current.get_text().strip()
                                if text:
                                    content.append(text)
                            elif isinstance(current, str) and current.strip():
                                content.append(current.strip())
                            
                            current = current.next_sibling
                        
                        if content:
                            return "\n".join(content)
            
            # 如果没找到标题，尝试查找表格
            for keyword in keywords:
                for table in soup.find_all('table'):
                    table_text = table.get_text().lower()
                    if keyword.lower() in table_text:
                        # 提取表格内容
                        rows = []
                        for row in table.find_all('tr'):
                            cells = [cell.get_text().strip() for cell in row.find_all(['td', 'th'])]
                            if cells:
                                rows.append(" | ".join(cells))
                        
                        if rows:
                            return "\n".join(rows)
            
            # 如果还没找到，尝试查找包含关键词的任何元素
            for keyword in keywords:
                elements = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
                for element in elements:
                    parent = element.parent
                    if parent:
                        text = parent.get_text().strip()
                        if text and len(text) > len(keyword) + 10:  # 确保有足够的内容
                            return text
        
        except Exception as e:
            print(f"警告：解析{section_name}时出错: {e}")
        
        return f"{section_name}: 未找到相关内容"
    
    def extract_all_sections(self, page_url: str) -> Dict[str, str]:
        """
        提取所有需要的部分
        
        Args:
            page_url: Confluence页面URL
            
        Returns:
            包含所有提取部分的字典
        """
        page_data = self.get_page_content(page_url)
        if not page_data:
            return {
                "next_milestone": "无法获取页面内容",
                "highlight_blocked": "无法获取页面内容",
                "test_status": "无法获取页面内容",
                "next_action": "无法获取页面内容"
            }
        
        html_content = page_data["html_content"]
        
        return {
            "next_milestone": self.extract_next_milestone(html_content),
            "highlight_blocked": self.extract_highlight_blocked_issues(html_content),
            "test_status": self.extract_test_status(html_content),
            "next_action": self.extract_next_action(html_content),
            "page_title": page_data["title"]
        }
    
    def test_connection(self) -> bool:
        """测试Confluence连接"""
        if not self.base_url or not self.api_token:
            return False
        
        try:
            # 尝试获取用户信息
            response = self.session.get(f"{self.base_url}/rest/api/user/current")
            return response.status_code == 200
        except:
            return False


# 单例实例
_confluence_client: Optional[ConfluenceClient] = None

def get_confluence_client() -> ConfluenceClient:
    """获取Confluence客户端单例"""
    global _confluence_client
    if _confluence_client is None:
        _confluence_client = ConfluenceClient()
    return _confluence_client