from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import HTMLResponse, Response

from app.api.dependencies import (
    get_analysis_storage,
    get_export_service,
    get_file_service,
    get_pdf_service,
    get_pipeline,
)
from app.models.analysis_record import AnalysisRecord
from app.schemas.analysis import (
    AnalysisCreateResponse,
    AnalysisRecordResponse,
    UploadResponse,
)
from app.services.analysis_pipeline import CertificateAnalysisPipeline
from app.services.file_service import FileService
from app.services.html_exporter import HTMLExportService
from app.services.pdf_exporter import PDFExportService
from app.services.storage import InMemoryAnalysisStorage

router = APIRouter(prefix="/analyses", tags=["analyses"])


def _to_response(record: AnalysisRecord) -> AnalysisRecordResponse:
    return AnalysisRecordResponse(
        id=record.id,
        filename=record.filename,
        content_type=record.content_type,
        analysis=record.analysis,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_certificate(
    file: UploadFile = File(...),
    file_service: FileService = Depends(get_file_service),
) -> UploadResponse:
    payload = await file_service.read_and_validate(file)
    return UploadResponse(
        upload_id=str(uuid4()),
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
    )


@router.post("", response_model=AnalysisCreateResponse, status_code=status.HTTP_201_CREATED)
async def analyze_certificate(
    file: UploadFile = File(...),
    form_file: UploadFile | None = File(default=None),
    clinical_file: UploadFile | None = File(default=None),
    observations: str | None = Form(default=None),
    file_service: FileService = Depends(get_file_service),
    pipeline: CertificateAnalysisPipeline = Depends(get_pipeline),
    storage: InMemoryAnalysisStorage = Depends(get_analysis_storage),
) -> AnalysisCreateResponse:
    payload = await file_service.read_and_validate(file)
    form_payload = None
    if form_file is not None:
        form_payload = await file_service.read_and_validate(form_file)
    clinical_payload = None
    if clinical_file is not None:
        clinical_payload = await file_service.read_and_validate(clinical_file)

    analysis = await pipeline.analyze(
        payload,
        form_payload=form_payload,
        clinical_payload=clinical_payload,
        observations=observations,
    )
    record = storage.create(
        filename=payload.filename,
        content_type=payload.content_type,
        size_bytes=payload.size_bytes,
        source_bytes=payload.raw_bytes,
        analysis=analysis,
    )
    return AnalysisCreateResponse(
        id=record.id,
        filename=record.filename,
        content_type=record.content_type,
        analysis=record.analysis,
    )


@router.get("/{analysis_id}", response_model=AnalysisRecordResponse)
async def get_analysis(
    analysis_id: str,
    storage: InMemoryAnalysisStorage = Depends(get_analysis_storage),
) -> AnalysisRecordResponse:
    record = storage.get(analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un análisis con ese ID.",
        )
    return _to_response(record)


@router.post("/{analysis_id}/regenerate", response_model=AnalysisRecordResponse)
async def regenerate_analysis(
    analysis_id: str,
    pipeline: CertificateAnalysisPipeline = Depends(get_pipeline),
    storage: InMemoryAnalysisStorage = Depends(get_analysis_storage),
) -> AnalysisRecordResponse:
    record = storage.get(analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un análisis con ese ID.",
        )

    from app.schemas.document import DocumentPayload

    payload = DocumentPayload(
        filename=record.filename,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        raw_bytes=record.source_bytes,
    )
    analysis = await pipeline.analyze(payload)
    updated_record = storage.update_analysis(analysis_id, analysis)
    if not updated_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El análisis no pudo actualizarse.",
        )
    return _to_response(updated_record)


@router.get("/{analysis_id}/html", response_class=HTMLResponse)
async def export_analysis_html(
    analysis_id: str,
    storage: InMemoryAnalysisStorage = Depends(get_analysis_storage),
    exporter: HTMLExportService = Depends(get_export_service),
) -> HTMLResponse:
    record = storage.get(analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un análisis con ese ID.",
        )
    return HTMLResponse(content=exporter.render(record.analysis))


@router.get("/{analysis_id}/pdf")
async def export_analysis_pdf(
    analysis_id: str,
    storage: InMemoryAnalysisStorage = Depends(get_analysis_storage),
    exporter: PDFExportService = Depends(get_pdf_service),
) -> Response:
    record = storage.get(analysis_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un análisis con ese ID.",
        )

    pdf_bytes = exporter.render(record.analysis)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": 'attachment; filename="informe_laboral_inclusivo.pdf"'
        },
    )
