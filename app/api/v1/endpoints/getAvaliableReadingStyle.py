
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_session
from app.services.token import TokenInfoSchema # Import TokenInfoSchema
from app.schemas.user import UserSchemaBase
from app.schemas.spread_type import SpreadTypeSchemaBase  # Import SpreadTypeSchemaBase
from app.schemas.draw import DrawSchemaBase  # Import DrawSchemaBase
from app.schemas.reading_style import ReadingStyleSchemaBase  # Import ReadingStyleSchemaBase
from app.schemas.user_type import UserTypeSchemaBase  # Import UserTypeSchemaBase
router = APIRouter()


@router.get(
    "/all",
    summary="Obter os estilos de leitura disponíveis para um usuário",
    description="Este endpoint retorna uma lista de estilos de leitura disponíveis para o usuário autenticado.",
    response_description="Uma lista contendo os IDs, nomes dos estilos de leitura disponíveis.",
    responses={
        200: {
            "description": "Lista de estilos de leitura disponíveis retornada com sucesso.",
            "content": {
                "application/json": {
                    "example": {
                        "data": [
                            {"id": 1, "name": "Estilo 1", "description": "Descrição do Estilo 1"},
                            {"id": 2, "name": "Estilo 2", "description": "Descrição do Estilo 2"}
                        ]
                    }
                }
            },
        },
        401: {
            "description": "Token de autenticação ausente ou inválido.",
            "content": {
                "application/json": {
                    "example": {"detail": "token information is missing"}
                }
            },
        },
        400: {
            "description": "Erro de validação ou usuário não encontrado.",
            "content": {
                "application/json": {
                    "example": {"detail": "User does not exist."}
                }
            },
        },
        500: {
            "description": "Erro interno do servidor.",
            "content": {
                "application/json": {
                    "example": {"detail": "Ocorreu um erro ao buscar as tiragens disponíveis."}
                }
            },
        },
    },
)

async def get_all_reading_styles(
    request: Request,
    db: AsyncSession = Depends(get_session)
):
    try:
        # pegar id do usuario enviado pelo token
        token_info: TokenInfoSchema = getattr(request.state, "token_info", None)
        if token_info is None:
            raise HTTPException(
                status_code=401, detail="token information is missing"
            )
        
        try:
            user_id = token_info.id
        except AttributeError:
            raise HTTPException(status_code=400, detail="User id not found in token")
        # verifica se o user existe
        userexists = await UserSchemaBase.user_exists(db, user_id)
        #print("userexists: ", userexists)
        if not userexists:
            raise HTTPException(
                status_code=400, 
                detail="User does not exist."
            )
        
        
        #ok, tem o id agora vc precisa pegar os tipos de tiragem
        # e a quantidade de tiragens disponiveis
        
        # pega o cliente do usuario
        id_user_type = await UserSchemaBase.get_user_type_by_id(db, user_id)

        reading_styles = await UserTypeSchemaBase.get_reading_styles_by_user_type_id(db, id_user_type)
        
        # pegar o nome de a descricao de cada estilo de leitura
        reading_styles_details = []
        for style in reading_styles:
            style_details: ReadingStyleSchemaBase = await ReadingStyleSchemaBase.get_reading_style_by_id(db, style)
            if style_details:
                reading_styles_details.append({
                    "id": style_details.id,
                    "name": style_details.name,
                    "description": style_details.description
                })
        return {"data": reading_styles_details}
    except HTTPException as e:
        raise HTTPException(status_code=e.status_code, detail=e.detail)
