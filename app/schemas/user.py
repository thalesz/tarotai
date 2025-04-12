from pydantic import BaseModel, EmailStr, Field, ValidationError
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
# Removed the top-level import of UserModel to avoid circular import issues
from app.core.security import pwd_context
from datetime import datetime, timezone
from app.models.user import UserModel
from app.schemas.wallet import WalletSchemaBase  # Import WalletSchemaBase

from app.services.token import TokenConfirmationSchema  # Importando o TokenConfirmationSchema
from app.services.email import EmailSchema

from app.core.typeofuser import TypeOfUser  # Importando o TypeOfUser



class UserSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True
        
    @staticmethod
    #verificar se o usuario existe
    async def user_exists(db: AsyncSession, id: int) -> bool:
        """
        Verifica se o usuário existe no banco de dados.
        """
        query = select(UserModel).where(UserModel.id == id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        return user is not None
    
    @staticmethod
    async def confirm_user_using_id(id:int, db: AsyncSession) -> dict:
        """
        Confirma o usuário pelo ID.
        """
        query = select(UserModel).where(UserModel.id == id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )
        
        # Atualiza o status do usuário para "active"
        user.status = "active"
        
        db.add(user)
        await db.commit()
        
        return {
            "message": "Usuário confirmado com sucesso",
            "user_id": user.id,
            "status": user.status,
        }
        
    @staticmethod
    async def get_status_by_id(id: int, db: AsyncSession) -> str:
        """
        Obtém o status do usuário pelo ID.
        """
        query = select(UserModel).where(UserModel.id == id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )
        
        return user.status
    
    # Busca o usuário associado ao refresh token no banco de dados
    @classmethod
    async def get_user_by_refresh_token(cls, db: AsyncSession, refresh_token: str) -> UserModel:
        query = select(UserModel).where(UserModel.refresh_token.any(refresh_token))
        result = await db.execute(query)
        user = result.scalars().first()
        if not user or not user.refresh_token or refresh_token not in user.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido",
            )
        return user
    
    
    @staticmethod
    async def remove_refresh_token(db,  user_id, refresh_token,):
        """
            Remover o refresh token do usuário no banco de dados.
        """
        if user_id:
            user: UserSchemaUpdate = await UserSchemaUpdate.get_user_by_id(db, user_id)
            if user and hasattr(user, "refresh_token") and refresh_token in user.refresh_token:
                user.refresh_token.remove(refresh_token)
                db.add(user)
                await db.commit()
                
    
        
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> "UserSchema":
        """
        Obtém um usuário do banco de dados pelo ID.

        :param db: Sessão assíncrona do banco de dados.
        :param user_id: ID do usuário a ser buscado.
        :raises HTTPException: Quando o usuário não é encontrado.
        :return: Objeto UserModel correspondente ao ID fornecido.
        """
        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Usuário não encontrado",
            )
        
        return user
        
        
        
    @staticmethod
    async def create_user(db: AsyncSession, user_data: "UserSchemaRegister") -> dict:
        """
        Cria um novo usuário no banco de dados com nome, email, senha e tipo de usuário.

        :param db: Sessão assíncrona do banco de dados.
        :param user_data: Dados para criação do usuário.
        :raises HTTPException: Quando os dados não são válidos ou ocorrem conflitos.
        :return: Novo objeto UserModel criado.
        """
        # Validação dos campos (ocorre automaticamente pelo Pydantic)
        try:
            user_data = UserSchemaRegister(**user_data.model_dump())
        except ValidationError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Erro de validação: {e.errors()}",
            )

        # Verifica se o email já está cadastrado
        query_email = select(UserModel).where(UserModel.email == user_data.email)
        existing_user = await db.execute(query_email)
        if existing_user.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email já está em uso."
            )
            
        # Verifica se o tipo de usuário é válido
        if user_data.user_type not in [TypeOfUser.ADM, TypeOfUser.STANDARD, TypeOfUser.PREMIUM]:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Tipo de usuário inválido.",
            )
            
        # Verifica se o username já está cadastrado
        query_username = select(UserModel).where(UserModel.username == user_data.username)
        existing_username = await db.execute(query_username)
        if existing_username.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username já está em uso."
            )
        hashed_password = pwd_context.hash(user_data.password)

        # Cria um novo usuário
        new_user = UserModel(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
            user_type=user_data.user_type,  # Adiciona o tipo de usuário
            status="pending_confirmation",  # Define o status como "pending_confirmation"
            created_at=datetime.now(),  # Define a data de criação como o momento atual
            full_name=user_data.full_name,
        )
        
        # Salva o novo usuário no banco de dados
        try:
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)  # Recupera o objeto atualizado do banco
        except Exception as e:
            await db.rollback()  # Reverte transação em caso de erro
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar usuário: {str(e)}",
            )

        # Cria a carteira do usuário (assumindo que a função create_wallet está definida corretamente)
        try:
            new_wallet = await WalletSchemaBase.create_wallet(
                user_id=new_user.id,
                wallet_type="BRL",
                session=db,
            )
        except Exception as e:
            await db.rollback()  # Reverte transação em caso de erro
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar carteira: {str(e)}",
            )

        return {
            "username": new_user.username,
            "email": new_user.email,
            "user_type": new_user.user_type,
            "wallet_id": new_wallet.id,
            "status": new_user.status,
        }


class UserSchemaLogin(UserSchemaBase):
    """
    Schema para o login de um novo usuário.
    """
    login: str = Field(
        ...,
        description="Nome de usuário ou email obrigatório.",
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Senha obrigatória, deve ter no mínimo 8 caracteres.",
    )
    
    def verify_password(self, hashed_password: str) -> bool:
        """
        Verifica se a senha fornecida corresponde à senha hash armazenada.
        """
        return pwd_context.verify(self.password, hashed_password)
    
    @classmethod
    async def authenticate_user(cls, db, login: str, password: str) -> "UserSchema":
        """
        Realiza a autenticação do usuário verificando as credenciais (usuário/email e senha).
        Retorna uma instância de UserSchema.
        """
        try:
            query_user = select(UserModel).where(
                (UserModel.username == login) | (UserModel.email == login)
            )
            result = await db.execute(query_user)
            user = result.scalar_one_or_none()

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado"
                )

            if not pwd_context.verify(password, user.password):  # Verifica a senha do usuário
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha incorreta"
                )

            return UserSchema(
                id=user.id,
                username=user.username,
                email=user.email,
                user_type=user.user_type,
                full_name=user.full_name,
                birth_date=user.birth_date or "",
                birth_time=user.birth_time or "",
                birth_place=user.birth_place or "",
                status=user.status,
                created_at=user.created_at.isoformat(),  # Certifica-se de que created_at está presente
                password="***********",  # Não retorna a senha real
            )
        except HTTPException as e:
            raise e
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erro ao autenticar usuário: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro interno do servidor"
            ) from e
    
class UserSchemaRegister(UserSchemaBase):
    """
    Schema para o registro de um novo usuário.
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username obrigatório e deve ter entre 3 e 50 caracteres.",
    )
    user_type: int = Field(
        ...,
        description="Tipo de usuário obrigatório.",
    )
    full_name: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Nome completo. deve ter entre 3 e 100 caracteres.",
    )
    email: EmailStr = Field(..., description="Email válido é obrigatório.")
    password: str = Field(
        ...,
        min_length=8,
        description="Senha obrigatória e deve ter no mínimo 8 caracteres.",
    )
    
class UserSchema(UserSchemaBase):
    
    id: int = Field(
        None,
        description="ID do usuário. Gerado automaticamente.",
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Username obrigatório e deve ter entre 3 e 50 caracteres.",
    )
    user_type: int = Field(
        ...,
        description="Tipo de usuário obrigatório.",
    )
    full_name: str = Field(
        None,
        min_length=3,
        max_length=100,
        description="Nome completo. deve ter entre 3 e 100 caracteres. Opcional inicialmente.",
    )
    email: EmailStr = Field(..., description="Email válido é obrigatório.")
    password: str = Field(
        ...,
        min_length=8,
        description="Senha obrigatória e deve ter no mínimo 8 caracteres.",
    )
    created_at: str = Field(
        ...,
        description="Data de criação do usuário.",
    )
    birth_date: str = Field(
        None,
        description="Data de nascimento do usuário no formato YYYY-MM-DD. Opcional inicialmente.",
    )
    birth_time: str = Field(
        None,
        description="Horário de nascimento do usuário no formato HH:MM:SS. Opcional inicialmente.",
    )
    birth_place: str = Field(
        None,
        description="Local de nascimento do usuário. Opcional inicialmente.",
    )
    status: str = Field(
        ...,
        description="Status do usuário obrigatório.",
    )
    
class UserSchemaUpdate(UserSchema):
    refresh_token: str = Field(
        None,
        description="Token de atualização do usuário. Opcional.",
    )  