from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_session
from app.schemas.draw import DrawSchemaBase
from app.schemas.spread_type import SpreadTypeSchema
from app.schemas.user import UserSchemaBase
from app.schemas.card import CardSchema
from app.schemas.deck import DeckSchema
from app.schemas.status import StatusSchema
from app.schemas.topic import TopicSchema
from app.schemas.card_styles import CardStylesSchema
from app.services.token import TokenInfoSchema

router = APIRouter()

@router.get(
    "/{draw_id}",
    summary="Buscar tiragem completa por ID",
    description=(
        "Retorna todos os detalhes de uma tiragem específica que pertença ao usuário autenticado. "
        "Inclui informações completas: baralho, cartas, cartas invertidas, contexto, tópicos, "
        "leitura completa, estilo de carta e todas as outras propriedades da tiragem."
    ),
    response_description="Detalhes completos da tiragem",
    responses={
        200: {
            "description": "Tiragem encontrada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "user_id": 123,
                        "spread_type": "Cruz Celta",
                        "deck": "Baralho Rider-Waite",
                        "cards": [
                            {"id": 1, "name": "O Louco", "position": 0},
                            {"id": 2, "name": "A Imperatriz", "position": 1}
                        ],
                        "reversed_cards": [1],
                        "context": "Pergunta detalhada sobre carreira e futuro profissional...",
                        "reading": "Interpretação completa da tiragem...",
                        "topics": ["Carreira", "Objetivos"],
                        "card_style": "traditional",
                        "status": "completed",
                        "created_at": "2024-05-25T15:30:00",
                        "updated_at": "2024-05-25T15:35:00"
                    }
                }
            }
        },
        400: {"description": "Dados inválidos ou usuário não encontrado."},
        401: {"description": "Token não fornecido ou inválido."},
        403: {"description": "Tiragem não pertence ao usuário autenticado."},
        404: {"description": "Tiragem não encontrada."},
        500: {"description": "Erro interno do servidor."},
    },
)
async def get_draw_by_id(
    request: Request,
    draw_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Recupera todos os detalhes de uma tiragem específica do usuário autenticado.
    Retorna informações completas incluindo leitura, cartas invertidas e todos os metadados.
    """

    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(status_code=401, detail="Informações do token estão ausentes.")

        user_id = getattr(token_info, "id", None)
        if user_id is None:
            raise HTTPException(status_code=400, detail="ID do usuário ausente no token.")

        # Verifica se o usuário existe
        if not await UserSchemaBase.user_exists(db, user_id):
            raise HTTPException(status_code=400, detail="Usuário não encontrado.")

        # Busca a tiragem pelo ID
        draw = await DrawSchemaBase.get_draw_by_id(db, draw_id)
        if draw is None:
            raise HTTPException(status_code=404, detail="Tiragem não encontrada.")

        # Verifica se a tiragem pertence ao usuário autenticado
        if draw.user_id != user_id:
            raise HTTPException(status_code=403, detail="Você não tem permissão para acessar esta tiragem.")
        
        # Verifica se a tiragem está completa
        id_completed = await StatusSchema.get_id_by_name(db, "completed")
        if draw.status_id != id_completed:
            raise HTTPException(status_code=404, detail="Tiragem não encontrada.")

        # Busca o nome do tipo de spread
        spread_type_name = await SpreadTypeSchema.get_spread_type_name_by_id(db, draw.spread_type_id)
        
        # Busca o nome do baralho
        deck_name = "Sem baralho"
        if draw.deck_id:
            deck_result = await DeckSchema.get_deck_name_by_id(db, draw.deck_id)
            if deck_result:
                deck_name = deck_result

        # Busca detalhes completos das cartas (ID e nome)
        cards_details = []
        if draw.cards:
            cards_names = await CardSchema.get_cards_names_by_group_ids(db, draw.cards, keep_order=True)
            if cards_names:
                cards_details = [
                    {
                        "id": draw.cards[idx],
                        "name": cards_names[idx],
                        "position": idx
                    }
                    for idx in range(len(cards_names))
                ]

        # Busca os nomes dos tópicos
        topics = []
        if draw.topics:
            topics = await TopicSchema.get_topic_names_by_id(db, draw.topics)
        
        # Busca o nome do estilo de carta
        card_style_id = draw.card_style if draw.card_style else 1
        card_style_name = await CardStylesSchema.get_card_style_name_by_id(db, card_style_id)
        
        # Busca o nome do status
        status_name = await StatusSchema.get_name_by_id(db, draw.status_id)

        # Monta a resposta completa
        draw_complete = {
            "id": draw.id,
            "user_id": draw.user_id,
            "spread_type": spread_type_name,
            "spread_type_id": draw.spread_type_id,
            "deck": deck_name,
            "deck_id": draw.deck_id,
            "cards": cards_details,
            "reversed_cards": draw.is_reversed if draw.is_reversed else [],
            "context": draw.context,
            "reading": draw.reading if draw.reading else "",
            "topics": topics,
            "card_style": card_style_name,
            "card_style_id": card_style_id,
            "status": status_name,
            "status_id": draw.status_id,
            "created_at": draw.created_at.isoformat(),
            "updated_at": draw.used_at.isoformat() if draw.used_at else None
        }

        return JSONResponse(content=draw_complete, status_code=200)

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro de banco de dados: {str(e)}") from e
