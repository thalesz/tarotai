from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_session
from app.dependencies.verifyjwt import verify_jwt
from app.schemas.user import UserSchemaBase
from app.schemas.wallet import WalletSchemaBase
from app.core.configs import settings
from app.services.email import EmailConfirmationSchema
from app.services.token import TokenConfirmationSchema

router = APIRouter()

@router.get(
    "/receive/{token}",
    response_class=HTMLResponse,
    summary="Recebe o token de confirmação por e-mail",
    description="Recebe um token de confirmação enviado anteriormente para o e-mail do usuário.",
)
async def receive_confirmation_token_by_email(
    token: str, db: AsyncSession = Depends(get_session)
):
    try:
        token_info: TokenConfirmationSchema = TokenConfirmationSchema.decode_token(
            token=token,
            secret_key=settings.CONFIRMATION_SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        print(f"Token decodificado: {token_info}")
    except HTTPException as e:
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>Confirmação Falhou</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">Erro ao confirmar!</h1>
                <p>{e.detail}</p>
            </body>
            </html>
            """,
            status_code=e.status_code
        )

    try:
        user_email = token_info.get("sub") if isinstance(token_info, dict) else token_info.sub
        user_id = token_info.get("id") if isinstance(token_info, dict) else token_info.id
        user_exists = await UserSchemaBase.user_exists(db=db, id=user_id)
        #se n existir lance exceção
        if not user_exists:
            return HTMLResponse(
                content="""
                <html>
                <head><title>Confirmação Falhou</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Erro!</h1>
                    <p>Usuário não encontrado.</p>
                </body>
                </html>
                """,
                status_code=404
            )
        
        
        status_atual = await UserSchemaBase.get_status_by_id(id=user_id, db=db)
        if status_atual != "pending_confirmation":
            return HTMLResponse(
                content="""
                <html>
                <head><title>Confirmação Falhou</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Erro!</h1>
                    <p>Usuário já confirmado.</p>
                </body>
                </html>
                """,
                status_code=404
            )
        confirmation_status = await UserSchemaBase.confirm_user_using_id(id=user_id, db=db)
        wallet_confirmation_status = await WalletSchemaBase.confirm_wallet_status_using_id(user_id=user_id, session=db)

        if not confirmation_status or not wallet_confirmation_status:
            return HTMLResponse(
                content="""
                <html>
                <head><title>Confirmação Falhou</title></head>
                <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                    <h1 style="color: red;">Erro!</h1>
                    <p>Usuário não encontrado ou  sua carteira não pôde ser encontrada.</p>
                </body>
                </html>
                """,
                status_code=404
            )

        await EmailConfirmationSchema.send_active_email(email=user_email)

        return HTMLResponse(
            content=f"""
            <html>
            <head>
                <title>Conta Confirmada</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        background-color: #f4f4f4;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                    }}
                    .container {{
                        background: white;
                        padding: 40px;
                        border-radius: 10px;
                        box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                        text-align: center;
                    }}
                    .container h1 {{
                        color: #2e7d32;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🎉 Conta Confirmada com Sucesso!</h1>
                    <p>Obrigado por confirmar seu e-mail, <strong>{user_email}</strong>.</p>
                    <p>Agora você pode acessar todos os recursos da plataforma.</p>
                </div>
            </body>
            </html>
            """,
            status_code=200
        )
    except AttributeError as e:
        return HTMLResponse(
            content=f"""
            <html>
            <head><title>Erro</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h1 style="color: red;">Erro interno</h1>
                <p>{str(e)}</p>
            </body>
            </html>
            """,
            status_code=400
        )
