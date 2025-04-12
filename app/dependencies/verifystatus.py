from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchema
from app.core.deps import get_session

def verify_status_factory(required_status: str):
    async def verify_status_dep(
        request: Request,
        db: AsyncSession = Depends(get_session)
    ):
        if not hasattr(request.state, "token_info"):
            raise HTTPException(status_code=401, detail="Token de autenticação ausente ou inválido")

        token_info: TokenInfoSchema = request.state.token_info
        if not token_info:
            raise HTTPException(status_code=401, detail="Token de autenticação ausente ou inválido")

        status = await UserSchema.get_status_by_id(id=token_info.id, db=db)
        if required_status != status:
            raise HTTPException(status_code=403, detail="Você não tem permissão para acessar este recurso. Seu status atual é: {}".format(status))
        return status

    return verify_status_dep
