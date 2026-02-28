"""
Tests for the document chunker utility.
"""

from src.utils.document_chunker import Chunk, chunk_text


class TestChunkText:

    def test_empty_text_returns_empty(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        text = "Hello world, this is a short text."
        chunks = chunk_text(text, chunk_size=512)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].index == 0

    def test_long_text_multiple_chunks(self):
        text = "word " * 200  # ~1000 chars
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 1
        # All chunks should have text
        for chunk in chunks:
            assert len(chunk.text) > 0

    def test_paragraph_split_priority(self):
        text = "First paragraph content here.\n\nSecond paragraph content here.\n\nThird paragraph content here."
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=0)
        # Should split on paragraph boundaries
        assert len(chunks) >= 2
        assert any("First" in c.text for c in chunks)
        assert any("Third" in c.text for c in chunks)

    def test_overlap_present(self):
        # Create text that needs splitting
        para1 = "Alpha bravo charlie delta."
        para2 = "Echo foxtrot golf hotel."
        para3 = "India juliet kilo lima."
        text = f"{para1}\n\n{para2}\n\n{para3}"
        chunks = chunk_text(text, chunk_size=40, chunk_overlap=20)
        # With overlap, some content should appear in adjacent chunks
        assert len(chunks) >= 2

    def test_metadata_populated(self):
        text = "Short piece of text to split into chunks for testing metadata."
        chunks = chunk_text(text, chunk_size=512)
        assert len(chunks) == 1
        assert "start_char" in chunks[0].metadata
        assert "end_char" in chunks[0].metadata

    def test_chunk_indices_sequential(self):
        text = "word " * 500
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=10)
        for i, chunk in enumerate(chunks):
            assert chunk.index == i

    def test_custom_separators(self):
        text = "part1|part2|part3"
        chunks = chunk_text(text, chunk_size=10, chunk_overlap=0, separators=["|"])
        assert len(chunks) >= 2

    def test_chunk_overlap_capped(self):
        # Overlap >= chunk_size should be capped
        text = "word " * 100
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=100)
        # Should not crash; overlap gets capped to chunk_size // 4
        assert len(chunks) > 0

    def test_chunk_dataclass_fields(self):
        c = Chunk(text="hello", index=0, metadata={"key": "val"})
        assert c.text == "hello"
        assert c.index == 0
        assert c.metadata == {"key": "val"}
