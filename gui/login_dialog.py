"""
登录对话框 - 处理Jira和Confluence认证
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QGroupBox, QCheckBox, QMessageBox, QProgressBar,
    QTabWidget, QWidget, QFormLayout, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
import threading
from typing import Dict, Any, Optional

from data_sources.jira_client import JiraClient, get_jira_client
from data_sources.confluence_client import get_confluence_client
from utils.config_manager import get_config_manager


class LoginWorker(QThread):
    """登录工作线程"""

    login_finished = pyqtSignal(str, bool, str)  # 服务名, 成功, 消息

    def __init__(self, service: str, url: str, username: str, password: str):
        super().__init__()
        self.service = service
        self.url = url
        self.username = username
        self.password = password

    def run(self):
        """执行登录测试"""
        try:
            if self.service == "jira":
                success, message = self.test_jira()
            elif self.service == "confluence":
                success, message = self.test_confluence()
            else:
                success, message = False, f"未知服务: {self.service}"

            self.login_finished.emit(self.service, success, message)
        except Exception as e:
            self.login_finished.emit(self.service, False, f"测试异常: {str(e)}")

    def test_jira(self):
        """测试Jira连接"""
        try:
            # 使用Jira客户端测试连接
            # 注意：Jira使用表单登录（os_username和os_password）

            # 创建临时的Jira客户端实例
            from utils.config_manager import get_config_manager
            config_manager = get_config_manager()
            api_config = config_manager.get_api_config()

            # 使用提供的凭据测试连接
            jira_client = JiraClient(use_mcp=False)

            # 测试连接
            success = jira_client.test_connection_with_credentials(
                base_url=self.url,
                username=self.username,
                password=self.password  # 使用密码进行表单登录
            )

            if success:
                return True, "Jira连接成功！"
            else:
                return False, "Jira连接失败：无效的用户名或密码"

        except Exception as e:
            return False, f"Jira连接测试异常: {str(e)}"

    def test_confluence(self):
        """测试Confluence连接"""
        if not self.url or not self.username or not self.password:
            return False, "Confluence连接失败：URL、用户名或密码为空"

        try:
            import requests
            from urllib.parse import urljoin

            session = requests.Session()
            session.auth = (self.username, self.password)
            session.headers.update({"Accept": "application/json"})
            current_user_url = urljoin(self.url.rstrip("/") + "/", "rest/api/user/current")
            response = session.get(current_user_url, timeout=10)

            if response.status_code == 200:
                return True, "Confluence连接成功！"
            if response.status_code in (401, 403):
                return False, "Confluence连接失败：无效的用户名或密码"
            return False, f"Confluence连接失败：HTTP {response.status_code}"
        except Exception as e:
            return False, f"Confluence连接测试异常: {str(e)}"


class LoginDialog(QDialog):
    """登录对话框 - 只负责保存凭据和测试连接"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("报告助手 - 登录配置")
        self.setMinimumSize(600, 500)

        self.login_workers = []
        self.login_results = {"jira": None, "confluence": None}
        self.accept_after_all_tests = False
        self.setup_ui()
        self.load_saved_credentials()

    def setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题
        title_label = QLabel("🔐 系统登录配置")
        title_font = QFont("Microsoft YaHei", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; padding-bottom: 10px;")
        layout.addWidget(title_label)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # Jira配置标签页
        jira_tab = self.create_jira_tab()
        self.tab_widget.addTab(jira_tab, "Jira配置")

        # Confluence配置标签页
        confluence_tab = self.create_confluence_tab()
        self.tab_widget.addTab(confluence_tab, "Confluence配置")

        layout.addWidget(self.tab_widget)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # 保存按钮
        save_btn = QPushButton("💾 保存配置")
        save_btn.setFixedSize(120, 35)
        save_btn.setStyleSheet(self.get_button_style("success"))
        save_btn.clicked.connect(lambda: self.save_credentials())
        button_layout.addWidget(save_btn)

        # 确定按钮
        ok_btn = QPushButton("✅ 登录并进入")
        ok_btn.setFixedSize(100, 35)
        ok_btn.setStyleSheet(self.get_button_style("success"))
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        # 取消按钮
        cancel_btn = QPushButton("❌ 取消")
        cancel_btn.setFixedSize(100, 35)
        cancel_btn.setStyleSheet(self.get_button_style("secondary"))
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def create_jira_tab(self) -> QWidget:
        """创建Jira配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Jira服务器配置组
        server_group = QGroupBox("Jira服务器配置")
        server_layout = QFormLayout()

        self.jira_url_edit = QLineEdit()
        self.jira_url_edit.setText("https://jira.amlogic.com/")
        self.jira_url_edit.setPlaceholderText("https://jira.amlogic.com/")
        server_layout.addRow("服务器URL:", self.jira_url_edit)

        self.jira_username_edit = QLineEdit()
        self.jira_username_edit.setPlaceholderText("输入用户名")
        server_layout.addRow("用户名:", self.jira_username_edit)

        self.jira_password_edit = QLineEdit()
        self.jira_password_edit.setPlaceholderText("请输入密码")
        self.jira_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        server_layout.addRow("密码:", self.jira_password_edit)

        # 显示密码复选框
        show_password = QCheckBox("显示密码")
        show_password.stateChanged.connect(
            lambda state: self.jira_password_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
            )
        )
        server_layout.addRow("", show_password)

        server_group.setLayout(server_layout)
        layout.addWidget(server_group)

        # 测试连接按钮
        test_jira_btn = QPushButton("测试Jira连接")
        test_jira_btn.setStyleSheet(self.get_button_style("primary"))
        test_jira_btn.clicked.connect(lambda: self.test_connection("jira"))
        layout.addWidget(test_jira_btn)

        # Jira状态标签
        self.jira_status_label = QLabel("状态: 未测试")
        self.jira_status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.jira_status_label)

        layout.addStretch()
        return widget

    def create_confluence_tab(self) -> QWidget:
        """创建Confluence配置标签页"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Confluence服务器配置组
        server_group = QGroupBox("Confluence服务器配置")
        server_layout = QFormLayout()

        self.confluence_url_edit = QLineEdit()
        self.confluence_url_edit.setPlaceholderText("https://confluence.company.com")
        server_layout.addRow("服务器URL:", self.confluence_url_edit)

        self.confluence_username_edit = QLineEdit()
        self.confluence_username_edit.setPlaceholderText("输入用户名")
        server_layout.addRow("用户名:", self.confluence_username_edit)

        self.confluence_password_edit = QLineEdit()
        self.confluence_password_edit.setPlaceholderText("请输入密码")
        self.confluence_password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        server_layout.addRow("密码:", self.confluence_password_edit)

        # 显示密码复选框
        show_password = QCheckBox("显示密码")
        show_password.stateChanged.connect(
            lambda state: self.confluence_password_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if state else QLineEdit.EchoMode.Password
            )
        )
        server_layout.addRow("", show_password)

        server_group.setLayout(server_layout)
        layout.addWidget(server_group)

        # 测试连接按钮
        test_confluence_btn = QPushButton("测试Confluence连接")
        test_confluence_btn.setStyleSheet(self.get_button_style("primary"))
        test_confluence_btn.clicked.connect(lambda: self.test_connection("confluence"))
        layout.addWidget(test_confluence_btn)

        # Confluence状态标签
        self.confluence_status_label = QLabel("状态: 未测试")
        self.confluence_status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.confluence_status_label)

        layout.addStretch()
        return widget


    def get_button_style(self, btn_type: str) -> str:
        """获取按钮样式"""
        styles = {
            "primary": """
                QPushButton {
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2980b9;
                }
                QPushButton:pressed {
                    background-color: #21618c;
                }
            """,
            "secondary": """
                QPushButton {
                    background-color: #95a5a6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #7f8c8d;
                }
                QPushButton:pressed {
                    background-color: #616a6b;
                }
            """,
            "success": """
                QPushButton {
                    background-color: #27ae60;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #219653;
                }
                QPushButton:pressed {
                    background-color: #1e8449;
                }
            """
        }
        return styles.get(btn_type, styles["primary"])

    def load_saved_credentials(self):
        """加载已保存的凭据"""
        config = get_config_manager()

        # 加载Jira配置
        jira_config = config.get_jira_config()
        if jira_config.get("base_url"):
            self.jira_url_edit.setText(jira_config["base_url"])
        if jira_config.get("username"):
            self.jira_username_edit.setText(jira_config["username"])

        # 加载Confluence配置
        confluence_config = config.get_confluence_config()
        if confluence_config.get("base_url"):
            self.confluence_url_edit.setText(confluence_config["base_url"])
        if confluence_config.get("username"):
            self.confluence_username_edit.setText(confluence_config["username"])

    def test_connection(self, service: str):
        """测试单个连接"""
        if service == "jira":
            url = self.jira_url_edit.text().strip()
            username = self.jira_username_edit.text().strip()
            password = self.jira_password_edit.text().strip()
            status_label = self.jira_status_label
        elif service == "confluence":
            url = self.confluence_url_edit.text().strip()
            username = self.confluence_username_edit.text().strip()
            password = self.confluence_password_edit.text().strip()
            status_label = self.confluence_status_label
        else:
            return

        if not url or not username or not password:
            QMessageBox.warning(self, "警告", f"请填写{service}的URL、用户名和密码")
            return

        # 更新状态
        status_label.setText("状态: 测试中...")
        status_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 5px;")

        # 创建工作线程
        worker = LoginWorker(service, url, username, password)
        worker.login_finished.connect(
            lambda s, success, msg: self.on_login_finished(s, success, msg, status_label)
        )
        worker.start()

        self.login_workers.append(worker)

    def test_all_connections(self):
        """测试所有连接"""
        errors = []

        jira_url = self.jira_url_edit.text().strip()
        jira_username = self.jira_username_edit.text().strip()
        jira_password = self.jira_password_edit.text().strip()
        if not jira_url or not jira_username or not jira_password:
            errors.append("Jira URL、用户名和密码")

        confluence_url = self.confluence_url_edit.text().strip()
        confluence_username = self.confluence_username_edit.text().strip()
        confluence_password = self.confluence_password_edit.text().strip()
        if not confluence_url or not confluence_username or not confluence_password:
            errors.append("Confluence URL、用户名和密码")

        if errors:
            self.accept_after_all_tests = False
            QMessageBox.warning(self, "警告", f"请先填写: {', '.join(errors)}")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 2)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在测试所有连接...")

        self.jira_status_label.setText("状态: 测试中...")
        self.jira_status_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 5px;")
        self.confluence_status_label.setText("状态: 测试中...")
        self.confluence_status_label.setStyleSheet("color: #f39c12; font-weight: bold; padding: 5px;")

        self.login_workers.clear()
        self.login_results = {"jira": None, "confluence": None}

        jira_worker = LoginWorker("jira", jira_url, jira_username, jira_password)
        jira_worker.login_finished.connect(
            lambda s, success, msg: self.on_all_login_finished(s, success, msg)
        )

        confluence_worker = LoginWorker("confluence", confluence_url, confluence_username, confluence_password)
        confluence_worker.login_finished.connect(
            lambda s, success, msg: self.on_all_login_finished(s, success, msg)
        )

        self.login_workers.extend([jira_worker, confluence_worker])

        for worker in self.login_workers:
            worker.start()

    def on_login_finished(self, service: str, success: bool, message: str, status_label: QLabel):
        """单个登录完成"""
        self.login_results[service] = success
        if success:
            status_label.setText(f"状态: ✓ {message}")
            status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px;")
        else:
            status_label.setText(f"状态: ✗ {message}")
            status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")

    def on_all_login_finished(self, service: str, success: bool, message: str):
        """所有登录完成处理"""
        self.login_results[service] = success
        # 更新进度条
        current_value = self.progress_bar.value()
        self.progress_bar.setValue(current_value + 1)

        # 更新状态标签
        if service == "jira":
            self.on_login_finished(service, success, message, self.jira_status_label)
        elif service == "confluence":
            self.on_login_finished(service, success, message, self.confluence_status_label)

        # 检查是否全部完成
        if self.progress_bar.value() >= self.progress_bar.maximum():
            self.progress_bar.setVisible(False)
            self.status_label.setText("所有连接测试完成")

            # 检查结果
            jira_ok = "✓" in self.jira_status_label.text()
            confluence_ok = "✓" in self.confluence_status_label.text()

            if jira_ok and confluence_ok:
                if self.accept_after_all_tests:
                    if self.save_credentials(show_message=False):
                        self.accept_after_all_tests = False
                        super(LoginDialog, self).accept()
                    else:
                        self.accept_after_all_tests = False
                else:
                    QMessageBox.information(self, "成功", "所有连接测试成功！")
            else:
                self.accept_after_all_tests = False
                QMessageBox.warning(self, "警告", "Jira和Confluence都必须登录成功后才能进入报告助手页面")

    def accept(self):
        """只有两套连接都测试成功后才关闭登录弹窗。"""
        self.accept_after_all_tests = True
        self.test_all_connections()

    def save_credentials(self, show_message: bool = True) -> bool:
        """保存凭据"""
        credentials = {
            "jira": {
                "url": self.jira_url_edit.text().strip(),
                "username": self.jira_username_edit.text().strip(),
                "password": self.jira_password_edit.text().strip(),
            },
            "confluence": {
                "url": self.confluence_url_edit.text().strip(),
                "username": self.confluence_username_edit.text().strip(),
                "password": self.confluence_password_edit.text().strip(),
            }
        }

        missing = []
        for service_name, label in (("jira", "Jira"), ("confluence", "Confluence")):
            service = credentials[service_name]
            if not service["url"] or not service["username"] or not service["password"]:
                missing.append(f"{label}的URL、用户名和密码")
        if missing:
            QMessageBox.warning(self, "警告", "请填写" + "、".join(missing))
            return False

        try:
            config = get_config_manager()
            config.set_jira_config(
                credentials["jira"]["url"],
                credentials["jira"]["username"],
                credentials["jira"]["password"]
            )
            config.set_confluence_config(
                credentials["confluence"]["url"],
                credentials["confluence"]["username"],
                credentials["confluence"]["password"]
            )

            if show_message:
                QMessageBox.information(self, "成功", "凭据保存成功！")
            self.status_label.setText("凭据已保存")
            return True
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
            return False

    def get_credentials(self) -> Dict[str, Any]:
        """获取凭据数据"""
        return {
            "jira": {
                "url": self.jira_url_edit.text().strip(),
                "username": self.jira_username_edit.text().strip(),
                "password": self.jira_password_edit.text().strip(),
            },
            "confluence": {
                "url": self.confluence_url_edit.text().strip(),
                "username": self.confluence_username_edit.text().strip(),
                "password": self.confluence_password_edit.text().strip(),
            }
        }


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = LoginDialog()
    dialog.show()
    sys.exit(app.exec())
