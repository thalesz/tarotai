from typing import Optional

from fastapi import APIRouter, Query, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.user import UserSchemaBase
from app.services.token import TokenInfoSchema
from app.services.openai import OpenAIService
from app.schemas.welcome import WelcomeResponse
import datetime
import random

router = APIRouter()


_WELCOME_MESSAGES = {
    "general": "Bem-vindo ao TarotAI! Explore leituras, decks e mais.",
    "zodiac": "Bem-vindo à seção Zodíaco! Confira previsões e insights astrológicos personalizados.",
    "deck": "Bem-vindo aos Baralhos! Aqui você pode escolher e experimentar diferentes decks.",
    "reading": "Pronto para uma leitura? Vamos começar a interpretar suas cartas.",
}
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
    role = (
        "Você é um assistente acolhedor e inteligente, que escreve mensagens de boas-vindas curtas, naturais e humanas. "
        "Use um tom leve, simpático e descontraído, como alguém recebendo um amigo. "
        "A mensagem deve ter no máximo 1–2 frases e pode incluir uma pequena piada bem suave, mas sem exageros. "
        "Evite linguagem robótica, evite formalidade excessiva e não explique o que está fazendo. "
        "Não utilize estrutura de lista, não utilize markdown e não inclua instruções técnicas. "
        "Apenas entregue a mensagem de forma direta, espontânea e amigável."
    )

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
    # instruções adicionais: caso `include_date` seja True, inclua o contexto de data
    date_context = f"Data atual: {today_str}, dia da semana: {weekday_pt}."
    date_instruction = (
        f" Você pode começar a mensagem com uma menção natural à data/dia (ex.: 'Hoje, {weekday_pt}, ...') ou incluir a data brevemente. {date_context}"
        if include_date
        else ""
    )

    if user_name:
        prompt = (
            f"Crie uma mensagem de boas-vindas curta e simpática (1–2 frases) para o usuário '{user_name}' "
            f"que acabou de entrar em {friendly_name}. "
            f"Escreva em português brasileiro, com leveza e proximidade, incluindo uma piada suave e amigável. "
            f"A mensagem deve parecer algo dito por uma pessoa real."
            + date_instruction
            + " Não inclua explicações, markdown ou detalhes técnicos."
        )
    else:
        prompt = (
            f"Gere uma mensagem de boas-vindas curta (1-2 frases) e uma piadinha para um usuário que acabou de acessar {friendly_name}. "
            f"A mensagem deve ser em português, calorosa e convidativa. Não inclua marcações nem instruções técnicas." 
            + date_instruction
        )

    try:
        openai_service = OpenAIService()
        # parâmetros sensatos para uma mensagem curta
        ai_message = await openai_service.gerar_texto(
            prompt_ajustado=prompt, role=role, max_tokens=80, temperature=0.9
        )

        # Caso a IA retorne vazio ou erro textual, usamos fallback
        if not ai_message or ai_message.lower().startswith("erro"):
            raise Exception("IA retornou conteúdo inválido")

        return JSONResponse(content={"message": ai_message.strip(), "category": key, "source": "ai"})
    except Exception:
        # fallback para mensagem local
        fallback = _WELCOME_MESSAGES.get(key, _WELCOME_MESSAGES["general"])
        return JSONResponse(content={"message": fallback, "category": key, "source": "fallback"})
