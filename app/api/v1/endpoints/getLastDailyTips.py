from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

from app.core.deps import get_session
from app.schemas.user import UserSchemaBase
from app.schemas.daily_tips import DailyTipsSchemaBase
from app.services.token import TokenInfoSchema
from app.services.extract import JsonExtractor

router = APIRouter()


@router.get(
    "/daily-tips/{count}",
    summary="Receber última(s) dica(s) diária(s). Count define qual registro retornar, sendo 1 o mais recente até 7 o mais antigo",
    description="Retorna a(s) última(s) dica(s) diária(s) para o usuário autenticado. O parâmetro 'count' define qual registro retornar (1-7).",
    response_description="Dicas diárias retornadas com sucesso.",
    responses={
        200: {
            "description": "Dicas diárias retornadas com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "tips": [
                            "hábitos que te dão energia",
                            "começar pequeno e evoluir aos poucos",
                            "decisões impulsivas",
                            "sinais de sobrecarga",
                            "promessas fáceis demais",
                            "prioridades que não fazem mais sentido"
                        ]
                    }
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
            "description": "Dicas diárias não encontradas para o usuário.",
            "content": {
                "application/json": {
                    "example": {"detail": "Dicas diárias não encontradas para o usuário."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor devido a problemas no banco de dados ou outros.",
            "content": {
                "application/json": {
                    "example": {"detail": "An error occurred while fetching daily tips: <detalhes do erro>"}
                }
            },
        },
    },
)
async def get_daily_tips(
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

        # Verifica se o usuário existe
        user_exists = await UserSchemaBase.user_exists(db, user_id)
        if not user_exists:
            raise HTTPException(
                status_code=400,
                detail="User does not exist."
            )

        # Busca as dicas diárias do usuário
        daily_tips = await DailyTipsSchemaBase.get_daily_tips_by_user_id(
            session=db,
            user_id=user_id,
            count=count
        )

        if not daily_tips:
            raise HTTPException(
                status_code=404,
                detail="Dicas diárias não encontradas para o usuário."
            )

        # Extrai o JSON da reading
        tips_data = JsonExtractor.extract_json_from_reading(daily_tips.reading)
        
        return JSONResponse(content={"tips": tips_data}, status_code=200)

    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {str(e)}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching daily tips: {str(e)}") from e
