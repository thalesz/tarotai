from typing import Optional

from fastapi import APIRouter, Query, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.user import UserSchemaBase
from app.services.token import TokenInfoSchema
from app.services.openai import OpenAIService
from app.schemas.welcome import WelcomeResponse
from app.prompts.welcome import WELCOME_MESSAGES, build_welcome_role, build_welcome_prompt
import datetime
import random

router = APIRouter()

_WELCOME_MESSAGES = WELCOME_MESSAGES
@router.get(
    "/",
    summary="Mensagem de boas-vindas",
    response_description="Mensagem de boas-vindas personalizada conforme o tipo solicitado",
    response_model=WelcomeResponse,
    responses={
        200: {
            "description": "Mensagem gerada com sucesso",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Olá, Thales! Bem-vindo ao TarotAI — hoje é um ótimo dia para uma leitura rápida.",
                        "category": "general",
                        "source": "template",
                    }
                }
            },
        },
        401: {
            "description": "Token ausente ou inválido",
            "content": {"application/json": {"example": {"detail": "token information is missing"}}},
        },
        500: {
            "description": "Erro interno ao gerar mensagem",
            "content": {"application/json": {"example": {"detail": "Erro interno ao gerar mensagem"}}},
        },
    },
)
async def get_welcome(
    category: str = Query(
        "general", description="Tipo de boas-vindas (e.g. general, zodiac, deck, reading)"
    ),
    request: Request = None,
    db: AsyncSession = Depends(get_session),
):
    """Gera uma mensagem de boas-vindas via IA de acordo com `category`.

    - category: esperado em minúsculas: `general`, `zodiac`, `deck`, `reading`.
    - user_id: opcional; se fornecido, o nome do usuário será buscado e incluído no prompt.
    - Se a IA falhar, retorna uma mensagem padrão de fallback.
    """
    key = (category or "general").lower()

    # tenta obter informações do token, como em PutNewDraw
    user_name = None
    token_info: TokenInfoSchema = getattr(request.state, "token_info", None) if request is not None else None
    if token_info is not None:
        try:
            user_id = token_info.id
            user_name = await UserSchemaBase.get_user_name_by_id(db, user_id)
        except Exception:
            user_name = None

    # Prompt e role para orientar a IA a gerar mensagens curtas e acolhedoras em português
    role = build_welcome_role()

    # informação de data para uso opcional pela IA
    today = datetime.date.today()
    weekday_map = {
        0: "segunda-feira",
        1: "terça-feira",
        2: "quarta-feira",
        3: "quinta-feira",
        4: "sexta-feira",
        5: "sábado",
        6: "domingo",
    }
    weekday_pt = weekday_map.get(today.weekday(), "")
    today_str = today.isoformat()

    # decide aleatoriamente (≈30%) se a mensagem deve mencionar a data/dia
    include_date = random.random() < 0.3

    friendly_name = {
        "general": "o aplicativo",
        "zodiac": "a seção Zodíaco",
        "deck": "a seleção de Baralhos",
        "reading": "a área de Leituras",
    }.get(key, "o aplicativo")

    # monta o prompt considerando o nome do usuário quando disponível
    date_context = f"Data atual: {today_str}, dia da semana: {weekday_pt}."
    prompt = build_welcome_prompt(user_name, friendly_name, key, include_date, date_context, weekday_pt)

    try:
        openai_service = OpenAIService()
        # parâmetros sensatos para uma mensagem curta (máximo 20 palavras)
        ai_message = await openai_service.gerar_texto(
            prompt_ajustado=prompt, role=role, max_tokens=40, temperature=0.9
        )

        # Caso a IA retorne vazio ou erro textual, usamos fallback
        if not ai_message or ai_message.lower().startswith("erro"):
            raise Exception("IA retornou conteúdo inválido")

        return JSONResponse(content={"message": ai_message.strip(), "category": key, "source": "ai"})
    except Exception:
        # fallback para mensagem local
        fallback = _WELCOME_MESSAGES.get(key, _WELCOME_MESSAGES["general"])
        return JSONResponse(content={"message": fallback, "category": key, "source": "fallback"})
