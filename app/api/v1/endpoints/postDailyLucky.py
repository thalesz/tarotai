from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_session
from app.schemas.draw import DrawCreate
from app.schemas.user import UserSchemaBase  # Import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchema  # Import SpreadTypeSchema
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.schemas.daily_lucky import DailyLuckySchemaBase  # Import DailyLuckySchemaBase

router = APIRouter()

@router.post(
        "/new",
    summary="Criar uma nova sorte diaria",
    description="Cria um novo 'biscoito da sorte' diario.",
    response_description="Mensagem de sucesso ou erro.",
    responses={
        201: {
            "description": "Criação bem-sucedida de uma nova tiragem.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Daily Lucky created successfully.",
                    }
                }
            },
        },
        400: {
            "description": "Requisição inválida devido a dados de entrada inválidos.",
            "content": {
                "application/json": {
                    "example": {"detail": "Dados de entrada inválidos."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao criar o sorteio."}
                }
            },
        },
    },
)
async def post_new_daily_lucky(
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
        
        # verifica se o usuario existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
            
        # Cria o novo Daily Lucky
        await DailyLuckySchemaBase.create_daily_lucky(
            session=db,
            user_id=user_id
        )
        
        return {"message": "Daily Lucky created successfully."}
        
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while creating the draw: {str(e)}"
        )