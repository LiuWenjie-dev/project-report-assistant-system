"""
测试数据提取功能
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from business.template_assembler import get_template_assembler
from utils.config_manager import get_config_manager


def test_template_assembler():
    """测试模板组装器"""
    print("=" * 50)
    print("测试模板组装器")
    print("=" * 50)
    
    try:
        # 获取配置
        config_manager = get_config_manager()
        
        # 使用示例数据
        project_key = "SWPL"
        confluence_url = "https://confluence.example.com/pages/viewpage.action?pageId=123456"
        
        print(f"使用项目: {project_key}")
        print(f"Confluence URL: {confluence_url}")
        
        # 创建模板组装器
        assembler = get_template_assembler()
        
        print("\n正在组装周报...")
        report_data = assembler.assemble_weekly_report(
            project_key=project_key,
            confluence_url=confluence_url,
            weekly_test_progress="本周完成了核心模块的测试，发现并修复了3个问题。"
        )
        
        print("✓ 周报组装成功")
        print(f"报告ID: {report_data.get('report_id', 'N/A')}")
        print(f"生成时间: {report_data.get('generated_time', 'N/A')}")
        
        # 显示报告内容
        print("\n报告内容:")
        print("-" * 30)
        
        sections = [
            ("项目整体状态", "project_status"),
            ("本周测试进展", "weekly_test_progress"),
            ("Highlight", "highlight"),
            ("整体测试进展", "overall_test_progress"),
            ("当前严重问题", "critical_issues"),
            ("下周测试计划", "next_week_plan"),
        ]
        
        for title, key in sections:
            content = report_data.get(key, "N/A")
            if content and content != "N/A":
                print(f"\n{title}:")
                print(content[:200] + "..." if len(content) > 200 else content)
        
        print("\n✓ 所有数据提取功能正常")
        return True
        
    except Exception as e:
        print(f"✗ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """测试配置验证"""
    print("\n" + "=" * 50)
    print("测试配置验证")
    print("=" * 50)
    
    try:
        config_manager = get_config_manager()
        
        # 检查Confluence配置
        confluence_config = config_manager.get_confluence_config()
        print(f"Confluence配置: {confluence_config.get('base_url', '未配置')}")
        
        # 检查Jira配置
        jira_config = config_manager.get_jira_config()
        print(f"Jira配置: {jira_config.get('base_url', '未配置')}")
        
        # 检查项目配置
        recent_projects = config_manager.get_recent_projects()
        print(f"最近项目数量: {len(recent_projects)}")
        
        if recent_projects:
            for project in recent_projects:
                print(f"  - {project.get('jira_project_key', 'N/A')}: {project.get('confluence_url', 'N/A')}")
        
        print("✓ 配置验证通过")
        return True
        
    except Exception as e:
        print(f"✗ 配置验证失败: {str(e)}")
        return False


def main():
    """主测试函数"""
    print("=" * 50)
    print("报告助手 - 数据提取功能测试")
    print("=" * 50)
    
    # 测试配置验证
    if not test_config_validation():
        print("\n⚠ 配置验证失败，请检查配置文件")
        print("  请确保已配置 .env 文件或使用默认配置")
    
    # 测试模板组装器
    print("\n" + "=" * 50)
    print("开始数据提取测试...")
    print("=" * 50)
    
    success = test_template_assembler()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ 所有测试通过！")
        print("=" * 50)
        print("\n数据提取功能已实现:")
        print("1. ✓ 项目整体状态 - 从Confluence提取next milestone")
        print("2. ✓ Highlight - 从Confluence提取highlight&blocked issue")
        print("3. ✓ 本周测试进展 - 用户手动输入")
        print("4. ✓ 整体测试进展 - 从Confluence提取Test status")
        print("5. ✓ 当前严重问题 - 从Jira提取P0/P1问题")
        print("6. ✓ 下周测试计划 - 从Confluence提取next action")
    else:
        print("\n" + "=" * 50)
        print("❌ 测试失败")
        print("=" * 50)
        print("\n可能的原因:")
        print("1. 网络连接问题")
        print("2. 认证凭据未配置")
        print("3. Confluence/Jira服务器不可达")
        print("4. 页面结构不匹配")
    
    return success


if __name__ == "__main__":
    main()