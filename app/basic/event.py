from datetime import datetime

event = [
    {
        "id": 1,
        "name": "Evento diário",
        "description": "Evento recorrente diariamente, disponível para múltiplos tipos de usuário, com renovação automática.",
        "missions": [1,7],
        "status": 2,
        "created_at": "2024-01-01T00:00:00",
        "start_date": "2025-05-25T00:00:00",
        "expired_date": "2026-05-30T00:00:00",
        "gift": [1],
        "user_type": [1, 987, 187],
        "recurrence_type": 1,  # Recorrência diária
        "recurrence_mode": 1,  # Modo de recorrência
        "auto_renew": True,  # Evento renovável automaticamente
        "reset_time": "00:00:00" 
    },
    {
        "id": 2,
        "name": "Evento semanal",
        "description": "Evento com recorrência semanal, disponível para múltiplos tipos de usuário.",
        "missions": [2,8],
        "status": 2,
        "created_at": "2024-02-01T00:00:00",
        "start_date": "2025-05-01T00:00:00",
        "expired_date": '2026-05-30T00:00:00',
        "gift": [1, 2],
        "user_type": [1, 987, 187],
        "recurrence_type": 2,  # Recorrência semanal
        "recurrence_mode": 1,  # Modo de recorrência
        "auto_renew": True,  # Evento renovável automaticamente
        "reset_time": "00:00:00"  # Hora de reinício do evento
    },
    {
        "id": 3,
        "name": "Evento mensal",
        "description": "Evento com recorrência mensal, oferece múltiplos presentes e renovação automática.",
        "missions": [3],
        "status": 2,
        "created_at": "2024-03-01T00:00:00",
        "start_date": "2025-05-01T00:00:00",
        "expired_date": "2026-05-31T00:00:00",
        "gift": [1, 1, 1, 2, 3],
        "user_type": [1, 987, 187],
        "recurrence_type": 3,  # Recorrência mensal
        "recurrence_mode": 1,  # Modo de recorrência
        "auto_renew": True,  # Evento renovável automaticamente
        "reset_time": "00:00:00" 
    },
    {
        "id": 4,
        "name": "Evento anual",
        "description": "Evento com recorrência anual, não renovável automaticamente, com vários presentes.",
        "missions": [4],
        "status": 2,
        "created_at": "2024-04-01T00:00:00",
        "start_date": "2025-01-01T00:00:00",
        "expired_date": "2026-01-31T00:00:00",
        "gift": [1, 2, 3, 4],
        "user_type": [1, 987, 187],
        "recurrence_type": 4,  # Recorrência anual
        "recurrence_mode": 1,  # Modo de recorrência
        "auto_renew": False,  # Evento não renovável automaticamente
        "reset_time": "00:00:00" 
    },
    {
        "id": 5,
        "name": "Evento com data de expiração",
        "description": "Evento com recorrência baseada em data de expiração, disponível para todos os tipos de usuário.",
        "missions": [5],
        "status": 2,
        "created_at": "2024-05-01T00:00:00",
        "start_date": "2025-09-01T00:00:00",
        "expired_date": "2026-09-30T00:00:00",
        "gift": [1, 2, 3, 4, 5],
        "user_type": [1, 987, 187],
        "recurrence_type": 5,  # Recorrência com data de expiração
        "recurrence_mode": 3,  # Modo de recorrência baseado em data de expiração
        "auto_renew": False,  # Evento não renovável automaticamente
        "reset_time": "00:00:00" 
    },
    {
        "id": 6,
        "name": "Baseado no usuario",
        "description": "Evento com recorrência baseada no usuário, exclusivo para o tipo de usuário 187.",
        "missions": [6],
        "status": 2,
        "created_at": "2024-06-01T00:00:00",
        "start_date": "2025-10-01T00:00:00",
        "expired_date": "2026-10-31T00:00:00",
        "gift": [1, 2, 3, 4, 5, 6],
        "user_type": [187],
        "recurrence_type": 5,  # Recorrência baseada no usuário
        "recurrence_mode": 2,  # Modo de recorrência baseado no usuário
        "auto_renew": False,  # Evento renovável automaticamente
        "reset_time": "00:00:00" 
    }
]