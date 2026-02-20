#!/usr/bin/env python3
"""
广告拦截列表精简工具（白名单模式）
- 仅保留指定 TLD 后缀的规则，其余全部丢弃
- 输入：domainset 格式（.example.com / example.com）
- 输出：DOMAIN-SUFFIX,example.com / DOMAIN,example.com
- 输出路径：./rules/lite/reject.list
"""

import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ──────────────────────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────────────────────

SOURCE_URL = "https://ruleset.skk.moe/List/domainset/reject.conf"
OUTPUT_PATH = Path("./rules/lite/reject.list")

# 【白名单】只有在此列表中的 TLD 才会被保留
KEEP_TLDS = {
    "cn",
    # 通用顶级域
    "com",
    "net",
    "org",
    # "edu",
    # "gov",
    # 科技 / 互联网常用
    "io",
    "ai",
    # "app",
    # "dev",
    # "api",
    # 商业常用
    # "co",
    # "inc",
    # "ltd",
    # "online"
    # 媒体 / 内容
    # "tv",
    # "media",
    # "news",
    # 其他主流
    # "info",
    # "tech",
    # "cloud",
    # 常见二级域（大公司会用）
    "com.cn",
}

# ──────────────────────────────────────────────────────────────
# 核心函数
# ──────────────────────────────────────────────────────────────


def fetch(url: str) -> list[str]:
    """下载远程文件，携带浏览器 UA 绕过 403。"""
    print(f"[*] 正在下载: {url}")
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8").splitlines()


def get_tld(domain: str) -> str | None:
    """
    检查域名的 TLD 是否在白名单中。
    优先匹配两级后缀（如 co.uk），再匹配单级。
    返回匹配到的 TLD，或 None（不在白名单）。
    """
    parts = domain.lower().split(".")
    if len(parts) >= 3:
        two = ".".join(parts[-2:])
        if two in KEEP_TLDS:
            return two
    if len(parts) >= 2:
        one = parts[-1]
        if one in KEEP_TLDS:
            return one
    return None


def parse_line(raw: str) -> tuple[str, str] | None:
    """
    解析 domainset 一行，返回 (rule_type, domain) 或 None（注释/空行）。
    - ".example.com"  → ("DOMAIN-SUFFIX", "example.com")
    - "example.com"   → ("DOMAIN",        "example.com")
    """
    line = raw.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith("."):
        return ("DOMAIN-SUFFIX", line[1:])
    return ("DOMAIN", line)


def build_header(
    source: str, total: int, kept_count: int, removed_count: int, tld_counter: Counter
) -> str:
    """构建写入文件开头的统计注释块。"""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    top_tlds = tld_counter.most_common(20)

    lines = [
        "################################################################################",
        f"# Generated : {now}",
        f"# Source    : {source}",
        f"# Mode      : ALLOWLIST (only listed TLDs are kept)",
        f"# Total     : {total}",
        f"# Kept      : {kept_count}",
        f"# Removed   : {removed_count}",
        "#",
        "# Removed breakdown (Top 20 TLDs):",
    ]
    for tld, count in top_tlds:
        lines.append(f"#   .{tld:<24} {count}")
    lines.append(
        "################################################################################"
    )
    return "\n".join(lines) + "\n"


def process(source: str, output: Path) -> None:
    # ── 读取 ──
    if source.startswith("http://") or source.startswith("https://"):
        raw_lines = fetch(source)
    else:
        raw_lines = Path(source).read_text(encoding="utf-8").splitlines()

    total = sum(1 for l in raw_lines if l.strip() and not l.strip().startswith("#"))
    print(f"[*] 原始规则数: {total}")

    # ── 过滤 ──
    kept: list[str] = []
    removed_tlds: list[str] = []

    for raw in raw_lines:
        parsed = parse_line(raw)

        # 注释 / 空行：跳过，不写入输出文件
        if parsed is None:
            continue

        rule_type, domain = parsed
        tld = get_tld(domain)

        if tld:
            # 在白名单中 → 保留
            kept.append(f"{rule_type},{domain}")
        else:
            # 不在白名单中 → 移除，记录其 TLD 用于统计
            parts = domain.lower().split(".")
            removed_tlds.append(parts[-1] if len(parts) >= 1 else domain)

    # ── 写出 ──
    output.parent.mkdir(parents=True, exist_ok=True)

    tld_counter = Counter(removed_tlds)
    header = build_header(source, total, len(kept), len(removed_tlds), tld_counter)

    with output.open("w", encoding="utf-8") as f:
        f.write(header)
        for line in kept:
            f.write(line + "\n")

    # ── 终端统计 ──
    print(f"[✓] 保留规则数: {len(kept)}")
    print(f"[✗] 移除规则数: {len(removed_tlds)}")
    print(f"[*] 结果已写入: {output}")

    if removed_tlds:
        print("\n── 移除统计（按 TLD，Top 20）──")
        for tld, count in tld_counter.most_common(20):
            print(f"  .{tld:<24} {count} 条")


# ──────────────────────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    source = sys.argv[1] if len(sys.argv) >= 2 else SOURCE_URL
    output = Path(sys.argv[2]) if len(sys.argv) >= 3 else OUTPUT_PATH
    process(source, output)
