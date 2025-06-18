from fastapi import APIRouter, Depends, Request, Path
from fastapi.responses import JSONResponse
from fastapi.openapi.models import Example
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.core.deps import get_session
from app.schemas.user import UserSchemaBase
from app.core.configs import settings
from app.services.email import EmailConfirmationSchema
from app.services.token import TokenConfirmationSchema
from app.schemas.token_blacklist import TokenBlacklistSchema
from app.core.security import pwd_context

router = APIRouter()

class PasswordResetRequest(BaseModel):
    new_password: str = Field(
        ...,
        min_length=6,
        example="NovaSenha123!",
        description="A nova senha do usuário. Deve ter pelo menos 6 caracteres."
    )

class PasswordResetResponseSuccess(BaseModel):
    message: str = Field(
        ...,
        example="Senha alterada com sucesso. Um e-mail de confirmação foi enviado."
    )

class PasswordResetResponseError(BaseModel):
    error: str = Field(
        ...,
        example="Nova senha inválida ou muito curta."
    )
    status_code: int = Field(
        ...,
        example=422
    )
    details: str | None = Field(
        None,
        example="Detalhes do erro, se houver."
    )

@router.put(
    "/receive/{token}",
    summary="Recebe o token de confirmação por e-mail e nova senha",
    description="""
Recebe um token de confirmação enviado na URL e a nova senha no corpo da requisição.

- O token é enviado como parte da URL.
- A nova senha deve ser enviada no corpo da requisição como JSON.
- A senha deve ter pelo menos 6 caracteres e ser diferente da senha atual.
- Um e-mail de confirmação será enviado após a alteração bem-sucedida da senha.
""",
    response_model=PasswordResetResponseSuccess,
    responses={
        200: {
            "description": "Senha alterada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Senha alterada com sucesso. Um e-mail de confirmação foi enviado."
                    }
                }
            }
        },
        400: {
            "model": PasswordResetResponseError,
            "description": "Erro ao redefinir a senha.",
            "content": {
                "application/json": {
                    "examples": {
                        "invalid_password": {
                            "summary": "Senha inválida",
                            "value": {
                                "error": "Nova senha inválida ou muito curta.",
                                "status_code": 422
                            }
                        },
                        "same_password": {
                            "summary": "Senha igual à anterior",
                            "value": {
                                "error": "A nova senha não pode ser a mesma que a atual.",
                                "status_code": 400
                            }
                        },
                        "token_invalid": {
                            "summary": "Token inválido",
                            "value": {
                                "error": "Token inválido ou expirado.",
                                "status_code": 401,
                                "details": "Detalhes do erro, se houver."
                            }
                        },
                        "user_not_found": {
                            "summary": "Usuário não encontrado",
                            "value": {
                                "error": "Usuário não encontrado.",
                                "status_code": 404
                            }
                        }
                    }
                }
            }
        }
    }
)
async def receive_confirmation_token_by_email(
    request: Request,
    db: AsyncSession = Depends(get_session),
    token: str = Path(
        ...,
        title="Token de redefinição de senha",
        description="Token JWT enviado por e-mail para redefinição de senha.",
        example="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    )
):
    """
    Recebe um token de confirmação enviado na URL e a nova senha no corpo da requisição.

    Exemplo de corpo da requisição:
    {
        "new_password": "NovaSenha123!"
    }
    """
    try:
        body = await request.json()
        new_password = body.get("new_password")
        if not new_password or len(new_password) < 6:
            return JSONResponse(
                status_code=422,
                content={"error": "Nova senha inválida ou muito curta.", "status_code": 422}
            )

        try:
            
            
            token_info: TokenConfirmationSchema = TokenConfirmationSchema.decode_token(
                token=token,
                secret_key=settings.RESET_PASSWORD_SECRET_KEY,
                algorithm=settings.ALGORITHM,
            )
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"error": "Token inválido ou expirado.", "status_code": 401, "details": str(e)}
            )

        user_id = int(token_info.get("sub")) if isinstance(token_info, dict) else int(token_info.sub)
        if not user_id:
            return JSONResponse(
                status_code=400,
                content={"error": "ID do usuário não encontrado no token.", "status_code": 400}
            )
        # Verifica se o token está na blacklist
        is_blacklisted = await TokenBlacklistSchema.verify_token(
            session=db,
            token=token,
        )
        if is_blacklisted:
            return JSONResponse(
                status_code=401,
                content={"error": "Token já usado anteriormente.", "status_code": 401}
            )
        
        existing_password = await UserSchemaBase.get_user_password_by_id(user_id=user_id, db=db)
        if existing_password and pwd_context.verify(new_password, existing_password):
            return JSONResponse(
                status_code=400,
                content={"error": "A nova senha não pode ser a mesma que a atual.", "status_code": 400}
            )

        updated = await UserSchemaBase.update_password(user_id=user_id, new_password=new_password, db=db)
        if not updated:
            return JSONResponse(
                status_code=404,
                content={"error": "Usuário não encontrado.", "status_code": 404}
            )

        user_email = await UserSchemaBase.get_user_email_by_id(user_id=user_id, db=db)
        if not user_email:
            return JSONResponse(
                status_code=404,
                content={"error": "E-mail do usuário não encontrado.", "status_code": 404}
            )

        await EmailConfirmationSchema.send_reset_confirmation_email(email=user_email)

        # Invalida o token após o uso (exemplo: adicionando a um blacklist ou marcando como usado)
        await TokenBlacklistSchema.add_token_to_blacklist(
            session=db,
            token=token,
            user_id=user_id
        )

        return {"message": "Senha alterada com sucesso. Um e-mail de confirmação foi enviado."}
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Erro ao redefinir a senha: {str(e)}", "status_code": 400}
        )
