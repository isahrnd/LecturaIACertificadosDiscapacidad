from __future__ import annotations

from app.core.logging import logger
from app.schemas.analysis import CertificateAnalysisSchema
from app.schemas.document import DocumentPayload, OpenAIAnalysisRequest
from app.services.file_service import FileService
from app.services.openai_service import OpenAIAnalysisService


class CertificateAnalysisPipeline:
    def __init__(
        self,
        file_service: FileService,
        openai_service: OpenAIAnalysisService,
    ) -> None:
        self.file_service = file_service
        self.openai_service = openai_service

    async def analyze(
        self,
        payload: DocumentPayload,
        *,
        form_payload: DocumentPayload | None = None,
        clinical_payload: DocumentPayload | None = None,
        observations: str | None = None,
    ) -> CertificateAnalysisSchema:
        extracted = self.file_service.extract_document_content(payload)
        form_text = ""
        if form_payload is not None:
            form_text = self.file_service.extract_supporting_text(form_payload)
        clinical_text = ""
        if clinical_payload is not None:
            clinical_text = self.file_service.extract_supporting_text(clinical_payload)

        logger.info(
            "Documento procesado. source_type=%s page_count=%s used_vision=%s form_attached=%s clinical_attached=%s",
            extracted.source_type,
            extracted.page_count,
            extracted.used_vision,
            form_payload is not None,
            clinical_payload is not None,
        )
        request = OpenAIAnalysisRequest(
            text=extracted.extracted_text,
            image_data_urls=extracted.image_data_urls,
            filename=payload.filename,
            content_type=payload.content_type,
            observations=(observations or "").strip() or None,
            form_text=form_text or None,
        )
        return await self.openai_service.analyze_certificate(
            request,
            used_vision=extracted.used_vision,
            clinical_text=clinical_text or None,
        )


def get_analysis_pipeline() -> CertificateAnalysisPipeline:
    return CertificateAnalysisPipeline(
        file_service=FileService(),
        openai_service=OpenAIAnalysisService(),
    )
