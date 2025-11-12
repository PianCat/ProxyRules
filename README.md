# PianCat 的代理规则仓库

此处存放我为多个代理工具编写的覆写规则，本仓库实现如下：

*  集成 [SukkaW/Surge](https://github.com/SukkaW/Surge) 、 [Cats-Team/AdRules](https://github.com/Cats-Team/AdRules) 、 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script) 和 [dler-io/Rules](https://github.com/dler-io/Rules) 规则
*  包含多种分流策略
*  支持 Mihomo、Stash、Loon 等代理工具的覆写文件或配置文件自动生成


## 当前支持情况

| 工具 | 状态 | 说明 |
|------|------|------|
| Mihomo | ✅ 已支持 | `.yaml` 覆写文件 和 `.js` 覆写脚本 |
| Stash | ✅ 已支持 | `.yaml` 覆写文件 和 `.stoverride` 覆写文件 |
| Loon | ✅ 已支持 | `.lcf` 配置文件 |
| QuantumultX | ❌ 未支持 | 与其他代理工具配置差异较大，暂不支持 |
| Surge | 📋 计划中 | 尚未实现 |


## 快速开始

### Mihomo (Clash Meta)

**覆写文件 (.yaml)**
  - [config_ipv6-1_full-0.yaml](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/config_ipv6-1_full-0.yaml) - 启用 IPv6，基础配置 ⭐ 推荐
  - [config_ipv6-0_full-0.yaml](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/config_ipv6-0_full-0.yaml) - 禁用 IPv6，基础配置
  - [config_ipv6-0_full-1.yaml](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/config_ipv6-0_full-1.yaml) - 禁用 IPv6，完整配置
  - [config_ipv6-1_full-1.yaml](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/config_ipv6-1_full-1.yaml) - 启用 IPv6，完整配置

**覆写脚本 (.js)**
  - [mihomo_convert_ipv6-1_full-0.js](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/mihomo_convert_ipv6-1_full-0.js) - 启用 IPv6，基础配置 ⭐ 推荐
  - [mihomo_convert_ipv6-0_full-0.js](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/mihomo_convert_ipv6-0_full-0.js) - 禁用 IPv6，基础配置
  - [mihomo_convert_ipv6-0_full-1.js](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/mihomo_convert_ipv6-0_full-1.js) - 禁用 IPv6，完整配置
  - [mihomo_convert_ipv6-1_full-1.js](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/mihomo_convert_ipv6-1_full-1.js) - 启用 IPv6，完整配置


**Sparkle/Clash Party 使用方法**

推荐使用 [Sparkle](https://github.com/xishang0128/sparkle)

1. 打开覆写
2. 在上方地址栏中粘贴上方腹泻脚本的链接
3. 点击「导入」按钮，（可选）将导入后的文件更改名称为你认为合适的名称，并且开启全局
4. 为对应的配置文件添加该覆写（如果已开启全局则不需要）

**Sparkle/Clash Party 特别设置**

需要注意，Sparkle/Clash Party 在默认设置下还会接管 DNS 和 SNI（域名嗅探），需要手动在设置中关闭「控制 DNS 设置」和「控制域名嗅探」两个选项。

**SubStore 使用方法**

  -  [mihomo_convert_args.js](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/mihomo_convert_args.js) - SubStore 可导入参数脚本

可传入参数，传入多个参数时，用`&`分隔：
* `ipv6`：是否启用 IPv6，取值 `0`（禁用）或 `1`（启用），默认值 `1`
* `full`：是否使用完整配置，取值 `0`（基础配置）或 `1`（完整配置），默认值 `0`

用例：
```
https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Mihomo/mihomo_convert_args.js#ipv6=1&full=0
```

### Stash

**配置文件 (.yaml)**
  - [Stash_config_full.yaml](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Stash/Stash_config_full.yaml) - 启用 IPv6 版本 ⭐ 推荐
  - [Stash_config_full_no_ipv6.yaml](https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Stash/Stash_config_full_no_ipv6.yaml) - 禁用 IPv6 版本

**覆写文件 (.stoverride)**
- 点击以下链接直接导入到 Stash（推荐）：
  - [一键导入 Stash_override.stoverride](https://intradeus.github.io/http-protocol-redirector?r=stash://install-override?url=https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Stash/Stash_override.stoverride) - 启用 IPv6 版本 ⭐ 推荐
  - [一键导入 Stash_override_no_ipv6.stoverride](https://intradeus.github.io/http-protocol-redirector?r=stash://install-override?url=https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Stash/Stash_override_no_ipv6.stoverride) - 禁用 IPv6 版本

### Loon

**配置文件 (.lcf)**
- 点击以下链接直接导入到 Loon（推荐）：
  - [一键导入 config.lcf](https://intradeus.github.io/http-protocol-redirector?r=loon://import?sub=https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Loon/config.lcf) - 启用 IPv6 版本 ⭐ 推荐
  - [一键导入 config_no_ipv6.lcf](https://intradeus.github.io/http-protocol-redirector?r=loon://import?sub=https://raw.githubusercontent.com/PianCat/ProxyRules/main/Config/Loon/config_no_ipv6.lcf) - 禁用 IPv6 版本


## 分流策略

本仓库包含以下分流策略组：

```yaml
分流策略组:
  - AI                    # AI 服务
  - Telegram              # Telegram 即时通讯
  - YouTube               # YouTube 视频平台
  - Netflix               # Netflix 流媒体
  - TikTok                # TikTok 短视频
  - Spotify               # Spotify 音乐
  - Steam                 # Steam 游戏平台
  - Game                  # 游戏服务
  - E-Hentai              # E-Hentai 画廊
  - PornSite              # 成人网站
  - Stream_US             # 美国流媒体
  - Stream_TW             # 台湾流媒体
  - Stream_JP             # 日本流媒体
  - Stream_Global         # 全球流媒体
  - Apple                 # Apple 服务
  - Microsoft             # Microsoft 服务
  - Google                # Google 服务
  - GoogleFCM             # Google FCM 推送
  - SogouPrivacy          # 搜狗输入法隐私保护
  - ADBlock               # 广告拦截

节点组:
  - HongKong              # 香港节点
  - Taiwan                # 台湾节点
  - Singapore             # 新加坡节点
  - Unite State           # 美国节点
  - Japan                 # 日本节点
  - Others                # 其他地区节点
```

## 感谢

本仓库集成了以下优秀的规则源项目，感谢所有开发者的贡献：

### 规则源项目

- **[SukkaW/Surge](https://github.com/SukkaW/Surge)** - 提供 Telegram、流媒体、搜狗输入法等规则
- **[Cats-Team/AdRules](https://github.com/Cats-Team/AdRules)** - 提供广告拦截规则
- **[blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)** - 提供 YouTube、Netflix、TikTok、Spotify、Steam、游戏、Apple、Microsoft、Google 等服务规则
- **[dler-io/Rules](https://github.com/dler-io/Rules)** - 提供 AI 服务规则

### 工具与资源

- **[MetaCubeX/meta-rules-dat](https://github.com/MetaCubeX/meta-rules-dat)** - 提供 GeoIP 和 IPASN 数据库

---

**注意**：使用本仓库的配置文件前，请确保你已经配置好代理节点。配置文件中的策略组需要你手动指定对应的代理节点。