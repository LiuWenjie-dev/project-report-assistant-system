"""
仪表板主窗口 - 简约版本（包含完整6个部分）
"""

import sys
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QGroupBox,
    QComboBox, QMessageBox, QStatusBar, QApplication, QScrollArea,
    QFormLayout, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from typing import Dict, Any, List

from business.template_assembler import get_template_assembler
from utils.config_manager import get_config_manager
from data_sources.jira_client import get_jira_client
from .multi_select_combo import SimpleMultiSelectComboBox


class JiraSearchWorker(QThread):
    """Jira搜索工作线程"""

    search_finished = pyqtSignal(list)  # 搜索结果
    search_error = pyqtSignal(str)      # 错误消息

    def __init__(self, jql: str, max_results: int = 50):
        super().__init__()
        self.jql = jql
        self.max_results = max_results

    def run(self):
        """执行Jira搜索"""
        try:
            jira_client = get_jira_client()
            issues = jira_client.search_issues(self.jql, self.max_results)
            self.search_finished.emit(issues)
        except Exception as e:
            self.search_error.emit(str(e))


class DataFetcherWorker(QThread):
    """数据获取工作线程"""

    data_fetched = pyqtSignal(dict)  # 报告数据
    error_occurred = pyqtSignal(str)  # 错误消息

    def __init__(self, project_key: str, confluence_url: str):
        super().__init__()
        self.project_key = project_key
        self.confluence_url = confluence_url
        self.template_assembler = get_template_assembler()

    def run(self):
        """执行数据获取"""
        try:
            # 获取本周测试进展（从UI获取，这里暂时为空）
            weekly_test_progress = ""

            # 使用模板组装器获取数据
            report_data = self.template_assembler.assemble_weekly_report(
                project_key=self.project_key,
                confluence_url=self.confluence_url,
                weekly_test_progress=weekly_test_progress
            )

            # 发送数据
            self.data_fetched.emit(report_data)

        except Exception as e:
            self.error_occurred.emit(str(e))


class DashboardWindow(QMainWindow):
    """仪表板主窗口"""

    def __init__(self):
        super().__init__()
        self.current_report_data = None
        self.template_assembler = get_template_assembler()
        self.config_manager = get_config_manager()
        self.jira_options_loaded = False

        self.setup_ui()
        self.setup_connections()
        # 注意：不在初始化时加载选项，等待登录成功后调用 initialize_after_login()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("报告助手")
        self.setMinimumSize(1000, 800)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        self.setCentralWidget(scroll_area)

        # 创建中央部件
        central_widget = QWidget()
        scroll_area.setWidget(central_widget)

        # 主布局
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 标题
        title_label = QLabel("报告助手 - 周报生成工具")
        title_font = QFont("Microsoft YaHei", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # 项目选择区域 - 重新设计为分开的Jira和Confluence配置
        project_group = QGroupBox("项目配置")
        project_layout = QVBoxLayout()

        # Jira配置部分 - 增强版，包含筛选器
        jira_config_group = QGroupBox("Jira配置")
        jira_layout = QVBoxLayout()

        # 筛选器配置 - 使用网格布局
        filter_grid = QGridLayout()
        filter_grid.setSpacing(10)

        # Project ID筛选（第一个）
        filter_grid.addWidget(QLabel("Project ID:"), 0, 0)
        self.project_id_combo = SimpleMultiSelectComboBox()
        self.project_id_combo.setMinimumWidth(200)
        filter_grid.addWidget(self.project_id_combo, 0, 1)

        # 优先级筛选（第二个）
        filter_grid.addWidget(QLabel("优先级:"), 0, 2)
        self.priority_combo = SimpleMultiSelectComboBox()
        self.priority_combo.setMinimumWidth(200)
        filter_grid.addWidget(self.priority_combo, 0, 3)

        # 状态筛选（第三个）
        filter_grid.addWidget(QLabel("状态:"), 1, 0)
        self.status_combo = SimpleMultiSelectComboBox()
        self.status_combo.setMinimumWidth(200)
        filter_grid.addWidget(self.status_combo, 1, 1)

        # 标签筛选（第四个）
        filter_grid.addWidget(QLabel("标签:"), 1, 2)
        self.label_combo = SimpleMultiSelectComboBox()
        self.label_combo.setMinimumWidth(200)
        filter_grid.addWidget(self.label_combo, 1, 3)

        jira_layout.addLayout(filter_grid)

        # Jira筛选器按钮
        jira_button_row = QHBoxLayout()
        self.jira_filter_btn = QPushButton("🔍 应用筛选并获取问题")
        self.jira_filter_btn.setMinimumHeight(35)
        self.jira_filter_btn.setStyleSheet("""
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
        """)
        jira_button_row.addWidget(self.jira_filter_btn)
        self.login_config_btn = QPushButton("登录配置")
        self.login_config_btn.setMinimumHeight(35)
        self.login_config_btn.clicked.connect(self.open_login_config)
        jira_button_row.addWidget(self.login_config_btn)
        jira_button_row.addStretch()
        jira_layout.addLayout(jira_button_row)

        jira_config_group.setLayout(jira_layout)
        project_layout.addWidget(jira_config_group)

        # Confluence配置部分
        confluence_config_group = QGroupBox("Confluence配置")
        confluence_layout = QVBoxLayout()

        # Confluence URL
        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Confluence页面URL:"))
        self.confluence_url_edit = QLineEdit()
        self.confluence_url_edit.setPlaceholderText("https://confluence.example.com/pages/page-id")
        url_row.addWidget(self.confluence_url_edit)
        confluence_layout.addLayout(url_row)

        # Confluence页面说明
        confluence_info = QLabel("请输入Confluence页面的完整URL，用于提取项目状态信息")
        confluence_info.setStyleSheet("color: #7f8c8d; font-size: 11px; padding: 5px;")
        confluence_layout.addWidget(confluence_info)

        confluence_config_group.setLayout(confluence_layout)
        project_layout.addWidget(confluence_config_group)

        # 操作按钮
        button_row = QHBoxLayout()
        self.fetch_btn = QPushButton("🚀 一键获取数据")
        self.fetch_btn.setMinimumHeight(40)
        self.fetch_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        button_row.addWidget(self.fetch_btn)
        button_row.addStretch()
        project_layout.addLayout(button_row)

        project_group.setLayout(project_layout)
        main_layout.addWidget(project_group)

        # 报告编辑区域
        edit_group = QGroupBox("报告内容（6个部分）")
        edit_layout = QGridLayout()
        edit_layout.setSpacing(10)

        # 1. 项目整体状态
        edit_layout.addWidget(QLabel("1. 项目整体情况:"), 0, 0)
        self.project_status_edit = QTextEdit()
        self.project_status_edit.setPlaceholderText("从Confluence Next Milestone提取")
        self.project_status_edit.setMinimumHeight(100)
        edit_layout.addWidget(self.project_status_edit, 1, 0)

        # 2. 本周测试进展
        edit_layout.addWidget(QLabel("2. 本周测试进展:"), 0, 1)
        self.weekly_test_edit = QTextEdit()
        self.weekly_test_edit.setPlaceholderText("手动填写本周测试工作")
        self.weekly_test_edit.setMinimumHeight(100)
        edit_layout.addWidget(self.weekly_test_edit, 1, 1)

        # 3. Highlight
        edit_layout.addWidget(QLabel("3. Highlight:"), 2, 0)
        self.highlight_edit = QTextEdit()
        self.highlight_edit.setPlaceholderText("从Confluence Highlight & Blocked提取")
        self.highlight_edit.setMinimumHeight(100)
        edit_layout.addWidget(self.highlight_edit, 3, 0)

        # 4. 整体测试进展
        edit_layout.addWidget(QLabel("4. 整体测试进展:"), 2, 1)
        self.overall_test_edit = QTextEdit()
        self.overall_test_edit.setPlaceholderText("从Confluence Test Status提取")
        self.overall_test_edit.setMinimumHeight(100)
        edit_layout.addWidget(self.overall_test_edit, 3, 1)

        # 5. 当前严重问题
        edit_layout.addWidget(QLabel("5. 当前严重问题:"), 4, 0)
        self.critical_issues_edit = QTextEdit()
        self.critical_issues_edit.setPlaceholderText("从Jira P0/P1问题提取")
        self.critical_issues_edit.setMinimumHeight(100)
        edit_layout.addWidget(self.critical_issues_edit, 5, 0)

        # 6. 下周测试计划
        edit_layout.addWidget(QLabel("6. 下周测试计划:"), 4, 1)
        self.next_week_plan_edit = QTextEdit()
        self.next_week_plan_edit.setPlaceholderText("从Confluence Next Action提取")
        self.next_week_plan_edit.setMinimumHeight(100)
        edit_layout.addWidget(self.next_week_plan_edit, 5, 1)

        edit_group.setLayout(edit_layout)
        main_layout.addWidget(edit_group, 1)

        # 底部按钮
        bottom_buttons = QHBoxLayout()
        bottom_buttons.addStretch()

        self.preview_btn = QPushButton("预览报告")
        self.preview_btn.setMinimumWidth(100)
        bottom_buttons.addWidget(self.preview_btn)

        main_layout.addLayout(bottom_buttons)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def setup_connections(self):
        """设置信号连接"""
        self.fetch_btn.clicked.connect(self.fetch_data)
        self.jira_filter_btn.clicked.connect(self.open_jira_filter)
        self.preview_btn.clicked.connect(self.preview_report)

    def load_jira_options(self):
        """加载Jira选项"""
        try:
            # 获取Jira客户端
            jira_client = get_jira_client()

            # 获取可用选项（包含验证信息）
            result = jira_client.get_available_options()

            # 显示验证结果
            validation = result.get("validation", {})
            if validation.get("errors"):
                error_msg = "Jira配置错误: " + ", ".join(validation["errors"])
                self.status_bar.showMessage(error_msg)
                QMessageBox.warning(self, "配置错误", error_msg)
                return

            if not result.get("success", False):
                error_msg = result.get("error", "未知错误")
                self.status_bar.showMessage(f"加载Jira选项失败: {error_msg}")
                QMessageBox.warning(self, "加载失败", f"加载Jira选项失败: {error_msg}")
                return

            # 获取选项数据
            options = result.get("options", {})

            # Project ID 保留手动输入，不在登录初始化阶段自动扫描选项
            self.project_id_combo.clear()
            self.project_id_combo.lineEdit().setPlaceholderText("输入SW Project ID，可用逗号分隔")

            # 更新优先级选项
            priorities = options.get("priorities", [])
            self.priority_combo.clear()
            self.priority_combo.addItem("所有优先级")
            if priorities:
                for priority in sorted(priorities):
                    self.priority_combo.addItem(priority)
            else:
                self.status_bar.showMessage("未从Jira获取到优先级选项，选项为空")

            # 更新状态选项
            statuses = options.get("statuses", [])
            self.status_combo.clear()
            self.status_combo.addItem("所有状态")
            if statuses:
                for status in sorted(statuses):
                    self.status_combo.addItem(status)
            else:
                self.status_bar.showMessage("未从Jira获取到状态选项，选项为空")

            # 更新标签选项
            labels = options.get("labels", [])
            self.label_combo.clear()
            self.label_combo.addItem("所有标签")
            if labels:
                for label in sorted(labels):
                    self.label_combo.addItem(label)
            else:
                self.status_bar.showMessage("未从Jira获取到标签选项，选项为空")

            # 显示成功消息
            self.jira_options_loaded = True
            success_msg = "Jira选项加载完成"

            # 添加统计信息
            stats = []
            if priorities:
                stats.append(f"优先级: {len(priorities)}个")
            if statuses:
                stats.append(f"状态: {len(statuses)}个")
            if labels:
                stats.append(f"标签: {len(labels)}个")

            if stats:
                success_msg += f" ({', '.join(stats)})"

            self.status_bar.showMessage(success_msg)

            # 显示警告信息（如果有）
            warning = result.get("warning")
            if warning:
                QMessageBox.information(self, "加载完成", f"{success_msg}\n\n注意: {warning}")

        except Exception as e:
            error_msg = f"加载Jira选项失败: {str(e)}"
            self.status_bar.showMessage(error_msg)
            print(f"加载Jira选项失败: {e}")
            QMessageBox.critical(self, "错误", error_msg)

    def open_login_config(self):
        """打开登录配置对话框。"""
        from gui.login_dialog import LoginDialog
        import data_sources.jira_client
        dialog = LoginDialog(self)
        if dialog.exec():
            credentials = dialog.get_credentials()
            jira = credentials.get("jira", {})
            confluence = credentials.get("confluence", {})
            if not jira.get("url") or not jira.get("username") or not jira.get("password"):
                QMessageBox.warning(self, "配置未保存", "请完整填写Jira的URL、用户名和密码")
                return
            self.config_manager.set_jira_config(jira["url"], jira["username"], jira["password"])
            if confluence.get("url") and confluence.get("username") and confluence.get("password"):
                self.config_manager.set_confluence_config(confluence["url"], confluence["username"], confluence["password"])
            data_sources.jira_client._jira_client = None
            self.status_bar.showMessage("登录配置已保存，正在重新加载Jira选项...")
            self.load_jira_options()

    def initialize_after_login(self):
        """登录成功后初始化"""
        self.status_bar.showMessage("登录成功，正在加载Jira选项...")
        self.load_jira_options()

    def on_project_changed(self, project_name: str):
        """项目选择变化（保留方法，但不再使用）"""
        pass

    def fetch_data(self):
        """获取数据"""
        confluence_url = self.confluence_url_edit.text().strip()
        if not confluence_url:
            QMessageBox.warning(self, "警告", "请输入Confluence URL")
            return

        # 禁用按钮，防止重复点击
        self.fetch_btn.setEnabled(False)
        self.fetch_btn.setText("获取中...")
        self.status_bar.showMessage("正在从Confluence获取数据...")

        # 使用工作线程获取数据（项目参数设为空，因为项目选择已删除）
        self.data_worker = DataFetcherWorker("", confluence_url)
        self.data_worker.data_fetched.connect(self.on_data_fetched)
        self.data_worker.error_occurred.connect(self.on_data_fetch_error)
        self.data_worker.start()

    def on_data_fetched(self, report_data):
        """数据获取完成"""
        try:
            # 更新UI状态
            self.fetch_btn.setEnabled(True)
            self.fetch_btn.setText("获取数据")

            # 保存报告数据
            self.current_report_data = report_data

            # 提取并显示数据
            sections = report_data.get("sections", {})

            # 1. 项目整体状态 (Next Milestone)
            if sections.get("next_milestone"):
                self.project_status_edit.setPlainText(sections["next_milestone"])
            else:
                self.project_status_edit.setPlainText("未找到Next Milestone信息")

            # 2. Highlight & Blocked Issues
            if sections.get("highlight_blocked"):
                self.highlight_edit.setPlainText(sections["highlight_blocked"])
            else:
                self.highlight_edit.setPlainText("未找到Highlight & Blocked Issues信息")

            # 3. 整体测试进展 (Test Status)
            if sections.get("test_status"):
                self.overall_test_edit.setPlainText(sections["test_status"])
            else:
                self.overall_test_edit.setPlainText("未找到Test Status信息")

            # 4. 当前严重问题 (P0/P1 Issues)
            if sections.get("priority_issues"):
                self.critical_issues_edit.setPlainText(sections["priority_issues"])
            else:
                self.critical_issues_edit.setPlainText("未找到P0/P1问题")

            # 5. 下周测试计划 (Next Action)
            if sections.get("next_action"):
                self.next_week_plan_edit.setPlainText(sections["next_action"])
            else:
                self.next_week_plan_edit.setPlainText("未找到Next Action信息")

            # 显示问题统计
            issue_count = report_data.get("jira_issue_count", 0)
            if issue_count > 0:
                self.status_bar.showMessage(f"数据获取完成，发现{issue_count}个P0/P1问题")
            else:
                self.status_bar.showMessage("数据获取完成")

            QMessageBox.information(self, "成功", "数据获取完成！")

        except Exception as e:
            self.on_data_fetch_error(str(e))

    def on_data_fetch_error(self, error_message):
        """数据获取错误"""
        self.fetch_btn.setEnabled(True)
        self.fetch_btn.setText("获取数据")
        self.status_bar.showMessage("数据获取失败")
        QMessageBox.critical(self, "错误", f"数据获取失败:\n{error_message}")

    def preview_report(self):
        """预览报告"""
        # 检查是否有报告数据
        if not self.current_report_data:
            QMessageBox.warning(self, "警告", "请先获取数据")
            return

        # 获取完整报告
        complete_report = self.current_report_data.get("complete_report", "")
        if not complete_report:
            QMessageBox.warning(self, "警告", "报告数据不完整")
            return

        # 创建自定义预览对话框
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QScrollArea
        from PyQt6.QtCore import Qt, QTimer
        from PyQt6.QtGui import QFont, QTextCursor
        from PyQt6.QtWidgets import QApplication

        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("完整报告预览")
        preview_dialog.setMinimumSize(800, 600)
        preview_dialog.resize(1000, 700)

        # 主布局
        layout = QVBoxLayout(preview_dialog)

        # 标题
        title_label = QLabel("完整报告预览")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_font = QFont("Arial", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; padding: 10px;")
        layout.addWidget(title_label)

        # 文本编辑框（用于显示和复制）
        text_edit = QTextEdit()
        text_edit.setPlainText(complete_report)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)

        # 添加滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidget(text_edit)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 复制按钮
        copy_button = QPushButton("📋 一键复制")
        copy_button.setToolTip("复制全部内容到剪贴板")
        copy_button.clicked.connect(lambda: self._copy_to_clipboard(complete_report, text_edit, copy_status_label))
        copy_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
        """)

        # 关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(preview_dialog.accept)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        button_layout.addWidget(copy_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)

        layout.addLayout(button_layout)

        # 状态标签
        copy_status_label = QLabel("")
        copy_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        copy_status_label.setStyleSheet("color: #27ae60; padding: 5px;")
        layout.addWidget(copy_status_label)

        preview_dialog.exec()

    def _format_jql_value(self, value: str) -> str:
        """格式化JQL值；简单ID保持不加引号，含空格或特殊字符时加引号。"""
        import re
        value = value.strip()
        if re.fullmatch(r"[A-Za-z0-9_.-]+", value):
            return value
        return '"' + value.replace('"', '\\"') + '"'

    def _build_jql_condition(self, field_name: str, values: list) -> str:
        """根据字段和值列表构建JQL条件。"""
        cleaned = [v.strip() for v in values if v and v.strip()]
        if not cleaned:
            return ""
        parts = [f"{field_name} = {self._format_jql_value(value)}" for value in cleaned]
        return parts[0] if len(parts) == 1 else "(" + " OR ".join(parts) + ")"

    def _normalize_priority_values(self, values: list) -> list:
        """将内部P级别习惯名转换成Jira标准优先级值。"""
        mapping = {
            "P0": "Highest",
            "P1": "High",
            "P2": "Medium",
            "P3": "Low",
            "P4": "Lowest",
        }
        normalized = []
        for value in values:
            raw = value.strip()
            upper = raw.upper()
            matched = None
            for code, jira_value in mapping.items():
                if upper == code or upper.startswith(code + " ") or upper.startswith(code + "-"):
                    matched = jira_value
                    break
            normalized.append(matched or raw)
        return normalized

    def open_jira_filter(self):
        """应用Jira筛选并获取问题"""
        # 构建JQL查询
        jql_parts = []
        jira_client = get_jira_client()
        project_id_field = jira_client.get_project_id_jql_field()

        # Project ID筛选（使用多选下拉框）
        project_ids = self.project_id_combo.get_selected_items()
        if project_ids and "所有ID" not in project_ids:
            condition = self._build_jql_condition(project_id_field, project_ids)
            if condition:
                jql_parts.append(condition)

        # 优先级筛选（使用完整优先级值，不截断为P0/P1）
        priorities = self.priority_combo.get_selected_items()
        if priorities and "所有优先级" not in priorities:
            priorities = self._normalize_priority_values(priorities)
            condition = self._build_jql_condition("priority", priorities)
            if condition:
                jql_parts.append(condition)

        # 状态筛选（使用多选下拉框）
        statuses = self.status_combo.get_selected_items()
        if statuses and "所有状态" not in statuses:
            condition = self._build_jql_condition("status", statuses)
            if condition:
                jql_parts.append(condition)

        # 标签筛选（使用多选下拉框）
        labels = self.label_combo.get_selected_items()
        if labels and "所有标签" not in labels:
            condition = self._build_jql_condition("labels", labels)
            if condition:
                jql_parts.append(condition)
        # 如果没有筛选条件，使用宽查询
        if not jql_parts:
            jql = 'ORDER BY updated DESC'
        else:
            jql = " AND ".join(jql_parts)

        # 显示状态
        self.status_bar.showMessage(f"正在搜索: {jql}")
        self.jira_filter_btn.setEnabled(False)
        self.jira_filter_btn.setText("搜索中...")

        # 使用工作线程执行搜索
        self.jira_search_worker = JiraSearchWorker(jql, max_results=50)
        self.jira_search_worker.search_finished.connect(self.on_jira_search_finished)
        self.jira_search_worker.search_error.connect(self.on_jira_search_error)
        self.jira_search_worker.start()

    def on_jira_search_finished(self, issues: List[Dict[str, Any]]):
        """Jira搜索完成"""
        try:
            # 更新UI状态
            self.jira_filter_btn.setEnabled(True)
            self.jira_filter_btn.setText("🔍 应用筛选并获取问题")

            if not issues:
                self.status_bar.showMessage("未找到匹配的问题")
                QMessageBox.information(self, "搜索结果", "未找到匹配的问题")
                return

            # 格式化问题列表
            issue_text = f"找到 {len(issues)} 个问题:\n\n"
            for i, issue in enumerate(issues, 1):
                key = issue.get("key", "UNKNOWN")
                summary = issue.get("summary", "无标题")
                status = issue.get("status", "未知状态")
                priority = issue.get("priority", "未知优先级")

                issue_text += f"{i}. [{key}] {summary}\n"
                issue_text += f"   状态: {status}, 优先级: {priority}\n"

                # 添加描述（如果有）
                description = issue.get("description", "")
                if description and len(description) > 100:
                    description = description[:100] + "..."
                if description:
                    issue_text += f"   描述: {description}\n"

                issue_text += "\n"

            # 将结果放入"当前严重问题"文本框
            self.critical_issues_edit.setPlainText(issue_text)

            # 显示成功消息
            self.status_bar.showMessage(f"找到 {len(issues)} 个问题，已添加到报告")
            QMessageBox.information(self, "成功", f"找到 {len(issues)} 个问题，已添加到报告内容")

        except Exception as e:
            self.on_jira_search_error(str(e))

    def on_jira_search_error(self, error_message: str):
        """Jira搜索错误"""
        self.jira_filter_btn.setEnabled(True)
        self.jira_filter_btn.setText("🔍 应用筛选并获取问题")
        self.status_bar.showMessage("搜索失败")
        QMessageBox.critical(self, "错误", f"Jira搜索失败:\n{error_message}")

    def _copy_to_clipboard(self, text: str, text_edit, status_label):
        """复制文本到剪贴板"""
        try:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)

            # 高亮显示已复制
            text_edit.selectAll()
            text_edit.setStyleSheet("""
                QTextEdit {
                    background-color: #d5f4e6;
                    border: 2px solid #27ae60;
                    border-radius: 5px;
                    padding: 10px;
                    font-family: 'Consolas', 'Monaco', monospace;
                }
            """)

            # 显示成功消息
            status_label.setText("✓ 已复制到剪贴板")
            status_label.setStyleSheet("color: #27ae60; font-weight: bold; padding: 5px;")

            # 2秒后恢复原样式
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self._reset_text_edit_style(text_edit))
            QTimer.singleShot(2000, lambda: status_label.setText(""))

        except Exception as e:
            status_label.setText(f"✗ 复制失败: {str(e)}")
            status_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 5px;")

    def _reset_text_edit_style(self, text_edit):
        """恢复文本编辑框样式"""
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 2px solid #3498db;
                border-radius: 5px;
                padding: 10px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)
        from PyQt6.QtGui import QTextCursor
        text_edit.moveCursor(QTextCursor.MoveOperation.End)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = DashboardWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
