#!/usr/bin/env python3
"""Build selected Anywhere routing rule sets from local and remote sources."""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .converter import convert_lines


MAX_RULES_PER_SET = 100000

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = (REPOSITORY_ROOT / "rules").resolve()
OUTPUT_DIR = (RULES_DIR / "Anywhere").resolve()

ICON_HEADER_RE = re.compile(
    r"^icon-(?:light|dark)\s*=\s*\S+\s*$"
)


RULE_SETS: list[dict[str, object]] = [
    {
        "name": "AI",
        "description": "常见 AI 服务",
        "sources": [
            {
                "type": "remote",
                "url": "https://ruleset.skk.moe/List/non_ip/ai.conf",
            },
            {
                "type": "remote",
                "url": (
                    "https://raw.githubusercontent.com/Repcz/Tool/X/Surge/Custom/AI.list"
                ),
            },
            {
                "type": "local",
                "path": "ProxyHK.list",
            },
        ],
    },
    {
        "name": "Proxy",
        "description": "常用代理域名集合",
        "sources": [
            {
                "type": "remote",
                "url": "https://ruleset.skk.moe/List/non_ip/global.conf",
            },
            {
                "type": "local",
                "path": "lite/Amazon.list",
            },
        ],
    },
    {
        "name": "ForceDirect",
        "description": "ForceDirect rules",
        "routing": 1,
        "sources": [
            {
                "type": "local",
                "path": "ForceDirect.list",
            },
        ],
    },
    {
        "name": "IP_Domestic",
        "description": "China IPv4 and IPv6 rules",
        "routing": 1,
        "sources": [
            {
                "type": "remote",
                "path": "https://raw.githubusercontent.com/SukkaLab/ruleset.skk.moe/refs/heads/master/List/ip/china_ip.conf",
            },
            {
                "type": "remote",
                "path": "https://raw.githubusercontent.com/SukkaLab/ruleset.skk.moe/refs/heads/master/List/ip/china_ipv6.conf",
            },
        ],
    },
]


@dataclass
class BuiltRuleSet:
    name: str
    description: str
    output_path: str
    rule_count: int
    skipped_count: int
    unsupported_types: dict[str, int] = field(
        default_factory=dict
    )
    sources: list[str] = field(default_factory=list)


def request_headers() -> dict[str, str]:
    return {
        "Accept": "text/plain,*/*",
        "User-Agent": "anywhere-rules-builder",
    }


def fetch_bytes(
    url: str,
    retries: int = 4,
    timeout: int = 60,
) -> bytes:
    """Download a remote source with retry and exponential backoff."""
    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            request = Request(
                url,
                headers=request_headers(),
            )

            with urlopen(
                request,
                timeout=timeout,
            ) as response:
                return response.read()

        except (
            HTTPError,
            URLError,
            TimeoutError,
            socket.timeout,
            OSError,
        ) as exc:
            last_error = exc

            if attempt == retries - 1:
                break

            time.sleep(2**attempt)

    raise RuntimeError(
        f"Failed to fetch remote source {url}: {last_error}"
    ) from last_error


def read_local_source(relative_path: str) -> list[str]:
    """Read a local source strictly from rules/."""
    source_path = (RULES_DIR / relative_path).resolve()

    if not source_path.is_relative_to(RULES_DIR):
        raise ValueError(
            f"Local source must stay inside rules/: {relative_path}"
        )

    if source_path.is_relative_to(OUTPUT_DIR):
        raise ValueError(
            "Generated Anywhere files cannot be used as input: "
            f"{relative_path}"
        )

    if not source_path.is_file():
        raise FileNotFoundError(
            f"Local source does not exist: {source_path}"
        )

    return source_path.read_text(
        encoding="utf-8-sig",
        errors="replace",
    ).splitlines()


def read_remote_source(url: str) -> list[str]:
    """Download and decode a remote rule source."""
    if not url.startswith(("https://", "http://")):
        raise ValueError(
            f"Unsupported remote URL: {url}"
        )

    return fetch_bytes(url).decode(
        "utf-8-sig",
        errors="replace",
    ).splitlines()


def load_source(
    source: object,
) -> tuple[list[str], str]:
    """Load one explicitly configured local or remote source."""
    if not isinstance(source, dict):
        raise TypeError(
            "Each source must be a mapping."
        )

    source_type = str(source.get("type", "")).lower()

    if source_type == "local":
        relative_path = str(source.get("path", "")).strip()

        if not relative_path:
            raise ValueError(
                "Local source requires a non-empty path."
            )

        lines = read_local_source(relative_path)

        return lines, f"rules/{Path(relative_path).as_posix()}"

    if source_type == "remote":
        url = str(source.get("url", "")).strip()

        if not url:
            raise ValueError(
                "Remote source requires a non-empty URL."
            )

        return read_remote_source(url), url

    raise ValueError(
        f"Unsupported source type: {source_type!r}"
    )


def read_icon_headers(path: Path) -> list[str]:
    """Preserve manually maintained icon headers."""
    if not path.is_file():
        return []

    return [
        line.strip()
        for line in path.read_text(
            encoding="utf-8",
            errors="replace",
        ).splitlines()
        if ICON_HEADER_RE.fullmatch(line.strip())
   ]


def validate_rule_set_name(name: str) -> None:
    """Prevent output names from escaping rules/Anywhere."""
    if not name:
        raise ValueError("Rule set name cannot be empty.")

    if Path(name).name != name:
        raise ValueError(
            f"Rule set name cannot contain a path: {name}"
        )

    if "/" in name or "\\" in name:
        raise ValueError(
            f"Invalid rule set name: {name}"
        )


def managed_output_paths(name: str) -> list[Path]:
    """Return existing output files owned by one rule set."""
    paths: list[Path] = []

    direct = OUTPUT_DIR / f"{name}.arrs"

    if direct.is_file():
        paths.append(direct)

    for path in OUTPUT_DIR.glob(f"{name}_*.arrs"):
        suffix = path.stem.removeprefix(f"{name}_")

        if len(suffix) == 2 and suffix.isdigit():
            paths.append(path)

    return sorted(set(paths))


def preserved_icons_for(name: str) -> dict[str, list[str]]:
    """Collect icons from current direct and split outputs."""
    icons: dict[str, list[str]] = {}

    for path in managed_output_paths(name):
        headers = read_icon_headers(path)

        if headers:
            icons[path.name] = headers

    return icons


def remove_managed_outputs(name: str) -> None:
    """Remove only files owned by the selected rule set."""
    for path in managed_output_paths(name):
        path.unlink()


def write_rule_set_file(
    output: Path,
    name: str,
    description: str,
    rules: list[tuple[int, str]],
    sources: list[str],
    unsupported: dict[str, int],
    routing: int | None,
    icon_headers: list[str] | None = None,
    total_rules: int | None = None,
) -> None:
    """Write one Anywhere .arrs file."""
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    body = [
        f"# NAME: {name}",
        "# GENERATED-FOR: Anywhere Routing Rule Set",
        f"# DESCRIPTION: {description}",
        f"# RULES: {len(rules)}",
        f"# SKIPPED: {sum(unsupported.values())}",
   ]

    if total_rules is not None and total_rules != len(rules):
        body.append(
            f"# SOURCE-RULES: {total_rules}"
        )

    if unsupported:
        summary = ", ".join(
            f"{key}={unsupported[key]}"
            for key in sorted(unsupported)
        )

        body.append(
            f"# SKIPPED-TYPES: {summary}"
        )

    body.append("# SOURCES:")
    body.extend(
        f"# - {source}"
        for source in sources
    )

    body.extend([
        "",
        f"name = {name}",
    ])

    body.extend(icon_headers or [])

    if routing is not None:
        body.append(
            f"routing = {routing}"
        )

    body.extend(
        f"{rule_type}, {value}"
        for rule_type, value in rules
    )

    output.write_text(
        "\n".join(body) + "\n",
        encoding="utf-8",
    )


def build_rule_set_outputs(
    name: str,
    description: str,
    rules: list[tuple[int, str]],
    unsupported: dict[str, int],
    sources: list[str],
    routing: int | None,
    preserved_icons: dict[str, list[str]],
) -> list[BuiltRuleSet]:
    """Write either one output or multiple 100k-rule chunks."""
    if len(rules) <= MAX_RULES_PER_SET:
        output = OUTPUT_DIR / f"{name}.arrs"

        write_rule_set_file(
            output=output,
            name=name,
            description=description,
            rules=rules,
            sources=sources,
            unsupported=unsupported,
            routing=routing,
            icon_headers=preserved_icons.get(output.name),
        )

        return [
            BuiltRuleSet(
                name=name,
                description=description,
                output_path=output.relative_to(
                    REPOSITORY_ROOT
                ).as_posix(),
                rule_count=len(rules),
                skipped_count=sum(
                    unsupported.values()
                ),
                unsupported_types=unsupported.copy(),
                sources=sources.copy(),
            )
       ]

    chunks = [
        rules[index:index + MAX_RULES_PER_SET]
        for index in range(
           0,
            len(rules),
            MAX_RULES_PER_SET,
        )
   ]

    built: list[BuiltRuleSet] = []

    for index, chunk in enumerate(
        chunks,
        start=1,
    ):
        part_name = f"{name}_{index:02d}"
        output = OUTPUT_DIR / f"{part_name}.arrs"

        part_description = (
            f"{description}（分片 {index}/{len(chunks)}）"
        )

        part_unsupported = (
            unsupported.copy()
            if index == 1
            else {}
        )

        write_rule_set_file(
            output=output,
            name=part_name,
            description=part_description,
            rules=chunk,
            sources=sources,
            unsupported=part_unsupported,
            routing=routing,
            icon_headers=preserved_icons.get(output.name),
            total_rules=len(rules),
        )

        built.append(
            BuiltRuleSet(
                name=part_name,
                description=part_description,
                output_path=output.relative_to(
                    REPOSITORY_ROOT
                ).as_posix(),
                rule_count=len(chunk),
                skipped_count=sum(
                    part_unsupported.values()
                ),
                unsupported_types=part_unsupported,
                sources=sources.copy(),
            )
        )

    return built


def build_rule_set(
    config: dict[str, object],
) -> list[BuiltRuleSet]:
    """Build one explicitly configured rule set."""
    name = str(config["name"]).strip()

    validate_rule_set_name(name)

    description = str(
        config.get("description", "")
    )

    routing_value = config.get("routing")
    routing = (
        int(routing_value)
        if routing_value is not None
        else None
    )

    source_configs = config.get(
        "sources",
        [],
    )

    if not isinstance(source_configs, list):
        raise TypeError(
            f"{name}: sources must be a list."
        )

    if not source_configs:
        raise ValueError(
            f"{name}: at least one source is required."
        )

    all_lines: list[str] = []
    source_labels: list[str] = []

    for source in source_configs:
        lines, label = load_source(source)

        all_lines.extend(lines)
        all_lines.append("")
        source_labels.append(label)

    rules, unsupported = convert_lines(
        all_lines
    )

    excluded_values = {
        str(value).strip().lower()
        for value in config.get(
            "excluded_values",
            [],
        )
        if str(value).strip()
    }

    if excluded_values:
        rules = [
            rule
            for rule in rules
            if rule[1].lower()
            not in excluded_values
       ]

    if not rules:
        raise RuntimeError(
            f"{name}: conversion produced no rules."
        )

    icons = preserved_icons_for(name)

    # Only remove old outputs after all sources have been
    # loaded and conversion has succeeded.
    remove_managed_outputs(name)

    return build_rule_set_outputs(
        name=name,
        description=description,
        rules=rules,
        unsupported=unsupported,
        sources=source_labels,
        routing=routing,
        preserved_icons=icons,
    )


def write_index(
    built: list[BuiltRuleSet],
) -> None:
    """Write a machine-readable index for this build."""
    index = {
        "total_files": len(built),
        "total_rules": sum(
            item.rule_count
            for item in built
        ),
        "total_skipped": sum(
            item.skipped_count
            for item in built
        ),
        "files": [
            {
                "name": item.name,
                "description": item.description,
                "output_path": item.output_path,
                "rule_count": item.rule_count,
                "skipped_count": item.skipped_count,
                "unsupported_types": (
                    item.unsupported_types
                ),
                "sources": item.sources,
            }
            for item in built
        ],
    }

    (OUTPUT_DIR / "index.json").write_text(
        json.dumps(
            index,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )


def write_catalog(
    built: list[BuiltRuleSet],
) -> None:
    """Write a human-readable Markdown catalog."""
    lines = [
        "# Anywhere Rules",
        "",
        "Selected Anywhere routing rule sets.",
        "",
        "| Name | Rules | Skipped | Description | File |",
        "| --- | ---: | ---: | --- | --- |",
   ]

    for item in built:
        description = item.description.replace(
            "|",
            "\\|",
        )

        filename = Path(
            item.output_path
        ).name

        lines.append(
            f"| {item.name} | "
            f"{item.rule_count} | "
            f"{item.skipped_count} | "
            f"{description} | "
            f"[{filename}](./{filename}) |"
        )

    (OUTPUT_DIR / "catalog.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build selected Anywhere routing rule sets."
        )
    )

    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="NAME",
        help=(
            "Build only the named rule set. "
            "May be specified multiple times."
        ),
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    available = {
        str(config["name"]): config
        for config in RULE_SETS
    }

    if args.include:
        unknown = sorted(
            set(args.include) - available.keys()
        )

        if unknown:
            raise ValueError(
                "Unknown rule set(s): "
                + ", ".join(unknown)
            )

        selected = [
            available[name]
            for name in args.include
       ]
    else:
        selected = RULE_SETS

    if not selected:
        raise RuntimeError(
            "No rule sets were selected."
        )

    built: list[BuiltRuleSet] = []

    for config in selected:
        name = str(config["name"])

        print(
            f"Building {name}...",
            file=sys.stderr,
        )

        outputs = build_rule_set(config)
        built.extend(outputs)

        print(
            f"Built {name}: "
            f"{sum(item.rule_count for item in outputs)} rules.",
            file=sys.stderr,
        )

    built.sort(
        key=lambda item: item.output_path.lower()
    )

    write_index(built)
    write_catalog(built)

    print(
        f"Built {len(built)} Anywhere files, "
        f"{sum(item.rule_count for item in built)} rules, "
        f"skipped "
        f"{sum(item.skipped_count for item in built)} entries.",
        file=sys.stderr,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
