# ProxyRules 配置生成器

ProxyRules 配置生成器是一个 Python 工具，用于自动生成多种代理工具的配置文件。

## 支持的代理工具

- ✅ **Mihomo** (Clash Meta) - 生成 YAML 覆写文件和 JS 动态脚本
- ✅ **Stash** - 生成 .yaml 覆写文件
- ✅ **Loon** - 生成 .conf 配置文件

## 功能特性

### 🎯 核心功能

- **规则加载器** - 自动解析 `Base/Rules/` 目录中的规则定义，支持动态 URL 生成
- **节点解析器** - 智能识别节点国家/地区（香港、台湾、美国、日本、新加坡、其他）
- **代理组生成器** - 根据节点自动生成基础代理组、地区节点组和分流策略组
- **多工具支持** - 一键生成多种代理工具的配置文件

### ⚙️ 配置选项

- **IPv6 支持** - 可选启用/禁用 IPv6
- **完整配置** - Mihomo 支持生成完整配置（适合纯内核启动）
- **Fake-IP 模式** - 默认启用 Fake-IP DNS 增强模式

## 安装和使用

### 前置要求

- Python 3.9+
- pip

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 使用方法

#### 1. 生成所有工具的配置文件

```bash
python Generator/config_generator.py --tool all
```

#### 2. 生成特定工具的配置

```bash
# 仅生成 Mihomo 配置
python Generator/config_generator.py --tool mihomo

# 生成多个工具的配置
python Generator/config_generator.py --tool mihomo stash
```

#### 3. 测试模式（使用模拟节点）

```bash
python Generator/config_generator.py --tool all --test
```

#### 4. 自定义输出目录

```bash
python Generator/config_generator.py --tool all --output /path/to/output
```

### 命令行参数

| 参数 | 说明 | 可选值 | 默认值 |
|------|------|--------|--------|
| `--tool` | 指定要生成的工具 | mihomo, stash, loon, all | all |
| `--test` | 使用测试节点生成配置 | - | - |
| `--output` | 自定义输出目录 | 目录路径 | Output/ |

## 输出目录结构

生成的配置文件将保存在 `Output/` 目录下：

```
Output/
├── Mihomo/
│   ├── config_ipv6-0_full-0.yaml    # 默认配置
│   ├── config_ipv6-0_full-1.yaml    # 完整配置
│   ├── config_ipv6-1_full-0.yaml    # IPv6 配置
│   ├── config_ipv6-1_full-1.yaml    # IPv6 完整配置
│   └── convert.js                    # JS 动态覆写脚本
├── Stash/
│   ├── config.yaml                   # 默认配置（IPv6启用）
│   └── config_no_ipv6.yaml           # 禁用IPv6配置
└── Loon/
    ├── config.conf                   # 默认配置（IPv6启用）
    └── config_no_ipv6.conf           # 禁用IPv6配置
```

## 项目结构

```
Generator/
├── config_generator.py       # 主入口文件
├── core/                     # 核心模块
│   ├── rule_loader.py        # 规则加载器
│   ├── node_parser.py        # 节点解析器
│   └── proxy_groups.py       # 代理组生成器
├── generators/               # 各工具生成器
│   ├── mihomo_generator.py
│   ├── stash_generator.py
│   └── loon_generator.py
└── utils/                    # 工具类
    ├── yaml_helper.py        # YAML 处理
    └── file_helper.py        # 文件操作
```

## GitHub Actions 自动化

项目配置了 GitHub Actions 工作流，会在以下情况自动生成配置文件：

1. 当 `Base/` 目录有变更并推送到 main 分支时
2. 手动触发工作流
3. 每周日凌晨 2 点（定时更新）

工作流文件位于：`.github/workflows/auto_generate.yml`

## 开发指南

### 测试单个生成器

每个生成器文件都包含测试代码，可以单独运行：

```bash
# 测试规则加载器
python Generator/core/rule_loader.py

# 测试节点解析器
python Generator/core/node_parser.py

# 测试代理组生成器
python Generator/core/proxy_groups.py

# 测试 Mihomo 生成器
python Generator/generators/mihomo_generator.py
```

### 添加新的规则

1. 在 `Base/Rules/RemoteRules.yaml` 中添加规则定义
2. 如果需要新的规则源，在 `Base/Rules/RemoteRulesLinkBase.yaml` 中添加 URL 模板
3. 重新运行生成器

### 自定义代理组

修改 `Generator/core/proxy_groups.py` 中的 `generate_policy_groups` 方法，添加或修改策略组。

## 常见问题

### Q: 如何修改 DNS 配置？

A: DNS 配置定义在各个生成器中（如 `mihomo_generator.py` 的 `_build_dns_config` 方法），修改后重新运行生成器。

### Q: 如何添加新的国家/地区节点识别？

A: 在 `Generator/core/node_parser.py` 的 `COUNTRIES_META` 字典中添加新的国家/地区定义。

### Q: 生成的配置文件在哪里？

A: 默认在项目根目录的 `Output/` 文件夹下，按工具分类存放。

## 依赖项

- **PyYAML** (>=6.0.1) - YAML 文件处理
- **Jinja2** (>=3.1.2) - 模板引擎（备用）

## 许可证

本项目遵循项目根目录的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request！

---

**ProxyRules 配置生成器** - 让代理配置管理更简单

