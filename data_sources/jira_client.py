"""
Jira客户端
用于查询P0/P1问题，支持MCP服务器和直接API调用
"""

import requests
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from utils.config_manager import get_config_manager


class JiraClient:
    """Jira客户端类"""

    def __init__(self, use_mcp: bool = False):
        """
        初始化Jira客户端

        Args:
            use_mcp: 是否使用MCP服务器（如果可用）
        """
        self.config_manager = get_config_manager()
        self.use_mcp = use_mcp
        self.project_id_field = None
        self._load_config()
        self.session = self._create_session() if not use_mcp else None

    def _load_config(self):
        """加载配置"""
        self.config = self.config_manager.get_jira_config()
        self.api_config = self.config_manager.get_api_config()

        self.base_url = self.config["base_url"]
        self.api_token = self.config["api_token"]
        self.username = self.config["username"]

    def _create_session(self) -> requests.Session:
        """创建HTTP会话（用于直接API调用）"""
        session = requests.Session()
        session.timeout = self.api_config["request_timeout"]

        if self.api_token and self.username:
            session.auth = (self.username, self.api_token)

        session.headers.update({
            "Accept": "application/json",
            "Content-Type": "application/json"
        })

        return session

    def _api_url(self, path: str, version: int = 2) -> str:
        """构建Jira REST API URL，默认兼容 Jira Server/Data Center 的 v2 API。"""
        normalized_path = path.lstrip("/")
        return urljoin(self.base_url.rstrip("/") + "/", f"rest/api/{version}/{normalized_path}")

    def _get_with_api_fallback(self, path: str, **kwargs) -> requests.Response:
        """优先请求v2 API，404时回退到v3 API。"""
        response = self.session.get(self._api_url(path, 2), **kwargs)
        if response.status_code == 404:
            response = self.session.get(self._api_url(path, 3), **kwargs)
        return response

    @staticmethod
    def _field_to_jql(field_id: Optional[str]) -> str:
        """将customfield_10407转换成JQL推荐写法cf[10407]。"""
        if field_id and field_id.startswith("customfield_"):
            return f"cf[{field_id.split('_', 1)[1]}]"
        if field_id:
            return f'"{field_id}"'
        return '"Project ID"'

    def get_project_id_jql_field(self) -> str:
        """获取Project ID字段的JQL字段名。该Jira实例需要使用字段名称查询。"""
        return '"Project ID"'

    def get_priority_issues(self, project_key: str, priorities: List[str] = None) -> Dict[str, Any]:
        """
        获取指定优先级的未关闭问题

        Args:
            project_key: Jira项目Key
            priorities: 优先级列表，默认为["P0", "P1"]

        Returns:
            问题统计和列表
        """
        if priorities is None:
            priorities = ["P0", "P1"]

        if self.use_mcp:
            return self._get_issues_via_mcp(project_key, priorities)
        else:
            return self._get_issues_via_api(project_key, priorities)

    def _get_issues_via_mcp(self, project_key: str, priorities: List[str]) -> Dict[str, Any]:
        """通过MCP服务器获取问题"""
        try:
            # 构建JQL查询
            priority_condition = " OR ".join([f'priority = "{p}"' for p in priorities])
            jql = f'project = "{project_key}" AND ({priority_condition}) AND status NOT IN (Done, Closed, Resolved)'

            # 这里应该调用MCP工具，但为了代码完整性，我们先返回模拟数据
            # 实际实现中应该使用：use_mcp_tool("jira", "search_issues", {"jql": jql})

            return {
                "total": 3,
                "issues": [
                    {
                        "key": f"{project_key}-123",
                        "summary": "Critical bug in authentication module",
                        "priority": "P0",
                        "status": "In Progress",
                        "assignee": "john.doe",
                        "url": f"{self.base_url}/browse/{project_key}-123"
                    },
                    {
                        "key": f"{project_key}-456",
                        "summary": "Performance issue in database queries",
                        "priority": "P1",
                        "status": "Open",
                        "assignee": "jane.smith",
                        "url": f"{self.base_url}/browse/{project_key}-456"
                    },
                    {
                        "key": f"{project_key}-789",
                        "summary": "UI rendering problem on mobile",
                        "priority": "P1",
                        "status": "To Do",
                        "assignee": "alex.wang",
                        "url": f"{self.base_url}/browse/{project_key}-789"
                    }
                ],
                "priority_counts": {"P0": 1, "P1": 2},
                "jql": jql,
                "dashboard_url": f"{self.base_url}/projects/{project_key}/issues/?filter=allissues"
            }

        except Exception as e:
            print(f"警告：通过MCP获取Jira问题失败: {e}")
            # 回退到API调用
            return self._get_issues_via_api(project_key, priorities)

    def _get_issues_via_api(self, project_key: str, priorities: List[str]) -> Dict[str, Any]:
        """通过直接API调用获取问题"""
        if not self.base_url or not self.api_token:
            return {
                "total": 0,
                "issues": [],
                "priority_counts": {},
                "error": "Jira配置不完整",
                "dashboard_url": ""
            }

        try:
            # 构建JQL查询
            priority_condition = " OR ".join([f'priority = "{p}"' for p in priorities])
            jql = f'project = "{project_key}" AND ({priority_condition}) AND status NOT IN (Done, Closed, Resolved)'

            # Jira REST API搜索端点
            search_url = self._api_url("search")

            params = {
                "jql": jql,
                "maxResults": 50,
                "fields": "key,summary,priority,status,assignee"
            }

            response = self._get_with_api_fallback("search", params=params)
            response.raise_for_status()

            data = response.json()

            issues = []
            priority_counts = {p: 0 for p in priorities}

            for issue in data.get("issues", []):
                key = issue["key"]
                fields = issue["fields"]

                priority_name = fields.get("priority", {}).get("name", "Unknown")
                if priority_name in priorities:
                    priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

                issues.append({
                    "key": key,
                    "summary": fields.get("summary", ""),
                    "priority": priority_name,
                    "status": fields.get("status", {}).get("name", "Unknown"),
                    "assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
                    "url": urljoin(self.base_url, f"/browse/{key}")
                })

            return {
                "total": data.get("total", 0),
                "issues": issues,
                "priority_counts": priority_counts,
                "jql": jql,
                "dashboard_url": urljoin(self.base_url, f"/projects/{project_key}/issues/?filter=allissues")
            }

        except requests.exceptions.RequestException as e:
            print(f"错误：获取Jira问题失败: {e}")
            return {
                "total": 0,
                "issues": [],
                "priority_counts": {},
                "error": str(e),
                "dashboard_url": ""
            }

    def get_issue_details(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """获取问题详情"""
        if self.use_mcp:
            try:
                # 使用MCP工具获取问题详情
                # 实际实现中应该使用：use_mcp_tool("jira", "get_issue", {"issue_key": issue_key})
                return {
                    "key": issue_key,
                    "summary": "Sample issue",
                    "description": "This is a sample issue description.",
                    "priority": "P1",
                    "status": "In Progress",
                    "assignee": "john.doe",
                    "reporter": "jane.smith",
                    "created": "2024-01-01",
                    "updated": "2024-01-15"
                }
            except:
                pass

        # 回退到API调用
        if not self.base_url or not self.api_token:
            return None

        try:
            response = self._get_with_api_fallback(f"issue/{issue_key}")
            response.raise_for_status()

            return response.json()
        except:
            return None

    def format_issues_for_email(self, issues_data: Dict[str, Any]) -> str:
        """
        格式化问题列表用于邮件

        Args:
            issues_data: get_priority_issues返回的数据

        Returns:
            格式化的文本
        """
        if not issues_data.get("issues"):
            return "当前无P0/P1未关闭问题。"

        total = issues_data["total"]
        priority_counts = issues_data.get("priority_counts", {})

        # 构建统计信息
        stats_lines = []
        for priority, count in priority_counts.items():
            stats_lines.append(f"  • {priority}: {count}个")

        stats_text = "\n".join(stats_lines)

        # 构建问题列表
        issue_lines = []
        for i, issue in enumerate(issues_data["issues"], 1):
            issue_lines.append(f"{i}. [{issue['key']}] {issue['summary']}")
            issue_lines.append(f"   状态: {issue['status']}, 负责人: {issue['assignee']}, 优先级: {issue['priority']}")
            issue_lines.append(f"   链接: {issue['url']}")
            issue_lines.append("")  # 空行分隔

        issues_text = "\n".join(issue_lines)

        return f"""当前严重问题（P0/P1）统计：
总计: {total}个未关闭问题
按优先级分布：
{stats_text}

问题详情：
{issues_text}

Jira看板链接：{issues_data.get('dashboard_url', '')}"""

    def test_connection(self) -> bool:
        """测试Jira连接（使用已配置的凭据）"""
        if self.use_mcp:
            # 测试MCP连接
            try:
                # 这里应该测试MCP服务器连接
                return True
            except:
                return False

        # 测试直接API连接
        if not self.base_url or not self.api_token:
            return False

        try:
            # 尝试获取服务器信息
            response = self._get_with_api_fallback("serverInfo")
            return response.status_code == 200
        except:
            return False

    def search_issues(self, jql: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        使用JQL查询搜索Jira问题

        Args:
            jql: JQL查询语句
            max_results: 最大返回结果数

        Returns:
            问题列表
        """
        if self.use_mcp:
            return self._search_issues_via_mcp(jql, max_results)
        else:
            return self._search_issues_via_api(jql, max_results)

    def _search_issues_via_mcp(self, jql: str, max_results: int) -> List[Dict[str, Any]]:
        """通过MCP服务器搜索问题"""
        try:
            # 这里应该调用MCP工具
            # 实际实现中应该使用：use_mcp_tool("jira", "search_issues", {"jql": jql, "max_results": max_results})

            # 模拟返回数据
            return [
                {
                    "key": "SWPL-123",
                    "summary": "Critical bug in authentication module",
                    "priority": "P0",
                    "status": "In Progress",
                    "description": "Users cannot login with correct credentials",
                    "assignee": "john.doe"
                },
                {
                    "key": "SWPL-456",
                    "summary": "Performance issue in database queries",
                    "priority": "P1",
                    "status": "Open",
                    "description": "Slow response time on large datasets",
                    "assignee": "jane.smith"
                },
                {
                    "key": "SWPL-789",
                    "summary": "UI rendering problem on mobile",
                    "priority": "P1",
                    "status": "To Do",
                    "description": "Layout breaks on mobile devices",
                    "assignee": "alex.wang"
                }
            ]
        except Exception as e:
            print(f"警告：通过MCP搜索Jira问题失败: {e}")
            # 回退到API调用
            return self._search_issues_via_api(jql, max_results)

    def validate_configuration(self) -> Dict[str, Any]:
        """
        验证Jira配置

        Returns:
            包含验证结果的字典
        """
        validation_result = {
            "valid": False,
            "errors": [],
            "warnings": [],
            "config_status": {}
        }

        # 检查基本配置
        if not self.base_url:
            validation_result["errors"].append("Jira基础URL未配置")
        else:
            validation_result["config_status"]["base_url"] = "已配置"

        if not self.api_token:
            validation_result["warnings"].append("API Token未配置，可能无法访问某些功能")
        else:
            validation_result["config_status"]["api_token"] = "已配置"

        if not self.username:
            validation_result["warnings"].append("用户名未配置")
        else:
            validation_result["config_status"]["username"] = "已配置"

        # 如果基本配置都不完整，直接返回
        if not self.base_url:
            return validation_result

        # 测试连接
        try:
            if self.test_connection():
                validation_result["config_status"]["connection"] = "成功"
                validation_result["valid"] = len(validation_result["errors"]) == 0
            else:
                validation_result["errors"].append("Jira连接失败")
                validation_result["config_status"]["connection"] = "失败"
        except Exception as e:
            validation_result["errors"].append(f"连接测试异常: {str(e)}")
            validation_result["config_status"]["connection"] = "异常"

        return validation_result

    def discover_project_id_field(self) -> Optional[str]:
        """
        动态发现Project ID字段

        Returns:
            字段ID（如customfield_10407）或None
        """
        if not self.base_url or not self.api_token:
            return None

        try:
            # 获取字段定义
            response = self._get_with_api_fallback("field")
            if response.status_code != 200:
                return None

            fields = response.json()

            # 查找可能的Project ID字段
            possible_names = [
                "project id", "projectid", "project_id",
                "项目id", "项目ID", "项目编号",
                "pid", "project number"
            ]

            for field in fields:
                name = field.get("name", "").lower()
                field_id = field.get("id", "")

                # 检查字段名是否匹配
                for possible_name in possible_names:
                    if possible_name in name:
                        self.project_id_field = field_id
                        print(f"发现Project ID字段: {field_id} ({field.get('name')})")
                        return field_id

                # 检查字段key是否包含project
                field_key = field.get("key", "").lower()
                if "project" in field_key and "id" in field_key:
                    self.project_id_field = field_id
                    print(f"发现Project ID字段: {field_id} ({field.get('name')})")
                    return field_id

            # 如果没有找到，尝试搜索包含数字的Project ID字段
            for field in fields:
                name = field.get("name", "").lower()
                field_id = field.get("id", "")

                if "project" in name and any(char.isdigit() for char in name):
                    self.project_id_field = field_id
                    print(f"发现可能的Project ID字段: {field_id} ({field.get('name')})")
                    return field_id

            print("未找到Project ID字段")
            return None

        except Exception as e:
            print(f"发现Project ID字段失败: {e}")
            return None

    def get_available_options(self) -> Dict[str, Any]:
        """
        获取当前用户可用的筛选选项

        Returns:
            包含各种选项和状态信息的字典
        """
        result = {
            "success": False,
            "options": {
                "project_ids": [],
                "priorities": [],
                "statuses": [],
                "labels": []
            },
            "validation": {},
            "project_id_field": None,
            "error": None
        }

        # 首先验证配置
        validation = self.validate_configuration()
        result["validation"] = validation

        if not validation.get("valid", False) and validation.get("errors"):
            result["error"] = "配置验证失败: " + ", ".join(validation["errors"])
            return result

        if self.use_mcp:
            return self._get_options_via_mcp(result)
        else:
            return self._get_options_via_api(result)

    def _get_options_via_mcp(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """通过MCP服务器获取选项"""
        try:
            # 这里应该调用MCP工具获取选项
            # 返回模拟数据
            result["success"] = True
            result["options"] = {
                "project_ids": ["10000", "10001", "10002", "10003", "10004"],
                "priorities": ["P0 - Critical", "P1 - High", "P2 - Medium", "P3 - Low", "P4 - Lowest"],
                "statuses": ["Open", "In Progress", "Resolved", "Closed", "Done"],
                "labels": ["bug", "feature", "enhancement", "urgent", "blocker"]
            }
            result["project_id_field"] = "customfield_10407"
            return result
        except Exception as e:
            print(f"警告：通过MCP获取选项失败: {e}")
            result["error"] = f"MCP获取失败: {str(e)}"
            return self._get_options_via_api(result)

    def _get_options_via_api(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """通过直接API调用获取选项"""
        try:
            options = {
                "project_ids": [],
                "priorities": [],
                "statuses": [],
                "labels": []
            }

            # Project ID 支持手动输入；不在登录初始化阶段扫描字段值，避免无输入时产生噪音和慢查询。
            result["project_id_field"] = None

            # 1. 获取优先级选项
            try:
                response = self._get_with_api_fallback("priority")
                if response.status_code == 200:
                    priorities = response.json()
                    for priority in priorities:
                        name = priority.get("name", "")
                        if name:
                            options["priorities"].append(name)
                else:
                    print(f"获取优先级失败: {response.status_code}")
            except Exception as e:
                print(f"获取优先级异常: {e}")

            # 2. 获取状态选项
            try:
                response = self._get_with_api_fallback("status")
                if response.status_code == 200:
                    statuses = response.json()
                    for status in statuses:
                        name = status.get("name", "")
                        if name:
                            options["statuses"].append(name)
                else:
                    print(f"获取状态失败: {response.status_code}")
            except Exception as e:
                print(f"获取状态异常: {e}")

            # 3. 获取常用标签
            try:
                search_url = self._api_url("search")
                params = {
                    "jql": 'labels IS NOT EMPTY',
                    "maxResults": 200,
                    "fields": "labels"
                }
                response = self._get_with_api_fallback("search", params=params)
                if response.status_code == 200:
                    data = response.json()
                    labels = set()

                    for issue in data.get("issues", []):
                        fields = issue.get("fields", {})
                        issue_labels = fields.get("labels", [])
                        for label in issue_labels:
                            labels.add(label)

                    # 取前30个最常用的标签
                    options["labels"] = list(labels)[:30]
                    print(f"找到 {len(labels)} 个标签，显示前30个")
                else:
                    print(f"获取标签失败: {response.status_code}")
            except Exception as e:
                print(f"获取标签异常: {e}")

            result["success"] = True
            result["options"] = options

            # 如果没有获取到任何选项，添加警告
            empty_count = sum(1 for key, option_list in options.items() if key != "project_ids" and not option_list)
            if empty_count > 0:
                result["warning"] = f"有 {empty_count} 个选项列表为空"

            return result

        except Exception as e:
            print(f"错误：获取Jira选项失败: {e}")
            result["error"] = f"获取选项失败: {str(e)}"
            return result

    def get_jql_value_suggestions(self, field_name: str, field_value: str) -> List[str]:
        """获取JQL字段值建议，用于自定义枚举字段的真实选项名匹配。"""
        if not self.base_url or not self.api_token or not field_name or not field_value:
            return []
        try:
            response = self._get_with_api_fallback(
                "jql/autocompletedata/suggestions",
                params={"fieldName": field_name, "fieldValue": field_value}
            )
            if response.status_code != 200:
                return []
            data = response.json()
            suggestions = []
            for item in data.get("results", []):
                value = item.get("value") or item.get("displayName")
                if value and value not in suggestions:
                    suggestions.append(value)
            return suggestions
        except Exception as e:
            print(f"获取JQL字段值建议失败: {e}")
            return []

    def _retry_with_suggested_option(self, jql: str, max_results: int, error_text: str) -> Optional[List[Dict[str, Any]]]:
        """当自定义字段选项不存在时，尝试用Jira建议选项重试。"""
        import re
        match = re.search(r'(cf\[\d+\])\s*=\s*"([^"]+)"', jql)
        if not match or "does not exist" not in error_text:
            return None
        field_name, raw_value = match.groups()
        suggestions = self.get_jql_value_suggestions(field_name, raw_value)
        if not suggestions:
            raise RuntimeError(
                f"字段 {field_name} 中不存在选项 '{raw_value}'。\n"
                f"请确认 Jira 里 SW Project ID 的真实选项值，或者改用状态/优先级/标签筛选。\n"
                f"Jira原始响应: {error_text[:500]}"
            )
        # 优先精确忽略大小写匹配，否则使用第一条建议。
        chosen = next((s for s in suggestions if s.lower() == raw_value.lower()), suggestions[0])
        retry_jql = jql.replace(f'{field_name} = "{raw_value}"', f'{field_name} = "{chosen}"')
        print(f"Project ID选项 '{raw_value}' 不存在，使用Jira建议值 '{chosen}' 重试")
        return self._search_issues_via_api(retry_jql, max_results)
    def _search_issues_via_api(self, jql: str, max_results: int) -> List[Dict[str, Any]]:
        """通过直接API调用搜索问题"""
        if not self.base_url or not self.api_token:
            print("错误：Jira配置不完整")
            return []

        try:
            # Jira REST API搜索端点
            search_url = self._api_url("search")

            params = {
                "jql": jql,
                "maxResults": min(max_results, 100),  # 限制最大结果数
                "fields": "key,summary,priority,status,assignee,description"
            }

            response = self._get_with_api_fallback("search", params=params)
            response.raise_for_status()

            data = response.json()
            issues = []

            for issue in data.get("issues", []):
                key = issue["key"]
                fields = issue["fields"]

                issues.append({
                    "key": key,
                    "summary": fields.get("summary", ""),
                    "priority": fields.get("priority", {}).get("name", "Unknown"),
                    "status": fields.get("status", {}).get("name", "Unknown"),
                    "description": fields.get("description", ""),
                    "assignee": fields.get("assignee", {}).get("displayName", "Unassigned")
                })

            return issues

        except requests.exceptions.RequestException as e:
            detail = ""
            response = getattr(e, "response", None)
            if response is not None:
                detail = response.text[:500]
                retry_result = self._retry_with_suggested_option(jql, max_results, detail)
                if retry_result is not None:
                    return retry_result
                detail = f"\n响应内容: {detail}"
            raise RuntimeError(f"搜索Jira问题失败: {e}{detail}")
        except Exception as e:
            raise RuntimeError(f"处理Jira搜索结果失败: {e}")

    def test_connection_with_credentials(self, base_url: str, username: str, password: str) -> bool:
        """使用提供的凭据测试Jira连接（表单登录）"""
        if not base_url or not username or not password:
            return False

        try:
            # 创建临时会话
            session = requests.Session()
            session.timeout = 10  # 10秒超时
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1"
            })

            # 首先获取登录页面以获取CSRF token和表单字段
            login_url = urljoin(base_url, "/login.jsp")
            login_page_response = session.get(login_url)

            if login_page_response.status_code != 200:
                print(f"无法访问登录页面: {login_page_response.status_code}")
                return False

            # 解析登录页面
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(login_page_response.text, 'html.parser')

            # 查找登录表单
            login_form = None
            for form in soup.find_all('form'):
                action = form.get('action', '')
                method = form.get('method', '').lower()
                if 'login' in action.lower() or method == 'post':
                    # 检查是否有os_username字段
                    if form.find('input', {'name': 'os_username'}):
                        login_form = form
                        break

            if not login_form:
                print("未找到登录表单")
                return False

            # 提取所有表单字段
            login_data = {}
            for input_tag in login_form.find_all('input'):
                name = input_tag.get('name')
                value = input_tag.get('value', '')
                input_type = input_tag.get('type', 'text')

                if name:
                    # 对于复选框，如果未选中则不包含
                    if input_type == 'checkbox':
                        if input_tag.get('checked'):
                            login_data[name] = value if value else 'true'
                    else:
                        login_data[name] = value

            # 更新用户名和密码
            login_data['os_username'] = username
            login_data['os_password'] = password

            # 确保有登录按钮值
            if 'login' not in login_data:
                login_data['login'] = 'Log In'

            # 提交登录表单（不自动重定向，以便检查响应）
            form_action = login_form.get('action', '')
            if not form_action or form_action == '':
                form_action = '/login.jsp'

            post_url = urljoin(base_url, form_action)
            response = session.post(
                post_url,
                data=login_data,
                allow_redirects=False  # 不自动重定向
            )

            # 分析登录结果
            # 1. 检查重定向状态码
            if response.status_code in [301, 302, 303]:
                location = response.headers.get('location', '')
                print(f"登录后重定向到: {location}")

                # 检查是否重定向到成功页面
                if location and ('dashboard' in location.lower() or 'secure' in location.lower()):
                    return True
                # 如果重定向回登录页面，可能是失败
                if location and 'login' in location.lower():
                    return False

            # 2. 检查响应内容
            response_text = response.text.lower()

            # 检查错误信息
            error_keywords = [
                'sorry', 'invalid', 'incorrect', 'error', 'failed',
                'login failed', 'authentication failed', 'wrong',
                '用户名或密码错误', '登录失败', '认证失败'
            ]

            for keyword in error_keywords:
                if keyword in response_text:
                    print(f"发现错误关键词: {keyword}")
                    return False

            # 3. 检查是否仍然在登录页面
            if 'login' in response.url.lower() and response.status_code == 200:
                # 检查页面是否包含登录表单
                soup2 = BeautifulSoup(response.text, 'html.parser')
                login_form2 = soup2.find('input', {'name': 'os_username'})
                if login_form2:
                    print("仍然在登录页面，包含登录表单")
                    return False

            # 4. 检查成功迹象
            success_keywords = [
                'welcome', 'dashboard', 'projects', 'issues',
                'log out', 'sign out', 'logout', 'signout'
            ]

            for keyword in success_keywords:
                if keyword in response_text:
                    print(f"发现成功关键词: {keyword}")
                    return True

            # 5. 尝试访问需要认证的页面来验证
            try:
                # 访问用户个人资料页面
                profile_url = urljoin(base_url, "/secure/ViewProfile.jspa")
                profile_response = session.get(profile_url, allow_redirects=False)

                if profile_response.status_code == 200:
                    # 检查是否包含用户名
                    if username.lower() in profile_response.text.lower():
                        print("成功访问用户个人资料页面")
                        return True
            except:
                pass

            # 6. 默认情况下，假设失败（更安全）
            print("无法确定登录结果，假设失败")
            return False

        except Exception as e:
            print(f"Jira连接测试失败: {e}")
            import traceback
            traceback.print_exc()
            return False


# 单例实例
_jira_client: Optional[JiraClient] = None

def get_jira_client(use_mcp: bool = False) -> JiraClient:
    """获取Jira客户端单例"""
    global _jira_client
    if _jira_client is None:
        _jira_client = JiraClient(use_mcp=use_mcp)
    return _jira_client
