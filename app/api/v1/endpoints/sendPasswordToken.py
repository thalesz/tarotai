from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from fastapi import Request, HTTPException
import traceback


from app.core.configs import settings
from app.services.email import EmailConfirmationSchema
from app.services.token import TokenInfoSchema, TokenConfirmationSchema
from app.schemas.user import UserSchemaBase  # Add this import, adjust path if needed
from datetime import timedelta

router = APIRouter()


@router.post(
    "/send-password-token/{login}",
    summary="Enviar token de recuperação de senha por e-mail",
    description="Envia um token de recuperação de senha para o e-mail do usuário.",
    responses={
        200: {
            "description": "Token de recuperação de senha enviado com sucesso.",
            "content": {
                "application/json": {
                    "example": {"message": "Token de recuperação de senha enviado para o e-mail"}
                }
            },
        },
        400: {
            "description": "Erro no corpo da requisição ou email não encontrado no token.",
            "content": {
                "application/json": {
                    "example": {"detail": "Email não encontrado no token"}
                }
            },
        },
        401: {
            "description": "Token inválido ou informações do token ausentes.",
            "content": {
                "application/json": {
                    "example": {"detail": "Informações do token estão ausentes"}
                }
            },
        },
        500: {
            "description": "Erro interno ao criar o token de confirmação.",
            "content": {
                "application/json": {
                    "example": {"detail": "Erro ao criar token de confirmação"}
                }
            },
        },
    },
)
async def send_password_token_by_email(
    login: str, db: AsyncSession = Depends(get_session)
):
    # verifica se existe e pega o id
    try:
        user_id = await UserSchemaBase.get_id_by_login(
            db=db, login=login
        )

        if user_id is None:
            raise HTTPException(
                status_code=404, detail="Usuário não encontrado"
            )
            

        expires_delta = timedelta(hours=settings.RESET_PASSWORD_TOKEN_EXPIRE_MINUTES)
        encoded_token = TokenConfirmationSchema.create_token(
            data={"sub": str(user_id)},
            secret_key=settings.RESET_PASSWORD_SECRET_KEY,
            expires_delta=expires_delta,
        )
        print(f"Token de recuperação gerado: {encoded_token}")
        #pega o email do usuario
        user_email = await UserSchemaBase.get_user_email_by_id(
            db=db, user_id=user_id
        )
        await EmailConfirmationSchema.send_reset_email(
            email=user_email, token=encoded_token
        )
    # Log the stack trace for debugging purposes
    # traceback.print_stack()

        # Retorna a primeira letra do email, depois ** para o restante antes do @, seguido do domínio
        email_split = user_email.split("@")
        local = email_split[0]
        masked_local = local[0] + "**"
        masked_email = f"{masked_local}@{email_split[1]}"
        return {
            "message": "Token de recuperação enviado para o e-mail",
            "email": masked_email,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Erro ao criar token de recuperação de senha"
        )


    # return {"message": f"Token de confirmação enviado para o e-mail"}
