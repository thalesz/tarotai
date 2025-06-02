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

from app.services.extract import JsonExtractor  # Import JsonExtractor

router = APIRouter()



@router.get(
    "/five/{count}",
    summary="Pegar cinco biscoitos da sorte diários por usuário de acordo com o count",
    description="Retorna cinco biscoitos da sorte diários para o usuário autenticado, "
                "limitados pelo parâmetro 'count'. ",
    response_description="Lista de biscoitos da sorte diários.",
    responses={
        200: {
            "description": "Atualização bem-sucedida da tiragem.",
            "content": {
                "application/json": {
                    "example": {
                        "leitura": {
                            "introducao": "Esta é a introdução da leitura de tarot.",
                            "carta_1": "Interpretação da primeira carta.",
                            "carta_2": "Interpretação da segunda carta.",
                            "conclusao": "Esta é a conclusão da leitura de tarot."
                        }
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida devido a dados de entrada inválidos ou ausentes.",
            "content": {
                "application/json": {
                    "example": {"detail": "Dados de entrada inválidos."}
                }
            },
        },
        401: {
            "description": "Acesso não autorizado devido a token ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "Informações do token estão ausentes."}
                }
            },
        },
        404: {
            "description": "Recurso não encontrado, como uma tiragem inexistente.",
            "content": {
                "application/json": {
                    "example": {"detail": "Draw not found."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor devido a problemas no banco de dados ou outros.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while updating the draw."}
                }
            },
        },
    },
)



async def get_five_draws(
    request: Request,
    count: int,
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
        #print("userexists: ", userexists)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )

        id_completed = await StatusSchema.get_id_by_name(
            db=db,
            name="completed",
        )
        
        
        #agora pegar os ultimos 
        daily_luckies = await DailyLuckySchema.get_five_daily_lucky_by_user_id(
            session=db,
            user_id=user_id,
            status_id=id_completed,
            count=count
        )
        if not daily_luckies:
            raise HTTPException(
                status_code=404, 
                detail="No daily luckies found for the user."
            )
            
        # Prepare the response data
        response_data = []
        for daily_lucky in daily_luckies:
            reading = JsonExtractor.extract_json_from_reading(daily_lucky.reading)
            response_data.append({
                "id": daily_lucky.id,
                "reading": reading,
                "created_at": daily_lucky.created_at.isoformat(),
                "used_at": daily_lucky.used_at.isoformat() if daily_lucky.used_at else None
            })
        
        return JSONResponse(content=response_data, status_code=200)
        
        
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while updating the draw: {str(e)}") from e