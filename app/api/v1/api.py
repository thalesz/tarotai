from fastapi import APIRouter, Depends
from app.api.v1.endpoints import test, register, auth, refresh, logout, testjwt, sendConfirmationToken, receiveConfirmationToken
from app.core.deps import get_session
from app.dependencies.verifyjwt import verify_jwt
from app.dependencies.verifystatus import verify_status_factory


api_router = APIRouter()

#rota de teste de conexão de database
api_router.include_router(test.router, prefix="/test", tags=["test"])

api_router.include_router(register.router, prefix="/register", tags=["register"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(refresh.router, prefix="/refresh", tags=["refresh"])
api_router.include_router(logout.router, prefix="/logout", tags=["logout"])

# não precisa estar logado por motivos de vai acessar o link com o token de confirmação
# e o token de confirmação vai ser enviado para o email do usuário
api_router.include_router(receiveConfirmationToken.router, prefix="/confirm-email", tags=["confirm-email"])


#Tem que ter o jwt para acessar as rotas abaixo
protected_router = APIRouter(dependencies=[Depends(verify_jwt)])
protected_router.include_router(testjwt.router, prefix="/test", tags=["test"])

api_router.include_router(protected_router)


# enviar email de verificação de conta - precisa estar logado e ter o status de "pending_confirmation"
confirm_email_router = APIRouter(dependencies=[
    Depends(verify_jwt),
    Depends(verify_status_factory("pending_confirmation"))
])
confirm_email_router.include_router(sendConfirmationToken.router, prefix="/confirm-email", tags=["confirm-email"])

api_router.include_router(confirm_email_router)