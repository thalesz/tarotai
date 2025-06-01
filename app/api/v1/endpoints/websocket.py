from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.websocket import ws_manager

router = APIRouter()
# No additional code needed here; the WebSocketManager is already instantiated above.
@router.websocket("/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()  # Mantém a conexão viva
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
