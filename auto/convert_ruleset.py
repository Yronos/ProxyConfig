#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Domain-Set 转 Rule-Set 格式转换工具
将 .domain 格式转换为 DOMAIN-SUFFIX，普通域名转换为 DOMAIN
"""

import argparse
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import requests

# 获取脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# 默认输出目录为脚本同级的 rule-set 文件夹
DEFAULT_OUTPUT_DIR = os.path.join(SCRIPT_DIR, "rule-set")


def download_content(url: str, timeout: int = 30) -> str:
    """下载文件内容"""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[错误] 下载失败 {url}: {e}")
        return ""


def convert_line(line: str) -> str | None:
    """
    转换单行内容
    - 以 . 开头 → DOMAIN-SUFFIX
    - 普通域名 → DOMAIN
    - 注释/空行 → 跳过
    """
    line = line.strip()

    # 跳过空行和注释
    if not line or line.startswith("#") or line.startswith("//"):
        return None

    # 以点开头，转换为 DOMAIN-SUFFIX
    if line.startswith("."):
        domain = line[1:]  # 去掉开头的点
        return f"DOMAIN-SUFFIX,{domain}"
    else:
        # 普通域名，转换为 DOMAIN
        return f"DOMAIN,{line}"


def convert_content(content: str) -> list[str]:
    """转换整个文件内容"""
    results = []
    for line in content.splitlines():
        converted = convert_line(line)
        if converted:
            results.append(converted)
    return results


def process_url(url: str, output_dir: str = DEFAULT_OUTPUT_DIR) -> dict:
    """处理单个 URL"""
    print(f"[处理中] {url}")

    # 下载内容
    content = download_content(url)
    if not content:
        return {"url": url, "success": False, "count": 0}

    # 转换格式
    converted_lines = convert_content(content)

    # 生成输出文件名（保持原文件名不变）
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)  # 直接使用原文件名
    output_path = os.path.join(output_dir, filename)

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 写入文件
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# 转换自: {url}\n")
        f.write(f"# 规则数量: {len(converted_lines)}\n\n")
        f.write("\n".join(converted_lines))
        f.write("\n")  # 文件末尾添加换行

    print(f"[完成] {output_path} ({len(converted_lines)} 条规则)")
    return {
        "url": url,
        "success": True,
        "count": len(converted_lines),
        "output": output_path,
    }


def batch_convert(
    urls: list[str], output_dir: str = DEFAULT_OUTPUT_DIR, max_workers: int = 5
):
    """批量转换多个 URL"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_url, url, output_dir): url for url in urls}

        for future in as_completed(futures):
            result = future.result()
            results.append(result)

    # 打印汇总
    print("\n" + "=" * 50)
    print("转换汇总:")
    success_count = sum(1 for r in results if r["success"])
    total_rules = sum(r["count"] for r in results)
    print(f"成功: {success_count}/{len(urls)}")
    print(f"总规则数: {total_rules}")
    print(f"输出目录: {output_dir}")

    return results


def merge_all(
    output_dir: str = DEFAULT_OUTPUT_DIR, merged_filename: str = "merged.conf"
):
    """合并所有转换后的文件"""
    merged_path = os.path.join(output_dir, merged_filename)
    all_rules = set()  # 使用 set 去重

    for filename in os.listdir(output_dir):
        if filename.endswith(".conf") and filename != merged_filename:
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        all_rules.add(line)

    # 排序并写入
    sorted_rules = sorted(all_rules)
    with open(merged_path, "w", encoding="utf-8") as f:
        f.write(f"# 合并后的规则集\n")
        f.write(f"# 总规则数: {len(sorted_rules)}\n\n")
        f.write("\n".join(sorted_rules))
        f.write("\n")

    print(f"[合并完成] {merged_path} ({len(sorted_rules)} 条规则)")


def main():
    parser = argparse.ArgumentParser(description="Domain-Set 转 Rule-Set 格式转换工具")
    parser.add_argument("-u", "--urls", nargs="+", help="要转换的 URL 列表")
    parser.add_argument("-f", "--file", help="包含 URL 列表的文件（每行一个 URL）")
    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT_DIR,
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument("-m", "--merge", action="store_true", help="合并所有输出文件")
    parser.add_argument(
        "-w", "--workers", type=int, default=5, help="并发下载数 (默认: 5)"
    )

    args = parser.parse_args()

    urls = []

    # 从命令行参数获取 URL
    if args.urls:
        urls.extend(args.urls)

    # 从文件获取 URL
    if args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    urls.append(line)

    if not urls:
        # 默认 URL 列表（示例）
        urls = [
            "https://ruleset.skk.moe/List/domainset/apple_cdn.conf",
            "https://ruleset.skk.moe/List/domainset/cdn.conf",
            "https://ruleset.skk.moe/List/domainset/download.conf",
            "https://ruleset.skk.moe/List/domainset/reject.conf",
        ]
        print("[提示] 未指定 URL，使用默认示例 URL")

    # 执行转换
    batch_convert(urls, args.output, args.workers)

    # 合并文件
    if args.merge:
        merge_all(args.output)


if __name__ == "__main__":
    main()
