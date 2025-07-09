from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.schemas.user import UserSchema, UserSchemaRegister
from app.schemas.mission import MissionSchemaBase
from app.schemas.mission_type import  MissionTypeSchemaBase  # Add this import, adjust the path if needed

router = APIRouter()


@router.post(
    "/",
    summary="Registrar um novo usuário",
    responses={
        201: {
            "description": "Usuário criado com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "username": "johndoe",
                        "email": "johndoe@example.com",
                        "user_type": 1,
                        "wallet_id": 123,
                        "status": 1,
                    }
                }
            },
        },
        409: {
            "description": "Conflito: Email ou username já estão em uso.",
            "content": {
                "application/json": {"example": {"detail": "Email já está em uso."}}
            },
        },
        422: {
            "description": "Erro de validação de dados.",
            "content": {
                "application/json": {
                    "examples": {
                        "Múltiplos erros": {
                            "summary": "Exemplo com vários erros",
                            "value": {
                                "detail": [
                                    {
                                        "type": "string_too_short",
                                        "loc": ["body", "password"],
                                        "msg": "String should have at least 8 characters",
                                        "input": "short",
                                        "ctx": {"min_length": 8},
                                    },
                                    {
                                        "type": "value_error.email",
                                        "loc": ["body", "email"],
                                        "msg": "value is not a valid email address",
                                        "input": "invalid-email",
                                    },
                                ]
                            },
                        }
                    }
                }
            },
        },
        500: {
            "description": "Erro interno do servidor ao criar o usuário.",
            "content": {
                "application/json": {
                    "example": {"detail": "Erro ao criar usuário: [detalhes do erro]"}
                }
            },
        },
    },
)
async def register_user(
    user_data: UserSchemaRegister,  # Corpo da requisição exibido nos parâmetros
    db: AsyncSession = Depends(get_session),
):
    """
    Registrar um novo usuário.

    Parameters:
    - **username**: Nome de usuário único (3 a 50 caracteres).
    - **email**: Email de usuário único.
    - **password**: Senha de usuário (mínimo de 8 caracteres).
    - **user_type**: Tipo de usuário (1 = STANDART).
    - **full_name**: Nome completo do usuário (3 a 100 caracteres).
    """
    response = await UserSchemaRegister.create_user(db=db, user_data=user_data)
    
    print(f"Usuário registrado: {response}")
    mission_type_id_consultar = await MissionTypeSchemaBase.get_id_by_name(db, "Confirmar conta de usuário")

    await MissionSchemaBase.create_mission(db, mission_type_id_consultar, response['id'])

    mission_type_id_adicionar = await MissionTypeSchemaBase.get_id_by_name(db, "Adicionar informações de nascimento")

    await MissionSchemaBase.create_mission(db, mission_type_id_adicionar, response['id'])


    return response
