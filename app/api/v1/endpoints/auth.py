from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.token import TokenAccessSchema, TokenRefreshSchema
from app.core.deps import get_session
from app.schemas.user import UserSchemaLogin, UserSchema, UserSchemaBase
from sqlalchemy.future import select
from datetime import timedelta
from app.core.configs import settings  # Import the settings object

router = APIRouter()


@router.post(
    "/",
    response_model=TokenAccessSchema,
    summary="Realizar autenticação do usuário e gerar tokens de acesso e atualização(access & refresh tokens).",
    responses={
        # 401: {
        #     "description": "Credenciais inválidas ou token expirado.",
        #     "content": {
        #         "application/json": {
        #             "example": {
        #                 "detail": "Credenciais inválidas"
        #             }
        #         }
        #     }
        # },
        401: {
            "description": "Credenciais inválidas",
            "content": {"application/json": {"example": {"detail": "Senha incorreta"}}},
        },
        404: {
            "description": "Usuário não encontrado.",
            "content": {
                "application/json": {"example": {"detail": "Usuário não encontrado"}}
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Erro interno no servidor: [mensagem do erro]"
                    }
                }
            },
        },
        422: {
            "description": "Campo obrigatório não informado.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "type": "missing",
                                "loc": ["body", "password"],
                                "msg": "Field required",
                                "input": {"username": "thales"},
                            }
                        ]
                    }
                }
            },
        },
    },
)
async def login(user_data: UserSchemaLogin, db: AsyncSession = Depends(get_session)):
    """
    Endpoint para realizar o login de um usuário, verificando as credenciais
    e retornando o token JWT.

    - **username**: Nome de usuário. (3 a 50 caracteres).
    - **password**: Senha do usuário. (8 caracteres no mínimo).

    """
    try:
        # Chama a função de login, passando o db e as credenciais do usuário
        user = await user_data.authenticate_user(
            db=db, login=user_data.login, password=user_data.password
        )
        # print("user", user)

        if not isinstance(user, UserSchema):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
            )

        access_token = TokenAccessSchema.create_token(
            data={
                # "sub": user.username,
                "id": user.id,
                # "email": user.email,
                # "user_type": user.user_type,
                # "status": user.status,
                # "full_name": user.full_name,
                # "birth_date": user.birth_date,
                # "birth_time": user.birth_time,
            },
            secret_key=settings.ACCESS_SECRET_KEY,
            expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        # print("access_token", access_token)
        refresh_token = TokenRefreshSchema.create_token(
            data={"sub": user.username, "id": user.id},
            secret_key=settings.REFRESH_SECRET_KEY,
            expires_delta=timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        print("refresh_token", refresh_token)

        # Atualiza o refresh_token no banco de dados
        await TokenRefreshSchema.update_refresh_token(
            db=db, user_id=user.id, refresh_token=refresh_token
        )

        return TokenAccessSchema(
            access_token=access_token, refresh_token=refresh_token, token_type="Bearer"
        )

    except HTTPException as http_err:
        # Captura exceções específicas do FastAPI (HTTPException)
        raise http_err
    except Exception as err:
        # Captura exceções gerais e loga o erro
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no servidor: {str(err)}",
        )
