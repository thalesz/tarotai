from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from fastapi import Request, HTTPException
import traceback


from app.core.configs import settings
from app.schemas.user import UserSchemaBase
from app.services.email import EmailConfirmationSchema
from app.services.token import TokenInfoSchema, TokenConfirmationSchema

router = APIRouter()


@router.post(
    "/send-confirmation-token",
    summary="Enviar token de confirmação por e-mail",
    description="Envia um token de confirmação para o e-mail do usuário.",
    responses={
        200: {
            "description": "Token de confirmação enviado com sucesso.",
            "content": {
                "application/json": {
                    "example": {"message": "Token de confirmação enviado para o e-mail"}
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
async def send_confirmation_token_by_email(
    request: Request, db: AsyncSession = Depends(get_session)
):
    # Pega o email e o id do corpo da requisição
    token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
    if token_info is None:
        raise HTTPException(
            status_code=401, detail="Informações do token estão ausentes"
        )

    try:
        
        user_id = token_info.id
        user_email = await UserSchemaBase.get_user_email_by_id(db=db, user_id=user_id)
    except AttributeError:
        raise HTTPException(status_code=400, detail="Email não encontrado no token")

    # Cria o token de confirmaçao
    try:
        from datetime import timedelta

        expires_delta = timedelta(hours=settings.CONFIRMATION_TOKEN_EXPIRE_MINUTES)
        encoded_token = TokenConfirmationSchema.create_token(
            data={"id": user_id},
            secret_key=settings.CONFIRMATION_SECRET_KEY,
            expires_delta=expires_delta,
        )
        print(f"Token de confirmação gerado: {encoded_token}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Erro ao criar token de confirmação"
        )

    await EmailConfirmationSchema.send_confirmation_email(
        email=user_email, token=encoded_token
    )
    # Log the stack trace for debugging purposes
    # traceback.print_stack()

    return {"message": "Token de confirmação enviado para o e-mail"}

    # return {"message": f"Token de confirmação enviado para o e-mail"}
