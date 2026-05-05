#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filter_amazon.py
从源规则文件中过滤/添加规则，生成精简版规则文件
支持本地文件和远程 URL

【更新特性】
- 支持精准匹配删除（RULES_TO_REMOVE_EXACT）
- 支持包含匹配删除（RULES_TO_REMOVE_CONTAINS）
"""

import os
import re
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ============================================================
# 用户配置区域
# ============================================================

# 输出文件名（不含路径，自动放到 ./rules/lite/ 下）
OUTPUT_FILENAME = "Amazon.list"

# 源文件路径（支持本地路径或 HTTP/HTTPS URL）
SOURCE_FILE = "./rules/non_ip/Amazon.list"

# 输出目录
OUTPUT_DIR = "./rules/lite"

# 网络请求配置
REQUEST_TIMEOUT = 30  # 超时时间（秒）
REQUEST_RETRIES = 3  # 重试次数

# ---------- 删除规则列表 ----------
# 1. 精准匹配删除（必须完全相同，优先级最高）
RULES_TO_REMOVE_EXACT = [
    # 示例：只删除完全相同的这一条
    # "DOMAIN,example.com",
    "USER-AGENT,InstantVideo.US*",
    "USER-AGENT,Prime%20Video*",
    "PROCESS-NAME,com.amazon.avod.thirdpartyclient",
]

# 2. 包含匹配删除（规则中只要包含任意一个关键词就删除，适合批量清理）
#    注意：越具体越好，避免误删
RULES_TO_REMOVE_CONTAINS = [
    # "amazon",  # 删除所有包含 amazon 的规则
    # "amazonaws",  # 删除 AWS 相关
    # "cloudfront",
    # ".com",           # 非常危险，谨慎使用
    ".cn"
]

# ---------- 添加规则列表 ----------
RULES_TO_ADD = [
    # "DOMAIN,example.com",
    # "DOMAIN-SUFFIX,amazon.com",
]

# ============================================================
# 支持的规则类型（用于校验/解析）
# ============================================================
VALID_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "GEOIP",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-NAME",
}


# ============================================================
# 核心逻辑
# ============================================================


def is_url(path: str) -> bool:
    """判断是否为 URL"""
    return path.startswith(("http://", "https://"))


def fetch_remote_content(
    url: str, timeout: int = REQUEST_TIMEOUT, retries: int = REQUEST_RETRIES
) -> str:
    """下载远程文件内容"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    }

    last_error = None
    for attempt in range(retries):
        try:
            print(f"[*] 正在下载远程文件 (尝试 {attempt + 1}/{retries})...")
            request = Request(url, headers=headers)
            with urlopen(request, timeout=timeout) as response:
                content = response.read().decode("utf-8")
                print(f"[✓] 下载成功，大小: {len(content)} 字节")
                return content
        except HTTPError as e:
            last_error = f"HTTP 错误 {e.code}: {e.reason}"
            print(f"[!] {last_error}")
            if e.code == 404:
                break
        except URLError as e:
            last_error = f"网络错误: {e.reason}"
            print(f"[!] {last_error}")
        except Exception as e:
            last_error = f"未知错误: {str(e)}"
            print(f"[!] {last_error}")

        if attempt < retries - 1:
            print(f"[*] 等待 2 秒后重试...")
            import time

            time.sleep(2)

    raise Exception(f"下载失败: {last_error}")


def normalize_rule(line: str) -> str:
    """去除注释、首尾空白，统一大写类型前缀"""
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    # 去除行内注释
    line = re.sub(r"\s*#.*$", "", line).strip()
    # 统一规则类型为大写
    parts = line.split(",")
    if parts and parts[0].upper() in VALID_RULE_TYPES:
        parts[0] = parts[0].upper()
    return ",".join(parts)


def build_remove_sets():
    """构建精准和包含两种删除集合"""
    exact_set = {normalize_rule(r) for r in RULES_TO_REMOVE_EXACT if normalize_rule(r)}

    contains_list = []
    for r in RULES_TO_REMOVE_CONTAINS:
        norm = normalize_rule(r)
        if norm:
            contains_list.append(norm.lower())  # 包含匹配统一转小写

    return exact_set, contains_list


def should_remove(normalized: str, exact_set: set, contains_list: list) -> bool:
    """判断是否应该删除该规则"""
    if not normalized:
        return False

    # 1. 精准匹配（最高优先级）
    if normalized in exact_set:
        return True

    # 2. 包含匹配（不区分大小写）
    norm_lower = normalized.lower()
    for keyword in contains_list:
        if keyword in norm_lower:
            return True

    return False


def is_rule_line(line: str) -> bool:
    """判断是否为有效规则行"""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def read_source(path: str) -> list:
    """读取源文件，支持本地和远程"""
    if is_url(path):
        content = fetch_remote_content(path)
        return content.splitlines(keepends=True)
    else:
        if not os.path.exists(path):
            raise FileNotFoundError(f"源文件不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()


def process_rules(
    source_lines: list, exact_set: set, contains_list: list, rules_to_add: list
) -> tuple:
    """处理规则：精准 + 包含删除 + 去重"""
    result_lines = []
    removed_count = 0
    seen_rules = set()

    for raw_line in source_lines:
        normalized = normalize_rule(raw_line)

        # 保留原始注释和空行（当前默认跳过，如需保留可修改）
        if not normalized:
            continue

        # 删除判断
        if should_remove(normalized, exact_set, contains_list):
            removed_count += 1
            continue

        # 去重
        if normalized in seen_rules:
            continue
        seen_rules.add(normalized)

        result_lines.append(raw_line.rstrip("\n"))

    # 追加新增规则
    added_count = 0
    add_section = []
    for rule in rules_to_add:
        normalized = normalize_rule(rule)
        if not normalized:
            continue
        if normalized not in seen_rules:
            add_section.append(normalized)
            seen_rules.add(normalized)
            added_count += 1

    stats = {
        "source_total": sum(1 for l in source_lines if is_rule_line(l)),
        "removed": removed_count,
        "added": added_count,
        "output_total": sum(1 for l in result_lines if is_rule_line(l)) + added_count,
    }

    return result_lines, add_section, stats


def write_output(
    output_path: str, lines: list, add_section: list, stats: dict, source_path: str
):
    """写入输出文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = [
        f"# Generated by filter_amazon.py",
        f"# Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Source   : {source_path}",
        f"# Rules    : {stats['output_total']} "
        f"(source {stats['source_total']}, "
        f"-{stats['removed']} removed, "
        f"+{stats['added']} added)",
        "################################################################################",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header) + "\n\n")

        for line in lines:
            f.write(line + "\n")

        if add_section:
            f.write("\n# --- Custom Added Rules ---\n")
            for rule in add_section:
                f.write(rule + "\n")


def main():
    source_type = "远程 URL" if is_url(SOURCE_FILE) else "本地文件"
    print(f"[*] 源类型  : {source_type}")
    print(f"[*] 源地址  : {SOURCE_FILE}")

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    print(f"[*] 输出文件: {output_path}")

    try:
        source_lines = read_source(SOURCE_FILE)
        print(f"[*] 源文件共 {len(source_lines)} 行")

        # 构建删除集合
        exact_set, contains_list = build_remove_sets()

        if exact_set:
            print(f"[*] 精准删除规则: {len(exact_set)} 条")
            for r in sorted(exact_set):
                print(f"    - [精准] {r}")

        if contains_list:
            print(f"[*] 包含删除关键词: {len(contains_list)} 个")
            for r in contains_list:
                print(f"    - [包含] {r}")

        if RULES_TO_ADD:
            print(f"[*] 待添加规则: {len(RULES_TO_ADD)} 条")

        # 处理规则
        result_lines, add_section, stats = process_rules(
            source_lines, exact_set, contains_list, RULES_TO_ADD
        )

        # 写入输出
        write_output(output_path, result_lines, add_section, stats, SOURCE_FILE)

        print(f"\n[✓] 处理完成")
        print(f"    源规则数  : {stats['source_total']}")
        print(f"    删除规则  : {stats['removed']}")
        print(f"    新增规则  : {stats['added']}")
        print(f"    输出规则数: {stats['output_total']}")
        print(f"    输出路径  : {output_path}")

    except Exception as e:
        print(f"\n[✗] 错误: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
