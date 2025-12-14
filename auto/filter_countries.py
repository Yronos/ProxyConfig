import os
import re
from collections import defaultdict
from datetime import datetime
from urllib.parse import urlparse

import requests


class DomainRuleFilter:
    def __init__(self):
        """
        初始化过滤器
        脚本位于 ./auto 目录
        原始文件存放在 ./auto/original/{rule_type}
        过滤后文件存放在 ./auto/new/{rule_type}
        """
        # 获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # 设置基础目录路径
        self.original_base_dir = os.path.join(self.script_dir, "original")
        self.new_base_dir = os.path.join(self.script_dir, "new")

        # 规则类型映射表（URL路径关键字 -> 目录名）
        self.rule_type_mapping = {
            "clash": "mihomo",
            "mihomo": "mihomo",
            "loon": "loon",
            "surge": "surge",
            "quantumultx": "quantumultx",
            "quantumult": "quantumult",
            "shadowrocket": "shadowrocket",
            "stash": "stash",
            "egern": "egern",
            "singbox": "singbox",
            "sing-box": "singbox",
        }

        # 二级域名标识集合
        self.second_level_indicators = {
            "com",
            # "co",
            "net",
            "org",
            "gov",
            "edu",
            "ac",
            "mil",
            "nom",
            "sch",
            "gob",
            "int",
        }

        # 【重要】具有特殊意义的ccTLD（虽然是国家代码，但被广泛用作通用域名）
        # 这些不应被视为区域变体
        self.special_purpose_cctlds = {
            "io",  # 科技/初创公司（英属印度洋领地）
            "ai",  # AI/人工智能（安圭拉）
            "co",  # .com的替代品（哥伦比亚）
            "gg",  # 游戏/社区（根西岛）
            "tv",  # 视频/媒体（图瓦卢）
            "me",  # 个人品牌（黑山）
            "fm",  # 音频/广播（密克罗尼西亚）
            "cc",  # 通用用途（科科斯群岛）
            "ws",  # 网站服务（萨摩亚）
            "to",  # URL缩短（汤加）
            "sh",  # Shell/开发（圣赫勒拿）
            "nu",  # 通用（纽埃）
            "tk",  # 免费域名（托克劳）
        }

        # 通用顶级域名
        self.generic_tlds = {
            "com",
            "org",
            "net",
            "edu",
            "gov",
            "mil",
            "int",
            "info",
            "biz",
            "app",
            "dev",
            "xyz",
            "online",
            "site",
            "tech",
            "store",
            "club",
            "top",
            "vip",
            "pro",
            "ventures",
            "wiki",
            "ink",
            "link",
            "work",
            "today",
            "world",
            "life",
            "space",
            "solutions",
        }

        # 真正的区域性顶级域名（排除特殊用途ccTLD）
        self.regional_tlds = {
            "us",
            "uk",
            "cn",
            "jp",
            "kr",
            "de",
            "fr",
            "ca",
            "au",
            "in",
            "br",
            "ru",
            "it",
            "es",
            "nl",
            "se",
            "ch",
            "mx",
            "ar",
            "tw",
            "hk",
            "sg",
            "my",
            "th",
            "id",
            "ph",
            "vn",
            "za",
            "ae",
            "sa",
            "eg",
            "pk",
            "bd",
            "ng",
            "ke",
            "gh",
            "tn",
            "ma",
            "dz",
            "iq",
            "af",
            "ye",
            "sy",
            "jo",
            "lb",
            "kw",
            "om",
            "qa",
            "bh",
            "il",
            "ps",
            "tr",
            "ir",
            "kz",
            "uz",
            "tm",
            "tj",
            "kg",
            "mn",
            "np",
            "lk",
            "mm",
            "kh",
            "la",
            "bn",
            "bt",
            "mv",
            "fj",
            "pg",
            "nc",
            "pf",
            "ck",
            "vu",
            "sb",
            "ki",
            "nr",
            "pw",
            "mh",
            "mp",
            "gu",
            "as",
            "vi",
            "pr",
            "do",
            "cu",
            "jm",
            "ht",
            "bs",
            "bb",
            "tt",
            "gy",
            "sr",
            "gf",
            "ve",
            "ec",
            "pe",
            "bo",
            "py",
            "uy",
            "cl",
            "cr",
            "pa",
            "ni",
            "hn",
            "sv",
            "gt",
            "bz",
            "cz",
            "sk",
            "pl",
            "hu",
            "ro",
            "bg",
            "hr",
            "si",
            "ba",
            "rs",
            "mk",
            "al",
            "gr",
            "cy",
            "mt",
            "is",
            "ie",
            "pt",
            "dk",
            "no",
            "fi",
            "ee",
            "lv",
            "lt",
            "by",
            "ua",
            "md",
            "ge",
            "am",
            "az",
            "at",
            "be",
            "lu",
            "li",
            "mc",
            "ad",
            "sm",
            "va",
            "nz",
            "tl",
            "sc",
            "mu",
            "re",
            "yt",
            "km",
            "mg",
            "mw",
            "zm",
            "zw",
            "bw",
            "na",
            "sz",
            "ls",
            "ao",
            "mz",
            "tz",
            "ug",
            "rw",
            "bi",
            "et",
            "er",
            "dj",
            "so",
            "sd",
            "ss",
            "td",
            "cf",
            "cm",
            "gq",
            "ga",
            "cg",
            "cd",
            "st",
            "gw",
            "gm",
            "sn",
            "mr",
            "ml",
            "bf",
            "ne",
            "ci",
            "tg",
            "bj",
            "lr",
            "sl",
            "cv",
            "ag",
            "dm",
            "gi",
            "gl",
            "im",
            "je",
            "ly",
            "pn",
            "vc",
            "vg",
        }

        # 确保基础目录存在
        os.makedirs(self.original_base_dir, exist_ok=True)
        os.makedirs(self.new_base_dir, exist_ok=True)

    def detect_rule_type(self, url):
        """从URL中检测规则类型"""
        url_lower = url.lower()

        for keyword, directory in self.rule_type_mapping.items():
            pattern = f"/{keyword}/"
            if pattern in url_lower:
                return directory

        return "unknown"

    def get_directories_for_rule_type(self, rule_type):
        """根据规则类型获取对应的原始和输出目录"""
        original_dir = os.path.join(self.original_base_dir, rule_type)
        new_dir = os.path.join(self.new_base_dir, rule_type)

        os.makedirs(original_dir, exist_ok=True)
        os.makedirs(new_dir, exist_ok=True)

        return original_dir, new_dir

    def download_rule_list(self, url):
        """下载规则列表到对应的original子文件夹"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            rule_type = self.detect_rule_type(url)
            print(f"  🔍 检测到规则类型: {rule_type}")

            original_dir, _ = self.get_directories_for_rule_type(rule_type)

            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = "rules.list"

            filepath = os.path.join(original_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"  ✓ 已下载: {filename}")
            print(f"  📁 保存路径: {os.path.relpath(filepath)}")
            return filepath, filename, rule_type

        except Exception as e:
            print(f"  ✗ 下载失败: {e}")
            return None, None, None

    def parse_header(self, lines):
        """解析文件头部信息"""
        header_lines = []
        header_info = {}
        content_start = 0

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                header_lines.append(line)

                if ":" in stripped:
                    parts = stripped[1:].split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        header_info[key] = value
            else:
                content_start = idx
                break

        return header_lines, header_info, content_start

    def count_rule_types(self, lines, start_index=0):
        """统计各类规则的数量"""
        counts = defaultdict(int)

        for line in lines[start_index:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if stripped.startswith("DOMAIN-SUFFIX,"):
                counts["DOMAIN-SUFFIX"] += 1
            elif stripped.startswith("DOMAIN-KEYWORD,"):
                counts["DOMAIN-KEYWORD"] += 1
            elif stripped.startswith("DOMAIN,"):
                counts["DOMAIN"] += 1
            elif stripped.startswith("IP-CIDR6,"):
                counts["IP-CIDR6"] += 1
            elif stripped.startswith("IP-CIDR,"):
                counts["IP-CIDR"] += 1
            elif stripped.startswith("IP6-CIDR,"):
                counts["IP-CIDR6"] += 1
            elif stripped.startswith("USER-AGENT,"):
                counts["USER-AGENT"] += 1
            elif stripped.startswith("URL-REGEX,"):
                counts["URL-REGEX"] += 1
            elif stripped.startswith("PROCESS-NAME,"):
                counts["PROCESS-NAME"] += 1

        return counts

    def generate_header(self, header_info, rule_counts):
        """生成更新后的文件头部"""
        header_lines = []

        if "NAME" in header_info:
            header_lines.append(f"# NAME: {header_info['NAME']}\n")

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_lines.append(f"# UPDATED: {current_time}\n")

        total = 0
        for rule_type in sorted(rule_counts.keys()):
            count = rule_counts[rule_type]
            total += count
            header_lines.append(f"# {rule_type}: {count}\n")

        header_lines.append(f"# TOTAL: {total}\n")

        return header_lines

    def extract_domain_from_line(self, line):
        """从规则行中提取域名和规则类型"""
        line = line.strip()

        if not line or line.startswith("#"):
            return None, None

        patterns = [
            (r"DOMAIN-SUFFIX,([^,\s]+)", "DOMAIN-SUFFIX"),
            (r"DOMAIN,([^,\s]+)", "DOMAIN"),
            (r"DOMAIN-KEYWORD,([^,\s]+)", "DOMAIN-KEYWORD"),
        ]

        for pattern, rule_type in patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1).lower(), rule_type

        return None, None

    def get_base_domain(self, domain):
        """
        提取基础域名（主域名）

        正确处理各种域名格式：
        1. 二级国家域名：google.com.ag → google
        2. 二级国家域名：google.co.uk → google
        3. 国家顶级域名：google.cn → google
        4. 通用顶级域名：google.com → google
        5. 特殊用途ccTLD：google.io → google （不视为区域变体）
        6. 新通用TLD：google.dev → google
        """
        if not domain:
            return None

        # 移除 www. 前缀
        domain = re.sub(r"^www\.", "", domain)

        # 分割域名
        parts = domain.split(".")

        if len(parts) < 2:
            return domain

        # 处理二级国家域名（如 google.com.ag, google.co.uk）
        if len(parts) >= 3:
            tld = parts[-1]
            sld = parts[-2]

            # 如果是"二级标识.国家代码"的组合，返回主域名
            if tld in self.regional_tlds and sld in self.second_level_indicators:
                return parts[-3] if len(parts) >= 3 else parts[0]

        # 处理普通国家顶级域名（如 google.cn）
        if parts[-1] in self.regional_tlds:
            return parts[-2] if len(parts) >= 2 else domain

        # 处理特殊用途ccTLD（如 google.io, google.ai）
        if parts[-1] in self.special_purpose_cctlds:
            return parts[-2] if len(parts) >= 2 else domain

        # 处理通用顶级域名（如 google.com, google.dev）
        if parts[-1] in self.generic_tlds:
            return parts[-2] if len(parts) >= 2 else domain

        # 其他情况，返回倒数第二个部分
        return parts[-2] if len(parts) >= 2 else domain

    def is_regional_variant(self, domain):
        """
        判断域名是否是区域性变体

        区域变体包括：
        1. 二级国家域名：youtube.com.co, google.co.uk （优先级最高）
        2. 国家顶级域名：google.cn, google.jp

        不包括：
        1. 特殊用途ccTLD：google.co, github.io, discord.gg
        2. 通用TLD：google.com, google.org
        3. 新通用TLD：google.dev, google.ventures
        """
        if not domain:
            return False

        parts = domain.split(".")
        if len(parts) < 2:
            return False

        tld = parts[-1]

        # 【关键修复】优先检查二级国家域名结构
        # 例如：.com.co, .co.uk, .com.ag
        if len(parts) >= 3:
            sld = parts[-2]
            # 如果是"二级标识.国家代码"的组合
            # 即使TLD在special_purpose_cctlds中，也视为区域变体
            if sld in self.second_level_indicators and tld in self.regional_tlds:
                return True

        # 检查是否是特殊用途ccTLD（仅对非二级域名生效）
        if tld in self.special_purpose_cctlds:
            return False

        # 检查是否是纯通用TLD
        if tld in self.generic_tlds:
            return False

        # 检查TLD是否是真正的区域性国家代码
        if tld in self.regional_tlds:
            return True

        return False

    def filter_rules(self, input_file, output_file, threshold=5):
        """过滤规则文件，移除区域性域名变体"""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            header_lines, header_info, content_start = self.parse_header(lines)

            # 第一遍：分析域名
            base_domain_variants = defaultdict(list)
            domain_info = {}

            for idx in range(content_start, len(lines)):
                line = lines[idx]
                domain, rule_type = self.extract_domain_from_line(line)
                if domain:
                    base_domain = self.get_base_domain(domain)
                    is_regional = self.is_regional_variant(domain)

                    domain_info[idx] = (domain, rule_type, is_regional)

                    if is_regional and base_domain:
                        base_domain_variants[base_domain].append((domain, idx))

            # 找出需要过滤的基础域名
            base_domains_to_filter = set()
            for base_domain, variants in base_domain_variants.items():
                if len(variants) >= threshold:
                    base_domains_to_filter.add(base_domain)

            print(f"\n  📋 域名变体分析:")
            for base_domain in sorted(base_domain_variants.keys()):
                count = len(base_domain_variants[base_domain])
                if base_domain in base_domains_to_filter:
                    print(f"    🗑️  {base_domain}: {count} 个区域变体 → 将剔除")
                else:
                    print(f"    ✅ {base_domain}: {count} 个区域变体 → 保留")

                # 显示部分域名示例
                display_count = min(10, count)
                for i, (domain, _) in enumerate(
                    base_domain_variants[base_domain][:display_count]
                ):
                    symbol = "    ├─" if i < display_count - 1 else "    └─"
                    print(f"{symbol} {domain}")
                if count > display_count:
                    print(f"       ... 还有 {count - display_count} 个")

            # 第二遍：过滤规则
            filtered_lines = []
            removed_count = 0
            removed_domains = []

            for idx, line in enumerate(lines):
                if idx < content_start:
                    continue

                if idx not in domain_info:
                    filtered_lines.append(line)
                    continue

                domain, rule_type, is_regional = domain_info[idx]
                base_domain = self.get_base_domain(domain)

                if is_regional and base_domain in base_domains_to_filter:
                    removed_count += 1
                    removed_domains.append(domain)
                    continue

                filtered_lines.append(line)

            rule_counts = self.count_rule_types(filtered_lines)
            new_header = self.generate_header(header_info, rule_counts)

            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(new_header)
                f.writelines(filtered_lines)

            print(f"\n  📊 处理统计:")
            print(f"    • 原始规则数: {len(lines) - content_start}")
            print(f"    • 过滤后规则: {len(filtered_lines)}")
            print(f"    • 已移除规则: {removed_count}")
            if len(lines) - content_start > 0:
                print(
                    f"    • 保留比例: {len(filtered_lines) / (len(lines) - content_start) * 100:.1f}%"
                )

            if removed_domains and len(removed_domains) <= 30:
                print(f"\n  🗑️  移除的域名示例 (前 {min(len(removed_domains), 30)} 个):")
                for i, domain in enumerate(removed_domains[:30], 1):
                    print(f"    {i:2d}. {domain}")
                if len(removed_domains) > 30:
                    print(f"    ... 还有 {len(removed_domains) - 30} 个域名被移除")

            return True

        except Exception as e:
            print(f"  ❌ 处理失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def process_url(self, url, threshold=5):
        """处理单个URL"""
        print(f"\n{'=' * 70}")
        print(f"🚀 开始处理规则列表")
        print(f"{'=' * 70}")
        print(f"📎 URL: {url}")
        print(f"🎯 阈值: {threshold} (区域变体数)")

        input_file, filename, rule_type = self.download_rule_list(url)
        if not input_file:
            return False

        _, new_dir = self.get_directories_for_rule_type(rule_type)
        output_file = os.path.join(new_dir, filename)

        success = self.filter_rules(input_file, output_file, threshold)

        if success:
            print(f"\n✅ 处理完成!")
            print(f"📁 原始文件: {os.path.relpath(input_file)}")
            print(f"📁 输出文件: {os.path.relpath(output_file)}")
            print(f"🏷️  规则类型: {rule_type}")
        else:
            print(f"\n❌ 处理失败!")

        return success

    def process_urls(self, urls, threshold=5):
        """批量处理多个URL"""
        print(f"\n{'=' * 70}")
        print(f"🚀 批量处理模式")
        print(f"{'=' * 70}")
        print(f"📦 待处理列表: {len(urls)} 个")
        print(f"🎯 阈值: {threshold}")

        results = []
        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{len(urls)}] 处理中...")
            success = self.process_url(url, threshold)

            rule_type = self.detect_rule_type(url)
            filename = os.path.basename(urlparse(url).path)
            results.append((url, filename, rule_type, success))

        print(f"\n{'=' * 70}")
        print(f"📊 批量处理完成汇总")
        print(f"{'=' * 70}")
        success_count = sum(1 for _, _, _, success in results if success)
        fail_count = len(results) - success_count

        print(f"✅ 成功: {success_count} 个")
        print(f"❌ 失败: {fail_count} 个")
        if len(results) > 0:
            print(f"📈 成功率: {success_count / len(results) * 100:.1f}%")

        print(f"\n详细结果 (按规则类型分组):")
        by_type = defaultdict(list)
        for url, filename, rule_type, success in results:
            by_type[rule_type].append((filename, success))

        for rule_type in sorted(by_type.keys()):
            print(f"\n  📂 {rule_type.upper()}:")
            for filename, success in by_type[rule_type]:
                status = "✅" if success else "❌"
                print(f"    {status} {filename}")

        return results

    def list_directory_structure(self):
        """列出当前的目录结构"""
        print(f"\n{'=' * 70}")
        print(f"📁 当前目录结构")
        print(f"{'=' * 70}")

        for base_name, base_dir in [
            ("原始文件", self.original_base_dir),
            ("处理后文件", self.new_base_dir),
        ]:
            print(f"\n{base_name}: {os.path.relpath(base_dir)}")
            if os.path.exists(base_dir):
                subdirs = [
                    d
                    for d in os.listdir(base_dir)
                    if os.path.isdir(os.path.join(base_dir, d))
                ]
                if subdirs:
                    for subdir in sorted(subdirs):
                        subdir_path = os.path.join(base_dir, subdir)
                        file_count = len(
                            [
                                f
                                for f in os.listdir(subdir_path)
                                if os.path.isfile(os.path.join(subdir_path, f))
                            ]
                        )
                        print(f"  ├─ {subdir}/ ({file_count} 个文件)")
                else:
                    print(f"  └─ (空)")
            else:
                print(f"  └─ (目录不存在)")


# 使用示例
if __name__ == "__main__":
    print("=" * 70)
    print("🔧 域名规则过滤工具")
    print("=" * 70)
    print("📝 功能: 剔除区域性域名变体，保留通用域名")
    print("🎯 特性: 智能识别规则类型并分类存储")
    print("✨ 新增: 支持特殊用途ccTLD（.io, .ai, .gg等）")
    print("=" * 70)

    filter_tool = DomainRuleFilter()

    # 显示目录结构
    filter_tool.list_directory_structure()

    # 批量处理URL
    urls = [
        # Clash/Mihomo 规则
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/YouTube/YouTube.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Google/Google.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Facebook/Facebook.list",
        # Surge 规则
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/YouTube/YouTube.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Google/Google.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Surge/Facebook/Facebook.list",
        # Loon 规则
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Loon/YouTube/YouTube.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Loon/Google/Google.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Loon/Facebook/Facebook.list",
    ]

    filter_tool.process_urls(urls, threshold=5)

    # 处理完成后再次显示目录结构
    filter_tool.list_directory_structure()

    print("\n" + "=" * 70)
    print("✨ 程序执行完毕")
    print("=" * 70)
