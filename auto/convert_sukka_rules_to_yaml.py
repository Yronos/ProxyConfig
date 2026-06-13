#!/usr/bin/env python3
"""
Convert Sukka ruleset TXT files to mihomo YAML format.
Supports domain, IP CIDR, and mixed rule types.
"""

import os
import re
import sys
from pathlib import Path

# 域名规则类型（编译为 domain behavior）
DOMAIN_TYPES = {
    "DOMAIN",
    "HOST",
    "DOMAIN-SUFFIX",
    "HOST-SUFFIX",
    "DOMAIN-KEYWORD",
    "HOST-KEYWORD",
    "DOMAIN-WILDCARD",
}

# IP 规则类型（编译为 ipcidr behavior）
IPCIDR_TYPES = {
    "IP-CIDR",
    "IP-CIDR6",
    "IP6-CIDR",
}

# 不支持的规则类型
SKIP_TYPES = {
    "PROCESS-NAME",
    "PROCESS-PATH",
    "NETWORK",
    "DST-PORT",
    "SRC-PORT",
    "SRC-IP-CIDR",
    "GEOSITE",
    "GEOIP",
    "SRC-GEOIP",
    "IP-ASN",
    "RULE-SET",
    "AND",
    "OR",
    "NOT",
    "MATCH",
}

# Sukka 标记（需要删除）
SUKKA_MARKERS = [
    "7h1s_rul35et_i5_mad3_by_5ukk4w",
    "thisrulesetismadebysukka",
]


def is_sukka_marker(line):
    """检测是否为 Sukka 标记行"""
    line_clean = line.lower().replace("-", "").replace("_", "").replace(".", "")
    for marker in SUKKA_MARKERS:
        marker_clean = marker.lower().replace("-", "").replace("_", "").replace(".", "")
        if marker_clean in line_clean:
            return True
    return False


def is_ip_cidr(value):
    """检测是否为 IP CIDR 格式"""
    # 匹配 IPv4/IPv6 CIDR
    ipv4_pattern = r"^(\d{1,3}\.){3}\d{1,3}/\d{1,2}$"
    ipv6_pattern = r"^([0-9a-fA-F]{0,4}:){2,7}[0-9a-fA-F]{0,4}/\d{1,3}$"
    return bool(re.match(ipv4_pattern, value) or re.match(ipv6_pattern, value))


def convert_txt_to_yaml(txt_file):
    """将单个 TXT 文件转换为 YAML 格式"""
    domain_rules = []
    ipcidr_rules = []
    unsupported = []
    domain_seen = set()
    ipcidr_seen = set()
    unsupported_seen = set()

    try:
        with open(txt_file, "r", encoding="utf-8") as f:
            for line in f:
                original_line = line.strip()

                # 跳过空行和注释
                if not original_line or original_line.startswith("#"):
                    continue

                # 跳过 Sukka 标记
                if is_sukka_marker(original_line):
                    continue

                # 格式 1: domainset 格式 (+.example.com)
                if original_line.startswith("+."):
                    domain = original_line[2:]
                    if domain and domain not in domain_seen:
                        domain_rules.append(domain)
                        domain_seen.add(domain)
                    continue

                # 格式 2: 标准 Clash 格式 (TYPE,value[,options])
                if "," in original_line:
                    parts = [p.strip() for p in original_line.split(",")]
                    if len(parts) >= 2:
                        rule_type = parts[0].upper()
                        value = parts[1].strip('"').strip("'")

                        if not value:
                            continue

                        # 域名类规则
                        if rule_type in DOMAIN_TYPES:
                            if value not in domain_seen:
                                domain_rules.append(value)
                                domain_seen.add(value)
                        # IP CIDR 规则（去除 no-resolve 等参数）
                        elif rule_type in IPCIDR_TYPES:
                            if value not in ipcidr_seen:
                                ipcidr_rules.append(value)
                                ipcidr_seen.add(value)
                        # 不支持的规则类型
                        elif rule_type in SKIP_TYPES:
                            unsupported_line = f"{rule_type}: {value}"
                            if unsupported_line not in unsupported_seen:
                                unsupported.append(unsupported_line)
                                unsupported_seen.add(unsupported_line)
                    continue

                # 格式 3: 纯域名或 IP CIDR（domainset 中的纯域名/IP）
                if "." in original_line and " " not in original_line:
                    # 判断是 IP CIDR 还是域名
                    if is_ip_cidr(original_line):
                        if original_line not in ipcidr_seen:
                            ipcidr_rules.append(original_line)
                            ipcidr_seen.add(original_line)
                    else:
                        if original_line not in domain_seen:
                            domain_rules.append(original_line)
                            domain_seen.add(original_line)

        # 生成 YAML 文件（根据规则类型生成不同文件）
        converted_count = 0
        total_rules = 0

        # 如果有域名规则，生成 domain YAML
        if domain_rules:
            yaml_file = txt_file.with_suffix(".yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                if unsupported:
                    f.write(f"# 不支持的规则 ({len(unsupported)}):\n")
                    for u in unsupported[:10]:  # 最多显示 10 条
                        f.write(f"# - {u}\n")
                    if len(unsupported) > 10:
                        f.write(f"# ... 还有 {len(unsupported) - 10} 条\n")
                    f.write("\n")

                f.write("payload:\n")
                for rule in domain_rules:
                    f.write(f"  - '{rule}'\n")

            # 标记为 domain 类型（用于后续编译）
            meta_file = txt_file.with_suffix(".yaml.meta")
            with open(meta_file, "w", encoding="utf-8") as f:
                f.write("domain\n")

            converted_count += 1
            total_rules += len(domain_rules)
            print(f"✅ {txt_file.name}: {len(domain_rules)} domain rules")

        # 如果有 IP CIDR 规则，生成 ipcidr YAML
        if ipcidr_rules:
            yaml_file = txt_file.with_suffix(".ipcidr.yaml")
            with open(yaml_file, "w", encoding="utf-8") as f:
                f.write("payload:\n")
                for rule in ipcidr_rules:
                    f.write(f"  - '{rule}'\n")

            # 标记为 ipcidr 类型
            meta_file = txt_file.with_suffix(".ipcidr.yaml.meta")
            with open(meta_file, "w", encoding="utf-8") as f:
                f.write("ipcidr\n")

            converted_count += 1
            total_rules += len(ipcidr_rules)
            print(f"✅ {txt_file.name}: {len(ipcidr_rules)} ipcidr rules")

        return converted_count, total_rules

    except Exception as e:
        print(f"⚠️ Failed: {txt_file.name}: {e}", file=sys.stderr)
        return 0, 0


def main():
    """主函数：扫描当前目录的所有 TXT 文件并转换"""
    txt_files = sorted(Path(".").glob("*.txt"))

    if not txt_files:
        print(f"ERROR: No TXT files found in {os.getcwd()}", file=sys.stderr)
        sys.exit(1)

    print(f"📝 Found {len(txt_files)} TXT files")

    total_converted = 0
    total_rules = 0
    skipped = 0

    for txt_file in txt_files:
        converted, rules = convert_txt_to_yaml(txt_file)
        total_converted += converted
        total_rules += rules
        if converted == 0:
            skipped += 1

    print(f"\n✅ Converted {total_converted} rule files ({total_rules} total rules)")
    if skipped > 0:
        print(f"⚠️ Skipped {skipped} files")

    if total_converted == 0:
        print("ERROR: No files were successfully converted!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
