#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 domainset 格式的规则文件中筛选出被 rule-set 格式规则覆盖的规则
输出为 rule-set 格式（.list）
"""

# ============================================================
# 📝 配置区域 - 在这里填入你的文件链接
# ============================================================

# 前者文件 (domainset 格式) - 填入一个 URL 或本地路径
DOMAINSET_URL = "https://ruleset.skk.moe/List/domainset/cdn.conf"

# 后者文件列表 (rule-set 格式) - 可以填入多个 URL 或本地路径
RULESET_URLS = [
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/GitHub/GitHub.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Microsoft/Microsoft.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Google/Google.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/YouTube/YouTube.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Apple/Apple_All.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Twitter/Twitter.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Discord/Discord.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Reddit/Reddit.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Cloudflare/Cloudflare.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Facebook/Facebook.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Amazon/Amazon.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Akamai/Akamai.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Steam/Steam.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Epic/Epic.list",
    "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/OpenAI/OpenAI.list",
]

# 自定义规则 - 手动添加没有规则集的服务
# 格式：每行一条规则，支持三种类型
CUSTOM_RULES = """
DOMAIN-SUFFIX,fastly.net
DOMAIN-SUFFIX,lencr.org
DOMAIN-SUFFIX,teo-rum.com
DOMAIN-SUFFIX,jsdelivr.net
DOMAIN-SUFFIX,imgur.com
DOMAIN-SUFFIX,stripe.com
DOMAIN-SUFFIX,v2ex.co
DOMAIN-SUFFIX,v2ex.com
DOMAIN-SUFFIX,bsky.social
DOMAIN-SUFFIX,bsky.app
DOMAIN-SUFFIX,wikimedia.org
DOMAIN-SUFFIX,gravatar.com
DOMAIN-SUFFIX,esm.sh
DOMAIN-SUFFIX,111666.best
DOMAIN-SUFFIX,adtidy.org
"""

# 输出文件名 (留空则自动生成)
OUTPUT_FILE = "CDN_Lite.list"

# 是否显示详细匹配信息
VERBOSE = False

# ============================================================
# 以下是脚本代码，无需修改
# ============================================================

import os
import sys
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

import requests


class SuffixTrie:
    """反向字典树，用于高效的后缀匹配"""

    def __init__(self):
        self.root: Dict[str, any] = {}

    def add(self, domain: str):
        """添加后缀规则（反向存储）"""
        parts = domain.lower().split(".")[::-1]
        node = self.root

        for part in parts:
            if part not in node:
                node[part] = {}
            node = node[part]

        node["$"] = True

    def match(self, domain: str) -> bool:
        """检查域名是否被任一后缀规则覆盖"""
        parts = domain.lower().split(".")[::-1]
        node = self.root

        for part in parts:
            if part not in node:
                return False
            node = node[part]
            if "$" in node:
                return True

        return False


def convert_github_url(url: str) -> str:
    """将 GitHub 页面 URL 转换为 raw URL"""
    if "github.com" in url and "/blob/" in url:
        url = url.replace("github.com", "raw.githubusercontent.com")
        url = url.replace("/blob/", "/")
    return url


def download_file(url: str, timeout: int = 30) -> Optional[str]:
    """下载文件内容"""
    url = convert_github_url(url)
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[错误] 下载失败 {url}: {e}")
        return None


def read_local_file(filepath: str) -> Optional[str]:
    """读取本地文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        print(f"[错误] 读取文件失败 {filepath}: {e}")
        return None


def get_content(path: str) -> Optional[str]:
    """获取内容，支持 URL 和本地文件"""
    if path.startswith("http://") or path.startswith("https://"):
        return download_file(path)
    else:
        return read_local_file(path)


def parse_domainset(content: str) -> Tuple[List[str], List[str]]:
    """
    解析 domainset 格式的规则
    返回: (精确匹配规则列表, 后缀匹配规则列表)
    """
    exact_rules = []
    suffix_rules = []

    for line in content.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        if line.startswith("."):
            suffix_rules.append(line[1:])
        else:
            exact_rules.append(line)

    return exact_rules, suffix_rules


def parse_custom_rules(custom_rules_text: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    解析自定义规则
    返回: (DOMAIN集合, DOMAIN-SUFFIX集合, DOMAIN-KEYWORD集合)
    """
    domains = set()
    domain_suffixes = set()
    domain_keywords = set()

    for line in custom_rules_text.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        parts = line.split(",")
        if len(parts) < 2:
            continue

        rule_type = parts[0].strip().upper()
        value = parts[1].strip().lower()

        if rule_type == "DOMAIN":
            domains.add(value)
        elif rule_type == "DOMAIN-SUFFIX":
            domain_suffixes.add(value)
        elif rule_type == "DOMAIN-KEYWORD":
            domain_keywords.add(value)

    return domains, domain_suffixes, domain_keywords


def parse_ruleset(content: str) -> Tuple[Set[str], Set[str], Set[str]]:
    """
    解析 rule-set 格式的规则
    返回: (DOMAIN集合, DOMAIN-SUFFIX集合, DOMAIN-KEYWORD集合)
    """
    domains = set()
    domain_suffixes = set()
    domain_keywords = set()

    for line in content.strip().split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("//"):
            continue

        parts = line.split(",")
        if len(parts) < 2:
            continue

        rule_type = parts[0].strip().upper()
        value = parts[1].strip().lower()

        if rule_type == "DOMAIN":
            domains.add(value)
        elif rule_type == "DOMAIN-SUFFIX":
            domain_suffixes.add(value)
        elif rule_type == "DOMAIN-KEYWORD":
            domain_keywords.add(value)

    return domains, domain_suffixes, domain_keywords


def build_suffix_matcher(domain_suffixes: Set[str]) -> SuffixTrie:
    """构建后缀匹配器"""
    trie = SuffixTrie()
    for suffix in domain_suffixes:
        trie.add(suffix)
    return trie


def check_keyword_match(domain: str, keywords: Set[str]) -> bool:
    """检查域名是否包含任一关键词"""
    domain_lower = domain.lower()
    for keyword in keywords:
        if keyword in domain_lower:
            return True
    return False


def check_coverage_batch(
    exact_rules: List[str],
    suffix_rules: List[str],
    domains: Set[str],
    suffix_matcher: SuffixTrie,
    keywords: Set[str],
) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
    """
    批量检查规则覆盖情况
    返回: (被覆盖的精确规则列表, 被覆盖的后缀规则列表)
    每个元素为 (原始规则, 规则类型) 元组
    """
    covered_exact = []
    covered_suffix = []

    # 处理精确匹配规则
    for rule in exact_rules:
        rule_lower = rule.lower()

        # 优先级：DOMAIN > DOMAIN-SUFFIX > DOMAIN-KEYWORD
        if rule_lower in domains:
            covered_exact.append((rule, "DOMAIN"))
        elif suffix_matcher.match(rule_lower):
            covered_exact.append((rule, "DOMAIN"))
        elif check_keyword_match(rule_lower, keywords):
            covered_exact.append((rule, "DOMAIN"))

    # 处理后缀匹配规则
    for rule in suffix_rules:
        rule_lower = rule.lower()

        if suffix_matcher.match(rule_lower):
            covered_suffix.append((rule, "DOMAIN-SUFFIX"))
        elif check_keyword_match(rule_lower, keywords):
            covered_suffix.append((rule, "DOMAIN-SUFFIX"))

    return covered_exact, covered_suffix


def get_filename_from_path(path: str) -> str:
    """从路径或 URL 中提取文件名（不含扩展名）"""
    if path.startswith("http://") or path.startswith("https://"):
        path = urlparse(path).path
    filename = os.path.basename(path)
    name, _ = os.path.splitext(filename)
    return name


def generate_output_filename(ruleset_names: List[str], domainset_name: str) -> str:
    """生成输出文件名"""
    if not ruleset_names:
        ruleset_names = ["unknown"]
    return "-".join(ruleset_names) + "-" + domainset_name + ".list"


def ensure_output_dir():
    """确保输出目录存在"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(os.path.dirname(script_dir), "rules")

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[信息] 创建输出目录: {output_dir}")

    return output_dir


def main():
    print("=" * 60)
    print("规则合并与提取脚本")
    print("=" * 60)

    start_time = time.time()

    # 获取并解析前者文件（domainset）
    print(f"\n[1] 获取前者文件 (domainset):")
    print(f"    {DOMAINSET_URL}")
    domainset_content = get_content(DOMAINSET_URL)
    if domainset_content is None:
        print("[错误] 无法获取前者文件，退出")
        sys.exit(1)

    exact_rules, suffix_rules = parse_domainset(domainset_content)
    total_rules = len(exact_rules) + len(suffix_rules)
    print(f"    解析到 {total_rules} 条规则")
    print(f"      - 精确匹配: {len(exact_rules)} 条")
    print(f"      - 后缀匹配: {len(suffix_rules)} 条")

    if total_rules == 0:
        print("[错误] 前者文件中没有有效规则，退出")
        sys.exit(1)

    # 解析自定义规则
    print(f"\n[2] 解析自定义规则:")
    custom_domains, custom_suffixes, custom_keywords = parse_custom_rules(CUSTOM_RULES)
    custom_total = len(custom_domains) + len(custom_suffixes) + len(custom_keywords)
    print(f"    解析到 {custom_total} 条自定义规则")
    print(f"      - DOMAIN: {len(custom_domains)} 条")
    print(f"      - DOMAIN-SUFFIX: {len(custom_suffixes)} 条")
    print(f"      - DOMAIN-KEYWORD: {len(custom_keywords)} 条")

    # 获取并解析后者文件（rule-set）
    print(f"\n[3] 获取后者文件 (rule-set):")
    all_domains: Set[str] = set(custom_domains)
    all_domain_suffixes: Set[str] = set(custom_suffixes)
    all_domain_keywords: Set[str] = set(custom_keywords)
    ruleset_names: List[str] = []

    for ruleset_path in RULESET_URLS:
        print(f"    - {ruleset_path}")
        content = get_content(ruleset_path)
        if content is None:
            print(f"      [警告] 跳过此文件")
            continue

        domains, domain_suffixes, domain_keywords = parse_ruleset(content)
        all_domains.update(domains)
        all_domain_suffixes.update(domain_suffixes)
        all_domain_keywords.update(domain_keywords)
        ruleset_names.append(get_filename_from_path(ruleset_path))
        print(
            f"      DOMAIN: {len(domains)}, DOMAIN-SUFFIX: {len(domain_suffixes)}, DOMAIN-KEYWORD: {len(domain_keywords)}"
        )

    if not all_domains and not all_domain_suffixes and not all_domain_keywords:
        print("[错误] 后者文件中没有有效规则，退出")
        sys.exit(1)

    print(f"\n[4] 后者规则汇总:")
    print(f"    DOMAIN 规则总数: {len(all_domains)} (含自定义 {len(custom_domains)})")
    print(
        f"    DOMAIN-SUFFIX 规则总数: {len(all_domain_suffixes)} (含自定义 {len(custom_suffixes)})"
    )
    print(
        f"    DOMAIN-KEYWORD 规则总数: {len(all_domain_keywords)} (含自定义 {len(custom_keywords)})"
    )

    # 构建后缀匹配器
    print(f"\n[5] 构建后缀匹配器...")
    suffix_matcher = build_suffix_matcher(all_domain_suffixes)
    print(f"    完成")

    # 批量检查覆盖情况
    print(f"\n[6] 开始批量筛选...")
    covered_exact, covered_suffix = check_coverage_batch(
        exact_rules, suffix_rules, all_domains, suffix_matcher, all_domain_keywords
    )

    total_covered = len(covered_exact) + len(covered_suffix)
    print(f"    筛选完成: {total_covered}/{total_rules} 条规则被保留")
    print(f"      - 精确匹配: {len(covered_exact)}/{len(exact_rules)}")
    print(f"      - 后缀匹配: {len(covered_suffix)}/{len(suffix_rules)}")

    # 确保输出目录存在
    output_dir = ensure_output_dir()

    # 生成输出文件路径
    if OUTPUT_FILE:
        output_filename = OUTPUT_FILE
    else:
        domainset_name = get_filename_from_path(DOMAINSET_URL)
        output_filename = generate_output_filename(ruleset_names, domainset_name)

    output_path = os.path.join(output_dir, output_filename)

    # 写入输出文件（rule-set 格式）
    print(f"\n[7] 写入输出文件: {output_path}")
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# 规则合并与提取结果\n")
            f.write(f"# 前者文件: {DOMAINSET_URL}\n")
            f.write(f"# 后者文件: {', '.join(RULESET_URLS)}\n")
            f.write(f"# 自定义规则数: {custom_total}\n")
            f.write(f"# 前者规则总数: {total_rules}\n")
            f.write(f"# 筛选后规则数: {total_covered}\n")
            f.write(f"# 覆盖率: {total_covered / total_rules * 100:.2f}%\n")
            f.write(f"#\n")

            # 写入精确匹配规则
            for rule, rule_type in covered_exact:
                f.write(f"{rule_type},{rule}\n")

            # 写入后缀匹配规则
            for rule, rule_type in covered_suffix:
                f.write(f"{rule_type},{rule}\n")

        print(f"    成功写入 {total_covered} 条规则")
    except IOError as e:
        print(f"[错误] 写入文件失败: {e}")
        sys.exit(1)

    elapsed_time = time.time() - start_time

    print("\n" + "=" * 60)
    print("处理完成!")
    print("=" * 60)

    print(f"\n统计信息:")
    print(f"  前者规则总数: {total_rules}")
    print(f"  自定义规则数: {custom_total}")
    print(f"  筛选后规则数: {total_covered}")
    print(f"  覆盖率: {total_covered / total_rules * 100:.2f}%")
    print(f"  处理耗时: {elapsed_time:.2f} 秒")
    print(f"  输出文件: {output_path}")


if __name__ == "__main__":
    main()
