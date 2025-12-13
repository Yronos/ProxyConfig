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
        原始文件存放在 ./auto/original
        过滤后文件存放在 ./auto/new
        """
        # 获取脚本所在目录
        self.script_dir = os.path.dirname(os.path.abspath(__file__))

        # 设置子目录路径
        self.original_dir = os.path.join(self.script_dir, "original")
        self.new_dir = os.path.join(self.script_dir, "new")

        # 常见国家/地区顶级域名后缀
        self.regional_tlds = {
            # 国家代码顶级域名
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
            "ws",
            "to",
            "vu",
            "sb",
            "ki",
            "nr",
            "tv",
            "pw",
            "mh",
            "fm",
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
            "co",
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
            "me",
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
        }

        # 确保目录存在
        os.makedirs(self.original_dir, exist_ok=True)
        os.makedirs(self.new_dir, exist_ok=True)

    def download_rule_list(self, url):
        """下载规则列表到original文件夹"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            # 从URL中提取文件名
            filename = os.path.basename(urlparse(url).path)
            if not filename:
                filename = "rules.list"

            filepath = os.path.join(self.original_dir, filename)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response.text)

            print(f"  ✓ 已下载: {filename}")
            return filepath, filename

        except Exception as e:
            print(f"  ✗ 下载失败: {e}")
            return None, None

    def parse_header(self, lines):
        """
        解析文件头部信息
        返回: (header_lines, header_info, content_start_index)
        """
        header_lines = []
        header_info = {}
        content_start = 0

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("#"):
                header_lines.append(line)

                # 解析头部信息
                if ":" in stripped:
                    parts = stripped[1:].split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        header_info[key] = value
            else:
                # 遇到第一个非注释行，头部结束
                content_start = idx
                break

        return header_lines, header_info, content_start

    def count_rule_types(self, lines, start_index=0):
        """
        统计各类规则的数量
        """
        counts = defaultdict(int)

        for line in lines[start_index:]:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            # 识别规则类型
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
        """
        生成更新后的文件头部
        """
        header_lines = []

        # 保留原有的NAME, AUTHOR, REPO
        if "NAME" in header_info:
            header_lines.append(f"# NAME: {header_info['NAME']}\n")

        # 更新时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header_lines.append(f"# UPDATED: {current_time}\n")

        # 添加规则统计（按字母顺序）
        total = 0
        for rule_type in sorted(rule_counts.keys()):
            count = rule_counts[rule_type]
            total += count
            header_lines.append(f"# {rule_type}: {count}\n")

        # 总计
        header_lines.append(f"# TOTAL: {total}\n")

        return header_lines

    def extract_domain_from_line(self, line):
        """从规则行中提取域名和规则类型"""
        line = line.strip()

        # 跳过注释和空行
        if not line or line.startswith("#"):
            return None, None

        # 处理不同的规则格式
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
        例如：
        youtube.az -> youtube
        youtube.com -> youtube
        ggpht.cn -> ggpht
        www.youtube.com -> youtube
        """
        if not domain:
            return None

        # 移除 www. 前缀
        domain = re.sub(r"^www\.", "", domain)

        # 分割域名
        parts = domain.split(".")

        if len(parts) < 2:
            return domain

        # 如果最后一个部分是区域性TLD，返回倒数第二个部分
        if parts[-1] in self.regional_tlds:
            return parts[-2] if len(parts) >= 2 else domain

        # 对于通用TLD (com, org, net等)，也返回倒数第二个部分
        common_tlds = {
            "com",
            "org",
            "net",
            "edu",
            "gov",
            "mil",
            "int",
            "info",
            "biz",
            "io",
        }
        if parts[-1] in common_tlds:
            return parts[-2] if len(parts) >= 2 else domain

        # 其他情况返回倒数第二个部分
        return parts[-2] if len(parts) >= 2 else domain

    def is_regional_variant(self, domain):
        """
        判断域名是否是区域性变体
        """
        if not domain:
            return False

        parts = domain.split(".")
        if len(parts) < 2:
            return False

        # 检查TLD是否是国家/地区代码
        tld = parts[-1]
        return tld in self.regional_tlds

    def filter_rules(self, input_file, output_file, threshold=5):
        """过滤规则文件，移除区域性域名变体"""
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                lines = f.readlines()

            # 解析文件头部
            header_lines, header_info, content_start = self.parse_header(lines)

            # 第一遍：分析域名，统计每个基础域名的区域性变体数量
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
                if count <= 10:
                    for domain, _ in base_domain_variants[base_domain][:5]:
                        symbol = (
                            "    ├─"
                            if base_domain in base_domains_to_filter
                            else "    ├─"
                        )
                        print(f"{symbol} {domain}")
                    if count > 5:
                        print(f"    └─ ... 还有 {count - 5} 个")

            # 第二遍：过滤规则
            filtered_lines = []
            removed_count = 0
            removed_domains = []

            for idx, line in enumerate(lines):
                # 跳过头部（头部会重新生成）
                if idx < content_start:
                    continue

                # 保留非域名规则
                if idx not in domain_info:
                    filtered_lines.append(line)
                    continue

                domain, rule_type, is_regional = domain_info[idx]
                base_domain = self.get_base_domain(domain)

                # 过滤区域性变体
                if is_regional and base_domain in base_domains_to_filter:
                    removed_count += 1
                    removed_domains.append(domain)
                    continue

                filtered_lines.append(line)

            # 统计过滤后的规则数量
            rule_counts = self.count_rule_types(filtered_lines)

            # 生成新的头部
            new_header = self.generate_header(header_info, rule_counts)

            # 写入过滤后的文件
            with open(output_file, "w", encoding="utf-8") as f:
                f.writelines(new_header)
                f.writelines(filtered_lines)

            print(f"\n  📊 处理统计:")
            print(f"    • 原始规则数: {len(lines) - content_start}")
            print(f"    • 过滤后规则: {len(filtered_lines)}")
            print(f"    • 已移除规则: {removed_count}")
            print(
                f"    • 保留比例: {len(filtered_lines) / (len(lines) - content_start) * 100:.1f}%"
            )

            if removed_domains and len(removed_domains) <= 20:
                print(f"\n  🗑️  移除的域名示例 (前 {min(len(removed_domains), 20)} 个):")
                for i, domain in enumerate(removed_domains[:20], 1):
                    print(f"    {i:2d}. {domain}")
                if len(removed_domains) > 20:
                    print(f"    ... 还有 {len(removed_domains) - 20} 个域名被移除")

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

        # 下载
        input_file, filename = self.download_rule_list(url)
        if not input_file:
            return False

        # 过滤
        output_file = os.path.join(self.new_dir, filename)
        success = self.filter_rules(input_file, output_file, threshold)

        if success:
            print(f"\n✅ 处理完成!")
            print(f"📁 原始文件: {os.path.relpath(input_file)}")
            print(f"📁 输出文件: {os.path.relpath(output_file)}")
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
            results.append((url, success))

        # 汇总结果
        print(f"\n{'=' * 70}")
        print(f"📊 批量处理完成汇总")
        print(f"{'=' * 70}")
        success_count = sum(1 for _, success in results if success)
        fail_count = len(results) - success_count

        print(f"✅ 成功: {success_count} 个")
        print(f"❌ 失败: {fail_count} 个")
        print(f"📈 成功率: {success_count / len(results) * 100:.1f}%")

        print(f"\n详细结果:")
        for url, success in results:
            status = "✅" if success else "❌"
            filename = os.path.basename(urlparse(url).path)
            print(f"  {status} {filename}")

        return results


# 使用示例
if __name__ == "__main__":
    print("=" * 70)
    print("🔧 域名规则过滤工具")
    print("=" * 70)
    print("📝 功能: 剔除区域性域名变体，保留通用域名")
    print("=" * 70)

    # 初始化过滤器（自动使用 ./auto/original 和 ./auto/new）
    filter_tool = DomainRuleFilter()

    # 单个URL处理
    # url = "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/YouTube/YouTube.list"
    # filter_tool.process_url(url, threshold=5)

    # 批量处理多个URL示例
    urls = [
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/YouTube/YouTube.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Facebook/Facebook.list",
        "https://raw.githubusercontent.com/blackmatrix7/ios_rule_script/refs/heads/master/rule/Clash/Google/Google.list",
    ]
    filter_tool.process_urls(urls, threshold=5)

    print("\n" + "=" * 70)
    print("✨ 程序执行完毕")
    print("=" * 70)
