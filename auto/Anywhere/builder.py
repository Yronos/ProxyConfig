"""Build Anywhere routing rule sets from configured local and remote sources."""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .converter import convert_lines

MAX_RULES_PER_SET = 100_000
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RULES_DIR = (REPOSITORY_ROOT / "rules").resolve()
OUTPUT_DIR = (RULES_DIR / "Anywhere").resolve()

ICON_HEADER_RE = re.compile(r"^icon-(?:light|dark)\s*=\s*\S+\s*$")


@dataclass(frozen=True)
class Source:
    kind: str
    label: str
    path: str | None = None
    url: str | None = None


@dataclass(frozen=True)
class RuleSetConfig:
    name: str
    description: str
    sources: tuple[Source, ...]
    routing: int | None = None
    excluded_values: frozenset[str] = frozenset()
    icons: tuple[str, ...] = ()


@dataclass
class BuiltRuleSet:
    name: str
    description: str
    output_path: Path
    rule_count: int
    skipped_count: int
    unsupported_types: dict[str, int]
    sources: list[str] = field(default_factory=list)


def load_yaml(path: Path) -> dict[str, Any]:
    """Load config.yaml using PyYAML."""
    try:
        import yaml
    except ImportError as exc:
        raise RuntimeError(
            "Building Anywhere rule sets requires PyYAML. "
            "Install it with: python -m pip install PyYAML"
        ) from exc

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    if not isinstance(data, dict):
        raise ValueError(f"Invalid config root: {path}")

    return data


def parse_icons(value: Any) -> tuple[str, ...]:
    """Return valid icon-light/icon-dark header lines from config."""
    if value is None:
        return ()

    if isinstance(value, dict):
        result = []
        for theme in ("light", "dark"):
            icon = value.get(theme)
            if icon:
                result.append(f"icon-{theme}={str(icon).strip()}")
        return tuple(result)

    if isinstance(value, list):
        result = []
        for item in value:
            line = str(item).strip()
            if ICON_HEADER_RE.fullmatch(line):
                result.append(line)
        return tuple(result)

    return ()


def parse_source(raw: Any, index: int) -> Source:
    if isinstance(raw, str):
        # A plain string means a path relative to rules/.
        path = raw.replace("\\", "/")
        return Source(kind="local", label=path, path=path)

    if not isinstance(raw, dict):
        raise ValueError(f"Invalid source #{index}: expected string or mapping")

    kind = str(raw.get("type", "")).strip().lower()

    if kind == "local":
        path = str(raw.get("path", "")).strip().replace("\\", "/")
        if not path:
            raise ValueError(f"Source #{index}: local source requires path")
        return Source(kind="local", label=path, path=path)

    if kind == "remote":
        url = str(raw.get("url", "")).strip()
        if not url:
            raise ValueError(f"Source #{index}: remote source requires url")
        return Source(kind="remote", label=url, url=url)

    raise ValueError(
        f"Source #{index}: unsupported type {kind!r}; use local or remote"
    )


def load_config(path: Path) -> dict[str, RuleSetConfig]:
    """Parse config.yaml into validated Anywhere rule-set definitions."""
    data = load_yaml(path)
    raw_sets = data.get("rulesets", [])

    if not isinstance(raw_sets, list):
        raise ValueError("config.yaml: 'rulesets' must be a list")

    configs: dict[str, RuleSetConfig] = {}

    for index, raw in enumerate(raw_sets, start=1):
        if not isinstance(raw, dict):
            raise ValueError(f"Rule set #{index}: expected mapping")

        name = str(raw.get("name", "")).strip()
        if not name:
            raise ValueError(f"Rule set #{index}: missing name")
        if name in configs:
            raise ValueError(f"Duplicate rule set name: {name}")

        description = str(raw.get("description", "")).strip()
        raw_sources = raw.get("sources", [])

        if not isinstance(raw_sources, list) or not raw_sources:
            raise ValueError(f"{name}: sources must be a non-empty list")

        sources = tuple(
            parse_source(source, source_index)
            for source_index, source in enumerate(raw_sources, start=1)
        )

        routing = raw.get("routing")
        if routing is not None:
            try:
                routing = int(routing)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"{name}: routing must be an integer") from exc

        excluded = raw.get("excluded_values", [])
        if not isinstance(excluded, list):
            raise ValueError(f"{name}: excluded_values must be a list")

        configs[name] = RuleSetConfig(
            name=name,
            description=description,
            sources=sources,
            routing=routing,
            excluded_values=frozenset(
                str(value).strip().lower() for value in excluded if str(value).strip()
            ),
            icons=parse_icons(raw.get("icons")),
        )

    return configs


def fetch_bytes(url: str, retries: int = 4, timeout: int = 60) -> bytes:
    """Fetch remote source data with retries and exponential backoff."""
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "text/plain,*/*",
            "User-Agent": "anywhere-rules-builder",
        },
    )

    last_error: Exception | None = None

    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except (
            urllib.error.URLError,
            urllib.error.HTTPError,
            TimeoutError,
            socket.timeout,
        ) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2**attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def read_local_source(relative_path: str) -> list[str]:
    """Read a source strictly from the repository's rules/ directory."""
    path = (RULES_DIR / relative_path).resolve()

    try:
        path.relative_to(RULES_DIR)
    except ValueError as exc:
        raise ValueError(f"Local source escapes rules/: {relative_path}") from exc

    try:
        path.relative_to(OUTPUT_DIR)
    except ValueError:
        pass
    else:
        raise ValueError(f"Generated Anywhere output cannot be a source: {relative_path}")

    if not path.is_file():
        raise FileNotFoundError(f"Local source not found: {relative_path}")

    return path.read_text(encoding="utf-8-sig", errors="replace").splitlines()


def read_remote_source(url: str) -> list[str]:
    """Read an HTTP(S) source."""
    if not url.lower().startswith(("http://", "https://")):
        raise ValueError(f"Unsupported remote URL: {url}")

    return fetch_bytes(url).decode("utf-8-sig", errors="replace").splitlines()


def load_source(source: Source) -> tuple[list[str], str]:
    if source.kind == "local":
        assert source.path is not None
        return read_local_source(source.path), source.label

    assert source.url is not None
    return read_remote_source(source.url), source.label


def managed_output_paths(name: str) -> list[Path]:
    """Find output files currently managed by one logical rule set."""
    result = []

    base = OUTPUT_DIR / f"{name}.arrs"
    if base.is_file():
        result.append(base)

    prefix = f"{name}_"
    for path in OUTPUT_DIR.glob(f"{name}_*.arrs"):
        suffix = path.stem[len(prefix):]
        if len(suffix) == 2 and suffix.isdigit():
            result.append(path)

    return sorted(result)


def read_icon_headers(path: Path) -> list[str]:
    """Read legacy icon metadata from an existing .arrs output."""
    if not path.is_file():
        return []

    result = []
    for line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        line = line.strip()
        if ICON_HEADER_RE.fullmatch(line):
            result.append(line)

    return result


def preserved_icons_for(name: str) -> dict[str, list[str]]:
    """Preserve icons on existing physical outputs for compatibility."""
    return {
        path.name: read_icon_headers(path)
        for path in managed_output_paths(name)
    }


def remove_managed_outputs(name: str) -> None:
    for path in managed_output_paths(name):
        path.unlink()


def format_header(
    config: RuleSetConfig,
    rule_count: int,
    skipped_count: int,
    unsupported: dict[str, int],
    sources: list[str],
    *,
    split: bool,
    part_index: int,
    part_total: int,
) -> list[str]:
    description = config.description
    if split:
        description += f"（分片 {part_index}/{part_total}）"

    lines = [
        f"# NAME: {config.name}",
        "# GENERATED-FOR: Anywhere Routing Rule Set",
        f"# DESCRIPTION: {description}",
        f"# RULES: {rule_count}",
        f"# SKIPPED: {skipped_count}",
    ]

    if split:
        lines.append(f"# SOURCE-RULES: {rule_count}")

    if unsupported:
        values = ", ".join(
            f"{rule_type}={count}"
            for rule_type, count in sorted(unsupported.items())
        )
        lines.append(f"# SKIPPED-TYPES: {values}")

    lines.extend(["# SOURCES:", *[f"# - {source}" for source in sources], ""])
    return lines


def write_rule_set_file(
    path: Path,
    config: RuleSetConfig,
    rules: list[tuple[int, str]],
    skipped_count: int,
    unsupported: dict[str, int],
    sources: list[str],
    icons: list[str],
    *,
    split: bool,
    part_index: int,
    part_total: int,
    total_rules: int,
) -> None:
    lines = format_header(
        config,
        total_rules,
        skipped_count,
        unsupported,
        sources,
        split=split,
        part_index=part_index,
        part_total=part_total,
    )

    lines.append(f"name = {config.name}")

    # Explicit config icons take precedence. If no config icons exist,
    # preserve the icon metadata from the previous physical output.
    if icons:
        lines.extend(icons)

    if config.routing is not None:
        lines.append(f"routing = {config.routing}")

    lines.extend(
        f"{rule_type},{value}"
        for rule_type, value in rules
    )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_rule_set(config: RuleSetConfig) -> BuiltRuleSet:
    """Build one Anywhere rule set while retaining the original processing flow."""
    all_lines: list[str] = []
    source_labels: list[str] = []

    for source in config.sources:
        lines, label = load_source(source)
        all_lines.extend(lines)
        source_labels.append(label)

    rules, unsupported = convert_lines(all_lines)

    if config.excluded_values:
        rules = [
            rule
            for rule in rules
            if rule[1].lower() not in config.excluded_values
        ]

    if not rules:
        raise ValueError(f"{config.name}: no valid Anywhere rules were produced")

    skipped_count = sum(unsupported.values())
    legacy_icons = preserved_icons_for(config.name)

    remove_managed_outputs(config.name)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    chunks = [
        rules[start:start + MAX_RULES_PER_SET]
        for start in range(0, len(rules), MAX_RULES_PER_SET)
    ]
    split = len(chunks) > 1

    outputs: list[Path] = []

    for index, chunk in enumerate(chunks, start=1):
        path = (
            OUTPUT_DIR / f"{config.name}_{index:02d}.arrs"
            if split
            else OUTPUT_DIR / f"{config.name}.arrs"
        )

        if config.icons:
            icons = list(config.icons)
        else:
            icons = legacy_icons.get(path.name, [])

        write_rule_set_file(
            path,
            config,
            chunk,
            skipped_count,
            unsupported if index == 1 else {},
            source_labels,
            icons,
            split=split,
            part_index=index,
            part_total=len(chunks),
            total_rules=len(rules),
        )
        outputs.append(path)

    return BuiltRuleSet(
        name=config.name,
        description=config.description,
        output_path=outputs[0],
        rule_count=len(rules),
        skipped_count=skipped_count,
        unsupported_types=unsupported,
        sources=source_labels,
    )


def write_index(results: list[BuiltRuleSet]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "generated_for": "Anywhere Routing Rule Set",
        "total_rule_sets": len(results),
        "total_rules": sum(result.rule_count for result in results),
        "total_skipped": sum(result.skipped_count for result in results),
        "rule_sets": [
            {
                "name": result.name,
                "description": result.description,
                "rules": result.rule_count,
                "skipped": result.skipped_count,
                "unsupported_types": result.unsupported_types,
                "sources": result.sources,
            }
            for result in results
        ],
    }

    (OUTPUT_DIR / "index.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def write_catalog(results: list[BuiltRuleSet]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Anywhere Routing Rule Sets",
        "",
        f"共 {len(results)} 个规则集，"
        f"{sum(result.rule_count for result in results):,} 条规则。",
        "",
        "| NAME | DESCRIPTION | RULES | SKIPPED |",
        "| --- | --- | ---: | ---: |",
    ]

    for result in results:
        lines.append(
            f"| `{result.name}` | {result.description} | "
            f"{result.rule_count:,} | {result.skipped_count:,} |"
        )

    (OUTPUT_DIR / "catalog.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def parse_args(configs: dict[str, RuleSetConfig]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Anywhere routing rule sets."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(__file__).with_name("config.yaml"),
        help="Path to config.yaml",
    )
    parser.add_argument(
        "--include",
        action="append",
        metavar="NAME",
        help="Build only the specified rule set; may be repeated.",
    )

    args = parser.parse_args()

    if args.include:
        unknown = [name for name in args.include if name not in configs]
        if unknown:
            parser.error(
                "unknown rule set(s): " + ", ".join(sorted(set(unknown)))
            )

    return args


def main() -> int:
    config_path = Path(__file__).with_name("config.yaml")

    # Parse --config before loading the actual configuration.
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config", type=Path, default=config_path)
    pre_args, _ = pre_parser.parse_known_args()

    try:
        configs = load_config(pre_args.config)
        args = parse_args(configs)

        selected_names = args.include or list(configs)
        results = []

        for name in selected_names:
            config = configs[name]
            print(f"==> Building {name}")
            result = build_rule_set(config)
            results.append(result)
            print(
                f"    {result.rule_count:,} rules, "
                f"{result.skipped_count:,} skipped"
            )

        # Keep index/catalog generation compatible with the old builder:
        # when --include is used, only the selected build results are catalogued.
        write_index(results)
        write_catalog(results)

    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
