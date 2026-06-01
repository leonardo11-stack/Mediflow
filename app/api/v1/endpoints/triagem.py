import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import case, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.triagem import Triagem as TriagemModel
from app.schemas.triagem import Prioridade, TriagemCreate, TriagemResponse
from app.services.gemini_service import GeminiService, get_gemini_service

router = APIRouter()
logger = logging.getLogger(__name__)

def _to_response(model: TriagemModel) -> TriagemResponse:
    return TriagemResponse(
        id=model.id,
        nome=model.nome,
        email=model.email,
        idade=model.idade,
        sintomas=model.sintomas,
        observacoes=model.observacoes,
        prioridade=Prioridade(model.prioridade),
        resumo_clinico=model.resumo_clinico,
        possiveis_causas=list(model.possiveis_causas or []),
        medicamentos_iniciais=list(model.medicamentos_iniciais or []),
        criado_em=model.criado_em,
    )


def _notificar_n8n(triagem: TriagemResponse) -> None:
    payload = triagem.model_dump(mode="json")
    try:
        with httpx.Client(timeout=15.0) as client:
            response = client.post(settings.N8N_WEBHOOK_URL, json=payload)
            response.raise_for_status()
        logger.info("Webhook n8n notificado com sucesso (triagem id=%s)", triagem.id)
    except httpx.HTTPError as exc:
        logger.warning(
            "Falha ao notificar webhook n8n (triagem id=%s): %s",
            triagem.id,
            exc,
        )
    except Exception:
        logger.exception(
            "Erro inesperado ao notificar webhook n8n (triagem id=%s)",
            triagem.id,
        )


@router.get(
    "/triagem",
    response_model=list[TriagemResponse],
    status_code=status.HTTP_200_OK,
)
def listar_triagens(
    db: Session = Depends(get_db),
    order_by: str = "prioridade",
    limit: int = 50,
    offset: int = 0,
) -> list[TriagemResponse]:
    """
    Lista triagens salvas.

    order_by:
      - prioridade: ALTA → MEDIA → BAIXA (mais recentes primeiro dentro da mesma prioridade)
      - criado_em: mais recentes primeiro
    """
    limit = max(1, min(limit, 200))
    offset = max(0, offset)

    query = db.query(TriagemModel)

    if order_by == "criado_em":
        query = query.order_by(desc(TriagemModel.criado_em))
    else:
        prioridade_rank = case(
            (TriagemModel.prioridade == Prioridade.ALTA.value, 3),
            (TriagemModel.prioridade == Prioridade.MEDIA.value, 2),
            (TriagemModel.prioridade == Prioridade.BAIXA.value, 1),
            else_=0,
        )
        query = query.order_by(desc(prioridade_rank), desc(TriagemModel.criado_em))

    rows = query.offset(offset).limit(limit).all()
    return [_to_response(row) for row in rows]


@router.post(
    "/triagem",
    response_model=TriagemResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_triagem(
    payload: TriagemCreate,
    db: Session = Depends(get_db),
    gemini_service: GeminiService = Depends(get_gemini_service),
) -> TriagemResponse:
    try:
        analise = gemini_service.analisar_triagem(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.exception("Erro ao chamar Gemini")
        detail = str(exc) or repr(exc) or exc.__class__.__name__
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=detail,
        ) from exc

    registro = TriagemModel(
        nome=payload.nome,
        email=str(payload.email),
        idade=payload.idade,
        sintomas=payload.sintomas,
        observacoes=payload.observacoes,
        prioridade=analise.prioridade.value,
        resumo_clinico=analise.resumo_clinico,
        possiveis_causas=analise.possiveis_causas,
        medicamentos_iniciais=analise.medicamentos_iniciais,
    )

    try:
        db.add(registro)
        db.commit()
        db.refresh(registro)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Falha ao persistir triagem no banco de dados.",
        ) from exc

    triagem_response = _to_response(registro)
    _notificar_n8n(triagem_response)
    return triagem_response
