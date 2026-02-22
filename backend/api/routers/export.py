from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response

from backend.dependencies import get_rendering_service
from backend.services.contract_service import ContractNotFoundError
from backend.services.rendering_service import RenderingService

router = APIRouter(prefix="/contracts", tags=["export"])


@router.post("/{contract_id}/export/docx")
def export_docx(
    contract_id: UUID,
    rendering_service: RenderingService = Depends(get_rendering_service),
) -> Response:
    try:
        file_bytes = rendering_service.export_docx(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="arras-{contract_id}.docx"'},
    )


@router.post("/{contract_id}/export/pdf")
def export_pdf(
    contract_id: UUID,
    rendering_service: RenderingService = Depends(get_rendering_service),
) -> Response:
    try:
        file_bytes = rendering_service.export_pdf(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="arras-{contract_id}.pdf"'},
    )
