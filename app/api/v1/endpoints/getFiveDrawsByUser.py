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

from app.services.extract import JsonExtractor

router = APIRouter()

@router.get(
    "/five/{spread_type}/{count}",
    summary="Buscar últimas 5 tiragens por tipo de spread (resumido)",
    description=(
        "Retorna até 5 tiragens recentes associadas a um tipo de spread (método de leitura), "
        "que pertençam ao usuário autenticado e que estejam com status 'completo'. "
        "Retorna dados resumidos para listagem: baralho, cartas, contexto resumido e tópicos. "
        "Para detalhes completos (leitura, cartas invertidas, etc), use o endpoint específico da tiragem."
    ),
    response_description="Lista resumida de tiragens encontradas",
    responses={
        200: {
            "description": "Tiragens encontradas com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "draws": [
                            {
                                "id": 1,
                                "spread_type": "Cruz Celta",
                                "deck": "Baralho Rider-Waite",
                                "cards": ["O Louco", "A Imperatriz", "O Mundo"],
                                "context": "Pergunta sobre carreira...",
                                "topics": ["Carreira", "Objetivos"],
                                "created_at": "2024-05-25T15:30:00",
                                "card_style": "traditional"
                            }
                        ],
                        "pagination": {
                            "current_page": 1,
                            "total_pages": 3,
                            "total_items": 15,
                            "items_per_page": 5,
                            "has_next": True,
                            "has_previous": False
                        }
                    }
                }
            }
        },
        400: {"description": "Dados inválidos ou usuário não encontrado."},
        401: {"description": "Token não fornecido ou inválido."},
        404: {"description": "Tiragens, baralho, cartas ou tópicos não encontrados."},
        500: {"description": "Erro interno do servidor."},
    },
)
async def get_five_draws(
    request: Request,
    spread_type: int,
    count: int,
    db: AsyncSession = Depends(get_session)
):
    """
    Recupera até 5 tiragens resumidas de um usuário autenticado, baseado no tipo de spread.
    Retorna apenas informações essenciais para listagem.
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

        # Verifica se o tipo de spread existe
        if not await SpreadTypeSchema.spread_type_exists(db, spread_type):
            raise HTTPException(status_code=400, detail="Tipo de spread inexistente.")

        spreadname = await SpreadTypeSchema.get_spread_type_name_by_id(db, spread_type)

        # ID do status 'completed'
        id_completed = await StatusSchema.get_id_by_name(db, "completed")

        # Busca as tiragens completas
        # Busca o total de tiragens para metadados de paginação
        total_draws = await DrawSchemaBase.get_total_draws_count(
            session=db,
            user_id=user_id,
            spread_type=spread_type,
            status=id_completed
        )

        # Busca as tiragens completas
        draws = await DrawSchemaBase.get_draws_by_user(
            session=db,
            user_id=user_id,
            spread_type=spread_type,
            count=count,
            limit=5,
            status=id_completed
        )

        if not draws:
            raise HTTPException(status_code=404, detail="Nenhuma tiragem encontrada.")

        draws_list = []
        for draw in draws:
            # Busca o nome do baralho
            deck = await DeckSchema.get_deck_name_by_id(db, draw.deck_id)
            if not deck:
                raise HTTPException(status_code=404, detail="Baralho não encontrado.")

            # Busca nomes das cartas sorteadas
            cards = await CardSchema.get_card_names_by_ids(db, draw.cards)
            if not cards:
                raise HTTPException(status_code=404, detail="Cartas não encontradas.")

            # Busca os tópicos
            topics = await TopicSchema.get_topic_names_by_id(db, draw.topics)
            if not topics:
                raise HTTPException(status_code=404, detail="Tópicos não encontrados.")
            
            # Pegar o nome do estilo de carta
            # Se tiver vazio ou None, usar o padrão 1
            if not draw.card_style:
                draw.card_style = 1
            card_style_name = await CardStylesSchema.get_card_style_name_by_id(db, draw.card_style)
            
            # Resumir contexto (primeiros 100 caracteres)
            context_summary = draw.context[:100] + "..." if len(draw.context) > 100 else draw.context

            draws_list.append({
                "id": draw.id,
                "spread_type": spreadname,
                "deck": deck,
                "cards": cards,
                "context": context_summary,
                "topics": topics,
                "created_at": draw.created_at.isoformat(),
                "card_style": card_style_name
            })

        # Calcula metadados de paginação
        total_pages = (total_draws + 4) // 5  # Arredonda para cima
        has_next = count < total_pages
        has_previous = count > 1

        return JSONResponse(content={
            "draws": draws_list,
            "pagination": {
                "current_page": count,
                "total_pages": total_pages,
                "total_items": total_draws,
                "items_per_page": 5,
                "has_next": has_next,
                "has_previous": has_previous
            }
        }, status_code=200)

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro de banco de dados: {str(e)}") from e
