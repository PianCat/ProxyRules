/*
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

// ============================================
// 参数定义区域（可根据需要修改）
// ============================================
const ipv6Enabled = false;
const fullConfig = false;
const countryThreshold = 0;
// ============================================
// 参数定义区域结束
// ============================================

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
const DNS_IP_LIST = [
  "119.29.29.29",
  "2402:4e00::",
  "223.5.5.5",
  "2400:3200::1",
  "1.1.1.1",
  "2606:4700:4700::1111",
  "8.8.8.8",
  "2001:4860:4860::8888"
];
const DNS_DOH_LIST = [
  "https://doh.pub/dns-query",
  "https://dns.alidns.com/dns-query",
  "https://cloudflare-dns.com/dns-query",
  "https://dns.google/dns-query"
];
const FAKE_IP_FILTER = [
  "*.lan",
  "*.localdomain",
  "*.example",
  "*.invalid",
  "*.localhost",
  "*.test",
  "*.local",
  "*.home.arpa",
  "time.*.com",
  "time.*.gov",
  "time.*.edu.cn",
  "time.*.apple.com",
  "time1.*.com",
  "time2.*.com",
  "time3.*.com",
  "time4.*.com",
  "time5.*.com",
  "time6.*.com",
  "time7.*.com",
  "ntp.*.com",
  "ntp1.*.com",
  "ntp2.*.com",
  "ntp3.*.com",
  "ntp4.*.com",
  "ntp5.*.com",
  "ntp6.*.com",
  "ntp7.*.com",
  "*.time.edu.cn",
  "*.ntp.org.cn",
  "+.pool.ntp.org",
  "time1.cloud.tencent.com",
  "music.163.com",
  "*.music.163.com",
  "*.126.net",
  "musicapi.taihe.com",
  "music.taihe.com",
  "songsearch.kugou.com",
  "trackercdn.kugou.com",
  "*.kuwo.cn",
  "api-jooxtt.sanook.com",
  "api.joox.com",
  "joox.com",
  "y.qq.com",
  "*.y.qq.com",
  "streamoc.music.tc.qq.com",
  "mobileoc.music.tc.qq.com",
  "isure.stream.qqmusic.qq.com",
  "dl.stream.qqmusic.qq.com",
  "aqqmusic.tc.qq.com",
  "amobile.music.tc.qq.com",
  "*.xiami.com",
  "*.music.migu.cn",
  "music.migu.cn",
  "*.msftconnecttest.com",
  "*.msftncsi.com",
  "msftconnecttest.com",
  "msftncsi.com",
  "localhost.ptlogin2.qq.com",
  "localhost.sec.qq.com",
  "+.srv.nintendo.net",
  "+.stun.playstation.net",
  "xbox.*.microsoft.com",
  "+.battlenet.com.cn",
  "+.wotgame.cn",
  "+.wggames.cn",
  "+.wowsgame.cn",
  "+.wargaming.net",
  "proxy.golang.org",
  "stun.*.*",
  "stun.*.*.*",
  "stun.*.*.*.*",
  "heartbeat.belkin.com",
  "*.linksys.com",
  "*.linksyssmartwifi.com",
  "*.router.asus.com",
  "mesu.apple.com",
  "swscan.apple.com",
  "swquery.apple.com",
  "swdownload.apple.com",
  "swcdn.apple.com",
  "swdist.apple.com",
  "lens.l.google.com",
  "stun.l.google.com",
  "+.nflxvideo.net",
  "*.square-enix.com",
  "*.finalfantasyxiv.com",
  "*.ffxiv.com",
  "*.direct",
  "cable.auth.com",
  "network-test.debian.org",
  "detectportal.firefox.com",
  "resolver1.opendns.com",
  "*.xboxlive.com",
  "global.turn.twilio.com",
  "global.stun.twilio.com",
  "app.yinxiang.com",
  "injections.adguard.org",
  "local.adguard.org",
  "localhost.*.qq.com",
  "localhost.*.weixin.qq.com",
  "*.logon.battle.net",
  "*.blzstatic.cn",
  "*.mcdn.bilivideo.cn",
  "*.cmpassport.com",
  "id6.me",
  "open.e.189.cn",
  "opencloud.wostore.cn",
  "id.mail.wo.cn",
  "mdn.open.wo.cn",
  "hmrz.wo.cn",
  "nishub1.10010.com",
  "enrichgw.10010.com",
  "*.wosms.cn",
  "*.jegotrip.com.cn",
  "*.icitymobile.mobi",
  "*.pingan.com.cn",
  "*.cmbchina.com",
  "*.10099.com.cn",
  "*.microdone.cn"
];
const MIXED_PORT = 56365;

const ruleProviders = {
  "AI": {
    "type": "http",
    "behavior": "classical",
    "format": "yaml",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/dler-io/Rules/main/Clash/Provider/AI Suite.yaml",
    "path": "./ruleset/AI.yaml"
  },
  "Telegram": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/telegram.txt",
    "path": "./ruleset/Telegram.list"
  },
  "Video": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/YouTube/YouTube.list",
    "path": "./ruleset/YouTube.list"
  },
  "Music": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/YouTubeMusic/YouTubeMusic.list",
    "path": "./ruleset/YouTubeMusic.list"
  },
  "Netflix": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Netflix/Netflix.list",
    "path": "./ruleset/Netflix.list"
  },
  "TikTok": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/TikTok/TikTok.list",
    "path": "./ruleset/TikTok.list"
  },
  "Spotify": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Spotify/Spotify.list",
    "path": "./ruleset/Spotify.list"
  },
  "Steam": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Steam/Steam.list",
    "path": "./ruleset/Steam.list"
  },
  "Game": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Game/Game.list",
    "path": "./ruleset/Game.list"
  },
  "E-Hentai": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/EHGallery/EHGallery.list",
    "path": "./ruleset/E-Hentai.list"
  },
  "Main": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/PianCat/CustomProxyRuleset/main/PornSite/PornSite.list",
    "path": "./ruleset/PornSite.list"
  },
  "Furrybar": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/PianCat/CustomProxyRuleset/main/Furrybar/Furrybar.list",
    "path": "./ruleset/Furrybar.list"
  },
  "Stream_US": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/stream_us.txt",
    "path": "./ruleset/Stream_US.list"
  },
  "Stream_TW": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/stream_tw.txt",
    "path": "./ruleset/Stream_TW.list"
  },
  "Stream_JP": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/stream_jp.txt",
    "path": "./ruleset/Stream_JP.list"
  },
  "Stream_Global": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/stream.txt",
    "path": "./ruleset/Stream_Global.list"
  },
  "Apple": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Apple/Apple.list",
    "path": "./ruleset/Apple.list"
  },
  "Microsoft": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Microsoft/Microsoft.list",
    "path": "./ruleset/Microsoft.list"
  },
  "Google": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/Google/Google.list",
    "path": "./ruleset/Google.list"
  },
  "GoogleFCM": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/master/rule/Clash/GoogleFCM/GoogleFCM.list",
    "path": "./ruleset/GoogleFCM.list"
  },
  "SogouPrivacy": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/sogouinput.txt",
    "path": "./ruleset/SogouInput.list"
  },
  "ADBlock": {
    "type": "http",
    "behavior": "domain",
    "format": "mrs",
    "interval": 86400,
    "url": "https://adrules.top/adrules-mihomo.mrs",
    "path": "./ruleset/ADBlock.mrs"
  },
  "LocalNetwork_Non-IP": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/non_ip/lan.txt",
    "path": "./ruleset/LocalNetwork_Non-IP.list"
  },
  "LocalNetwork_IP": {
    "type": "http",
    "behavior": "classical",
    "format": "text",
    "interval": 86400,
    "url": "https://ruleset.skk.moe/Clash/ip/lan.txt",
    "path": "./ruleset/LocalNetwork_IP.list"
  }
};


const baseRules = [
  "RULE-SET,AI,AI",
  "RULE-SET,Telegram,Telegram",
  "RULE-SET,Netflix,Netflix",
  "RULE-SET,TikTok,TikTok",
  "RULE-SET,Spotify,Spotify",
  "RULE-SET,Steam,Steam",
  "RULE-SET,Game,Game",
  "RULE-SET,E-Hentai,E-Hentai",
  "RULE-SET,Furrybar,PornSite",
  "RULE-SET,Stream_US,US Media",
  "RULE-SET,Stream_TW,Taiwan Media",
  "RULE-SET,Stream_JP,Japan Media",
  "RULE-SET,Stream_Global,Global Media",
  "RULE-SET,Apple,Apple",
  "RULE-SET,Microsoft,Microsoft",
  "RULE-SET,Google,Google",
  "RULE-SET,GoogleFCM,Google FCM",
  "RULE-SET,SogouPrivacy,Sogou Privacy",
  "RULE-SET,ADBlock,ADBlock",
  "RULE-SET,LocalNetwork_Non-IP,直接连接",
  "RULE-SET,LocalNetwork_IP,直接连接",
  "GEOIP,CN,直接连接",
  "MATCH,选择代理"
];


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
            meta.pattern.replace(/^\(\?i\)/, ''),
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
                    .map(country => countriesMeta[country].pattern.replace(/^\(\?i\)/, ''))
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
