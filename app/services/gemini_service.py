import logging
from functools import lru_cache

from google import genai
from google.genai import types
from google.genai.errors import ClientError

from app.core.config import settings
from app.schemas.triagem import TriagemAIResponse, TriagemCreate

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Você é um assistente clínico de triagem do MediFlow AI.
Analise os dados do paciente e produza uma triagem estruturada em português brasileiro.
Classifique a prioridade como ALTA (emergência/risco iminente), MEDIA (atenção em horas) ou BAIXA (caso estável/rotina).
O resumo_clinico deve ser objetivo e em linguagem técnica acessível.
Liste possiveis_causas e medicamentos_iniciais apenas como sugestões iniciais de triagem — não substituem avaliação médica presencial.
Não invente dados que não foram informados."""


def _formatar_erro_gemini(exc: ClientError) -> str:
    message = str(exc)
    if "API_KEY_INVALID" in message or "API key not valid" in message:
        return "Gemini: API_KEY_INVALID — chave inválida ou revogada."
    if "429" in message or "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
        return (
            "Gemini: RESOURCE_EXHAUSTED — cota do plano gratuito esgotada ou indisponível "
            f"para o modelo '{settings.GEMINI_MODEL}'. Tente 'gemini-2.5-flash' ou 'gemini-2.5-flash-lite'."
        )
    if "503" in message or "UNAVAILABLE" in message:
        return (
            f"Gemini: UNAVAILABLE — modelo '{settings.GEMINI_MODEL}' sob alta demanda. "
            "Tente novamente em instantes ou use 'gemini-2.5-flash-lite'."
        )
    if "404" in message or "NOT_FOUND" in message:
        return f"Gemini: modelo '{settings.GEMINI_MODEL}' não encontrado ou indisponível."
    return f"Gemini: {message}"


class GeminiService:
    def __init__(self, client: genai.Client | None = None) -> None:
        self._client = client or genai.Client(api_key=settings.GEMINI_API_KEY)

    def analisar_triagem(self, dados: TriagemCreate) -> TriagemAIResponse:
        observacoes = dados.observacoes or "Nenhuma observação adicional."

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Paciente: {dados.nome}\n"
            f"Idade: {dados.idade} anos\n"
            f"Sintomas: {dados.sintomas}\n"
            f"Observações: {observacoes}"
        )

        try:
            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=TriagemAIResponse,
                ),
            )
        except ClientError as exc:
            erro = _formatar_erro_gemini(exc)
            logger.error("Falha na chamada ao Gemini: %s", erro)
            raise ValueError(erro) from exc

        if response.parsed is not None:
            if isinstance(response.parsed, TriagemAIResponse):
                return response.parsed
            return TriagemAIResponse.model_validate(response.parsed)

        if not response.text:
            raise ValueError("Resposta estruturada do Gemini ausente ou inválida.")

        return TriagemAIResponse.model_validate_json(response.text)


@lru_cache
def get_gemini_service() -> GeminiService:
    return GeminiService()
