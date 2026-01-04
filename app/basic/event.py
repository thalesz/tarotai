from datetime import datetime

event = [
    {
        "id": 1,
        "name": "Ritual Diário",
        "description": "Um ritual que se renova a cada dia. Complete missões diárias e mantenha sua energia sempre em fluxo.",
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
        "name": "Ciclo da Semana",
        "description": "Um ciclo que se completa toda semana, trazendo novos desafios e recompensas para quem mantém a constância.",
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
        "name": "Lua do Mês",
        "description": "A cada mês, uma nova fase se inicia. Conclua missões especiais e receba múltiplas recompensas ao longo do ciclo lunar.",
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
        "name": "Grande Convergência",
        "description": "Um evento raro que acontece apenas uma vez por ano, reunindo desafios únicos e recompensas especiais.",
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
        "name": "Portal do Tempo",
        "description": "Um portal aberto por tempo limitado. Complete as missões antes que ele se feche e garanta recompensas exclusivas.",
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
        "name": "Jornada Interior",
        "description": "Uma jornada personalizada, moldada pelo próprio usuário. Desafios e recompensas evoluem conforme sua trajetória.",
        "missions": [6],
        "status": 2,
        "created_at": "2024-06-01T00:00:00",
        "start_date": "2025-10-01T00:00:00",
        "expired_date": "2026-10-31T00:00:00",
        "gift": [1, 2, 3, 4, 5, 6],
        "user_type": [1, 987, 187],
        "recurrence_type": 5,  # Recorrência baseada no usuário
        "recurrence_mode": 2,  # Modo de recorrência baseado no usuário
        "auto_renew": False,  # Evento renovável automaticamente
        "reset_time": "00:00:00" 
    }
]