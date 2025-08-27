from __future__ import annotations

import re


def parse_headers(lines: list[str]) -> list[tuple[int, int, str]]:
    """Parses headers from a list of lines.

    Args:
        lines (list[str]): List of lines from the document.

    Returns:
        list[tuple[int, int, str]]: A list of tuples where each tuple contains:
            - The index of the header line in the original list.
            - The level of the header (number of '#' characters).
            - The title of the header.
    """
    header_pattern = re.compile(r'^(#+)\s+(.*)')
    headers = []
    for idx, line in enumerate(lines):
        match = header_pattern.match(line)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            headers.append((idx, level, title))
    return headers


def get_parent_headers(start_idx: int, headers: list[tuple[int, int, str]]) -> list[str]:
    """Finds parent headers for a given header.

    Args:
        start_idx (int): The current header idx.
        headers (list[tuple[int, int, str]]): List of parsed headers.
    Returns:
        list[str]: A list of parent headers, formatted as strings.
    """
    for idx, header in enumerate(headers):
        if start_idx == header[0]:
            _, current_level, _ = header
            break

    if current_level == 1:
        return []
    parents: list[str] = []
    for i in range(idx - 1, -1, -1):
        _, level, title = headers[i]
        if level < current_level:
            parents.insert(0, ('#' * level + ' ' + title))
            current_level = level
    return parents
