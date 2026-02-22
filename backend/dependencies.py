from backend.db.session import get_session
from backend.services.ai_service import AIService
from backend.services.contract_service import ContractService
from backend.services.logging_service import AuditLoggingService
from backend.services.rendering_service import RenderingService
from backend.storage.sqlalchemy_store import SQLAlchemyStore

_store = SQLAlchemyStore(session_factory=get_session)
_audit_logging_service = AuditLoggingService()
_contract_service = ContractService(store=_store, audit_logging_service=_audit_logging_service)
_ai_service = AIService()
_rendering_service = RenderingService(contract_service=_contract_service)


def get_contract_service() -> ContractService:
    return _contract_service


def get_ai_service() -> AIService:
    return _ai_service


def get_rendering_service() -> RenderingService:
    return _rendering_service
