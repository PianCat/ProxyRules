"""
检查生成器是否正确引用 Base 文件
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.utils.base_loader import BaseLoader
from Generator.generators.mihomo_generator import MihomoGenerator
from Generator.generators.stash_generator import StashGenerator
from Generator.generators.loon_generator import LoonGenerator
from Generator.scripts.generate_js_script import generate_mihomo_js_script


def check_base_loader():
    """检查 BaseLoader 是否正确加载所有 Base 文件"""
    print("=" * 60)
    print("检查 BaseLoader 文件引用")
    print("=" * 60)
    
    loader = BaseLoader()
    
    # 检查加载的文件
    base_files = {
        "DNS.yaml": loader.dns_ip_list and loader.dns_doh_list,
        "Ports.yaml": loader.mixed_port and loader.http_port and loader.socks5_port,
        "Fake_IP_Filter.yaml": loader.fake_ip_filter,
        "Test_URL.yaml": loader.internet_test_url and loader.proxy_test_url,
        "Head/Head_Mihomo.yaml": loader.head_mihomo,
        "Head/Head_Loon.conf": loader.head_loon,
        "Head/Head_Stash.yaml": loader.head_stash,
        "Rules/RemoteRules.yaml": loader.rule_loader.rules_data,
        "Rules/RemoteRulesLinkBase.yaml": loader.rule_loader.link_base_data,
    }
    
    print("\nBase 文件加载情况:")
    for file_name, is_loaded in base_files.items():
        status = "[OK]" if is_loaded else "[FAIL]"
        print(f"  {status} {file_name}")
    
    print(f"\nDNS IP 列表: {len(loader.dns_ip_list)} 个")
    print(f"DNS DoH 列表: {len(loader.dns_doh_list)} 个")
    print(f"Fake IP Filter: {len(loader.fake_ip_filter)} 条")
    print(f"规则提供者: {len(loader.get_rule_providers())} 个")
    print(f"规则列表: {len(loader.get_rules())} 条")
    
    return all(base_files.values())


def check_mihomo_generator():
    """检查 Mihomo 生成器是否正确使用 BaseLoader"""
    print("\n" + "=" * 60)
    print("检查 Mihomo 生成器")
    print("=" * 60)
    
    gen = MihomoGenerator()
    
    checks = {
        "使用 BaseLoader": hasattr(gen, 'base_loader'),
        "DNS 配置来自 Base": gen._build_dns_config(True, True) == gen.base_loader.get_dns_config(True, True),
        "Sniffer 配置来自 Base": gen._build_sniffer_config() == gen.base_loader.get_sniffer_config(),
        "GeoX URLs 来自 Base": gen._build_geox_urls() == gen.base_loader.get_geox_urls(),
        "规则来自 Base": gen._build_rules([]) == gen.base_loader.get_rules(),
        "规则提供者来自 Base": gen.base_loader.get_rule_providers() is not None,
    }
    
    print("\nMihomo 生成器检查:")
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {check_name}")
    
    return all(checks.values())


def check_stash_generator():
    """检查 Stash 生成器是否正确使用 BaseLoader"""
    print("\n" + "=" * 60)
    print("检查 Stash 生成器")
    print("=" * 60)
    
    gen = StashGenerator()
    
    checks = {
        "使用 BaseLoader": hasattr(gen, 'base_loader'),
        "DNS 配置来自 Base": gen._build_dns_config(True) == gen.base_loader.get_dns_config(True, True),
        "Sniffer 配置来自 Base": gen._build_sniffer_config() == gen.base_loader.get_sniffer_config(),
        "规则来自 Base": gen._build_rules() == gen.base_loader.get_rules(),
        "规则提供者来自 Base": gen.base_loader.get_rule_providers() is not None,
    }
    
    print("\nStash 生成器检查:")
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {check_name}")
    
    return all(checks.values())


def check_loon_generator():
    """检查 Loon 生成器是否正确使用 BaseLoader"""
    print("\n" + "=" * 60)
    print("检查 Loon 生成器")
    print("=" * 60)
    
    gen = LoonGenerator()
    
    checks = {
        "使用 BaseLoader": hasattr(gen, 'base_loader'),
        "DNS IP 列表来自 Base": len(gen.base_loader.dns_ip_list) > 0,
        "DNS DoH 列表来自 Base": len(gen.base_loader.dns_doh_list) > 0,
        "Fake IP Filter 来自 Base": len(gen.base_loader.fake_ip_filter) > 0,
        "端口配置来自 Base": gen.base_loader.http_port > 0,
        "测试 URL 来自 Base": gen.base_loader.internet_test_url and gen.base_loader.proxy_test_url,
        "规则加载器来自 Base": gen.rule_loader == gen.base_loader.rule_loader,
    }
    
    print("\nLoon 生成器检查:")
    for check_name, result in checks.items():
        status = "[OK]" if result else "[FAIL]"
        print(f"  {status} {check_name}")
    
    # 检查 General 段是否使用了 Base 配置
    general_section = gen._generate_general_section(False)
    uses_base_dns = '119.29.29.29' in general_section or '223.5.5.5' in general_section
    uses_base_port = str(gen.base_loader.http_port) in general_section
    uses_base_test_url = gen.base_loader.internet_test_url in general_section
    
    print("\nGeneral 段配置检查:")
    print(f"  {'[OK]' if uses_base_dns else '[FAIL]'} 使用 Base DNS 配置")
    print(f"  {'[OK]' if uses_base_port else '[FAIL]'} 使用 Base 端口配置")
    print(f"  {'[OK]' if uses_base_test_url else '[FAIL]'} 使用 Base 测试 URL")
    
    return all(checks.values()) and uses_base_dns and uses_base_port and uses_base_test_url


def check_js_script_generator():
    """检查 JS 脚本生成器是否正确使用 BaseLoader"""
    print("\n" + "=" * 60)
    print("检查 JS 脚本生成器")
    print("=" * 60)
    
    try:
        js_script = generate_mihomo_js_script()
        
        # 检查 JS 脚本中是否包含 Base 配置
        checks = {
            "生成成功": len(js_script) > 0,
            "包含 DNS IP 列表": '119.29.29.29' in js_script or 'DNS_IP_LIST' in js_script,
            "包含 DNS DoH 列表": 'doh.pub' in js_script or 'DNS_DOH_LIST' in js_script,
            "包含 Fake IP Filter": '*.lan' in js_script or 'FAKE_IP_FILTER' in js_script,
            "包含规则提供者": 'ruleProviders' in js_script,
            "包含规则列表": 'baseRules' in js_script or 'rules' in js_script,
        }
        
        print("\nJS 脚本生成器检查:")
        for check_name, result in checks.items():
            status = "[OK]" if result else "[FAIL]"
            print(f"  {status} {check_name}")
        
        return all(checks.values())
    except Exception as e:
        print(f"  [FAIL] 生成失败: {e}")
        return False


def main():
    """主函数"""
    print("\n" + "=" * 60)
    print("Base 文件引用检查报告")
    print("=" * 60)
    
    results = {
        "BaseLoader": check_base_loader(),
        "Mihomo 生成器": check_mihomo_generator(),
        "Stash 生成器": check_stash_generator(),
        "Loon 生成器": check_loon_generator(),
        "JS 脚本生成器": check_js_script_generator(),
    }
    
    print("\n" + "=" * 60)
    print("检查结果汇总")
    print("=" * 60)
    
    all_passed = True
    for component, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {component}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] 所有生成器都正确引用了 Base 文件")
    else:
        print("[FAIL] 部分生成器未正确引用 Base 文件")
    print("=" * 60)


if __name__ == '__main__':
    main()

