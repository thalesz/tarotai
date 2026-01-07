from fastapi import APIRouter, Depends, Request, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.schemas.user import UserSchemaBase
from app.core.configs import settings
from app.services.token import TokenConfirmationSchema
from app.schemas.token_blacklist import TokenBlacklistSchema

router = APIRouter()


@router.get(
    "/validate/{token}",
    summary="Valida token de redefinição de senha",
    description="Recebe apenas o token e verifica se ele ainda é válido (não expirado e não usado).",
)
async def validate_reset_token(
    request: Request,
    db: AsyncSession = Depends(get_session),
    token: str = Path(..., title="Token de redefinição de senha", description="Token JWT enviado por e-mail para redefinição de senha."),
):
    """
    Valida se o token de redefinição é válido sem alterar a senha.
    Retorna 200 quando válido; 401/404 quando inválido, expirado ou já usado.
    """
    try:
        token_info: TokenConfirmationSchema = TokenConfirmationSchema.decode_token(
            token=token,
            secret_key=settings.RESET_PASSWORD_SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
    except Exception as e:
        return JSONResponse(
            status_code=401,
            content={"error": "Token inválido ou expirado.", "status_code": 401, "details": str(e)},
        )

    user_id = int(token_info.get("sub")) if isinstance(token_info, dict) else int(token_info.sub)
    if not user_id:
        return JSONResponse(
            status_code=400,
            content={"error": "ID do usuário não encontrado no token.", "status_code": 400},
        )

    # Verifica se o token está na blacklist (já usado)
    is_blacklisted = await TokenBlacklistSchema.verify_token(
        session=db,
        token=token,
    )
    if is_blacklisted:
        return JSONResponse(
            status_code=401,
            content={"error": "Token já usado anteriormente.", "status_code": 401},
        )

    # Verifica se o usuário existe
    try:
        await UserSchemaBase.get_user_by_id(db=db, user_id=user_id)
    except Exception as e:
        return JSONResponse(
            status_code=404,
            content={"error": "Usuário não encontrado.", "status_code": 404, "details": str(e)},
        )

    return JSONResponse(status_code=200, content={"valid": True, "message": "Token válido."})
