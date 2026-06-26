"""
报告助手主程序入口 - 集成仪表板和登录功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gui.dashboard_window import DashboardWindow
from gui.login_dialog import LoginDialog
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer


def check_dependencies():
    """检查依赖"""
    dependencies = [
        ("PyQt6", "pip install PyQt6"),
        ("requests", "pip install requests"),
        ("win32com.client", "pip install pywin32"),
        ("bs4", "pip install beautifulsoup4"),
        ("jira", "pip install jira"),
    ]

    missing = []
    for dep, install_cmd in dependencies:
        try:
            if dep == "PyQt6":
                from PyQt6.QtWidgets import QApplication
            elif dep == "win32com.client":
                import win32com.client
            elif dep == "bs4":
                from bs4 import BeautifulSoup
            elif dep == "jira":
                import jira
            else:
                __import__(dep)
            print(f"✓ {dep} 已安装")
        except ImportError:
            print(f"✗ {dep} 未安装")
            missing.append((dep, install_cmd))

    # 可选检查atlassian
    try:
        from atlassian import Confluence
        print("✓ atlassian 已安装")
    except ImportError:
        print("⚠ atlassian 未安装 (Confluence功能可能受限)")

    return missing


def setup_environment():
    """设置环境"""
    from utils.config_manager import get_config_manager

    config = get_config_manager()

    # 检查配置文件是否存在
    if not config.config_file.exists():
        print("正在创建默认配置文件...")
        config.create_default_config()
        print("✓ 默认配置文件已创建")

    # 检查环境文件是否存在
    env_file = project_root / ".env"
    if not env_file.exists():
        print("⚠ 请复制 .env.example 为 .env 并填写您的配置")
        print(f"  配置文件位置: {env_file}")

    return True


def check_login_required():
    """检查是否需要登录"""
    from utils.config_manager import get_config_manager

    config = get_config_manager()

    # 检查是否有保存的凭据
    jira_config = config.get_jira_config()
    confluence_config = config.get_confluence_config()

    # 检查Jira凭据是否完整（URL、用户名、密码）
    has_jira_creds = jira_config.get("base_url") and jira_config.get("username") and jira_config.get("api_token")
    has_confluence_creds = confluence_config.get("base_url") and confluence_config.get("username") and confluence_config.get("api_token")

    # 如果Jira没有完整凭据，需要登录
    if not has_jira_creds:
        return True

    # 检查"记住我"选项
    login_options = config.get("login_options", {})
    if not login_options.get("remember_me", True):
        return True

    return False


def show_login_dialog(parent=None):
    """显示登录对话框并返回登录结果"""
    dialog = LoginDialog(parent)
    return dialog


def main():
    """主函数"""
    print("=" * 50)
    print("报告助手 - 一键生成周报邮件")
    print("=" * 50)
    print()

    # 检查依赖
    print("检查依赖...")
    missing_deps = check_dependencies()

    if missing_deps:
        print("\n以下依赖未安装:")
        for dep, install_cmd in missing_deps:
            print(f"  - {dep}: {install_cmd}")

        response = input("\n是否尝试自动安装缺失依赖? (y/n): ")
        if response.lower() == 'y':
            for dep, install_cmd in missing_deps:
                print(f"正在安装 {dep}...")
                os.system(install_cmd)

            # 重新检查依赖
            print("\n重新检查依赖...")
            missing_deps = check_dependencies()
            if missing_deps:
                print("\n仍有依赖未安装，请手动安装")
                input("按Enter键退出...")
                return
        else:
            print("\n请安装缺失的依赖后重试")
            input("按Enter键退出...")
            return

    print()

    # 设置环境
    print("设置环境...")
    if not setup_environment():
        print("\n环境设置失败")
        input("按Enter键退出...")
        return

    print()
    print("=" * 50)
    print("启动应用程序...")
    print("=" * 50)

    # 创建应用程序
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # 每次启动都先显示登录配置界面，只有Jira和Confluence都登录成功后才进入仪表盘
    need_login = True

    # 保留直进仪表盘分支用于后续需要恢复"记住登录"时复用
    if not need_login:
        print("\n使用已保存的凭据...")
        # 创建主窗口
        print("启动仪表板...")
        window = DashboardWindow()
        window.show()
        window.setWindowTitle("报告助手 - 仪表板")
        sys.exit(app.exec())
    else:
        # 需要登录，显示登录对话框
        print("\n需要配置系统登录...")

        # 循环直到登录成功或用户取消
        while True:
            dialog = show_login_dialog()

            if dialog.exec():
                # 登录成功，检查凭据是否完整
                credentials = dialog.get_credentials()

                jira_complete = all([
                    credentials["jira"]["url"],
                    credentials["jira"]["username"],
                    credentials["jira"]["password"]
                ])

                confluence_complete = all([
                    credentials["confluence"]["url"],
                    credentials["confluence"]["username"],
                    credentials["confluence"]["password"]
                ])

                # 如果Jira或Confluence未配置完整，阻止进入仪表盘
                if not jira_complete or not confluence_complete:
                    QMessageBox.critical(None, "登录失败",
                                       "Jira和Confluence凭据都必须配置完整！\n"
                                       "请完整填写两者的URL、用户名和密码。\n"
                                       "两边登录成功后才能进入报告助手页面。")
                    print("登录失败: Jira或Confluence凭据不完整")

                    # 询问用户是否重试
                    retry = QMessageBox.question(
                        None,
                        "登录失败",
                        "Jira和Confluence凭据都必须配置完整！是否重新尝试登录？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )

                    if retry == QMessageBox.StandardButton.No:
                        print("用户选择不重试，退出应用程序")
                        QMessageBox.information(None, "退出", "应用程序已退出")
                        return  # 退出应用程序
                    # 如果选择Yes，循环继续，重新显示登录对话框
                    continue

                # 登录成功
                message = "Jira和Confluence凭据均已配置"
                print(f"登录成功: {message}")

                # 登录成功后立即保存凭据，确保仪表板里的JiraClient能读取到配置
                from utils.config_manager import get_config_manager
                config_manager = get_config_manager()
                config_manager.set_jira_config(
                    credentials["jira"]["url"],
                    credentials["jira"]["username"],
                    credentials["jira"]["password"]
                )
                config_manager.set_confluence_config(
                    credentials["confluence"]["url"],
                    credentials["confluence"]["username"],
                    credentials["confluence"]["password"]
                )
                # 重置Jira客户端单例，强制重新初始化
                from data_sources.jira_client import _jira_client
                # 使用模块级别的全局变量
                import data_sources.jira_client
                import data_sources.confluence_client
                data_sources.jira_client._jira_client = None
                data_sources.confluence_client._confluence_client = None

                # 创建仪表盘窗口
                print("启动仪表板...")
                window = DashboardWindow()
                window.show()
                window.setWindowTitle("报告助手 - 仪表板")

                # 仪表盘自己负责初始化
                window.initialize_after_login()

                sys.exit(app.exec())
            else:
                # 用户取消登录
                print("用户取消登录")

                # 询问用户是否重试
                retry = QMessageBox.question(
                    None,
                    "登录取消",
                    "您取消了登录。是否重新尝试登录？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if retry == QMessageBox.StandardButton.No:
                    print("用户选择不重试，退出应用程序")
                    QMessageBox.information(None, "退出", "应用程序已退出")
                    return  # 退出应用程序
                # 如果选择Yes，循环继续，重新显示登录对话框


if __name__ == "__main__":
    main()
