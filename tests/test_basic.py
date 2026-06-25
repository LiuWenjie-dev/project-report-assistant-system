"""
基本功能测试
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.config_manager import ConfigManager
from utils.text_formatter import TextFormatter


def test_config_manager():
    """测试配置管理器"""
    print("测试配置管理器...")
    
    try:
        config = ConfigManager()
        
        # 测试获取配置
        confluence_config = config.get_confluence_config()
        jira_config = config.get_jira_config()
        email_config = config.get_email_config()
        
        print(f"✓ 配置管理器初始化成功")
        print(f"  Confluence配置: {confluence_config['base_url'][:30]}...")
        print(f"  Jira配置: {jira_config['base_url'][:30]}...")
        print(f"  邮件配置: 主题前缀={email_config['subject_prefix']}")
        
        # 测试项目配置
        test_project = {
            "name": "Test Project",
            "jira_project_key": "TEST",
            "confluence_page_url": "https://example.com/test",
            "confluence_page_id": "12345"
        }
        
        config.add_project(test_project)
        retrieved = config.get_project("TEST")
        
        if retrieved and retrieved["jira_project_key"] == "TEST":
            print("✓ 项目配置管理功能正常")
        else:
            print("✗ 项目配置管理功能异常")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置管理器测试失败: {e}")
        return False


def test_text_formatter():
    """测试文本格式化工具"""
    print("\n测试文本格式化工具...")
    
    try:
        formatter = TextFormatter()
        
        # 测试时间戳格式化
        timestamp = formatter.format_timestamp()
        print(f"✓ 时间戳格式化: {timestamp}")
        
        # 测试文本截断
        long_text = "这是一段很长的文本，需要被截断显示"
        truncated = formatter.truncate_text(long_text, max_length=10)
        print(f"✓ 文本截断: {truncated}")
        
        # 测试列表格式化
        items = ["项目1", "项目2", "项目3"]
        formatted_list = formatter.format_list_items(items)
        print(f"✓ 列表格式化:\n{formatted_list}")
        
        # 测试字数统计
        test_text = "这是一个测试文本\n包含两行内容"
        word_count = formatter.word_count(test_text)
        print(f"✓ 字数统计: {word_count}")
        
        return True
        
    except Exception as e:
        print(f"✗ 文本格式化工具测试失败: {e}")
        return False


def test_imports():
    """测试模块导入"""
    print("\n测试模块导入...")
    
    modules_to_test = [
        ("data_sources.confluence_client", "ConfluenceClient"),
        ("data_sources.jira_client", "JiraClient"),
        ("data_sources.outlook_client", "OutlookClient"),
        ("business.template_assembler", "TemplateAssembler"),
        ("gui.dashboard_window", "DashboardWindow"),
    ]
    
    all_passed = True
    
    for module_path, class_name in modules_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name, None)
            
            if cls:
                print(f"✓ {module_path}.{class_name} 导入成功")
            else:
                print(f"✗ {module_path}.{class_name} 导入失败 - 类不存在")
                all_passed = False
                
        except ImportError as e:
            print(f"✗ {module_path}.{class_name} 导入失败: {e}")
            all_passed = False
        except Exception as e:
            print(f"✗ {module_path}.{class_name} 导入异常: {e}")
            all_passed = False
    
    return all_passed


def main():
    """主测试函数"""
    print("=" * 50)
    print("报告助手 - 基本功能测试")
    print("=" * 50)
    
    tests = [
        ("配置管理器", test_config_manager),
        ("文本格式化工具", test_text_formatter),
        ("模块导入", test_imports),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ 测试执行异常: {e}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    passed_count = 0
    total_count = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed_count += 1
    
    print(f"\n总计: {passed_count}/{total_count} 个测试通过")
    
    if passed_count == total_count:
        print("\n✅ 所有基本功能测试通过!")
        return 0
    else:
        print("\n❌ 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())