#!/usr/bin/env python3
"""
将 mihomo/Clash 的 .list / .txt 规则文件转换为 mihomo YAML 格式规则集。

mihomo 规则集格式：
- payload: 可以包含域名和 IP CIDR 的混合列表
- 不支持的规则类型会作为注释写入文件头部

示例输出：
# 不支持的规则 (3):
# - PROCESS-NAME: com.google.chrome
# - GEOIP: CN
# - DST-PORT: 443
payload:
  - '.google.com'
  - 'youtube.com'
  - '142.250.185.0/24'
"""

import sys
from pathlib import Path
from typing import Dict, List, Set

# 确保在 Windows GBK 控制台等非 UTF-8 环境下也能正常输出 ✓ / ✗ 等字符。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

# ==================== 配置区域 ====================

CONFIG = {
    # 多文件模式配置 - 可以指定多个文件
    "files": [
        # 格式: (输入文件, 输出文件)
        ("./rules/Bahamut.list", "./rules/mihomo/Bahamut.yaml"),
        ("./rules/Biliintl.list", "./rules/mihomo/Biliintl.yaml"),
        ("./rules/cf_preferred.list", "./rules/mihomo/cf_preferred.yaml"),
        ("./rules/connectivity_check.list", "./rules/mihomo/connectivity_check.yaml"),
        ("./rules/ForceDirect.list", "./rules/mihomo/ForceDirect.yaml"),
        ("./rules/ProxyDownload.list", "./rules/mihomo/ProxyDownload.yaml"),
        ("./rules/ProxyForum.list", "./rules/mihomo/ProxyForum.yaml"),
        ("./rules/ProxyHK.list", "./rules/mihomo/ProxyHK.yaml"),
        ("./rules/ProxyJP.list", "./rules/mihomo/ProxyJP.yaml"),
        ("./rules/ProxyMusic.list", "./rules/mihomo/ProxyMusic.yaml"),
        ("./rules/ProxyUS.list", "./rules/mihomo/ProxyUS.yaml"),
        ("./rules/DirectSupplements.list", "./rules/mihomo/DirectSupplements.yaml"),
        # lite 部分
        ("./rules/lite/AI.list", "./rules/mihomo/lite/AI.yaml"),
        ("./rules/lite/Amazon.list", "./rules/mihomo/lite/Amazon.yaml"),
        ("./rules/lite/Bilibili.list", "./rules/mihomo/lite/Bilibili.yaml"),
        ("./rules/lite/CDN.list", "./rules/mihomo/lite/CDN.yaml"),
        ("./rules/lite/Cloudflare.list", "./rules/mihomo/lite/Cloudflare.yaml"),
        ("./rules/lite/Discord.list", "./rules/mihomo/lite/Discord.yaml"),
        ("./rules/lite/Domestic.list", "./rules/mihomo/lite/Domestic.yaml"),
        ("./rules/lite/GitHub.list", "./rules/mihomo/lite/GitHub.yaml"),
        ("./rules/lite/Global.list", "./rules/mihomo/lite/Global.yaml"),
        ("./rules/lite/Google.list", "./rules/mihomo/lite/Google.yaml"),
        ("./rules/lite/Lan.list", "./rules/mihomo/lite/Lan.yaml"),
        ("./rules/lite/Meta.list", "./rules/mihomo/lite/Meta.yaml"),
        ("./rules/lite/Microsoft.list", "./rules/mihomo/lite/Microsoft.yaml"),
        ("./rules/lite/Reddit.list", "./rules/mihomo/lite/Reddit.yaml"),
        ("./rules/lite/reject.list", "./rules/mihomo/lite/reject.yaml"),
        ("./rules/lite/Streaming.list", "./rules/mihomo/lite/Streaming.yaml"),
        ("./rules/lite/Twitter.list", "./rules/mihomo/lite/Twitter.yaml"),
        ("./rules/lite/YouTube.list", "./rules/mihomo/lite/YouTube.yaml"),
    ],
    # 通用配置
    "quiet": True,  # True 则不显示跳过的规则警告
    # 运行模式:
    #   "files"  - 多文件模式（使用上面的 files 列表）
    #   "cli"    - 命令行模式
    "mode": "files",
}

# ==================== 配置区域结束 ====================

# mihomo payload 支持的规则类型（域名和 IP 可以混写）
SUPPORTED_TYPES = {
    "DOMAIN",
    "HOST",
    "DOMAIN-SUFFIX",
    "HOST-SUFFIX",
    "DOMAIN-KEYWORD",
    "HOST-KEYWORD",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "IP6-CIDR",
}

# 需要跳过的规则类型（不适合转换为规则集的类型）
SKIP_TYPES = {
    "GEOSITE",
    "GEOIP",
    "SRC-GEOIP",
    "IP-ASN",
    "SRC-IP-ASN",
    "PROCESS-NAME",
    "PROCESS-PATH",
    "NETWORK",
    "DST-PORT",
    "SRC-PORT",
    "SRC-IP-CIDR",
    "IN-PORT",
    "IN-TYPE",
    "IN-USER",
    "IN-NAME",
    "RULE-SET",
    "AND",
    "OR",
    "NOT",
    "SUB-RULE",
    "MATCH",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-PATH-REGEX",
    "PROCESS-NAME-REGEX",
    "UID",
    "DSCP",
}


def parse_list_file(file_path: str, quiet: bool = False) -> tuple[List[str], List[str]]:
    """解析 .list 文件，提取支持的规则值和不支持的规则（去重、保持顺序）。

    Args:
        file_path: 输入文件路径
        quiet: 是否静默模式

    Returns:
        (支持的规则列表, 不支持的规则列表)
    """
    rules: List[str] = []
    seen: Set[str] = set()
    unsupported: List[str] = []
    unsupported_seen: Set[str] = set()

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line or line.startswith("#") or line.startswith(";"):
                continue

            parts = line.split(",")
            if len(parts) < 2:
                if not quiet:
                    print(
                        f"警告: 第 {line_num} 行格式无效，跳过: {line}", file=sys.stderr
                    )
                continue

            type_name = parts[0].strip().upper()
            value = parts[1].strip().strip('"').strip("'")

            if not value:
                continue

            if type_name in SUPPORTED_TYPES:
                # 根据规则类型转换为 mihomo payload 格式
                payload_value = None

                if type_name in ["DOMAIN-SUFFIX", "HOST-SUFFIX"]:
                    # DOMAIN-SUFFIX 转为 +. 前缀（通配符匹配，可匹配域名及其所有子域名）
                    payload_value = f"+.{value}"
                elif type_name in ["DOMAIN", "HOST"]:
                    # DOMAIN 保持原样（精确匹配）
                    payload_value = value
                elif type_name in ["DOMAIN-KEYWORD", "HOST-KEYWORD"]:
                    # DOMAIN-KEYWORD 无法正确转换为 payload
                    # payload 不支持 keyword 匹配，会导致功能丢失
                    unsupported_line = f"{type_name}: {value} (keyword matching not supported in payload)"
                    if unsupported_line not in unsupported_seen:
                        unsupported.append(unsupported_line)
                        unsupported_seen.add(unsupported_line)
                elif type_name in ["DOMAIN-WILDCARD"]:
                    # DOMAIN-WILDCARD 保持原样（mihomo 支持通配符 *）
                    payload_value = value
                elif type_name in ["IP-CIDR", "IP-CIDR6", "IP6-CIDR"]:
                    # IP CIDR 保持原样（去除 no-resolve 等参数）
                    payload_value = value

                if payload_value and payload_value not in seen:
                    rules.append(payload_value)
                    seen.add(payload_value)
            elif type_name in SKIP_TYPES:
                # 记录不支持的规则
                unsupported_line = f"{type_name}: {value}"
                if unsupported_line not in unsupported_seen:
                    unsupported.append(unsupported_line)
                    unsupported_seen.add(unsupported_line)
            elif not quiet:
                print(
                    f"警告: 第 {line_num} 行不支持的规则类型 '{type_name}'，跳过",
                    file=sys.stderr,
                )

    return rules, unsupported


def convert_to_yaml(rules: List[str], unsupported: List[str]) -> str:
    """将规则列表转换为 mihomo YAML 格式。

    Args:
        rules: 规则值列表
        unsupported: 不支持的规则列表

    Returns:
        YAML 格式字符串
    """
    lines = []

    # 添加不支持规则的注释
    if unsupported:
        lines.append(f"# 不支持的规则 ({len(unsupported)}):")
        for rule in unsupported:
            lines.append(f"# - {rule}")
        lines.append("")

    if not rules:
        lines.append("payload: []")
    else:
        lines.append("payload:")
        for rule in rules:
            # mihomo YAML payload 格式：纯值，带引号
            lines.append(f"  - '{rule}'")

    return "\n".join(lines)


def convert_file(input_path: str, output_path: str = None, quiet: bool = False) -> str:
    """转换单个文件

    Args:
        input_path: 输入文件路径
        output_path: 输出文件路径（可选）
        quiet: 是否静默模式

    Returns:
        输出文件路径
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if output_path is None:
        output_path = input_file.with_suffix(".yaml")
    else:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    rules, unsupported = parse_list_file(input_path, quiet)
    yaml_content = convert_to_yaml(rules, unsupported)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
        f.write("\n")  # 文件末尾换行

    print(f"✓ {input_path} -> {output_path}")
    print(f"  规则数: {len(rules)}", end="")
    if unsupported:
        print(f" | 不支持: {len(unsupported)}")
    else:
        print()

    return str(output_path)


def convert_multiple_files(file_list: list, quiet: bool = False):
    """转换多个指定文件

    Args:
        file_list: [(输入路径, 输出路径), ...] 的列表
        quiet: 是否静默模式
    """
    if not file_list:
        print("没有配置要转换的文件")
        return

    print(f"准备转换 {len(file_list)} 个文件\n")

    success = 0
    failed = 0

    for item in file_list:
        # 支持两种格式: (input, output) 或单独的 input
        if isinstance(item, (list, tuple)):
            input_path = item[0]
            output_path = item[1] if len(item) > 1 else None
        else:
            input_path = item
            output_path = None

        try:
            convert_file(input_path, output_path, quiet)
            success += 1
            print()
        except Exception as e:
            print(f"✗ 转换失败: {input_path}")
            print(f"  错误: {e}\n")
            failed += 1

    print(f"{'=' * 50}")
    print(f"转换完成: 成功 {success} 个, 失败 {failed} 个")


def run_with_config():
    """使用脚本内配置运行"""
    mode = CONFIG["mode"]
    quiet = CONFIG["quiet"]

    if mode == "files":
        convert_multiple_files(CONFIG["files"], quiet)
    elif mode == "cli":
        run_cli()
    else:
        print(f"错误: 未知的运行模式 '{mode}'", file=sys.stderr)
        sys.exit(1)


def run_cli():
    """命令行模式"""
    import argparse

    parser = argparse.ArgumentParser(
        description="将 .list 规则文件转换为 mihomo YAML 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.list                       # 转换单个文件
  %(prog)s input.list -o output.yaml        # 指定输出文件名
  %(prog)s input.list -q                    # 静默模式
        """,
    )

    parser.add_argument("input", help="输入文件路径")
    parser.add_argument("-o", "--output", help="输出文件路径（可选）")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")

    args = parser.parse_args()

    try:
        convert_file(args.input, args.output, args.quiet)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_with_config()
