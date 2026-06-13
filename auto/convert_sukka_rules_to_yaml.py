#!/usr/bin/env python3
"""
Convert Sukka ruleset TXT files to mihomo YAML format.
Supports domain and IP CIDR rules in mixed payload (mihomo compatible).
"""

import os
import sys
from pathlib import Path

# 域名规则类型
DOMAIN_TYPES = {
    "DOMAIN",
    "HOST",
    "DOMAIN-SUFFIX",
    "HOST-SUFFIX",
    "DOMAIN-KEYWORD",
    "HOST-KEYWORD",
    "DOMAIN-WILDCARD",
}

# IP 规则类型
IPCIDR_TYPES = {
    "IP-CIDR",
    "IP-CIDR6",
    "IP6-CIDR",
}

# 支持的规则类型（域名 + IP 可以混写在同一个 payload）
SUPPORTED_TYPES = DOMAIN_TYPES | IPCIDR_TYPES

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
    "this_ruleset_is_made_by_sukkaw",
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


def convert_txt_to_yaml(txt_file):
    """将单个 TXT 文件转换为 YAML 格式（domain 和 IP 混写）"""
    rules = []
    unsupported = []
    seen = set()
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
                    if domain and domain not in seen:
                        rules.append(domain)
                        seen.add(domain)
                    continue

                # 格式 2: 标准 Clash 格式 (TYPE,value[,options])
                if "," in original_line:
                    parts = [p.strip() for p in original_line.split(",")]
                    if len(parts) >= 2:
                        rule_type = parts[0].upper()
                        value = parts[1].strip('"').strip("'")

                        if not value:
                            continue

                        # 支持的规则类型（domain 和 IP 都放在一起）
                        if rule_type in SUPPORTED_TYPES:
                            if value not in seen:
                                rules.append(value)
                                seen.add(value)
                        # 不支持的规则类型
                        elif rule_type in SKIP_TYPES:
                            unsupported_line = f"{rule_type}: {value}"
                            if unsupported_line not in unsupported_seen:
                                unsupported.append(unsupported_line)
                                unsupported_seen.add(unsupported_line)
                    continue

                # 格式 3: 纯域名或 IP CIDR（domainset 中的纯域名/IP）
                if "." in original_line and " " not in original_line:
                    if original_line not in seen:
                        rules.append(original_line)
                        seen.add(original_line)

        # 生成 YAML 文件（domain 和 IP 混写在一个文件）
        if rules:
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
                for rule in rules:
                    f.write(f"  - '{rule}'\n")

            print(f"✅ {txt_file.name}: {len(rules)} rules")
            return 1, len(rules)
        else:
            return 0, 0

    except Exception as e:
        print(f"⚠️ Failed: {txt_file.name}: {e}", file=sys.stderr)
        return 0, 0


def main():
    """主函数：递归扫描当前目录及所有子目录的 TXT 文件并转换"""
    # 递归查找所有 .txt 文件
    txt_files = sorted(Path(".").rglob("*.txt"))

    if not txt_files:
        print(
            f"ERROR: No TXT files found in {os.getcwd()} (including subdirectories)",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"📝 Found {len(txt_files)} TXT files across all subdirectories")

    total_converted = 0
    total_rules = 0
    skipped = 0

    for txt_file in txt_files:
        # 显示相对路径以便识别来源
        relative_path = txt_file.relative_to(".")
        print(f"\n📄 Processing: {relative_path}")

        converted, rules = convert_txt_to_yaml(txt_file)
        total_converted += converted
        total_rules += rules
        if converted == 0:
            skipped += 1

    print(f"\n{'=' * 60}")
    print(f"✅ Converted {total_converted} rule files ({total_rules} total rules)")
    if skipped > 0:
        print(f"⚠️ Skipped {skipped} files")

    if total_converted == 0:
        print("ERROR: No files were successfully converted!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
