"""
Simple recursive character text splitter for document chunking.

No external dependency — splits text into overlapping chunks using a
hierarchy of separators: paragraphs -> newlines -> sentences -> words.
"""

from dataclasses import dataclass, field

DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " "]


@dataclass
class Chunk:
    """A single text chunk with positional metadata."""

    text: str
    index: int
    metadata: dict = field(default_factory=dict)


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    separators: list[str] | None = None,
) -> list[Chunk]:
    """Split text into overlapping chunks.

    Uses a separator hierarchy to split on natural boundaries
    (paragraphs first, then newlines, sentences, words).

    Args:
        text: The text to split.
        chunk_size: Target chunk size in characters.
        chunk_overlap: Number of overlapping characters between chunks.
        separators: Custom separator hierarchy (defaults to paragraph/newline/sentence/word).

    Returns:
        List of Chunk objects with text, index, and metadata.
    """
    if not text or not text.strip():
        return []

    if chunk_overlap >= chunk_size:
        chunk_overlap = chunk_size // 4

    if separators is None:
        separators = DEFAULT_SEPARATORS

    # If text fits in one chunk, return it directly
    if len(text) <= chunk_size:
        return [Chunk(text=text.strip(), index=0, metadata={"start_char": 0, "end_char": len(text)})]

    # Split recursively using separator hierarchy
    splits = _recursive_split(text, separators, chunk_size)

    # Merge splits into chunks with overlap
    return _merge_splits(splits, chunk_size, chunk_overlap)


def _recursive_split(text: str, separators: list[str], chunk_size: int) -> list[str]:
    """Recursively split text using separator hierarchy."""
    if not separators:
        # Last resort: hard character split
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    separator = separators[0]
    remaining_separators = separators[1:]

    parts = text.split(separator)

    result: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue

        if len(stripped) <= chunk_size:
            result.append(stripped)
        else:
            # Piece is still too large — split with next separator
            result.extend(_recursive_split(stripped, remaining_separators, chunk_size))

    return result


def _merge_splits(splits: list[str], chunk_size: int, chunk_overlap: int) -> list[Chunk]:
    """Merge small splits into chunks of approximately chunk_size, adding overlap."""
    if not splits:
        return []

    chunks: list[Chunk] = []
    current_parts: list[str] = []
    current_len = 0
    char_offset = 0

    for split in splits:
        split_len = len(split)

        # Would adding this split exceed the target?
        separator_overhead = 1 if current_parts else 0  # space between parts
        if current_len + separator_overhead + split_len > chunk_size and current_parts:
            # Emit current chunk
            chunk_text_str = " ".join(current_parts)
            chunks.append(Chunk(
                text=chunk_text_str,
                index=len(chunks),
                metadata={"start_char": char_offset, "end_char": char_offset + len(chunk_text_str)},
            ))

            # Calculate overlap: keep trailing parts that fit within overlap window
            overlap_parts: list[str] = []
            overlap_len = 0
            for part in reversed(current_parts):
                if overlap_len + len(part) + 1 > chunk_overlap:
                    break
                overlap_parts.insert(0, part)
                overlap_len += len(part) + 1

            char_offset += len(chunk_text_str) - overlap_len
            current_parts = overlap_parts
            current_len = overlap_len

        current_parts.append(split)
        current_len += separator_overhead + split_len

    # Emit remaining content
    if current_parts:
        chunk_text_str = " ".join(current_parts)
        chunks.append(Chunk(
            text=chunk_text_str,
            index=len(chunks),
            metadata={"start_char": char_offset, "end_char": char_offset + len(chunk_text_str)},
        ))

    return chunks
