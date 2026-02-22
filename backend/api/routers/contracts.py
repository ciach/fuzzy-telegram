from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.presenters import to_contract_view, to_log_view
from backend.dependencies import get_contract_service
from backend.schemas.contract_schema import (
    ContractLogView,
    ContractMutationRequest,
    ContractView,
    CreateContractRequest,
)
from backend.services.contract_service import ContractNotFoundError, ContractService, MutationValidationError

router = APIRouter(prefix="/contracts", tags=["contracts"])


@router.post("", response_model=ContractView, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: CreateContractRequest,
    contract_service: ContractService = Depends(get_contract_service),
) -> ContractView:
    record = contract_service.create_contract(language=payload.language, location=payload.location)
    return to_contract_view(record)


@router.get("/{contract_id}", response_model=ContractView)
def get_contract(
    contract_id: UUID,
    contract_service: ContractService = Depends(get_contract_service),
) -> ContractView:
    try:
        record = contract_service.get_contract(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return to_contract_view(record)


@router.patch("/{contract_id}", response_model=ContractView)
def mutate_contract(
    contract_id: UUID,
    payload: ContractMutationRequest,
    contract_service: ContractService = Depends(get_contract_service),
) -> ContractView:
    try:
        record, _ = contract_service.apply_update(
            contract_id=contract_id,
            path=payload.path,
            value=payload.value,
            action_type="update_field",
            triggered_by="user",
        )
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MutationValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return to_contract_view(record)


@router.get("/{contract_id}/logs", response_model=list[ContractLogView])
def get_contract_logs(
    contract_id: UUID,
    contract_service: ContractService = Depends(get_contract_service),
) -> list[ContractLogView]:
    try:
        records = contract_service.get_logs(contract_id)
    except ContractNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return [to_log_view(item) for item in records]

