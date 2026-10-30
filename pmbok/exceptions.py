"""Custom exceptions for the PMBOK system."""

from __future__ import annotations


class PMBOKError(Exception):
    """Base exception for all PMBOK system errors."""


class InputValidationError(PMBOKError):
    """Raised when a raw input fails validation (size, format, batch limit)."""


class OCRError(PMBOKError):
    """Raised when OCR processing fails on an image or PDF input."""


class LLMError(PMBOKError):
    """Raised when an LLM API call fails (network, auth, rate-limit, etc.)."""


class LLMParseError(PMBOKError):
    """
    Raised when an LLM response cannot be parsed into the expected data model.
    Should include location info and the first 500 chars of the raw response.
    """


class ProcessExecutionError(PMBOKError):
    """Raised when a Process_Agent encounters an unrecoverable execution error."""


class InputProcessingError(PMBOKError):
    """Raised when processing a single input fails (OCR, decode, etc.)."""
