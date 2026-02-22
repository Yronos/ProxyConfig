#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filter_facebook.py
从源规则文件中过滤/添加规则，生成精简版规则文件
支持本地文件和远程 URL
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
OUTPUT_FILENAME = "Reddit.list"

# 源文件路径（支持本地路径或 HTTP/HTTPS URL）
SOURCE_FILE = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Reddit/Reddit.list"

# 输出目录
OUTPUT_DIR = "./rules/lite"

# 网络请求配置
REQUEST_TIMEOUT = 30  # 超时时间（秒）
REQUEST_RETRIES = 3  # 重试次数

# ---------- 删除规则列表 ----------
RULES_TO_REMOVE = [
    # "DOMAIN-SUFFIX,acebooik.com",
    "DOMAIN-SUFFIX,redditstatic.com",
    "DOMAIN-SUFFIX,redditmedia.com",
    "DOMAIN-SUFFIX,redd.it",
]

# ---------- 添加规则列表 ----------
RULES_TO_ADD = [
    # "DOMAIN,example.com",
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
    """
    下载远程文件内容

    Args:
        url: 远程文件 URL
        timeout: 超时时间（秒）
        retries: 重试次数

    Returns:
        文件内容字符串

    Raises:
        Exception: 下载失败时抛出异常
    """
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
                break  # 404 不重试
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
    """去除注释、首尾空白，统一大写类型前缀，便于比较"""
    line = line.strip()
    if not line or line.startswith("#"):
        return ""
    # 去除行内注释（# 后内容）
    line = re.sub(r"\s*#.*$", "", line).strip()
    # 将规则类型部分统一大写
    parts = line.split(",")
    if parts and parts[0].upper() in VALID_RULE_TYPES:
        parts[0] = parts[0].upper()
    return ",".join(parts)


def build_remove_set(rules: list) -> set:
    """将 RULES_TO_REMOVE 列表构建为规范化 set"""
    return {normalize_rule(r) for r in rules if normalize_rule(r)}


def is_rule_line(line: str) -> bool:
    """判断是否为有效规则行（非注释、非空）"""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def read_source(path: str) -> list:
    """
    读取源文件，支持本地文件和远程 URL

    Args:
        path: 本地文件路径或 HTTP/HTTPS URL

    Returns:
        原始行列表
    """
    if is_url(path):
        # 远程文件
        content = fetch_remote_content(path)
        return content.splitlines(keepends=True)
    else:
        # 本地文件
        if not os.path.exists(path):
            raise FileNotFoundError(f"源文件不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return f.readlines()


def process_rules(source_lines: list, remove_set: set, rules_to_add: list) -> tuple:
    """
    处理规则：
    - 过滤掉 remove_set 中的规则
    - 追加 rules_to_add 中的规则（去重）
    返回 (处理后的行列表, 统计信息 dict)
    """
    result_lines = []
    removed_count = 0
    seen_rules = set()  # 用于全局去重

    for raw_line in source_lines:
        normalized = normalize_rule(raw_line)

        # 保留注释行和空行（原样输出）
        if not normalized:
            # result_lines.append(raw_line.rstrip("\n"))
            continue

        # 检查是否需要删除
        if normalized in remove_set:
            removed_count += 1
            continue

        # 去重处理（源文件本身可能有重复）
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
    """写入输出文件，包含文件头注释"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = [
        f"# Generated by filter_reddit.py",
        f"# Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Source   : {source_path}",
        f"# Rules    : {stats['output_total']} "
        f"(source {stats['source_total']}, "
        f"-{stats['removed']} removed, "
        f"+{stats['added']} added)",
        "################################################################################",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        # 写入文件头
        f.write("\n".join(header) + "\n")

        # 写入处理后的规则
        for line in lines:
            f.write(line + "\n")

        # 写入新增规则段
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
        # 读取源文件
        source_lines = read_source(SOURCE_FILE)
        print(f"[*] 源文件共 {len(source_lines)} 行")

        # 构建删除集合
        remove_set = build_remove_set(RULES_TO_REMOVE)
        if remove_set:
            print(f"[*] 待删除规则: {len(remove_set)} 条")
            for r in sorted(remove_set):
                print(f"    - {r}")

        if RULES_TO_ADD:
            print(f"[*] 待添加规则: {len(RULES_TO_ADD)} 条")
            for r in RULES_TO_ADD:
                print(f"    + {r}")

        # 处理规则
        result_lines, add_section, stats = process_rules(
            source_lines, remove_set, RULES_TO_ADD
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
