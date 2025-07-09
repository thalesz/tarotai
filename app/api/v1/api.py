from fastapi import APIRouter, Depends
from app.api.v1.endpoints import (
    getAllMissionsByEvents,
    test,
    register,
    auth,
    refresh,
    logout,
    testjwt,
    sendConfirmationToken,
    receiveConfirmationToken,
    registerOnlyUsers,
    getAllDeck,
    getCardByDeckId,
    getAllSpreadTypes,
    PostNewDraw, 
    PutNewDraw,
    returnAvaliablesDraws, 
    postDailyLucky, 
    putDailyLucky,
    getAllEvents,
    putMissionStatusById,
    postNewPrize,
    websocket,
    postNotification,
    putStatusNotification,
    getAllNotification,
    postNotificationForAll,
    getFiveDrawsByUser,
    getFiveDailyLuckyByUser,
    putPremiumStatus,
    getAvaliableReadingStyle,
    postReview,
    getFiveReviewByUser,
    putBirthInfo,
    getAllPlanet,
    getSignByPlanet,
    getLastZodiacDaily,
    getLastDailyPath,
    sendPasswordToken,
    receivePasswordToken,
    getReviewByDraw,
    getAllUsers,
    getInfoUser,
    getFiveRecomendations
)
from app.core.deps import get_session
from app.dependencies.verifyjwt import verify_jwt
from app.dependencies.verifystatus import verify_status_factory
from app.dependencies.verifytypeofuser import verify_user_type_factory


api_router = APIRouter()

# rota de teste de conexão de database
api_router.include_router(test.router, prefix="/test", tags=["test"])

api_router.include_router(registerOnlyUsers.router, prefix="/register", tags=["register"])

register_adm_router = APIRouter(
    # dependencies=[
    #     Depends(verify_jwt),
    #     Depends(verify_user_type_factory("ADM")),
    # ]
)

register_adm_router.include_router(register.router, prefix="/register", tags=["register"])

api_router.include_router(register_adm_router)

# api_router.include_router()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(refresh.router, prefix="/refresh", tags=["refresh"])
api_router.include_router(logout.router, prefix="/logout", tags=["logout"])
api_router.include_router(sendPasswordToken.router, prefix="/password", tags=["password"])
api_router.include_router(
    receivePasswordToken.router, prefix="/password", tags=["password"]
)
# não precisa estar logado por motivos de vai acessar o link com o token de confirmação
# e o token de confirmação vai ser enviado para o email do usuário
api_router.include_router(
    receiveConfirmationToken.router, prefix="/confirm-email", tags=["confirm-email"]
)
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])


# Tem que ter o jwt para acessar as rotas abaixo
protected_router = APIRouter(dependencies=[Depends(verify_jwt)])
protected_router.include_router(testjwt.router, prefix="/test", tags=["test"])

protected_router.include_router(getAllUsers.router, prefix="/user", tags=["user"])

api_router.include_router(protected_router)
# enviar email de verificação de conta - precisa estar logado e ter o status de "pending_confirmation"
pending_confirmation_router = APIRouter(
    dependencies=[
        Depends(verify_jwt),
        Depends(verify_status_factory("pending_confirmation")),
    ]
)
pending_confirmation_router.include_router(
    sendConfirmationToken.router, prefix="/confirm-email", tags=["confirm-email"]
)

api_router.include_router(pending_confirmation_router)



# enviar email de verificação de conta - precisa estar logado e ter o status de "pending_active"
active_router = APIRouter(
    dependencies=[
        Depends(verify_jwt),
        Depends(verify_status_factory("active")),
    ]
)
active_router.include_router(
    getAllDeck.router, prefix="/deck", tags=["deck"]
)

active_router.include_router(
    getAllSpreadTypes.router, prefix="/spread", tags=["spread"]
)
active_router.include_router(getFiveDrawsByUser.router, prefix="/draw", tags=["draw"])


active_router.include_router(
    getCardByDeckId.router, prefix="/card", tags=["card"]
)

active_router.include_router(
    PostNewDraw.router, prefix="/draw", tags=["draw"]
)
active_router.include_router(
    PutNewDraw.router, prefix="/draw", tags=["draw"]
)
active_router.include_router(
    returnAvaliablesDraws.router, prefix="/spread", tags=["spread"]
)
active_router.include_router(
    postDailyLucky.router, prefix="/daily-lucky", tags=["daily-lucky"]
)
active_router.include_router(
    putDailyLucky.router, prefix="/daily-lucky", tags=["daily-lucky"]
)
active_router.include_router(
    getAllMissionsByEvents.router, prefix="/mission", tags=["mission"]
)
active_router.include_router(
    getAllEvents.router, prefix="/event", tags=["event"]
)
active_router.include_router(
    putMissionStatusById.router, prefix="/mission", tags=["mission"]
)
active_router.include_router(
    postNewPrize.router, prefix="/event", tags=["event"]
)
active_router.include_router(
    getFiveDailyLuckyByUser.router, prefix="/daily-lucky", tags=["daily-lucky"]
)

active_router.include_router(
    getAvaliableReadingStyle.router, prefix="/reading-style", tags=["reading-style"]
)

active_router.include_router(
    postReview.router, prefix="/review", tags=["review"]    
)

active_router.include_router(
    getFiveReviewByUser.router, prefix="/review", tags=["review"]
    
)
active_router.include_router(
    getSignByPlanet.router, prefix="/planet", tags=["planet"]
)

active_router.include_router(
    getAllPlanet.router, prefix="/planet", tags=["planet"]
)
active_router.include_router(
    putBirthInfo.router, prefix="/user", tags=["user"]
)
active_router.include_router(
    getLastZodiacDaily.router, prefix="/daily-zodiac", tags=["daily-zodiac"]
)
active_router.include_router(
    getLastDailyPath.router, prefix="/daily-path", tags=["daily-path"]
)
active_router.include_router(
    getReviewByDraw.router, prefix="/review", tags=["review"]
)   

active_router.include_router(
    getFiveRecomendations.router, prefix="/questions", tags=["questions"]
)

api_router.include_router(active_router)


adm_active_router = APIRouter(
    dependencies=[
        Depends(verify_jwt),
        Depends(verify_user_type_factory("ADM")),
        Depends(verify_status_factory("active")),
    ]
)
adm_active_router.include_router(
    getAllSpreadTypes.router, prefix="/spread", tags=["spread"]
)

adm_active_router.include_router(
    postNotification.router, prefix="/notification", tags=["notification"]
)

adm_active_router.include_router(
    postNotificationForAll.router, prefix="/notification", tags=["notification"]
)

adm_active_router.include_router(
    putPremiumStatus.router, prefix="/subscription", tags=["premium"]
)
       
api_router.include_router(adm_active_router)

active_and_pending_router = APIRouter(
    dependencies=[
        Depends(verify_jwt),
        Depends(verify_status_factory(["pending_confirmation", "active"])),
    ]
)

active_and_pending_router.include_router(
    putStatusNotification.router, prefix="/notification", tags=["notification"]
)

active_and_pending_router.include_router(
    getAllNotification.router, prefix="/notification", tags=["notification"]
)

active_and_pending_router.include_router(
    getInfoUser.router, prefix="/user", tags=["user"]
)
api_router.include_router(active_and_pending_router)