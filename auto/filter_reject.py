#!/usr/bin/env python3
"""
广告拦截列表精简工具
- 过滤国家 ccTLD 及小众 TLD 变体
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

# 常见国家/地区代码 TLD（ccTLD）
COUNTRY_CODE_TLDS = {
    # 亚洲
    # "cn",
    "hk",
    "tw",
    "jp",
    "kr",
    "sg",
    "my",
    "th",
    "vn",
    "ph",
    "id",
    "in",
    "pk",
    "bd",
    "lk",
    "np",
    "mm",
    "kh",
    "la",
    "bn",
    "mn",
    # 欧洲
    "uk",
    "de",
    "fr",
    "it",
    "es",
    "nl",
    "be",
    "ch",
    "at",
    "se",
    "no",
    "dk",
    "fi",
    "pl",
    "cz",
    "sk",
    "hu",
    "ro",
    "bg",
    "hr",
    "si",
    "rs",
    "gr",
    "pt",
    "ie",
    "lu",
    "lt",
    "lv",
    "ee",
    "is",
    "mt",
    "cy",
    "al",
    "ba",
    "mk",
    "me",
    "md",
    "ua",
    "by",
    "ru",
    "tr",
    "ge",
    "am",
    "az",
    # 美洲
    "us",
    "ca",
    "mx",
    "br",
    "ar",
    "cl",
    "co",
    "pe",
    "ve",
    "ec",
    "bo",
    "py",
    "uy",
    "gy",
    "sr",
    "cr",
    "pa",
    "gt",
    "hn",
    "sv",
    "ni",
    "cu",
    # 中东 / 非洲
    "sa",
    "ae",
    "qa",
    "kw",
    "bh",
    "om",
    "jo",
    "lb",
    "il",
    "ir",
    "iq",
    "eg",
    "za",
    "ng",
    "ke",
    "et",
    "tz",
    "gh",
    "ma",
    "dz",
    "tn",
    "ly",
    # 大洋洲
    "au",
    "nz",
    "fj",
    "pg",
    # 其他
    "eu",
    "ac",
    "ag",
    "nu",
    "ao",
    "as",
    "bi",
    "bz",
    "ci",
    "cw",
    "cm",
    "cx",
    "fo",
    "ga",
    "gf",
    "gl",
    "gp",
    "ht",
    "im",
    "tl",
    "tm",
    "tj",
    "tf",
    "tc",
    "sz",
    "su",
    "sx",
    "st",
    "ss",
    "sn",
    "sm",
    "sc",
    "sb",
    "re",
    "pw",
    "pm",
    "pf",
    "nc",
    "na",
    "mz",
    "mw",
    "mu",
    "mq",
    "mp",
    "mo",
    "ml",
    "mg",
    "ls",
    "li",
    "kz",
    "bw",
    "bg",
    "bf",
    "ax"
    # 英国二级域
    "co.uk",
    "org.uk",
    "me.uk",
    "net.uk",
}

# 小众 / 大公司不会使用的 TLD
OBSCURE_TLDS = {
    # 城市 TLD
    "amsterdam",
    "barcelona",
    "berlin",
    "budapest",
    "capetown",
    "chicago",
    "dubai",
    "istanbul",
    "london",
    "madrid",
    "melbourne",
    "miami",
    "milan",
    "moscow",
    "nagoya",
    "nyc",
    "osaka",
    "paris",
    "quebec",
    "rio",
    "rome",
    "sydney",
    "taipei",
    "tokyo",
    "vegas",
    "wien",
    "yokohama",
    "zuerich",
    # 行业小众
    "accountant",
    "accountants",
    "actor",
    "adult",
    "airforce",
    "apartments",
    "auction",
    "audio",
    "author",
    "baby",
    "band",
    "bargains",
    "beer",
    "bible",
    "bingo",
    "black",
    "blackfriday",
    "boats",
    "boo",
    "boutique",
    "broker",
    "build",
    "builders",
    "buzz",
    "cab",
    "cafe",
    "camera",
    "camp",
    "cards",
    "careers",
    "cash",
    "casino",
    "catering",
    "center",
    "chat",
    "cheap",
    "church",
    "city",
    "claims",
    "cleaning",
    "clinic",
    "clothing",
    "club",
    "coach",
    "codes",
    "coffee",
    "community",
    "company",
    "computer",
    "condos",
    "construction",
    "consulting",
    "contractors",
    "cool",
    "coupons",
    "credit",
    "creditcard",
    "cruises",
    "dance",
    "dating",
    "deals",
    "degree",
    "democrat",
    "dental",
    "diamonds",
    "digital",
    "direct",
    "directory",
    "discount",
    "dog",
    "domains",
    "education",
    "email",
    "energy",
    "engineering",
    "equipment",
    "estate",
    "events",
    "exchange",
    "expert",
    "exposed",
    "fail",
    "farm",
    "finance",
    "fish",
    "fitness",
    "flights",
    "florist",
    "flowers",
    "fm",
    "football",
    "forsale",
    "foundation",
    "fund",
    "furniture",
    "gallery",
    "gift",
    "gifts",
    "gives",
    "glass",
    "global",
    "golf",
    "graphics",
    "gripe",
    "guide",
    "guitars",
    "guru",
    "haus",
    "healthcare",
    "hockey",
    "holiday",
    "horse",
    "hospital",
    "house",
    "immo",
    "immobilien",
    "industries",
    "institute",
    "insure",
    "investments",
    "jewelry",
    "juegos",
    "kitchen",
    "land",
    "lease",
    "legal",
    "life",
    "lighting",
    "limited",
    "limo",
    "loans",
    "luxury",
    "maison",
    "management",
    "marketing",
    "mba",
    "media",
    "memorial",
    "money",
    "mortgage",
    "motel",
    "movie",
    "network",
    "news",
    "ninja",
    "partners",
    "parts",
    "photography",
    "photos",
    "pics",
    "pizza",
    "place",
    "plumbing",
    "poker",
    "productions",
    "properties",
    "pub",
    "recipes",
    "rehab",
    "reisen",
    "rentals",
    "repair",
    "republican",
    "restaurant",
    "reviews",
    "rich",
    "rocks",
    "run",
    "sale",
    "salon",
    "school",
    "services",
    "shoes",
    "show",
    "solar",
    "solutions",
    "surgery",
    "systems",
    "tattoo",
    "tax",
    "tires",
    "today",
    "tools",
    "tours",
    "training",
    "university",
    "vacation",
    "ventures",
    "vision",
    "watch",
    "wines",
    "works",
    "wtf",
    "yoga",
    "zone",
    "technology",
    "realestate",
    "bnpparibas",
    "delivery",
    "wedding",
    "christmas",
    "trading",
    "toshiba",
    "realtor",
    "organic",
    "monster",
    "hamburg",
    "fashion",
    "express",
    "dentist",
    "cooking",
    "capital",
    "bauhaus",
    "academy",
    "travel",
    "webcam",
    "supply",
    "sanofi",
    "realty",
    "racing",
    "physio",
    "click",
    "team",
    "icu",
    "cfd",
    "qpon",
    "rent",
    "rest",
    "ruhr",
    "saxo",
    "scot",
    "sexy",
    "shop",
    "skin",
    "sncf",
    "taxi",
    "website",
    "online",
    "space",
    "site",
    "name",
    "mobi",
    "menu",
    "love",
    "hair",
    "gmbh",
    "desi",
    "cyou",
    "pro",
    "lol",
    "law",
    "lat",
    "int",
    "ink",
    "fyi",
    "fun",
    "fox",
    "fit",
    "fan",
    "eus",
    "eco",
    "biz",
    "bid",
    "bio",
    "bet",
    "art",
    # 国家二级域
    # "com.cn",
    # "net.cn",
    # "org.cn",
    # "gov.cn",
    # "edu.cn",
    "com.tw",
    "net.tw",
    "org.tw",
    "com.hk",
    "net.hk",
    "org.hk",
    "co.jp",
    "ne.jp",
    "or.jp",
    "ac.jp",
    "co.kr",
    "ne.kr",
    "or.kr",
    "com.au",
    "net.au",
    "org.au",
    "com.br",
    "net.br",
    "org.br",
    "com.ar",
    "net.ar",
    "com.mx",
    "net.mx",
    "co.in",
    "net.in",
    "org.in",
    "co.id",
    "net.id",
    "co.nz",
    "net.nz",
    "co.za",
    "net.za",
    "co.il",
    "skk.moe",
}

ALL_REMOVE_TLDS = COUNTRY_CODE_TLDS | OBSCURE_TLDS


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
    """优先匹配两级后缀（如 co.uk），再匹配单级。"""
    parts = domain.lower().split(".")
    if len(parts) >= 3:
        two = ".".join(parts[-2:])
        if two in ALL_REMOVE_TLDS:
            return two
    if len(parts) >= 2:
        one = parts[-1]
        if one in ALL_REMOVE_TLDS:
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
        if parsed is None:
            # 注释 / 空行：跳过，不写入输出文件
            continue
        rule_type, domain = parsed
        tld = get_tld(domain)
        if tld:
            removed_tlds.append(tld)
        else:
            kept.append(f"{rule_type},{domain}")
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
