from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchema
from app.schemas.user_type import UserTypeSchema  # Import UserTypeSchema
from app.core.deps import get_session


def verify_user_type_factory(required_user_type: str):
    async def verify_user_type_dep(
        request: Request, db: AsyncSession = Depends(get_session)
    ):
        if not hasattr(request.state, "token_info"):
            raise HTTPException(
                status_code=401, detail="Token de autenticação ausente ou inválido"
            )

        token_info: TokenInfoSchema = request.state.token_info
        if not token_info:
            raise HTTPException(
                status_code=401, detail="Token de autenticação ausente ou inválido"
            )

        user_type_object = await UserSchema.get_user_by_id(user_id=token_info.id, db=db)
        user_type = user_type_object.user_type
        if not user_type:
            raise HTTPException(
                status_code=401, detail="Token de autenticação ausente ou inválido"
            )
            
        #pega o nome do tipo de usuário usando id   
        name_user_type = await UserTypeSchema.get_name_by_id(
            session=db , id=user_type
        )
            
        if required_user_type != name_user_type:
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar este recurso. Seu tipo de usuário atual é: {}".format(
                    user_type
                ),
            )
        return user_type

    return verify_user_type_dep
