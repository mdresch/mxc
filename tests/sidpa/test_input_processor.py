"""Tests for InputProcessor."""

from __future__ import annotations

import asyncio
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from pmbok.exceptions import InputProcessingError, InputValidationError
from pmbok.models.enums import InputSourceType
from pmbok.models.inputs import RawInput
from pmbok.processors.input_processor import InputProcessor


def make_raw_input(
    source_type: InputSourceType,
    data: bytes = b"hello world",
    filename: str = "test.txt",
    size_bytes: int | None = None,
) -> RawInput:
    if size_bytes is None:
        size_bytes = len(data)
    return RawInput(
        source_type=source_type,
        filename=filename,
        data=data,
        size_bytes=size_bytes,
    )


def _inject_pytesseract_mock(ocr_return: str = "OCR text") -> tuple[MagicMock, MagicMock]:
    """Inject fake pytesseract and PIL.Image modules so tests don't need them installed."""
    fake_pytesseract = MagicMock()
    fake_pytesseract.image_to_string.return_value = ocr_return

    fake_image = MagicMock()
    fake_pil = MagicMock()
    fake_pil.Image.open.return_value = fake_image

    sys.modules.setdefault("pytesseract", fake_pytesseract)
    sys.modules.setdefault("PIL", fake_pil)
    sys.modules.setdefault("PIL.Image", fake_pil.Image)

    return fake_pytesseract, fake_pil


# ── Text passthrough ──────────────────────────────────────────────────────────

def test_process_single_text_passthrough():
    processor = InputProcessor()
    item = make_raw_input(InputSourceType.TEXT, data=b"My project idea")
    result = asyncio.run(processor.process_single(item))
    assert result.extracted_text == "My project idea"
    assert result.source_type == InputSourceType.TEXT
    assert result.raw_input_id == item.id


def test_process_single_markdown_passthrough():
    processor = InputProcessor()
    item = make_raw_input(InputSourceType.MARKDOWN, data=b"# Title\nContent", filename="doc.md")
    result = asyncio.run(processor.process_single(item))
    assert result.extracted_text == "# Title\nContent"
    assert result.source_type == InputSourceType.MARKDOWN


# ── OCR image ─────────────────────────────────────────────────────────────────

def test_process_single_image_ocr():
    fake_pytesseract, fake_pil = _inject_pytesseract_mock("Extracted OCR text")
    processor = InputProcessor()
    fake_image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    item = make_raw_input(InputSourceType.IMAGE, data=fake_image_data, filename="diagram.png")

    result = asyncio.run(processor.process_single(item))

    fake_pytesseract.image_to_string.assert_called_once()
    assert result.extracted_text == "Extracted OCR text"
    assert result.source_type == InputSourceType.IMAGE


def test_process_single_image_empty_ocr_triggers_diagram_description():
    """When OCR returns empty text, _describe_diagram should be called (returns placeholder)."""
    fake_pytesseract, _ = _inject_pytesseract_mock("   ")  # whitespace-only → empty
    # Ensure the shared mock returns whitespace for this test
    sys.modules["pytesseract"].image_to_string.return_value = "   "

    processor = InputProcessor()
    fake_image_data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
    item = make_raw_input(InputSourceType.IMAGE, data=fake_image_data, filename="diagram.png")

    result = asyncio.run(processor.process_single(item))

    # No LLM client → placeholder description
    assert "[Diagram description unavailable" in result.extracted_text


# ── Validation: oversized file ────────────────────────────────────────────────

def test_validate_oversized_file_raises():
    processor = InputProcessor(max_file_size_mb=20)
    oversized = make_raw_input(
        InputSourceType.TEXT,
        data=b"x",
        size_bytes=21 * 1024 * 1024,  # 21 MB
    )
    with pytest.raises(InputValidationError, match="20 MB"):
        processor._validate(oversized)


def test_process_single_oversized_raises():
    processor = InputProcessor(max_file_size_mb=20)
    oversized = make_raw_input(
        InputSourceType.TEXT,
        data=b"x",
        size_bytes=21 * 1024 * 1024,
    )
    with pytest.raises((InputValidationError, InputProcessingError)):
        asyncio.run(processor.process_single(oversized))


# ── Validation: unsupported format ────────────────────────────────────────────

def test_validate_unsupported_source_type_raises():
    """Simulate an unsupported source type by temporarily removing it from the mapping."""
    processor = InputProcessor()
    item = make_raw_input(InputSourceType.TEXT)

    import pmbok.processors.input_processor as ip_module
    original = ip_module.SOURCE_TYPE_TO_MIME.copy()
    try:
        del ip_module.SOURCE_TYPE_TO_MIME[InputSourceType.TEXT]
        with pytest.raises(InputValidationError, match="Unsupported source type"):
            processor._validate(item)
    finally:
        ip_module.SOURCE_TYPE_TO_MIME.update(original)


# ── Batch processing ──────────────────────────────────────────────────────────

def test_process_batch_success():
    processor = InputProcessor()
    items = [
        make_raw_input(InputSourceType.TEXT, data=b"item one", filename="a.txt"),
        make_raw_input(InputSourceType.TEXT, data=b"item two", filename="b.txt"),
    ]
    result = asyncio.run(processor.process_batch(items))
    assert len(result.successful) == 2
    assert len(result.failed) == 0


def test_process_batch_failure_isolation():
    """A failing item should not prevent other items from being processed."""
    processor = InputProcessor(max_file_size_mb=20)
    good = make_raw_input(InputSourceType.TEXT, data=b"good content", filename="good.txt")
    bad = make_raw_input(
        InputSourceType.TEXT,
        data=b"x",
        size_bytes=21 * 1024 * 1024,
        filename="bad.txt",
    )
    result = asyncio.run(processor.process_batch([good, bad]))
    assert len(result.successful) == 1
    assert len(result.failed) == 1
    assert result.failed[0].filename == "bad.txt"
    assert "20 MB" in result.failed[0].reason


def test_process_batch_exceeds_max_raises():
    processor = InputProcessor(max_batch_size=3)
    items = [
        make_raw_input(InputSourceType.TEXT, data=b"x", filename=f"{i}.txt")
        for i in range(4)
    ]
    with pytest.raises(InputValidationError, match="exceeds maximum"):
        asyncio.run(processor.process_batch(items))


def test_process_batch_never_raises_on_item_failure():
    """process_batch must not raise even when all items fail."""
    processor = InputProcessor(max_file_size_mb=1)
    items = [
        make_raw_input(
            InputSourceType.TEXT,
            data=b"x",
            size_bytes=2 * 1024 * 1024,
            filename=f"big_{i}.txt",
        )
        for i in range(3)
    ]
    result = asyncio.run(processor.process_batch(items))
    assert len(result.successful) == 0
    assert len(result.failed) == 3
