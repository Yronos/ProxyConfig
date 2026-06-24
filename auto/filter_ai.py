#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
filter_ai.py

从主规则集中生成精简版 AI.list：

功能：
1. 支持远程 / 本地规则源
2. 支持多个远程排除规则集，例如 Google / Twitter
3. 支持手动删除规则
4. 支持手动添加规则
5. 全局去重
6. 并发下载
7. 本地缓存远程规则，提升速度
8. 输出 Surge / Loon / Stash / Clash classical rule-provider 可用的规则格式

Python 版本：3.8+
"""

import hashlib
import os
import re
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

# ============================================================
# 用户配置区域
# ============================================================

OUTPUT_DIR = "./rules/lite"
OUTPUT_FILENAME = "AI.list"

# 主规则源：你要精简的 ai 规则
MAIN_RULESET = {
    "name": "Sukka AI",
    "url": "https://raw.githubusercontent.com/SukkaLab/ruleset.skk.moe/refs/heads/master/List/non_ip/ai.conf",
}

# 用于从 AI 中剔除的规则集
# 例如你有单独的 Google / Twitter 策略组，那么这些规则就没必要再留在 AI 里
EXCLUDE_RULESETS = []

# 手动删除规则
# 这些规则会从主规则中强制剔除
CUSTOM_REMOVE_RULES = [
    # Twitter 示例
    # "DOMAIN-SUFFIX,t.co",
    # "DOMAIN-SUFFIX,twimg.com",
    "DOMAIN,7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
    "DOMAIN-KEYWORD,openai",
    "DOMAIN-KEYWORD,alkalimakersuite-pa.clients6.google.com",
]

# 手动添加规则
# 这些规则会追加到最终 AI.list
CUSTOM_ADD_RULES = [
    # "DOMAIN,example.com",
    # "DOMAIN-SUFFIX,example.org",
    "DOMAIN-SUFFIX,openai.com",
]

# 如果手动添加的规则同时存在于 EXCLUDE_RULESETS 中，是否仍然保留？
# True  = 手动添加优先，强制保留
# False = 只要命中排除规则集，就不加入 AI
CUSTOM_ADD_OVERRIDES_EXCLUDE = True

# 输出是否排序
# True  = 输出更稳定，方便 Git diff
# False = 尽量保留主规则源原始顺序
SORT_OUTPUT_RULES = False

# 是否在输出中加入头部注释
WRITE_HEADER = True

# 网络请求配置
REQUEST_TIMEOUT = 30
REQUEST_RETRIES = 3
MAX_WORKERS = 6

# 缓存配置
ENABLE_CACHE = False
CACHE_DIR = ".cache/ruleset"
CACHE_TTL_SECONDS = 6 * 60 * 60
# 6 小时缓存。你也可以改成：
# 24 * 60 * 60     # 24 小时
# 0                # 永不过期，只要缓存存在就使用


# ============================================================
# 支持的规则类型
# ============================================================

VALID_RULE_TYPES = {
    "DOMAIN",
    "DOMAIN-SUFFIX",
    "DOMAIN-KEYWORD",
    "DOMAIN-WILDCARD",
    "DOMAIN-REGEX",
    "IP-CIDR",
    "IP-CIDR6",
    "IP-ASN",
    "GEOIP",
    "USER-AGENT",
    "URL-REGEX",
    "PROCESS-NAME",
    "PROCESS-PATH",
    "DEST-PORT",
    "SRC-IP",
    "SRC-PORT",
    # Surge / Clash 常见
    "RULE-SET",
    "DOMAIN-SET",
}


# ============================================================
# 工具函数
# ============================================================


def is_url(path: str) -> bool:
    return path.startswith(("http://", "https://"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def get_cache_path(url: str) -> Path:
    name = sha256_text(url) + ".txt"
    return Path(CACHE_DIR) / name


def cache_is_valid(path: Path) -> bool:
    if not path.exists():
        return False

    if CACHE_TTL_SECONDS == 0:
        return True

    age = time.time() - path.stat().st_mtime
    return age <= CACHE_TTL_SECONDS


def read_cache(url: str) -> str:
    path = get_cache_path(url)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_cache(url: str, content: str):
    path = get_cache_path(url)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(content)

    os.replace(tmp, path)


def fetch_remote_content(url: str) -> str:
    """
    下载远程规则，带重试和缓存。
    """

    if ENABLE_CACHE:
        cache_path = get_cache_path(url)
        if cache_is_valid(cache_path):
            print(f"[cache] {url}")
            return read_cache(url)

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        ),
        "Accept": "text/plain,*/*",
    }

    last_error = None

    for attempt in range(1, REQUEST_RETRIES + 1):
        try:
            print(f"[download] {url} ({attempt}/{REQUEST_RETRIES})")
            req = Request(url, headers=headers)

            with urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                raw = resp.read()

            content = raw.decode("utf-8-sig", errors="replace")

            if ENABLE_CACHE:
                write_cache(url, content)

            return content

        except HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            print(f"[warn] {last_error}")

            if e.code == 404:
                break

        except URLError as e:
            last_error = f"URL error: {e.reason}"
            print(f"[warn] {last_error}")

        except Exception as e:
            last_error = str(e)
            print(f"[warn] {last_error}")

        if attempt < REQUEST_RETRIES:
            time.sleep(1.5)

    raise RuntimeError(f"下载失败：{url}，原因：{last_error}")


def read_source(path_or_url: str) -> str:
    if is_url(path_or_url):
        return fetch_remote_content(path_or_url)

    path = Path(path_or_url)
    if not path.exists():
        raise FileNotFoundError(f"源文件不存在：{path_or_url}")

    with open(path, "r", encoding="utf-8-sig") as f:
        return f.read()


def strip_inline_comment(line: str) -> str:
    """
    移除行内注释。

    注意：
    一般 Surge / Clash 规则中 # 后面多为注释。
    如果你的 URL-REGEX 中确实需要 #，可以按需关闭这一步。
    """
    return re.sub(r"\s+#.*$", "", line).strip()


def parse_rule(line: str):
    """
    将规则行解析为：
    {
        "type": "DOMAIN-SUFFIX",
        "value": "google.com",
        "extra": []
    }

    返回 None 表示非规则行。
    """

    line = line.strip()

    if not line:
        return None

    if line.startswith("#"):
        return None

    if line.startswith("//"):
        return None

    if line.startswith(";"):
        return None

    line = strip_inline_comment(line)

    if not line:
        return None

    parts = [p.strip() for p in line.split(",")]

    if len(parts) < 2:
        return None

    rule_type = parts[0].upper()

    if rule_type not in VALID_RULE_TYPES:
        return None

    value = parts[1].strip()

    if not value:
        return None

    extra = [p.strip() for p in parts[2:] if p.strip()]

    return {
        "type": rule_type,
        "value": value,
        "extra": extra,
    }


def normalize_rule_key(line: str):
    """
    用于比较和去重的 key。

    重点：
    - DOMAIN / DOMAIN-SUFFIX / DOMAIN-KEYWORD 等域名类规则统一小写
    - 忽略策略名和 no-resolve 等额外字段
    - 例如：
      DOMAIN-SUFFIX,Google.com,Proxy
      DOMAIN-SUFFIX,google.com
      会被视为同一条规则
    """

    rule = parse_rule(line)

    if not rule:
        return None

    rule_type = rule["type"]
    value = rule["value"]

    if rule_type.startswith("DOMAIN") or rule_type in {
        "USER-AGENT",
        "PROCESS-NAME",
        "PROCESS-PATH",
    }:
        value = value.lower()

    return f"{rule_type},{value}"


def normalize_rule_output(line: str):
    """
    用于最终输出的规则格式。
    输出时只保留：
    RULE-TYPE,VALUE

    这样生成的规则更适合放入单独的 .list 规则文件。
    """

    rule = parse_rule(line)

    if not rule:
        return None

    rule_type = rule["type"]
    value = rule["value"]

    if rule_type.startswith("DOMAIN"):
        value = value.lower()

    return f"{rule_type},{value}"


def parse_rules_from_content(content: str):
    """
    从文本中提取规则。

    返回：
    ordered_rules: [(key, output_rule), ...]
    """

    result = []

    for line in content.splitlines():
        key = normalize_rule_key(line)
        output = normalize_rule_output(line)

        if key and output:
            result.append((key, output))

    return result


def load_ruleset(name: str, path_or_url: str):
    """
    加载一个规则集。
    """
    content = read_source(path_or_url)
    rules = parse_rules_from_content(content)

    return {
        "name": name,
        "source": path_or_url,
        "rules": rules,
        "count": len(rules),
    }


def load_rulesets_concurrently(rulesets: list):
    """
    并发加载多个规则集。
    """
    results = []

    if not rulesets:
        return results

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {}

        for item in rulesets:
            name = item["name"]
            source = item.get("url") or item.get("path")
            future = executor.submit(load_ruleset, name, source)
            future_map[future] = item

        for future in as_completed(future_map):
            item = future_map[future]
            try:
                result = future.result()
                print(f"[ok] {result['name']}: {result['count']} 条规则")
                results.append(result)
            except Exception as e:
                raise RuntimeError(f"加载规则集失败：{item.get('name')}，原因：{e}")

    return results


def build_rule_set_from_lines(lines: list):
    result = set()

    for line in lines:
        key = normalize_rule_key(line)
        if key:
            result.add(key)

    return result


def generate_lite_ai():
    """
    核心流程：
    1. 加载主 AI 规则
    2. 加载多个排除规则集
    3. 合并排除规则
    4. 过滤主 AI
    5. 手动添加规则
    6. 输出去重后的规则
    """

    print("============================================================")
    print("生成 Lite AI.list")
    print("============================================================")

    # 加载主规则
    print(f"[main] {MAIN_RULESET['name']}")
    main = load_ruleset(MAIN_RULESET["name"], MAIN_RULESET["url"])
    print(f"[ok] {main['name']}: {main['count']} 条规则")

    # 并发加载排除规则
    print("\n[exclude] 加载排除规则集")
    exclude_results = load_rulesets_concurrently(EXCLUDE_RULESETS)

    exclude_set = set()

    for item in exclude_results:
        for key, _ in item["rules"]:
            exclude_set.add(key)

    # 加入手动删除规则
    custom_remove_set = build_rule_set_from_lines(CUSTOM_REMOVE_RULES)
    exclude_set.update(custom_remove_set)

    print(f"\n[exclude] 排除规则总数：{len(exclude_set)}")
    print(f"[exclude] 其中手动删除：{len(custom_remove_set)}")

    # 处理主规则
    output_rules = []
    seen = set()

    source_total = len(main["rules"])
    removed_count = 0
    duplicate_count = 0

    for key, output in main["rules"]:
        if key in exclude_set:
            removed_count += 1
            continue

        if key in seen:
            duplicate_count += 1
            continue

        seen.add(key)
        output_rules.append(output)

    # 处理手动添加规则
    added_count = 0
    skipped_add_duplicate = 0
    skipped_add_excluded = 0

    for line in CUSTOM_ADD_RULES:
        key = normalize_rule_key(line)
        output = normalize_rule_output(line)

        if not key or not output:
            continue

        if key in seen:
            skipped_add_duplicate += 1
            continue

        if key in exclude_set and not CUSTOM_ADD_OVERRIDES_EXCLUDE:
            skipped_add_excluded += 1
            continue

        seen.add(key)
        output_rules.append(output)
        added_count += 1

    if SORT_OUTPUT_RULES:
        output_rules = sorted(output_rules)

    stats = {
        "source_total": source_total,
        "exclude_total": len(exclude_set),
        "removed": removed_count,
        "duplicate": duplicate_count,
        "custom_added": added_count,
        "custom_add_duplicate": skipped_add_duplicate,
        "custom_add_excluded": skipped_add_excluded,
        "output_total": len(output_rules),
    }

    return output_rules, stats, exclude_results


def atomic_write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        dir=str(path.parent),
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    os.replace(tmp_path, path)


def write_output(rules: list, stats: dict, exclude_results: list):
    output_path = Path(OUTPUT_DIR) / OUTPUT_FILENAME

    lines = []

    if WRITE_HEADER:
        lines.extend(
            [
                "# Generated by filter_ai.py",
                f"# Date       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"# Main       : {MAIN_RULESET['url']}",
                f"# Rules      : {stats['output_total']}",
                f"# Source     : {stats['source_total']}",
                f"# Removed    : {stats['removed']}",
                f"# Duplicates : {stats['duplicate']}",
                f"# Added      : {stats['custom_added']}",
                "#",
                "# Exclude rulesets:",
            ]
        )

        for item in exclude_results:
            lines.append(f"# - {item['name']}: {item['source']}")

        lines.extend(
            [
                "################################################################################",
                "",
            ]
        )

    lines.extend(rules)
    lines.append("")

    atomic_write_text(output_path, "\n".join(lines))

    return output_path


def main():
    try:
        rules, stats, exclude_results = generate_lite_ai()
        output_path = write_output(rules, stats, exclude_results)

        print("\n============================================================")
        print("[完成]")
        print("============================================================")
        print(f"源规则数        : {stats['source_total']}")
        print(f"排除规则总数    : {stats['exclude_total']}")
        print(f"从主规则删除    : {stats['removed']}")
        print(f"主规则重复跳过  : {stats['duplicate']}")
        print(f"手动新增        : {stats['custom_added']}")
        print(f"新增重复跳过    : {stats['custom_add_duplicate']}")
        print(f"新增被排除跳过  : {stats['custom_add_excluded']}")
        print(f"最终输出规则数  : {stats['output_total']}")
        print(f"输出文件        : {output_path}")

    except Exception as e:
        print(f"\n[错误] {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
