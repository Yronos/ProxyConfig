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
# 在这里直接配置源文件和输出路径

CONFIG = {
    # 单文件模式配置
    "single_file": {
        "input": "./rules/example.list",  # 源文件路径
        "output": "./output/example.json",  # 输出文件路径
    },
    # 批量模式配置
    "batch": {
        "input_dir": "./rules",  # 源文件目录
        "output_dir": "./rules/sing-box",  # 输出文件目录
        "pattern": "*.list",  # 文件匹配模式
    },
    # 通用配置
    "indent": 2,  # JSON 缩进空格数
    "quiet": False,  # 是否静默模式（不显示警告）
    # 运行模式: "single" 单文件模式, "batch" 批量模式, "cli" 命令行模式
    "mode": "batch",
}

# ==================== 配置区域结束 ====================


def parse_list_file(file_path: str, quiet: bool = False) -> Dict[str, List[str]]:
    """
    解析 .list 文件，提取规则
    """
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
                pass  # 静默跳过不支持的规则类型

    return rules


def convert_to_json(rules: Dict[str, List[str]], version: int = 2) -> dict:
    """
    将解析后的规则转换为 JSON 格式
    """
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
    """
    转换单个文件
    """
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if output_path is None:
        output_path = input_file.with_suffix(".json")
    else:
        # 确保输出目录存在
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

    rules = parse_list_file(input_path, quiet)
    json_data = convert_to_json(rules)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=indent, ensure_ascii=False)

    total = sum(len(v) for v in rules.values())
    print(f"转换完成: {input_path} -> {output_path}")
    print(f"  - DOMAIN: {len(rules['domain'])} 条")
    print(f"  - DOMAIN-SUFFIX: {len(rules['domain_suffix'])} 条")
    print(f"  - DOMAIN-KEYWORD: {len(rules['domain_keyword'])} 条")
    print(f"  - 总计: {total} 条")

    return str(output_path)


def batch_convert(
    input_dir: str,
    output_dir: str = None,
    pattern: str = "*.list",
    indent: int = 2,
    quiet: bool = False,
):
    """
    批量转换目录下的所有 .list 文件
    """
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path

    if not input_path.is_dir():
        raise NotADirectoryError(f"输入路径不是目录: {input_dir}")

    output_path.mkdir(parents=True, exist_ok=True)

    files = list(input_path.glob(pattern))

    if not files:
        print(f"在 {input_dir} 中没有找到匹配 '{pattern}' 的文件")
        return

    print(f"找到 {len(files)} 个文件待转换\n")

    for file in files:
        output_file = output_path / file.with_suffix(".json").name
        try:
            convert_file(str(file), str(output_file), indent, quiet)
            print()
        except Exception as e:
            print(f"转换 {file} 失败: {e}\n", file=sys.stderr)


def run_with_config():
    """
    使用脚本内配置运行
    """
    mode = CONFIG["mode"]
    indent = CONFIG["indent"]
    quiet = CONFIG["quiet"]

    if mode == "single":
        # 单文件模式
        cfg = CONFIG["single_file"]
        convert_file(cfg["input"], cfg["output"], indent, quiet)

    elif mode == "batch":
        # 批量模式
        cfg = CONFIG["batch"]
        batch_convert(
            cfg["input_dir"], cfg["output_dir"], cfg["pattern"], indent, quiet
        )

    elif mode == "cli":
        # 命令行模式
        run_cli()
    else:
        print(f"错误: 未知的运行模式 '{mode}'", file=sys.stderr)
        sys.exit(1)


def run_cli():
    """
    命令行模式
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="将 .list 规则文件转换为 sing-box JSON 格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.list                    # 转换单个文件
  %(prog)s input.list -o output.json     # 指定输出文件名
  %(prog)s -d ./rules                    # 批量转换目录下所有 .list 文件
  %(prog)s -d ./rules -o ./output        # 批量转换并输出到指定目录
        """,
    )

    parser.add_argument("input", nargs="?", help="输入文件路径")
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
            convert_file(args.input, args.output, args.indent, args.quiet)
        else:
            parser.print_help()
            sys.exit(1)
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    run_with_config()
