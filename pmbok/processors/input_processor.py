"""InputProcessor: validates, OCR-s, and batch-processes raw inputs."""

from __future__ import annotations

import io
import logging
import uuid
from enum import Enum
from typing import Any

from pmbok.exceptions import InputProcessingError, InputValidationError, LLMError, OCRError
from pmbok.models.enums import InputSourceType
from pmbok.models.inputs import BatchResult, FailedItem, ParsedInput, RawInput

logger = logging.getLogger(__name__)

# Supported MIME types and their mapping to InputSourceType
MIME_TO_SOURCE_TYPE: dict[str, InputSourceType] = {
    "image/png": InputSourceType.IMAGE,
    "image/jpeg": InputSourceType.IMAGE,
    "application/pdf": InputSourceType.PDF,
    "text/plain": InputSourceType.TEXT,
    "text/markdown": InputSourceType.MARKDOWN,
}

SOURCE_TYPE_TO_MIME: dict[InputSourceType, list[str]] = {
    InputSourceType.IMAGE: ["image/png", "image/jpeg"],
    InputSourceType.PDF: ["application/pdf"],
    InputSourceType.TEXT: ["text/plain"],
    InputSourceType.MARKDOWN: ["text/markdown"],
}

SUPPORTED_MIME_TYPES = list(MIME_TO_SOURCE_TYPE.keys())

MAX_FILE_SIZE_BYTES_DEFAULT = 20 * 1024 * 1024  # 20 MB


class OCREngine(str, Enum):
    TESSERACT = "tesseract"
    AZURE = "azure"


class InputProcessor:
    def __init__(
        self,
        ocr_engine: OCREngine | str = OCREngine.TESSERACT,
        max_file_size_mb: int = 20,
        max_batch_size: int = 20,
        llm_client: Any = None,
    ) -> None:
        self.ocr_engine = ocr_engine
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        self.max_batch_size = max_batch_size
        self.llm_client = llm_client

    async def process_batch(self, items: list[RawInput]) -> BatchResult:
        """Process a batch of raw inputs. Never raises; failures captured in BatchResult.failed."""
        if len(items) > self.max_batch_size:
            raise InputValidationError(
                f"Batch size {len(items)} exceeds maximum of {self.max_batch_size} items."
            )

        session_id = str(uuid.uuid4())
        successful: list[ParsedInput] = []
        failed: list[FailedItem] = []

        for item in items:
            try:
                parsed = await self.process_single(item)
                successful.append(parsed)
            except (InputValidationError, OCRError, LLMError) as exc:
                logger.warning(
                    "Failed to process input %s (%s): %s",
                    item.id,
                    item.filename,
                    exc,
                )
                failed.append(
                    FailedItem(
                        raw_input_id=item.id,
                        filename=item.filename,
                        reason=str(exc),
                    )
                )
            except Exception as exc:
                logger.error(
                    "Unexpected error processing input %s (%s): %s",
                    item.id,
                    item.filename,
                    exc,
                )
                failed.append(
                    FailedItem(
                        raw_input_id=item.id,
                        filename=item.filename,
                        reason=str(exc),
                    )
                )

        return BatchResult(session_id=session_id, successful=successful, failed=failed)

    async def process_single(self, item: RawInput) -> ParsedInput:
        """Parse a single RawInput. Raises InputProcessingError on failure."""
        try:
            self._validate(item)
            mime_type = self._source_type_to_mime(item.source_type)

            if item.source_type in (InputSourceType.IMAGE, InputSourceType.PDF):
                extracted_text = await self._ocr_image(item.data, mime_type)
                diagram_description: str | None = None
                if not extracted_text.strip():
                    diagram_description = await self._describe_diagram(item.data)
                    extracted_text = diagram_description
            else:
                # text/plain or text/markdown — decode bytes directly
                try:
                    extracted_text = item.data.decode("utf-8")
                except UnicodeDecodeError as exc:
                    raise InputProcessingError(
                        f"Could not decode text input '{item.filename}': {exc}"
                    ) from exc
                diagram_description = None

            return ParsedInput(
                raw_input_id=item.id,
                extracted_text=extracted_text,
                diagram_description=diagram_description,
                source_type=item.source_type,
            )
        except (InputValidationError, InputProcessingError):
            raise
        except Exception as exc:
            raise InputProcessingError(
                f"Unexpected error processing '{item.filename}': {exc}"
            ) from exc

    def _validate(self, item: RawInput) -> None:
        """Raise InputValidationError if format or size is invalid."""
        # Validate source type has a known MIME mapping
        if item.source_type not in SOURCE_TYPE_TO_MIME:
            supported = ", ".join(SUPPORTED_MIME_TYPES)
            raise InputValidationError(
                f"Unsupported source type '{item.source_type}'. "
                f"Supported formats: {supported}"
            )

        # Validate file size
        if item.size_bytes > self.max_file_size_bytes:
            max_mb = self.max_file_size_bytes // (1024 * 1024)
            raise InputValidationError(
                f"File '{item.filename}' is {item.size_bytes} bytes, "
                f"which exceeds the {max_mb} MB size limit."
            )

    async def _ocr_image(self, data: bytes, mime_type: str) -> str:
        """Extract text from image bytes using pytesseract."""
        try:
            import pytesseract
            from PIL import Image

            if mime_type == "application/pdf":
                # Try pdf2image if available; otherwise return empty string gracefully
                try:
                    from pdf2image import convert_from_bytes

                    pages = convert_from_bytes(data)
                    texts = []
                    for page in pages:
                        texts.append(pytesseract.image_to_string(page))
                    return "\n".join(texts)
                except ImportError:
                    logger.warning("pdf2image not installed; returning empty OCR for PDF.")
                    return ""
                except Exception as exc:
                    logger.warning("PDF OCR failed: %s", exc)
                    return ""
            else:
                image = Image.open(io.BytesIO(data))
                return pytesseract.image_to_string(image)
        except ImportError as exc:
            raise OCRError(
                "pytesseract or Pillow is not installed. Install them to enable OCR."
            ) from exc
        except Exception as exc:
            raise OCRError(f"OCR failed: {exc}") from exc

    async def _describe_diagram(self, data: bytes) -> str:
        """Use vision LLM to produce a structural description of visual content."""
        if self.llm_client is None:
            return "[Diagram description unavailable: no LLM client configured]"
        try:
            # Stub: real implementation would encode data as base64 and call the vision LLM
            description = await self.llm_client.describe_image(data)
            return description
        except Exception as exc:
            logger.warning("Vision LLM diagram description failed: %s", exc)
            return "[Diagram description failed]"

    @staticmethod
    def _source_type_to_mime(source_type: InputSourceType) -> str:
        """Return the primary MIME type for a given InputSourceType."""
        mapping = {
            InputSourceType.IMAGE: "image/png",
            InputSourceType.PDF: "application/pdf",
            InputSourceType.TEXT: "text/plain",
            InputSourceType.MARKDOWN: "text/markdown",
        }
        return mapping[source_type]
