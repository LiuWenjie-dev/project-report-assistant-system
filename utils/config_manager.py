"""
配置管理器
负责管理应用程序配置，包括环境变量、JSON配置文件和项目缓存
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from utils.credential_store import CredentialStore, CredentialStoreError


class ConfigManager:
    """配置管理器类"""

    def __init__(self, base_dir: str = None):
        """
        初始化配置管理器

        Args:
            base_dir: 基础目录路径，默认为当前目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.config_dir = self.base_dir / "config"
        self.config_file = self.config_dir / "config.json"
        self.projects_file = self.config_dir / "projects.json"

        # 确保配置目录存在
        self.config_dir.mkdir(exist_ok=True)

        # 加载环境变量
        self._load_environment()
        self._migrate_plaintext_credentials()

        # 加载配置文件
        self.config = self._load_config()
        self.projects = self._load_projects()

    def _load_environment(self) -> None:
        """加载环境变量"""
        env_file = self.base_dir / ".env"
        if env_file.exists():
            load_dotenv(env_file, override=True)
        else:
            # 使用系统环境变量
            pass

    def _load_config(self) -> Dict[str, Any]:
        """加载主配置文件"""
        default_config = {
            "email_settings": {
                "default_subject_prefix": "[Weekly Report]",
                "default_to": "",
                "default_cc": "",
                "signature": "Best regards,\n[Your Name]"
            },
            "ui_settings": {
                "window_width": 1200,
                "window_height": 800,
                "theme": "light"
            },
            "api_settings": {
                "request_timeout": 30,
                "max_retries": 3
            }
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # 合并配置，用户配置优先
                    self._merge_dicts(default_config, user_config)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告：无法加载配置文件 {self.config_file}: {e}")

        return default_config

    def _load_projects(self) -> List[Dict[str, Any]]:
        """加载项目配置文件"""
        default_projects = []

        if self.projects_file.exists():
            try:
                with open(self.projects_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"警告：无法加载项目文件 {self.projects_file}: {e}")

        return default_projects

    def _merge_dicts(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """递归合并字典"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_dicts(base[key], value)
            else:
                base[key] = value

    def save_config(self) -> None:
        """保存配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"错误：无法保存配置文件 {self.config_file}: {e}")

    def save_projects(self) -> None:
        """保存项目配置"""
        try:
            with open(self.projects_file, 'w', encoding='utf-8') as f:
                json.dump(self.projects, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"错误：无法保存项目文件 {self.projects_file}: {e}")

    def _read_env_vars(self) -> Dict[str, str]:
        """读取.env中的键值。"""
        env_vars = {}
        env_file = self.base_dir / ".env"
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key] = value
        return env_vars

    def _write_env_vars(self, env_vars: Dict[str, str], header: str = "# Report Assistant Configuration") -> None:
        """写入非敏感.env配置。"""
        env_file = self.base_dir / ".env"
        secret_keys = {"JIRA_API_TOKEN", "CONFLUENCE_API_TOKEN", "JIRA_USERNAME", "CONFLUENCE_USERNAME"}
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(header + "\n")
            for key in sorted(env_vars):
                if key not in secret_keys:
                    f.write(f"{key}={env_vars[key]}\n")

    def _migrate_plaintext_credentials(self) -> None:
        """迁移.env中的明文凭据到Windows凭据管理器。"""
        env_vars = self._read_env_vars()
        changed = False
        try:
            jira_token = env_vars.get("JIRA_API_TOKEN", "")
            if jira_token:
                CredentialStore.set_secret("jira", env_vars.get("JIRA_USERNAME", "jira"), jira_token)
                env_vars.pop("JIRA_API_TOKEN", None)
                os.environ.pop("JIRA_API_TOKEN", None)
                changed = True
            if env_vars.get("JIRA_USERNAME") and CredentialStore.get_secret("jira"):
                env_vars.pop("JIRA_USERNAME", None)
                os.environ.pop("JIRA_USERNAME", None)
                changed = True

            confluence_token = env_vars.get("CONFLUENCE_API_TOKEN", "")
            if confluence_token:
                CredentialStore.set_secret("confluence", env_vars.get("CONFLUENCE_USERNAME", "confluence"), confluence_token)
                env_vars.pop("CONFLUENCE_API_TOKEN", None)
                os.environ.pop("CONFLUENCE_API_TOKEN", None)
                changed = True
            if env_vars.get("CONFLUENCE_USERNAME") and CredentialStore.get_secret("confluence"):
                env_vars.pop("CONFLUENCE_USERNAME", None)
                os.environ.pop("CONFLUENCE_USERNAME", None)
                changed = True
        except CredentialStoreError as e:
            print(f"警告：无法迁移凭据到系统凭据管理器: {e}")
            return
        if changed:
            self._write_env_vars(env_vars)
            self._load_environment()
    def get_confluence_config(self) -> Dict[str, str]:
        """获取Confluence配置，敏感凭据来自系统凭据管理器。"""
        return {
            "base_url": os.getenv("CONFLUENCE_BASE_URL", ""),
            "api_token": CredentialStore.get_secret("confluence") or os.getenv("CONFLUENCE_API_TOKEN", ""),
            "username": CredentialStore.get_username("confluence") or os.getenv("CONFLUENCE_USERNAME", "")
        }

    def get_jira_config(self) -> Dict[str, str]:
        """获取Jira配置，敏感凭据来自系统凭据管理器。"""
        return {
            "base_url": os.getenv("JIRA_BASE_URL", ""),
            "api_token": CredentialStore.get_secret("jira") or os.getenv("JIRA_API_TOKEN", ""),
            "username": CredentialStore.get_username("jira") or os.getenv("JIRA_USERNAME", "")
        }

    def get_email_config(self) -> Dict[str, str]:
        """获取邮件配置"""
        return {
            "default_to": os.getenv("DEFAULT_TO_EMAIL", self.config["email_settings"]["default_to"]),
            "default_cc": os.getenv("DEFAULT_CC_EMAIL", self.config["email_settings"]["default_cc"]),
            "subject_prefix": os.getenv("DEFAULT_EMAIL_SUBJECT_PREFIX",
                                       self.config["email_settings"]["default_subject_prefix"]),
            "signature": self.config["email_settings"]["signature"]
        }

    def get_ui_config(self) -> Dict[str, Any]:
        """获取UI配置"""
        return self.config["ui_settings"]

    def get_api_config(self) -> Dict[str, Any]:
        """获取API配置"""
        return self.config["api_settings"]

    def add_project(self, project: Dict[str, Any]) -> None:
        """添加项目配置"""
        # 检查是否已存在
        for i, p in enumerate(self.projects):
            if p.get("jira_project_key") == project.get("jira_project_key"):
                self.projects[i] = project
                break
        else:
            self.projects.append(project)

        self.save_projects()

    def get_project(self, project_key: str) -> Optional[Dict[str, Any]]:
        """获取项目配置"""
        for project in self.projects:
            if project.get("jira_project_key") == project_key:
                return project
        return None

    def delete_project(self, project_key: str) -> bool:
        """删除项目配置"""
        for i, project in enumerate(self.projects):
            if project.get("jira_project_key") == project_key:
                del self.projects[i]
                self.save_projects()
                return True
        return False

    def get_recent_projects(self, limit: int = 5) -> List[Dict[str, Any]]:
        """获取最近使用的项目"""
        return self.projects[-limit:] if self.projects else []

    def set_jira_config(self, base_url: str, username: str, api_token: str) -> None:
        """设置Jira配置；密码/Token保存到Windows凭据管理器。"""
        env_vars = self._read_env_vars()
        env_vars["JIRA_BASE_URL"] = base_url
        env_vars.pop("JIRA_USERNAME", None)
        env_vars.pop("JIRA_API_TOKEN", None)
        CredentialStore.set_secret("jira", username, api_token)
        os.environ["JIRA_BASE_URL"] = base_url
        os.environ.pop("JIRA_USERNAME", None)
        os.environ.pop("JIRA_API_TOKEN", None)
        self._write_env_vars(env_vars)
        self._load_environment()

    def set_confluence_config(self, base_url: str, username: str, api_token: str) -> None:
        """设置Confluence配置；密码/Token保存到Windows凭据管理器。"""
        env_vars = self._read_env_vars()
        env_vars["CONFLUENCE_BASE_URL"] = base_url
        env_vars.pop("CONFLUENCE_USERNAME", None)
        env_vars.pop("CONFLUENCE_API_TOKEN", None)
        CredentialStore.set_secret("confluence", username, api_token)
        os.environ["CONFLUENCE_BASE_URL"] = base_url
        os.environ.pop("CONFLUENCE_USERNAME", None)
        os.environ.pop("CONFLUENCE_API_TOKEN", None)
        self._write_env_vars(env_vars)
        self._load_environment()

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值，支持点号路径。"""
        current = self.config
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def set(self, key: str, value: Any) -> None:
        """设置配置值"""
        keys = key.split('.')
        current = self.config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value
        self.save_config()


# 单例实例
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """获取配置管理器单例"""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


