from __future__ import annotations

import base64
import io
from pathlib import Path

import fitz
from fastapi import HTTPException, UploadFile, status
from PIL import Image, UnidentifiedImageError

from app.core.config import Settings, get_settings
from app.core.logging import logger
from app.schemas.document import DocumentPayload, ExtractedDocumentContent

ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
}

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".webp"}


class FileService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    async def read_and_validate(self, file: UploadFile) -> DocumentPayload:
        filename = file.filename or "documento"
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Formato de archivo no soportado. Use PDF, JPG, JPEG, PNG o WEBP.",
            )

        content = await file.read()
        if not content:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío.",
            )

        if len(content) > self.settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=(
                    f"El archivo supera el límite permitido de "
                    f"{self.settings.max_file_size_mb} MB."
                ),
            )

        content_type = (file.content_type or "").lower()
        if content_type and content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El content type del archivo no es válido para este servicio.",
            )

        if extension == ".pdf":
            detected_content_type = "application/pdf"
        else:
            detected_content_type = content_type or f"image/{extension.replace('.', '')}"

        return DocumentPayload(
            filename=filename,
            content_type=detected_content_type,
            size_bytes=len(content),
            raw_bytes=content,
        )

    def extract_document_content(
        self, payload: DocumentPayload
    ) -> ExtractedDocumentContent:
        if payload.content_type == "application/pdf":
            return self._extract_from_pdf(payload)
        return self._extract_from_image(payload)

    def extract_supporting_text(self, payload: DocumentPayload) -> str:
        extracted = self.extract_document_content(payload)
        return extracted.extracted_text.strip()

    def _extract_from_image(self, payload: DocumentPayload) -> ExtractedDocumentContent:
        image_data_url = self._normalize_image_to_data_url(
            payload.raw_bytes, payload.content_type
        )
        if self.settings.analysis_debug:
            logger.info(
                "[ANALYSIS_DEBUG][file_service] filename=%s is_pdf=%s extracted_chars=%s image_count=%s used_vision=%s pdf_always_include_images_for_openai=%s",
                payload.filename,
                False,
                0,
                1,
                True,
                self.settings.pdf_always_include_images_for_openai,
            )
        return ExtractedDocumentContent(
            extracted_text="",
            image_data_urls=[image_data_url],
            source_type="image",
            page_count=1,
            used_vision=True,
        )

    def _extract_from_pdf(self, payload: DocumentPayload) -> ExtractedDocumentContent:
        try:
            document = fitz.open(stream=payload.raw_bytes, filetype="pdf")
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fue posible leer el PDF proporcionado.",
            ) from exc

        extracted_text_parts: list[str] = []
        image_data_urls: list[str] = []
        pages_to_render = min(len(document), self.settings.max_pdf_pages_for_vision)

        for page_index, page in enumerate(document):
            page_text = page.get_text("text").strip()
            if page_text:
                extracted_text_parts.append(f"[Página {page_index + 1}]\n{page_text}")

            if page_index < pages_to_render:
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image_bytes = pixmap.tobytes("png")
                image_data_urls.append(
                    self._normalize_image_to_data_url(image_bytes, "image/png")
                )

        extracted_text = "\n\n".join(extracted_text_parts)
        used_vision = len(extracted_text.strip()) < 80
        include_images_for_openai = (
            self.settings.pdf_always_include_images_for_openai or used_vision
        )
        if self.settings.analysis_debug:
            logger.info(
                "[ANALYSIS_DEBUG][file_service] filename=%s is_pdf=%s extracted_chars=%s image_count=%s used_vision=%s pdf_always_include_images_for_openai=%s",
                payload.filename,
                True,
                len(extracted_text),
                len(image_data_urls if include_images_for_openai else []),
                used_vision,
                self.settings.pdf_always_include_images_for_openai,
            )
        return ExtractedDocumentContent(
            extracted_text=extracted_text,
            image_data_urls=image_data_urls if include_images_for_openai else [],
            source_type="pdf",
            page_count=len(document),
            used_vision=used_vision,
        )

    def _normalize_image_to_data_url(self, raw_bytes: bytes, content_type: str) -> str:
        try:
            image = Image.open(io.BytesIO(raw_bytes))
        except UnidentifiedImageError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="La imagen no pudo ser procesada.",
            ) from exc

        image = image.convert("RGB")
        image.thumbnail(
            (self.settings.max_image_dimension, self.settings.max_image_dimension)
        )

        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=90, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
