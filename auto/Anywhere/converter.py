#!/usr/bin/env python3
"""Convert common rule syntaxes into Anywhere routing rules."""

from __future__ import annotations

import csv
import ipaddress
import re
from typing import Iterable


SUPPORTED_TYPES = {
    "DOMAIN": 2,
    "DOMAIN-SUFFIX": 2,
    "DOMAIN-KEYWORD": 3,
    "IP-CIDR": 0,
    "IP-CIDR6": 1,
}

ALIASES = {
    "HOST": "DOMAIN",
    "HOST-SUFFIX": "DOMAIN-SUFFIX",
    "HOST-KEYWORD": "DOMAIN-KEYWORD",
    "HOST-WILDCARD": "DOMAIN-WILDCARD",
    "IP6-CIDR": "IP-CIDR6",
}

SOURCE_MARKER_DOMAINS = {
    "this_rule_set_is_made_by_sukkaw",
    "this_ruleset_is_made_by_sukkaw",
    "this_ruleset_is_made_by_sukkaw.ruleset.skk.moe",
    "th1s_rule5et_1s_m4d3_by_5ukk4w_ruleset.skk.moe",
    "this_rule_set_is_made_by_sukkaw.skk.moe",
    "7h1s_rul35et_i5_mad3_by_5ukk4w-ruleset.skk.moe",
    "7h15.ru1353t.1s.m4d3.by.5ukk4w.skk.moe",
}


def clean_line(raw: str) -> str | None:
    """Remove common comments, YAML prefixes and wrapping quotes."""
    line = raw.strip()

    if not line or line.startswith("#") or line.startswith(";"):
        return None

    if line.lower() in {
        "payload:",
        "rules:",
        "rule-providers:",
    }:
        return None

    if line.startswith("- "):
        line = line[2:].strip()

    if (
        len(line) >= 2
        and line[0] == line[-1]
        and line[0] in {"'", '"'}
    ):
        line = line[1:-1].strip()

    line = re.sub(r"\s+#.*$", "", line)
    line = re.sub(r"\s+//.*$", "", line)

    return line.strip() or None


def split_rule_line(line: str) -> list[str]:
    """Split a comma-separated rule while respecting quoted fields."""
    try:
        return [
            part.strip()
            for part in next(
                csv.reader([line], skipinitialspace=True)
            )
       ]
    except (csv.Error, StopIteration):
        return []


def infer_bare_rule(line: str) -> str | None:
    """Infer the type of a bare domain or CIDR rule."""
    bare = line.strip().strip("'\"")

    if not bare:
        return None

    if bare.startswith("+."):
        value = bare[2:].strip()
        return f"DOMAIN-SUFFIX,{value}" if value else None

    if bare.startswith("."):
        value = bare[1:].strip()
        return f"DOMAIN-SUFFIX,{value}" if value else None

    try:
        network = ipaddress.ip_network(bare, strict=False)
    except ValueError:
        network = None

    if network is not None:
        rule_type = "IP-CIDR6" if network.version == 6 else "IP-CIDR"
        return f"{rule_type},{network}"

    if "," not in bare and "." in bare and not any(
        char.isspace() for char in bare
    ):
        return f"DOMAIN,{bare}"

    return bare


def normalize_rule_syntax(line: str) -> str | None:
    """Normalize aliases before converting to Anywhere syntax."""
    inferred = infer_bare_rule(line)

    if inferred is None:
        return None

    fields = split_rule_line(inferred)

    if not fields:
        return None

    if len(fields) < 2:
        return inferred

    rule_type = ALIASES.get(
        fields[0].upper(),
        fields[0].upper(),
    )

    value = fields[1].strip()

    if not value:
        return None

    return f"{rule_type},{value}"


def normalize_domain(value: str) -> str | None:
    """Normalize a domain for Anywhere suffix matching."""
    domain = value.strip().lower().rstrip(".")

    if domain.startswith("+."):
        domain = domain[2:]
    elif domain.startswith("*."):
        domain = domain[2:]
    elif domain.startswith("."):
        domain = domain[1:]

    if not domain:
        return None

    if "*" in domain or "?" in domain or "/" in domain:
        return None

    if any(char.isspace() for char in domain):
        return None

    return domain


def normalize_keyword(value: str) -> str | None:
    """Normalize a domain keyword."""
    keyword = value.strip().lower()

    if not keyword:
        return None

    if "*" in keyword or "?" in keyword or "/" in keyword:
        return None

    return keyword


def normalize_cidr(
    value: str,
    expected_version: int,
) -> str | None:
    """Validate and canonicalize an IPv4 or IPv6 network."""
    try:
        network = ipaddress.ip_network(
            value.strip(),
            strict=False,
        )
    except ValueError:
        return None

    if network.version != expected_version:
        return None

    return str(network)


def convert_domain_wildcard(
    value: str,
) -> tuple[int, str] | None:
    """Convert a simple domain wildcard into suffix matching."""
    domain = normalize_domain(value)

    if domain is None:
        return None

    return 2, domain


def convert_line(
    line: str,
) -> tuple[tuple[int, str] | None, str | None]:
    """
    Convert a source rule into an Anywhere rule.

    Returns:
        ((type, value), None) on success.
        (None, skipped_type) when unsupported or invalid.
        (None, None) for ignored lines.
    """
    cleaned = clean_line(line)

    if cleaned is None:
        return None, None

    normalized = normalize_rule_syntax(cleaned)

    if normalized is None:
        return None, "UNKNOWN"

    fields = split_rule_line(normalized)

    if len(fields) < 2:
        return None, "UNKNOWN"

    rule_type = fields[0].upper()
    value = fields[1]

    if rule_type == "DOMAIN-WILDCARD":
        converted = convert_domain_wildcard(value)

        if converted is None:
            return None, rule_type

        return converted, None

    anywhere_type = SUPPORTED_TYPES.get(rule_type)

    if anywhere_type is None:
        return None, rule_type or "UNKNOWN"

    if anywhere_type == 2:
        domain = normalize_domain(value)

        if domain is None:
            return None, rule_type

        return (2, domain), None

    if anywhere_type == 3:
        keyword = normalize_keyword(value)

        if keyword is None:
            return None, rule_type

        return (3, keyword), None

    if anywhere_type == 0:
        cidr = normalize_cidr(value, expected_version=4)

        if cidr is None:
            return None, rule_type

        return (0, cidr), None

    if anywhere_type == 1:
        cidr = normalize_cidr(value, expected_version=6)

        if cidr is None:
            return None, rule_type

        return (1, cidr), None

    return None, rule_type


def convert_lines(
    lines: Iterable[str],
) -> tuple[list[tuple[int, str]], dict[str, int]]:
    """Convert, normalize and deduplicate multiple source rules."""
    rules: list[tuple[int, str]] = []
    seen: set[tuple[int, str]] = set()
    unsupported: dict[str, int] = {}

    for line in lines:
        converted, skipped_type = convert_line(line)

        if (
            converted is not None
            and converted[1].lower() in SOURCE_MARKER_DOMAINS
        ):
            continue

        if converted is not None:
            if converted not in seen:
                seen.add(converted)
                rules.append(converted)
            continue

        if skipped_type:
            unsupported[skipped_type] = (
                unsupported.get(skipped_type, 0) + 1
            )

    return rules, unsupported
