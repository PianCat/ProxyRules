"""
生成 JS 转换脚本
将 Base 文件的内容嵌入到 JS 脚本中
"""

from pathlib import Path
import sys
import json

project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from Generator.utils.base_loader import BaseLoader
from Generator.utils.file_helper import FileHelper
from Generator.utils.yaml_helper import YamlHelper


def generate_js_script_core(use_args: bool = True, ipv6_enabled: bool = True, full_config: bool = False) -> str:
    """
    生成 Mihomo JS 转换脚本核心内容
    
    Args:
        use_args: 是否使用 $arguments（True 为 args 版本，False 为固定参数版本）
        ipv6_enabled: IPv6 是否启用（仅在 use_args=False 时使用）
        full_config: 是否生成完整配置（仅在 use_args=False 时使用）
    
    Returns:
        JS 脚本字符串
    """
    loader = BaseLoader()
    
    # 将配置转换为 JS 格式
    dns_ip_list_js = json.dumps(loader.dns_ip_list, ensure_ascii=False, indent=2)
    dns_doh_list_js = json.dumps(loader.dns_doh_list, ensure_ascii=False, indent=2)
    fake_ip_filter_js = json.dumps(loader.fake_ip_filter, ensure_ascii=False, indent=2)
    rule_providers_js = json.dumps(loader.get_rule_providers(), ensure_ascii=False, indent=2)
    rules_js = json.dumps(loader.get_rules(), ensure_ascii=False, indent=2)
    
    # 生成规则提供者和规则的 JS 对象
    rule_providers_obj = "const ruleProviders = " + rule_providers_js + ";\n"
    rules_obj = "const baseRules = " + rules_js + ";\n"
    
    # 参数定义部分（根据 use_args 决定）
    if use_args:
        # args 版本：使用 $arguments
        param_section = """/**
 * 解析传入的脚本参数，并将其转换为内部使用的功能开关（feature flags）。
 * @param {object} args - 传入的原始参数对象，如 $arguments。
 * @returns {object} - 包含所有功能开关状态的对象。
 */
function buildFeatureFlags(args) {
    const spec = {
        ipv6: "ipv6Enabled",
        full: "fullConfig"
    };

    const flags = Object.entries(spec).reduce((acc, [sourceKey, targetKey]) => {
        // ipv6 默认为 true，其他默认为 false
        const defaultValue = (sourceKey === "ipv6") ? true : false;
        if (args[sourceKey] === undefined || args[sourceKey] === null) {
            acc[targetKey] = defaultValue;
        } else {
            acc[targetKey] = parseBool(args[sourceKey]);
        }
        return acc;
    }, {});

    // 单独处理数字参数
    flags.countryThreshold = parseNumber(args.threshold, 0);

    return flags;
}

const rawArgs = typeof $arguments !== 'undefined' ? $arguments : {};

const {
    ipv6Enabled,
    fullConfig,
    countryThreshold
} = buildFeatureFlags(rawArgs);"""
    else:
        # 固定参数版本：在脚本内定义参数（用注释框起来）
        ipv6_val = "true" if ipv6_enabled else "false"
        full_val = "true" if full_config else "false"
        param_section = f"""// ============================================
// 参数定义区域（可根据需要修改）
// ============================================
const ipv6Enabled = {ipv6_val};
const fullConfig = {full_val};
const countryThreshold = 0;
// ============================================
// 参数定义区域结束
// ============================================"""
    
    # JS 脚本模板
    js_template = """/*
PianCat 的 Substore 订阅转换脚本
https://github.com/PianCat/ProxyRules

支持的传入参数：
- ipv6: 启用 IPv6 支持（默认 true）
- full: 输出完整配置（适合纯内核启动，默认 false）
- threshold: 国家节点数量小于该值时不显示分组 (默认 0)

注意：DNS 始终使用 FakeIP 模式
*/

const NODE_SUFFIX = "节点";

function parseBool(value) {
    if (typeof value === "boolean") return value;
    if (typeof value === "string") {
        return value.toLowerCase() === "true" || value === "1";
    }
    return false;
}

function parseNumber(value, defaultValue = 0) {
    if (value === null || typeof value === 'undefined') {
        return defaultValue;
    }
    const num = parseInt(value, 10);
    return isNaN(num) ? defaultValue : num;
}

{param_section}

function getCountryGroupNames(countryInfo, minCount) {
    // 定义固定的顺序：香港 → 台湾 → 新加坡 → 日本 → 美国
    const countryOrder = ["香港", "台湾", "新加坡", "日本", "美国"];
    
    // 先过滤出满足最小数量要求的国家
    const filtered = countryInfo.filter(item => item.count >= minCount);
    
    // 按照固定顺序排序
    const sorted = countryOrder
        .map(country => filtered.find(item => item.country === country))
        .filter(Boolean);
    
    // 添加不在固定顺序中的其他国家（如果有的话）
    const otherCountries = filtered.filter(
        item => !countryOrder.includes(item.country)
    );
    
    // 合并并转换为组名
    return [...sorted, ...otherCountries]
        .map(item => item.country + NODE_SUFFIX);
}

function stripNodeSuffix(groupNames) {
    const suffixPattern = new RegExp(`${NODE_SUFFIX}$`);
    return groupNames.map(name => name.replace(suffixPattern, ""));
}

const PROXY_GROUPS = {
    SELECT: "选择代理",
    MANUAL: "手动选择",
    DIRECT: "直接连接",
};

// 辅助函数，用于根据条件构建数组，自动过滤掉无效值（如 false, null）
const buildList = (...elements) => elements.flat().filter(Boolean);

function buildBaseLists({ countryGroupNames }) {
    // 使用辅助函数和常量，以声明方式构建各个代理列表

    // "选择节点"组的候选列表 - 与 yaml 文件一致，包含地区节点、其他节点、手动选择、DIRECT
    const defaultSelector = buildList(
        countryGroupNames,
        "其他节点",
        PROXY_GROUPS.MANUAL,
        "DIRECT"
    );

    // 默认的代理列表，用于大多数策略组（与 yaml 文件中的 *a1 引用一致）
    // 包含：选择代理 → 地区节点 → 其他节点 → 手动选择 → 直接连接
    const defaultProxies = buildList(
        PROXY_GROUPS.SELECT,
        countryGroupNames,
        "其他节点",
        PROXY_GROUPS.MANUAL,
        PROXY_GROUPS.DIRECT
    );

    // "直连"优先的代理列表 - 用于 Apple、Microsoft 等需要直连优先的代理组
    // 顺序：直接连接 -> 地区节点 -> 选择代理 -> 手动选择
    const defaultProxiesDirect = buildList(
        PROXY_GROUPS.DIRECT,
        countryGroupNames,
        PROXY_GROUPS.SELECT,
        PROXY_GROUPS.MANUAL
    );

    return { defaultProxies, defaultProxiesDirect, defaultSelector };
}

// 从 Base 文件加载的配置
const DNS_IP_LIST = {dns_ip_list};
const DNS_DOH_LIST = {dns_doh_list};
const FAKE_IP_FILTER = {fake_ip_filter};
const MIXED_PORT = {mixed_port};

{rule_providers_code}

{rules_code}

function buildRules() {
    return [...baseRules];
}

const snifferConfig = {
    "sniff": {
        "HTTP": {
            "ports": [80, "8080-8880"],
            "override-destination": true
        },
        "TLS": {
            "ports": [443, 8443]
        },
        "QUIC": {
            "ports": [443, 8443]
        }
    },
    "skip-domain": [
        "Mijia Cloud",
        "dlg.io.mi.com",
        "+.push.apple.com"
    ]
};

function buildDnsConfig() {
    // 根据 IPv6 状态过滤 DNS IP 列表
    let defaultNameserver = [];
    for (const dnsIp of DNS_IP_LIST) {
        if (!ipv6Enabled && String(dnsIp).includes(':')) {
            // IPv6 禁用时，跳过 IPv6 地址
            continue;
        }
        defaultNameserver.push(String(dnsIp));
    }

    const config = {
        "enable": true,
        "ipv6": ipv6Enabled,
        "enhanced-mode": "fake-ip",
        "default-nameserver": defaultNameserver,
        "nameserver": DNS_DOH_LIST,
        "fake-ip-filter": FAKE_IP_FILTER
    };

    return config;
}

const dnsConfig = buildDnsConfig();

const geoxURL = {
    "geoip": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip-lite.dat",
    "geosite": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geosite.dat",
    "mmdb": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/geoip.metadb",
    "asn": "https://github.com/MetaCubeX/meta-rules-dat/releases/download/latest/GeoLite2-ASN.mmdb"
};

// 地区元数据 - 只保留 yaml 文件中实际使用的5个国家
const countriesMeta = {
    "香港": {
        pattern: "(?i)香港|港|HK|hk|Hong Kong|HongKong|hongkong|🇭🇰",
        icon: "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Hong_Kong.png"
    },
    "台湾": {
        pattern: "(?i)台|新北|彰化|TW|Taiwan|🇹🇼",
        icon: "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Taiwan.png"
    },
    "新加坡": {
        pattern: "(?i)新加坡|坡|狮城|SG|Singapore|🇸🇬",
        icon: "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Singapore.png"
    },
    "日本": {
        pattern: "(?i)日本|川日|东京|大阪|泉日|埼玉|沪日|深日|JP|Japan|🇯🇵",
        icon: "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Japan.png"
    },
    "美国": {
        pattern: "(?i)美国|美|US|United States|🇺🇸",
        icon: "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/United_States.png"
    },
};

function parseCountries(config) {
    const proxies = config.proxies || [];
    const ispRegex = /家宽|家庭|家庭宽带|商宽|商业宽带|星链|Starlink|落地/i;   // 需要排除的关键字

    // 用来累计各国节点数
    const countryCounts = Object.create(null);

    // 构建地区正则表达式，去掉 (?i) 前缀
    const compiledRegex = {};
    for (const [country, meta] of Object.entries(countriesMeta)) {
        compiledRegex[country] = new RegExp(
            meta.pattern.replace(/^\\(\\?i\\)/, ''),
            'i'
        );
    }

    // 逐个节点进行匹配与统计
    for (const proxy of proxies) {
        const name = proxy.name || '';

        // 过滤掉不想统计的 ISP 节点
        if (ispRegex.test(name)) continue;

        // 找到第一个匹配到的地区就计数并终止本轮
        for (const [country, regex] of Object.entries(compiledRegex)) {
            if (regex.test(name)) {
                countryCounts[country] = (countryCounts[country] || 0) + 1;
                break;    // 避免一个节点同时累计到多个地区
            }
        }
    }

    // 将结果对象转成数组形式
    const result = [];
    for (const [country, count] of Object.entries(countryCounts)) {
        result.push({ country, count });
    }

    return result;   // [{ country: 'Japan', count: 12 }, ...]
}


function buildCountryProxyGroups({ countries }) {
    const groups = [];

    for (const country of countries) {
        const meta = countriesMeta[country];
        if (!meta) continue;

        const groupConfig = {
            "name": `${country}${NODE_SUFFIX}`,
            "icon": meta.icon,
            "include-all": true,
            "filter": meta.pattern,
            "type": "url-test",
            "url": "https://cp.cloudflare.com/generate_204",
            "interval": 60,
            "tolerance": 20,
            "lazy": false
        };

        groups.push(groupConfig);
    }

    return groups;
}

function buildProxyGroups({
    countries,
    countryProxyGroups,
    countryGroupNames,
    defaultProxies,
    defaultProxiesDirect,
    defaultSelector
}) {
    // 查看是否有特定地区的节点
    const hasTW = countries.includes("台湾");
    const hasUS = countries.includes("美国");

    return [
        {
            "name": PROXY_GROUPS.SELECT,
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Proxy.png",
            "type": "select",
            "proxies": defaultSelector
        },
        {
            "name": PROXY_GROUPS.MANUAL,
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Round_Robin_1.png",
            "include-all": true,
            "type": "select"
        },
        {
            "name": "AI",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/AI.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Telegram",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Telegram.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "YouTube",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/YouTube.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Netflix",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Netflix.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Spotify",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Spotify.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "TikTok",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/TikTok.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Steam",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Steam.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Game",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Game.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "E-Hentai",
            "icon": "https://cdn.jsdelivr.net/gh/PianCat/CustomProxyRuleset@main/Icons/Ehentai.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "PornSite",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Pornhub.png",
            "type": "select",
            "proxies": defaultProxies
        },
        (hasUS) ? {
            "name": "US Media",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/United_States.png",
            "type": "select",
            "proxies": ["美国节点", PROXY_GROUPS.SELECT, PROXY_GROUPS.MANUAL, PROXY_GROUPS.DIRECT]
        } : null,
        (hasTW) ? {
            "name": "Taiwan Media",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Taiwan.png",
            "type": "select",
            "proxies": ["台湾节点", PROXY_GROUPS.SELECT, PROXY_GROUPS.MANUAL, PROXY_GROUPS.DIRECT]
        } : null,
        (countries.includes("日本")) ? {
            "name": "Japan Media",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Japan.png",
            "type": "select",
            "proxies": ["日本节点", PROXY_GROUPS.SELECT, PROXY_GROUPS.MANUAL, PROXY_GROUPS.DIRECT]
        } : null,
        {
            "name": "Global Media",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/DomesticMedia.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Apple",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Apple.png",
            "type": "select",
            "proxies": buildList(
                PROXY_GROUPS.DIRECT,
                PROXY_GROUPS.SELECT,
                countryGroupNames,
                PROXY_GROUPS.MANUAL
            )
        },
        {
            "name": "Microsoft",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Microsoft.png",
            "type": "select",
            "proxies": buildList(
                PROXY_GROUPS.DIRECT,
                PROXY_GROUPS.SELECT,
                countryGroupNames,
                PROXY_GROUPS.MANUAL
            )
        },
        {
            "name": "Google",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Google_Search.png",
            "type": "select",
            "proxies": defaultProxies
        },
        {
            "name": "Google FCM",
            "icon": "https://cdn.jsdelivr.net/gh/PianCat/CustomProxyRuleset@main/Icons/Firebase.png",
            "type": "select",
            "proxies": ["Google", PROXY_GROUPS.DIRECT]
        },
        {
            "name": "Sogou Privacy",
            "icon": "https://cdn.jsdelivr.net/gh/PianCat/CustomProxyRuleset@main/Icons/Sougou.png",
            "type": "select",
            "proxies": [PROXY_GROUPS.DIRECT, "REJECT"]
        },
        {
            "name": "ADBlock",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/AdBlack.png",
            "type": "select",
            "proxies": ["REJECT-DROP", "REJECT", PROXY_GROUPS.DIRECT]
        },
        {
            "name": PROXY_GROUPS.DIRECT,
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Direct.png",
            "type": "select",
            "proxies": [
                "DIRECT", PROXY_GROUPS.SELECT
            ]
        },
        ...countryProxyGroups,
        // 其他节点 - 排除已定义的地区节点（与 yaml 文件一致，只排除主要5个国家）
        {
            "name": "其他节点",
            "icon": "https://testingcf.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png",
            "include-all": true,
            "type": "select",
            "exclude-filter": (() => {
                // 只排除 yaml 文件中定义的5个主要国家
                const mainCountries = ["香港", "台湾", "美国", "日本", "新加坡"];
                const excludePatterns = mainCountries
                    .filter(country => countriesMeta[country])
                    .map(country => countriesMeta[country].pattern.replace(/^\\(\\?i\\)/, ''))
                    .filter(Boolean);
                return excludePatterns.length > 0 
                    ? `(?i)${excludePatterns.join('|')}`
                    : undefined;
            })()
        }
    ].filter(Boolean); // 过滤掉 null 值
}

function main(config) {
    const resultConfig = { proxies: config.proxies };
    // 解析地区信息
    const countryInfo = parseCountries(resultConfig); // [{ country, count }]
    const countryGroupNames = getCountryGroupNames(countryInfo, countryThreshold);
    const countries = stripNodeSuffix(countryGroupNames);

    // 构建基础数组
    const {
        defaultProxies,
        defaultProxiesDirect,
        defaultSelector
    } = buildBaseLists({ countryGroupNames });

    // 为地区构建对应的 url-test 组
    const countryProxyGroups = buildCountryProxyGroups({ countries });

    // 生成代理组
    const proxyGroups = buildProxyGroups({
        countries,
        countryProxyGroups,
        countryGroupNames,
        defaultProxies,
        defaultProxiesDirect,
        defaultSelector
    });
    
    // GLOBAL 代理组 - 完整书写以确保兼容性（包含所有已创建的代理组）
    const globalProxies = proxyGroups.map(item => item.name);
    proxyGroups.push(
        {
            "name": "GLOBAL",
            "icon": "https://cdn.jsdelivr.net/gh/Koolson/Qure@master/IconSet/Color/Global.png",
            "include-all": true,
            "type": "select",
            "proxies": globalProxies
        }
    );

    const finalRules = buildRules();

    if (fullConfig) Object.assign(resultConfig, {
        "mixed-port": MIXED_PORT,
        "allow-lan": true,
        "ipv6": ipv6Enabled,
        "mode": "rule",
        "unified-delay": true,
        "tcp-concurrent": true,
        "find-process-mode": "strict",
        "global-client-fingerprint": "chrome",
        "log-level": "info",
        "geodata-loader": "standard",
        "external-controller": ":9999",
        "external-ui": "ui",
        "external-ui-url": "https://github.com/MetaCubeX/metacubexd/archive/refs/heads/gh-pages.zip",
        "disable-keep-alive": true,
        "profile": {
            "store-selected": true,
        }
    });

    Object.assign(resultConfig, {
        "proxy-groups": proxyGroups,
        "rule-providers": ruleProviders,
        "rules": finalRules,
        "sniffer": snifferConfig,
        "dns": dnsConfig,
        "geodata-mode": true,
        "geo-auto-update": true,
        "geo-update-interval": 24,
        "geox-url": geoxURL,
    });

    return resultConfig;
}
"""
    
    # 替换占位符（使用字符串替换而不是 format，因为模板中包含 { 字符）
    js_script = js_template
    js_script = js_script.replace('{param_section}', param_section)
    js_script = js_script.replace('{dns_ip_list}', dns_ip_list_js)
    js_script = js_script.replace('{dns_doh_list}', dns_doh_list_js)
    js_script = js_script.replace('{fake_ip_filter}', fake_ip_filter_js)
    js_script = js_script.replace('{mixed_port}', str(loader.mixed_port))
    js_script = js_script.replace('{rule_providers_code}', rule_providers_obj)
    js_script = js_script.replace('{rules_code}', rules_obj)
    
    return js_script


def generate_mihomo_js_script_args() -> str:
    """
    生成 Mihomo JS 转换脚本（args 版本，使用 $arguments）
    
    Returns:
        JS 脚本字符串
    """
    return generate_js_script_core(use_args=True)


def generate_mihomo_js_script_fixed(ipv6_enabled: bool, full_config: bool) -> str:
    """
    生成 Mihomo JS 转换脚本（固定参数版本）
    
    Args:
        ipv6_enabled: IPv6 是否启用
        full_config: 是否生成完整配置
    
    Returns:
        JS 脚本字符串
    """
    return generate_js_script_core(use_args=False, ipv6_enabled=ipv6_enabled, full_config=full_config)


def main():
    """Main function"""
    print("=== Generating Mihomo JS Conversion Script ===\n")
    
    output_dir = project_root / "Config" / "Mihomo"
    FileHelper.ensure_dir(output_dir)
    
    # Generate args version
    js_script_args = generate_mihomo_js_script_args()
    output_file_args = output_dir / "mihomo_convert_args.js"
    FileHelper.write_file(js_script_args, output_file_args)
    print(f"[OK] Generated: mihomo_convert_args.js ({len(js_script_args)} bytes)")
    
    # Generate 4 fixed parameter versions
    combinations = [
        {'ipv6': True, 'full': False, 'name': 'mihomo_convert_ipv6-1_full-0.js'},
        {'ipv6': True, 'full': True, 'name': 'mihomo_convert_ipv6-1_full-1.js'},
        {'ipv6': False, 'full': False, 'name': 'mihomo_convert_ipv6-0_full-0.js'},
        {'ipv6': False, 'full': True, 'name': 'mihomo_convert_ipv6-0_full-1.js'},
    ]
    
    for combo in combinations:
        js_script = generate_mihomo_js_script_fixed(combo['ipv6'], combo['full'])
        output_file = output_dir / combo['name']
        FileHelper.write_file(js_script, output_file)
        print(f"[OK] Generated: {combo['name']} ({len(js_script)} bytes)")
    
    print("\nGeneration completed!")


if __name__ == '__main__':
    main()
