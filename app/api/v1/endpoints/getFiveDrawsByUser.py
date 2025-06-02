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
from app.services.token import TokenInfoSchema

router = APIRouter()

@router.get(
    "/five/{spread_type}/{count}",
    summary="Buscar últimas 5 tiragens por tipo de spread",
    description=(
        "Retorna até 5 tiragens recentes associadas a um tipo de spread (método de leitura), "
        "que pertençam ao usuário autenticado e que estejam com status 'completo'. "
        "Inclui informações como baralho, cartas sorteadas, contexto, tópicos e leitura gerada."
    ),
    response_description="Lista de tiragens encontradas",
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
                                "context": "Pergunta sobre carreira.",
                                "status": "Completo",
                                "reading": {
                                    "introducao": "Esta é a introdução da leitura de tarot.",
                                    "carta_1": "Interpretação da primeira carta.",
                                    "carta_2": "Interpretação da segunda carta.",
                                    "conclusao": "Esta é a conclusão da leitura de tarot."
                                },
                                "topics": ["Carreira", "Objetivos"],
                                "created_at": "2024-05-25T15:30:00",
                                "used_at": "2024-05-25T16:00:00"
                            }
                        ]
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
    Recupera até 5 tiragens completas de um usuário autenticado, baseado no tipo de spread.
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

            draws_list.append({
                "id": draw.id,
                "spread_type": spreadname,
                "deck": deck,
                "cards": cards,
                "context": draw.context,
                "status": "Completo",
                "reading": draw.reading,
                "topics": topics,
                "created_at": draw.created_at.isoformat(),
                "used_at": draw.used_at.isoformat() if draw.used_at else None
            })

        return JSONResponse(content={"draws": draws_list}, status_code=200)

    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro de banco de dados: {str(e)}") from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}") from e
