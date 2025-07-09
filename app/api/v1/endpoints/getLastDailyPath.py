from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.future import select
from fastapi.responses import JSONResponse

from app.core.deps import get_session
from app.schemas.draw import DrawUpdate  # Import DrawUpdate schema
from app.schemas.spread_type import SpreadTypeSchema  # Import SpreadTypeSchema
from app.schemas.user import UserSchemaBase  # Import UserSchemaBase
from app.schemas.draw import DrawSchemaBase  # Import DrawSchemaBase
from app.schemas.card import CardSchema  # Import CardSchema
from app.schemas.deck import DeckSchema  # Import DeckSchema
from app.schemas.user_type import UserTypeSchema  # Import ClientSchema
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.services.openai import OpenAIService  # Import OpenAIService
from app.schemas.topic import TopicSchema  # Import TopicSchema
from app.schemas.status import StatusSchema  # Import StatusSchema
from app.schemas.daily_lucky import DailyLuckySchema  # Import DailyLuckySchema
from app.schemas.daily_zodiac import DailyZodiacSchemaBase  # Import DailyZodiacSchemaBase
from app.schemas.daily_path import DailyPathSchemaBase  # Import DailyPathSchemaBase

from app.services.extract import JsonExtractor  # Import JsonExtractor
from app.services.confirmMissionService import ConfirmMissionService
from app.schemas.mission_type import MissionTypeSchemaBase  # Import MissionTypeSchemaBase

router = APIRouter()


@router.get(
    "/today",
    summary="Receber o caminho diario atual do zodíaco.",
    description="Retorna o caminho diario do usuário autenticado.",
    response_description="Caminho diario do zodíaco retornado com sucesso.",
    responses={
        200: {
            "description": "Horóscopos diário retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "horoscopo": {
                                "diario": "Hoje, a energia de Virgem se destaca, trazendo um foco em organização e detalhes. Com a Lua em Touro, você pode sentir uma necessidade maior de estabilidade e conforto emocional. É um dia favorável para refletir sobre suas prioridades e fazer ajustes práticos na sua rotina. Aproveite a energia para concluir tarefas pendentes e colocar seus planos em ação.",
                                "amor": "No amor, a sua posição de Vênus em Escorpião sugere um dia intenso e profundo nas relações. As conversas podem se aprofundar e você poderá se sentir mais atraído por conexões emocionais significativas. Se está em um relacionamento, aproveite para discutir sentimentos e reavaliar a cumplicidade. Para os solteiros, uma conversa sincera pode abrir portas para novas possibilidades.",
                                "trabalho": "No trabalho, a energia de Marte em Escorpião demanda foco e determinação. Este é um bom momento para se lançar em projetos que exigem pesquisa e análise. Esteja atento a desafios que podem surgir, mas lembre-se de que você tem a capacidade de superá-los. Uma abordagem cuidadosa e estratégica será sua aliada ao lidar com tarefas complexas.",
                                "saude": "A saúde deve ser uma prioridade hoje, especialmente com a Lua em Touro, que enfatiza o bem-estar físico. Considere incorporar práticas de autocuidado, como uma alimentação saudável e exercícios que promovam a estabilidade emocional. O estresse pode ser minimizado com atividades relaxantes, como meditação ou uma caminhada ao ar livre.",
                                "financas": "Em relação às finanças, o dia pode apresentar oportunidades de investimento, principalmente por conta da influência de Júpiter em Aquário. Esteja aberto a novas ideias e propostas, mas mantenha uma análise crítica antes de tomar decisões. Evite gastos impulsivos e foque em economizar para futuros projetos.",
                                "espiritualidade": "Hoje é um dia propício para a introspecção e a meditação, especialmente com a influência da Lua. Aproveite para se conectar com suas emoções e buscar respostas internas. A energia de Netuno em Capricórnio sugere que o foco em metas práticas pode coexistir com a busca por um propósito maior. Reserve um tempo para refletir sobre suas crenças e valores."
                            }
                        }
                    ]
                }
            },
        },
        400: {
            "description": "Requisição inválida devido a dados de entrada inválidos ou ausentes.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not exist."}
                }
            },
        },
        401: {
            "description": "Acesso não autorizado devido a token ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "token information is missing"}
                }
            },
        },
        404: {
            "description": "Horóscopo diário não encontrado para o usuário.",
            "content": {
                "application/json": {
                    "example": {"detail": "Zodiaco diario não encontrado para o usuário."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor devido a problemas no banco de dados ou outros.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while updating the draw: <detalhes do erro>"}
                }
            },
        },
    },
)
async def get_daily_zodiac(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    try:
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(
                status_code=401, detail="token information is missing"
            )

        try:
            user_id = token_info.id
        except AttributeError:
            raise HTTPException(status_code=400, detail="User id not found in token")
        # verifica se o user existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        if not userexists:
            raise HTTPException(
                status_code=400,
                detail="User does not exist."
            )

        daily_path = await DailyPathSchemaBase.get_daily_path_by_user_id(
            session=db,
            user_id=user_id
        )

        if not daily_path:
            raise HTTPException(
                status_code=404,
                detail="Caminho diario não encontrado para o usuário."
            )


        confirm_service = ConfirmMissionService()
        mission_type_id = await MissionTypeSchemaBase.get_id_by_name(db, "Abrir o caminho diário")
        await confirm_service.confirm_mission(db,  mission_type_id, user_id)
        
        reading = JsonExtractor.extract_json_from_reading(daily_path.reading)
        return JSONResponse(content={"daily": reading}, status_code=200)


    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the draw: {str(e)}") from e