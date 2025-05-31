# app/core/scheduler.py

import asyncio
import datetime
from typing import Callable, Awaitable, Optional

class DailyScheduler:
    def __init__(
        self,
        scheduled_time: datetime.time,
        functions: list[Callable[[], Awaitable[None]]],
    ):
        """
        Agendador que executa funções assíncronas diariamente em um horário específico.
        :param scheduled_time: Horário para execução (hh:mm)
        :param functions: Lista de funções async a serem executadas
        """
        self.scheduled_time = scheduled_time
        self.functions = functions
        self.last_execution_date: Optional[datetime.date] = None

    async def _run_functions(self):
        for func in self.functions:
            await func()

    async def start(self):
        print(f"🕒 Scheduler started for {self.scheduled_time.strftime('%H:%M')}")
        while True:
            now = datetime.datetime.now()
            if (now.hour, now.minute) == (self.scheduled_time.hour, self.scheduled_time.minute):
                if self.last_execution_date != now.date():
                    print(f"🚀 Executando funções agendadas para {self.scheduled_time.strftime('%H:%M')}")
                    await self._run_functions()
                    self.last_execution_date = now.date()
            await asyncio.sleep(30)
            
            
