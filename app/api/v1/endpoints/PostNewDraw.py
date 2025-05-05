from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_session
from app.schemas.draw import DrawCreate
from app.schemas.user import UserSchemaBase  # Import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchema  # Import SpreadTypeSchema
from app.services.token import TokenInfoSchema # Import TokenInfoSchema

router = APIRouter()

@router.post(
        "/new",
    summary="Criar uma nova tiragem de tarô",
    description="Cria um nova tiragem de tarô com os detalhes fornecidos.",
    response_description="Detalhes da tiragem criada.",
    responses={
        201: {
            "description": "Criação bem-sucedida de uma nova tiragem.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Draw created successfully.",
                        "draw": {
                            "id": 1,
                            "user_id": 123,
                            "spread_type_id": 2,
                            "status": "completed",
                            "created_at": "2023-10-01T12:00:00Z"
                        }
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
async def post_new_draw(
    request: Request,
    draw_data: DrawCreate,
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
        # verifica se o tipo de spread existe
        spreadexists = await SpreadTypeSchema.spread_type_exists(db, draw_data.spread_type_id)
        
        # spread_type_exists(db, draw_data.spread_type_id)
        if not spreadexists:
            raise HTTPException(
                status_code=400, 
                detail="Spread type does not exist."
            )
        
        
        new_draw = await DrawCreate.create_draw(
            db, 
            user_id=user_id, 
            spread_type_id=draw_data.spread_type_id
        )
        return {
            "message": "Draw created successfully.",
            "draw": {
                "id": new_draw.id,
                "user_id": user_id,
                "spread_type_id": new_draw.spread_type_id,
                "status": new_draw.status_id,
                "created_at": new_draw.created_at
            }
        }
    except SQLAlchemyError as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while creating the draw: {str(e)}"
        )