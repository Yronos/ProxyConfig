#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
filter_youtube.py
从源规则文件中过滤/添加规则，生成精简版规则文件
支持本地文件和远程 URL

【更新特性】
- 支持精准匹配删除（RULES_TO_REMOVE_EXACT）
- 支持包含匹配删除（RULES_TO_REMOVE_CONTAINS）
- 支持将部分 DOMAIN-SUFFIX 转换为 DOMAIN（RULES_SUFFIX_TO_DOMAIN）

【说明】
- DOMAIN-SUFFIX -> DOMAIN 转换仅对 RULES_SUFFIX_TO_DOMAIN 中指定的域名生效
- 转换匹配大小写不敏感
- 转换时会保留规则后续字段，例如策略名、no-resolve 等
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
OUTPUT_FILENAME = "YouTube.list"

# 源文件路径（支持本地路径或 HTTP/HTTPS URL）
SOURCE_FILE = "./rules/surge/YouTube.list"

# 输出目录
OUTPUT_DIR = "./rules/lite"

# 网络请求配置
REQUEST_TIMEOUT = 30  # 超时时间（秒）
REQUEST_RETRIES = 3  # 重试次数

# ---------- 删除规则列表 ----------
# 1. 精准匹配删除（必须完全相同，优先级最高）
RULES_TO_REMOVE_EXACT = [
    "DOMAIN-SUFFIX,ggpht.cn",
    "DOMAIN-SUFFIX,ggpht.com",
    "DOMAIN-SUFFIX,video.google.com",
    "DOMAIN-SUFFIX,wide-youtube.l.google.com",
    "DOMAIN-SUFFIX,youtube-ui.l.google.com",
    "DOMAIN-SUFFIX,youtube.cat",
    "DOMAIN-SUFFIX,youtube.co",
    "DOMAIN-SUFFIX,youtube.com.co",
    "DOMAIN-SUFFIX,youtube.me",
    "DOMAIN-SUFFIX,youtube.soy",
    "DOMAIN-SUFFIX,youtube.tv",
    "DOMAIN-SUFFIX,youtubeembeddedplayer.googleapis.com",
    "DOMAIN-SUFFIX,youtubefanfest.com",
    "DOMAIN-SUFFIX,youtubego.com",
    "DOMAIN-SUFFIX,youtubego.com.br",
    "DOMAIN-SUFFIX,youtubego.id",
    "DOMAIN-SUFFIX,youtubego.in",
    "DOMAIN-SUFFIX,ytimg.com",
    "DOMAIN-KEYWORD,youtube",
    "IP-CIDR,172.110.32.0/21,no-resolve",
    "IP-CIDR,216.73.80.0/20,no-resolve",
    "IP-CIDR6,2620:120:e000::/40,no-resolve",
    "USER-AGENT,*YouTubeMusic*",
    "USER-AGENT,*com.google.ios.youtubemusic*",
    "USER-AGENT,*youtube*",
    "USER-AGENT,YouTube*",
    "USER-AGENT,YouTubeMusic*",
    "USER-AGENT,com.google.ios.youtube*",
    "USER-AGENT,com.google.ios.youtubemusic*",
]

# 2. 包含匹配删除
RULES_TO_REMOVE_CONTAINS = [
    # "amazon",
    # "amazonaws",
    # "cloudfront",
]

# ---------- DOMAIN-SUFFIX 转 DOMAIN ----------
# 只对列表中的域名进行转换（填 suffix 部分即可）
#
# 示例：
# 源规则：
#   DOMAIN-SUFFIX,youtubei.googleapis.com
#
# 输出：
#   DOMAIN,youtubei.googleapis.com
#
# 注意：
# DOMAIN-SUFFIX,youtubei.googleapis.com 会匹配：
#   youtubei.googleapis.com
#   a.youtubei.googleapis.com
#
# DOMAIN,youtubei.googleapis.com 只匹配：
#   youtubei.googleapis.com
#
# 因此只建议对确实只需要精确匹配的域名进行转换。
RULES_SUFFIX_TO_DOMAIN = [
    "youtubei.googleapis.com",
    "youtube.googleapis.com",
    # 在这里添加你希望转为精确 DOMAIN 的域名
]

# ---------- 添加规则列表 ----------
RULES_TO_ADD = [
    # "DOMAIN,example.com",
    # "DOMAIN-SUFFIX,amazon.com",
]

# ============================================================
# 支持的规则类型
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

            # 404 通常无需重试
            if e.code == 404:
                break

        except URLError as e:
            last_error = f"网络错误: {e.reason}"
            print(f"[!] {last_error}")

        except Exception as e:
            last_error = f"未知错误: {str(e)}"
            print(f"[!] {last_error}")

        if attempt < retries - 1:
            print("[*] 等待 2 秒后重试...")
            import time

            time.sleep(2)

    raise Exception(f"下载失败: {last_error}")


def normalize_rule(line: str) -> str:
    """去除注释、首尾空白，统一大写类型前缀"""
    line = line.strip()

    if not line or line.startswith("#"):
        return ""

    # 去除行内注释
    # 注意：如果 URL-REGEX 规则中本身包含 #，此处可能会截断。
    # 当前保持原脚本逻辑不做大改。
    line = re.sub(r"\s*#.*$", "", line).strip()

    if not line:
        return ""

    # 对每个字段做 strip，避免：
    # DOMAIN-SUFFIX, youtube.com
    # 这种格式导致精准匹配、转换、去重失败。
    parts = [p.strip() for p in line.split(",")]

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
            contains_list.append(norm.lower())

    return exact_set, contains_list


def build_suffix_to_domain_set():
    """构建 DOMAIN-SUFFIX -> DOMAIN 转换集合，统一小写"""
    return {d.strip().lower() for d in RULES_SUFFIX_TO_DOMAIN if d.strip()}


def should_remove(normalized: str, exact_set: set, contains_list: list) -> bool:
    """判断是否应该删除该规则"""
    if not normalized:
        return False

    # 精准匹配删除
    if normalized in exact_set:
        return True

    # 包含匹配删除，大小写不敏感
    norm_lower = normalized.lower()
    for keyword in contains_list:
        if keyword in norm_lower:
            return True

    return False


def convert_suffix_to_domain(normalized: str, suffix_to_domain_set: set) -> str:
    """如果规则在转换列表中，则将 DOMAIN-SUFFIX 转为 DOMAIN

    示例：
    DOMAIN-SUFFIX,youtubei.googleapis.com
    ->
    DOMAIN,youtubei.googleapis.com

    示例，保留后续字段：
    DOMAIN-SUFFIX,youtubei.googleapis.com,Proxy
    ->
    DOMAIN,youtubei.googleapis.com,Proxy
    """
    if not normalized:
        return normalized

    parts = [p.strip() for p in normalized.split(",")]

    if len(parts) < 2:
        return normalized

    rule_type = parts[0].upper()
    domain = parts[1].lower()

    if rule_type != "DOMAIN-SUFFIX":
        return normalized

    if domain not in suffix_to_domain_set:
        return normalized

    # 将规则类型改为 DOMAIN，并统一域名为小写
    # 后续字段保持不变
    parts[0] = "DOMAIN"
    parts[1] = domain

    return ",".join(parts)


def is_rule_line(line: str) -> bool:
    """判断是否为有效规则行"""
    stripped = line.strip()
    return bool(stripped) and not stripped.startswith("#")


def read_source(path: str) -> list:
    """读取源文件，支持本地和远程"""
    if is_url(path):
        content = fetch_remote_content(path)
        return content.splitlines(keepends=True)

    if not os.path.exists(path):
        raise FileNotFoundError(f"源文件不存在: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return f.readlines()


def process_rules(
    source_lines: list,
    exact_set: set,
    contains_list: list,
    rules_to_add: list,
    suffix_to_domain_set: set,
) -> tuple:
    """处理规则：删除 + 转换 + 去重"""
    result_lines = []
    removed_count = 0
    seen_rules = set()

    for raw_line in source_lines:
        normalized = normalize_rule(raw_line)

        if not normalized:
            continue

        # 删除判断
        if should_remove(normalized, exact_set, contains_list):
            removed_count += 1
            continue

        # DOMAIN-SUFFIX 转 DOMAIN
        converted = convert_suffix_to_domain(normalized, suffix_to_domain_set)

        # 去重，使用转换后的规则判断
        if converted in seen_rules:
            continue

        seen_rules.add(converted)

        # 保留原始行：
        # - 如果发生转换，使用转换后的内容
        # - 如果未转换，保留源文件原始规则行
        if converted != normalized:
            result_lines.append(converted)
        else:
            result_lines.append(raw_line.rstrip("\n"))

    # 追加新增规则
    added_count = 0
    add_section = []

    for rule in rules_to_add:
        normalized = normalize_rule(rule)

        if not normalized:
            continue

        # 新增规则也支持 DOMAIN-SUFFIX -> DOMAIN 转换
        converted = convert_suffix_to_domain(normalized, suffix_to_domain_set)

        if converted not in seen_rules:
            add_section.append(converted)
            seen_rules.add(converted)
            added_count += 1

    stats = {
        "source_total": sum(1 for l in source_lines if is_rule_line(l)),
        "removed": removed_count,
        "added": added_count,
        "output_total": len([l for l in result_lines if is_rule_line(l)]) + added_count,
    }

    return result_lines, add_section, stats


def write_output(
    output_path: str,
    lines: list,
    add_section: list,
    stats: dict,
    source_path: str,
):
    """写入输出文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    header = [
        "# Generated by filter_youtube.py",
        f"# Date     : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"# Source   : {source_path}",
        f"# Rules    : {stats['output_total']} "
        f"(source {stats['source_total']}, "
        f"-{stats['removed']} removed, "
        f"+{stats['added']} added)",
        "# Note     : Some DOMAIN-SUFFIX converted to DOMAIN",
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
    print(f"[*] 待转换 DOMAIN-SUFFIX -> DOMAIN: {len(RULES_SUFFIX_TO_DOMAIN)} 条")

    output_path = os.path.join(OUTPUT_DIR, OUTPUT_FILENAME)
    print(f"[*] 输出文件: {output_path}")

    try:
        source_lines = read_source(SOURCE_FILE)
        print(f"[*] 源文件共 {len(source_lines)} 行")

        exact_set, contains_list = build_remove_sets()
        suffix_to_domain_set = build_suffix_to_domain_set()

        if exact_set:
            print(f"[*] 精准删除规则: {len(exact_set)} 条")

        if contains_list:
            print(f"[*] 包含删除关键词: {len(contains_list)} 个")

        if suffix_to_domain_set:
            print(f"[*] 转换列表: {len(suffix_to_domain_set)} 条")

        result_lines, add_section, stats = process_rules(
            source_lines,
            exact_set,
            contains_list,
            RULES_TO_ADD,
            suffix_to_domain_set,
        )

        write_output(output_path, result_lines, add_section, stats, SOURCE_FILE)

        print("\n[✓] 处理完成")
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
