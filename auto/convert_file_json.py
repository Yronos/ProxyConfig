#!/usr/bin/env python3
"""
将 mihomo/Clash 的 .list / .txt 规则文件转换为 sing-box 规则集 JSON 格式。

设计要点
========
1. 字段一一对应：将 mihomo 规则类型映射到语义相同的 sing-box headless-rule 字段
   （见 TYPE_MAPPING）。mihomo 有而 sing-box 没有、或 sing-box 有而 mihomo 没有的
   字段暂不处理（见 SKIP_TYPES）。

2. OR / AND 语义：sing-box 单个规则对象内的匹配逻辑为
       (domain || domain_suffix || domain_keyword || domain_regex || ip_cidr) && (其它字段)
   即域名/IP 组内部是“或”，与其它字段之间是“与”。而一个扁平的 list 文件里每一行都应当
   是相互独立的“或”关系。因此：
     - 域名/IP 组字段全部放进同一个规则对象（它们天然 OR）；
     - 其余每种字段各自独立成一个规则对象（顶层多个规则对象之间为 OR）。
   这样 `PROCESS-NAME` 之类的字段不会被错误地与域名做“与”运算。

3. 版本自动选择：根据实际用到的字段，自动挑选能支持这些字段的最小规则集版本。
       version 1 (sing-box 1.8.0)  : 初始版本
       version 2 (sing-box 1.10.0) : 优化 domain_suffix 的二进制内存占用
       version 3 (sing-box 1.11.0) : network_type / network_is_expensive / network_is_constrained
       version 4 (sing-box 1.13.0) : network_interface_address / default_interface_address
       version 5 (sing-box 1.14.0) : package_name_regex
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

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
        # 输出文件可以为 None，会自动生成同名 .json 文件
        ("./rules/Bahamut.list", "./rules/sing-box/Bahamut.json"),
        ("./rules/Biliintl.list", "./rules/sing-box/Biliintl.json"),
        ("./rules/cf_preferred.list", "./rules/sing-box/cf_preferred.json"),
        ("./rules/ForceDirect.list", "./rules/sing-box/ForceDirect.json"),
        ("./rules/ProxyDownload.list", "./rules/sing-box/ProxyDownload.json"),
        ("./rules/ProxyForum.list", "./rules/sing-box/ProxyForum.json"),
        ("./rules/ProxyHK.list", "./rules/sing-box/ProxyHK.json"),
        ("./rules/ProxyJP.list", "./rules/sing-box/ProxyJP.json"),
        ("./rules/ProxyMusic.list", "./rules/sing-box/ProxyMusic.json"),
        ("./rules/ProxyUS.list", "./rules/sing-box/ProxyUS.json"),
        ("./rules/DirectSupplements.list", "./rules/sing-box/DirectSupplements.json"),
        ("./rules/mihomo/Google.list", "./rules/sing-box/Google.json"),
        ("./rules/mihomo/YouTube.list", "./rules/sing-box/YouTube.json"),
        # lite 部分
        ("./rules/lite/Amazon.list", "./rules/sing-box/lite/Amazon.json"),
        ("./rules/lite/Bilibili.list", "./rules/sing-box/lite/Bilibili.json"),
        ("./rules/lite/CDN.list", "./rules/sing-box/lite/CDN.json"),
        ("./rules/lite/Cloudflare.list", "./rules/sing-box/lite/Cloudflare.json"),
        ("./rules/lite/Discord.list", "./rules/sing-box/lite/Discord.json"),
        ("./rules/lite/Domestic.list", "./rules/sing-box/lite/Domestic.json"),
        ("./rules/lite/GitHub.list", "./rules/sing-box/lite/GitHub.json"),
        ("./rules/lite/Global.list", "./rules/sing-box/lite/Global.json"),
        ("./rules/lite/Google.list", "./rules/sing-box/lite/Google.json"),
        ("./rules/lite/Lan.list", "./rules/sing-box/lite/Lan.json"),
        ("./rules/lite/Meta.list", "./rules/sing-box/lite/Meta.json"),
        ("./rules/lite/Reddit.list", "./rules/sing-box/lite/Reddit.json"),
        ("./rules/lite/reject.list", "./rules/sing-box/lite/reject.json"),
        ("./rules/lite/Streaming.list", "./rules/sing-box/lite/Streaming.json"),
        ("./rules/lite/Twitter.list", "./rules/sing-box/lite/Twitter.json"),
        ("./rules/lite/YouTube.list", "./rules/sing-box/lite/YouTube.json"),
    ],
    # 批量模式配置（可选）
    "batch": {
        "input_dir": "./rules",
        "output_dir": "./output",
        "pattern": "*.list",
    },
    # 通用配置
    "indent": 2,
    "quiet": True,  # True 则不显示跳过的规则警告
    # 运行模式:
    #   "files"  - 多文件模式（使用上面的 files 列表）
    #   "batch"  - 批量模式（转换目录下所有匹配文件）
    #   "cli"    - 命令行模式
    "mode": "files",
}

# ==================== 配置区域结束 ====================

# mihomo / Clash 规则类型  ->  sing-box headless-rule 字段。
# 仅包含两边语义相同的字段；没有对应关系的类型放进 SKIP_TYPES。
TYPE_MAPPING = {
    # 域名类
    "DOMAIN": "domain",
    "HOST": "domain",  # Surge/QuantumultX 的 HOST 等价于精确域名匹配
    "DOMAIN-SUFFIX": "domain_suffix",
    "HOST-SUFFIX": "domain_suffix",
    "DOMAIN-KEYWORD": "domain_keyword",
    "HOST-KEYWORD": "domain_keyword",
    "DOMAIN-REGEX": "domain_regex",
    # IP 类（sing-box 用 ip_cidr 同时承载 IPv4 / IPv6）
    "IP-CIDR": "ip_cidr",
    "IP-CIDR6": "ip_cidr",
    "IP6-CIDR": "ip_cidr",
    "SRC-IP-CIDR": "source_ip_cidr",
    # 端口类
    "DST-PORT": "port",
    "SRC-PORT": "source_port",
    # 网络
    "NETWORK": "network",
    # 进程类
    "PROCESS-NAME": "process_name",
    "PROCESS-PATH": "process_path",
    "PROCESS-PATH-REGEX": "process_path_regex",
}

# 已知但 sing-box 无对应字段（或属于逻辑/嵌套规则）的 mihomo 类型：静默跳过，不产生警告。
SKIP_TYPES = {
    "DOMAIN-WILDCARD",
    "GEOSITE",
    "IP-SUFFIX",
    "IP-ASN",
    "SRC-IP-SUFFIX",
    "SRC-IP-ASN",
    "GEOIP",
    "SRC-GEOIP",
    "IN-PORT",
    "IN-TYPE",
    "IN-USER",
    "IN-NAME",
    "PROCESS-PATH-WILDCARD",
    "PROCESS-NAME-WILDCARD",
    "PROCESS-NAME-REGEX",
    "UID",
    "DSCP",
    "RULE-SET",
    "AND",
    "OR",
    "NOT",
    "SUB-RULE",
    "MATCH",
    # 非 mihomo 但出现在部分规则集中的 Surge/QuantumultX 类型
    "USER-AGENT",
    "URL-REGEX",
}

# 域名/IP 组：sing-box 单规则对象内这些字段相互“或”。它们合并进同一个规则对象。
OR_GROUP_FIELDS = ["domain", "domain_suffix", "domain_keyword", "domain_regex", "ip_cidr"]

# 其余字段：在单个规则对象内会与域名组“与”运算，因此各自独立成规则对象以保持顶层“或”语义。
STANDALONE_FIELDS = [
    "source_ip_cidr",
    "network",
    "port",
    "source_port",
    "process_name",
    "process_path",
    "process_path_regex",
]

ALL_FIELDS = OR_GROUP_FIELDS + STANDALONE_FIELDS

# 需要转换为整数的字段
INT_FIELDS = {"port", "source_port"}

# 字段所需的最小规则集版本（未列出的字段默认为 1）。
FIELD_MIN_VERSION = {
    # version 2：domain_suffix 在二进制规则集中有专门的内存优化，使用 v2 更合适
    "domain_suffix": 2,
    # version 2：process_path_regex (sing-box 1.10.0)
    "process_path_regex": 2,
    # 以下字段当前不会由本脚本产生，仅作完整性记录
    "network_type": 3,
    "network_is_expensive": 3,
    "network_is_constrained": 3,
    "network_interface_address": 4,
    "default_interface_address": 4,
    "package_name_regex": 5,
}


def parse_list_file(file_path: str, quiet: bool = False) -> Dict[str, List]:
    """解析 .list 文件，按 sing-box 字段名归类规则值（保持顺序、去重）。"""
    rules: Dict[str, List] = {field: [] for field in ALL_FIELDS}

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

            rule_type = parts[0].strip().upper()
            value = parts[1].strip().strip('"').strip("'")

            if not value:
                continue

            if rule_type in TYPE_MAPPING:
                field = TYPE_MAPPING[rule_type]

                if field in INT_FIELDS:
                    try:
                        value = int(value)
                    except ValueError:
                        if not quiet:
                            print(
                                f"警告: 第 {line_num} 行端口值无效，跳过: {line}",
                                file=sys.stderr,
                            )
                        continue
                elif field == "network":
                    value = value.lower()

                if value not in rules[field]:
                    rules[field].append(value)
            elif rule_type in SKIP_TYPES:
                # 已知无对应字段，按要求暂不处理
                continue
            elif not quiet:
                print(
                    f"警告: 第 {line_num} 行不支持的规则类型 '{rule_type}'，跳过",
                    file=sys.stderr,
                )

    return rules


def select_version(used_fields: List[str]) -> int:
    """根据使用到的字段自动选择最小可用的规则集版本。"""
    return max((FIELD_MIN_VERSION.get(f, 1) for f in used_fields), default=1)


def convert_to_json(rules: Dict[str, List]) -> dict:
    """将解析后的规则转换为 sing-box 规则集 JSON。

    - 域名/IP 组字段合并进一个规则对象（组内 OR）。
    - 其余每种字段独立成规则对象（顶层多个对象之间 OR），避免与域名组发生 AND。
    """
    rule_objects: List[dict] = []
    used_fields: List[str] = []

    # 1) 域名/IP 组：合并为单个规则对象
    or_group_obj = {}
    for field in OR_GROUP_FIELDS:
        if rules.get(field):
            or_group_obj[field] = rules[field]
            used_fields.append(field)
    if or_group_obj:
        rule_objects.append(or_group_obj)

    # 2) 其余字段：每种独立成对象
    for field in STANDALONE_FIELDS:
        if rules.get(field):
            rule_objects.append({field: rules[field]})
            used_fields.append(field)

    version = select_version(used_fields)
    return {"version": version, "rules": rule_objects}


def convert_file(
    input_path: str, output_path: str = None, indent: int = 2, quiet: bool = False
) -> str:
    """转换单个文件"""
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if output_path is None:
        output_path = input_file.with_suffix(".json")
    else:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    rules = parse_list_file(input_path, quiet)
    json_data = convert_to_json(rules)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=indent, ensure_ascii=False)

    # 统计信息
    counts = {field: len(values) for field, values in rules.items() if values}
    total = sum(counts.values())
    detail = " | ".join(f"{field}: {n}" for field, n in counts.items())

    print(f"✓ {input_path} -> {output_path}  [version {json_data['version']}]")
    print(f"  {detail if detail else '(空规则集)'} | 总计: {total}")

    return str(output_path)


def convert_multiple_files(file_list: list, indent: int = 2, quiet: bool = False):
    """
    转换多个指定文件

    Args:
        file_list: [(输入路径, 输出路径), ...] 的列表
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
            convert_file(input_path, output_path, indent, quiet)
            success += 1
            print()
        except Exception as e:
            print(f"✗ 转换失败: {input_path}")
            print(f"  错误: {e}\n")
            failed += 1

    print(f"{'=' * 50}")
    print(f"转换完成: 成功 {success} 个, 失败 {failed} 个")


def batch_convert(
    input_dir: str,
    output_dir: str = None,
    pattern: str = "*.list",
    indent: int = 2,
    quiet: bool = False,
):
    """批量转换目录下的所有匹配文件"""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path

    if not input_path.is_dir():
        raise NotADirectoryError(f"输入路径不是目录: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    files = list(input_path.glob(pattern))

    if not files:
        print(f"在 {input_dir} 中没有找到匹配 '{pattern}' 的文件")
        return

    file_list = [
        (str(f), str(output_path / f.with_suffix(".json").name)) for f in files
    ]
    convert_multiple_files(file_list, indent, quiet)


def run_with_config():
    """使用脚本内配置运行"""
    mode = CONFIG["mode"]
    indent = CONFIG["indent"]
    quiet = CONFIG["quiet"]

    if mode == "files":
        convert_multiple_files(CONFIG["files"], indent, quiet)

    elif mode == "batch":
        cfg = CONFIG["batch"]
        batch_convert(
            cfg["input_dir"], cfg["output_dir"], cfg["pattern"], indent, quiet
        )

    elif mode == "cli":
        run_cli()
    else:
        print(f"错误: 未知的运行模式 '{mode}'", file=sys.stderr)
        sys.exit(1)


def run_cli():
    """命令行模式"""
    import argparse

    parser = argparse.ArgumentParser(
        description="将 .list 规则文件转换为 sing-box JSON 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.list                       # 转换单个文件
  %(prog)s a.list b.list c.list             # 转换多个文件
  %(prog)s input.list -o output.json        # 指定输出文件名
  %(prog)s -d ./rules                       # 批量转换目录
  %(prog)s -d ./rules -o ./output           # 批量转换并输出到指定目录
        """,
    )

    parser.add_argument("input", nargs="*", help="输入文件路径（可多个）")
    parser.add_argument("-o", "--output", help="输出文件/目录路径")
    parser.add_argument("-d", "--directory", help="批量转换目录")
    parser.add_argument(
        "--indent", type=int, default=2, help="JSON 缩进空格数 (默认: 2)"
    )
    parser.add_argument(
        "--pattern", default="*.list", help="文件匹配模式 (默认: *.list)"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")

    args = parser.parse_args()

    try:
        if args.directory:
            batch_convert(
                args.directory, args.output, args.pattern, args.indent, args.quiet
            )
        elif args.input:
            if len(args.input) == 1 and args.output:
                # 单文件指定输出
                convert_file(args.input[0], args.output, args.indent, args.quiet)
            else:
                # 多文件模式
                file_list = [(f, None) for f in args.input]
                convert_multiple_files(file_list, args.indent, args.quiet)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_with_config()
