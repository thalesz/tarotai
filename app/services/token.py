from pydantic import BaseModel, EmailStr, Field, ValidationError


from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import UserModel
from app.core.security import pwd_context
from jose import jwt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.configs import settings


class TokenSchemaBase(BaseModel):
    class Config:
        orm_mode = True
        arbitrary_types_allowed = True
        validate_assignment = True

    @staticmethod
    def create_token(
         data: dict, secret_key: str, expires_delta: timedelta = None
    ) -> str:
        try:
            to_encode = data.copy()
            expire = datetime.now() + expires_delta
            to_encode.update({"exp": expire})
            encoded_jwt = jwt.encode(
                to_encode, secret_key, algorithm=settings.ALGORITHM
            )
            # print(f"Token created: {encoded_jwt}")
            return encoded_jwt
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao criar token: {str(e)}",
            )

    @staticmethod
    def decode_token(token: str, secret_key: str, algorithm: str) -> dict:
        """
        Decodifica um token JWT e retorna os dados contidos nele.
        """
        try:
            print(f"Decoding token: {token}")
            payload = jwt.decode(token, secret_key, algorithms=[algorithm])
            return payload
        except jwt.ExpiredSignatureError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token expirado: {str(e)}",
            )
        except jwt.JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token inválido: {str(e)}",
            )
        except Exception as e:
            print(f"Error decoding token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao decodificar token: {str(e)}",
            )

    # @staticmethod
    # def create_token(email: EmailStr, token_type: str) -> BaseModel:
    #     if token_type == "access":
    #         print("Creating access token")
    #     elif token_type == "refresh":
    #         print("Creating refresh token")
    #     elif token_type == "confirmation":
    #         expiration = datetime.now() + timedelta(minutes=settings.CONFIRMATION_TOKEN_EXPIRE_MINUTES)
    #         secret_key = settings.CONFIRMATION_SECRET_KEY
    #         payload = {"sub": email, "exp": expiration}
    #         token = jwt.encode(payload, secret_key, algorithm=settings.ALGORITHM)
    #         return TokenConfirmationSchema(confirmation_token=token)
    #     else:
    #         raise ValueError("Invalid token type")
    

    @staticmethod
    def verify_token(token: str) -> str:
        SECRET_KEY = "your-secret-key"  # Replace with your actual secret key
        ALGORITHM = "HS256"

        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            return email
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )


class TokenConfirmationSchema(TokenSchemaBase):
    sub: str = Field(default=None)
    id: int = Field(default=None)


class TokenAccessSchema(TokenSchemaBase):
    access_token: str
    refresh_token: str = Field(default=None)
    token_type: str = Field(default="Bearer")


class TokenInfoSchema(TokenSchemaBase):
    sub: str = Field(default=None)
    id: int = Field(default=None)
    email: EmailStr = Field(default=None)
    user_type: int = Field(default=None)
    status: int = Field(default=None)
    full_name: str = Field(default=None)
    birth_date: str = Field(default=None)
    birth_time: str = Field(default=None)


class TokenRefreshSchema(TokenSchemaBase):
    refresh_token: str

    @staticmethod
    async def update_refresh_token(
        db: AsyncSession, user_id: str, refresh_token: str
    ) -> None:
        try:
            query = select(UserModel).where(UserModel.id == user_id)
            result = await db.execute(query)
            user = result.scalars().first()
            if user:
                if isinstance(user.refresh_token, list):
                    user.refresh_token.append(refresh_token)
                else:
                    user.refresh_token = [refresh_token]
                await db.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro ao atualizar o token de atualização: {str(e)}",
            )
