from fastapi import Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.status import StatusSchema
from app.services.token import TokenInfoSchema
from app.schemas.user import UserSchema
from app.core.deps import get_session
from collections.abc import Iterable


def verify_status_factory(required_status: str | list[str]):
    async def verify_status_dep(
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

        # Aceita string ou lista de strings
        if isinstance(required_status, str):
            required_status_list = [required_status]
        elif isinstance(required_status, Iterable) and not isinstance(required_status, str):
            required_status_list = list(required_status)
        else:
            raise HTTPException(
                status_code=400, detail="Parâmetro de status inválido"
            )

        status = await UserSchema.get_status_by_id(id=token_info.id, db=db)
        # Busca todos os ids dos status requeridos
        required_status_ids = []
        for name in required_status_list:
            status_id = await StatusSchema.get_id_by_name(db=db, name=name)
            required_status_ids.append(status_id)

        if status not in required_status_ids:
            # Pega os nomes dos status para mensagem
            names = []
            for status_id in required_status_ids:
                name = await StatusSchema.get_name_by_id(db=db, id=status_id)
                names.append(name if name else "Desconhecido")
            raise HTTPException(
                status_code=403,
                detail="Você não tem permissão para acessar este recurso. Seu status atual é: {}. Permitidos: {}".format(
                    await StatusSchema.get_name_by_id(db=db, id=status) or "Desconhecido",
                    ", ".join(names)
                ),
            )
        return status

    return verify_status_dep
