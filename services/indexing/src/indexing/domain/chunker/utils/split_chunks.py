from __future__ import annotations

from indexing.shared.utils import tokens_calculator

from indexing.domain.chunker.utils.header_processor import get_parent_headers


def split_chunks_by_tokens(
    content_lines: list[str],
    headers: list[tuple[int, int, str]],
    start_idx: int,
    max_chunk_length: int,
    min_chunk_length: int,
) -> list[list[str]]:
    """
    Splits content lines into chunks based on token length, considering headers.

    Args:
        content_lines (list[str]): List of content lines to be chunked.
        headers (list[tuple[int, int, str]]): List of headers parsed from the content.
        start_idx (int): The current header idx.
        max_chunk_length (int): Maximum token length for each chunk.
        min_chunk_length (int): Minimum token length for each chunk.

    Returns:
        list[list[str]]: List of chunks, where each chunk is a list of strings.
    """
    # If no headers are provided, treat all lines as content
    if headers:
        header = content_lines[0]
        parent_headers = get_parent_headers(start_idx, headers) + [header]
        content_lines = content_lines[1:]
    else:
        parent_headers = []
    chunks: list[list[str]] = []
    chunk: list[str] = []
    for line in content_lines:
        chunk_text = '\n'.join(chunk + [line]).strip()
        if tokens_calculator(chunk_text) <= max_chunk_length:
            chunk.append(line)
        else:
            chunks.append(parent_headers + chunk)
            chunk = [line]
    if tokens_calculator('\n'.join(chunk).strip()) < min_chunk_length:
        if len(chunks) > 0:
            chunks[-1].extend(chunk)
        else:
            chunks.append(chunk)
    else:
        chunks.append(parent_headers + chunk)
    return chunks