#!/usr/bin/env python3
"""
将 .list 规则文件转换为 sing-box JSON 格式
支持的规则类型：DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# ==================== 配置区域 ====================

CONFIG = {
    # 多文件模式配置 - 可以指定多个文件
    "files": [
        # 格式: (输入文件, 输出文件)
        # 输出文件可以为 None，会自动生成同名 .json 文件
        ("./rules/Bilibili.list", "./rules/sing-box/Bilibili.json"),
        ("./rules/lite/Bilibili.list", "./rules/sing-box/lite/Bilibili.json"),
        ("./rules/Biliintl.list", "./rules/sing-box/Biliintl.json"),
        ("./rules/CDNSupplements.list", "./rules/sing-box/CDNSupplements.json"),
        ("./rules/cf_preferred.list", "./rules/sing-box/cf_preferred.json"),
        ("./rules/ForceDirect.list", "./rules/sing-box/ForceDirect.json"),
        ("./rules/ProxyDownload.list", "./rules/sing-box/ProxyDownload.json"),
        ("./rules/ProxyForum.list", "./rules/sing-box/ProxyForum.json"),
        ("./rules/ProxyHK.list", "./rules/sing-box/ProxyHK.json"),
        ("./rules/ProxyJP.list", "./rules/sing-box/ProxyJP.json"),
        ("./rules/ProxyMusic.list", "./rules/sing-box/ProxyMusic.json"),
        ("./rules/ProxyUS.list", "./rules/sing-box/ProxyUS.json"),
        ("./rules/SupplementDirect.list", "./rules/sing-box/SupplementDirect.json"),
        ("./rules/mihomo/Google.list", "./rules/sing-box/Google.json"),
        ("./rules/mihomo/YouTube.list", "./rules/sing-box/YouTube.json"),
        ("./rules/lite/YouTube.list", "./rules/sing-box/lite/YouTube.json"),
        ("./rules/lite/Meta.list", "./rules/sing-box/lite/Meta.json"),
        ("./rules/lite/Reddit.list", "./rules/sing-box/lite/Reddit.json"),
        ("./rules/lite/Streaming.list", "./rules/sing-box/lite/Streaming.json"),
        ("./rules/lite/reject.list", "./rules/sing-box/lite/reject.json"),
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


def parse_list_file(file_path: str, quiet: bool = False) -> Dict[str, List[str]]:
    """解析 .list 文件，提取规则"""
    rules = {"domain": [], "domain_suffix": [], "domain_keyword": []}

    type_mapping = {
        "DOMAIN": "domain",
        "DOMAIN-SUFFIX": "domain_suffix",
        "DOMAIN-KEYWORD": "domain_keyword",
    }

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            parts = line.split(",")

            if len(parts) < 2:
                if not quiet:
                    print(
                        f"警告: 第 {line_num} 行格式无效，跳过: {line}", file=sys.stderr
                    )
                continue

            rule_type = parts[0].strip().upper()
            value = parts[1].strip()

            if rule_type in type_mapping:
                target_key = type_mapping[rule_type]
                if value not in rules[target_key]:
                    rules[target_key].append(value)
            elif not quiet:
                print(
                    f"警告: 第 {line_num} 行不支持的规则类型 '{rule_type}'，跳过",
                    file=sys.stderr,
                )

    return rules


def convert_to_json(rules: Dict[str, List[str]], version: int = 2) -> dict:
    """将解析后的规则转换为 JSON 格式"""
    rule_obj = {}

    if rules["domain"]:
        rule_obj["domain"] = rules["domain"]

    if rules["domain_suffix"]:
        rule_obj["domain_suffix"] = rules["domain_suffix"]

    if rules["domain_keyword"]:
        rule_obj["domain_keyword"] = rules["domain_keyword"]

    return {"version": version, "rules": [rule_obj] if rule_obj else []}


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

    total = sum(len(v) for v in rules.values())
    print(f"✓ {input_path} -> {output_path}")
    print(
        f"  DOMAIN: {len(rules['domain'])} | DOMAIN-SUFFIX: {len(rules['domain_suffix'])} | DOMAIN-KEYWORD: {len(rules['domain_keyword'])} | 总计: {total}"
    )

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
