from enum import Enum

class RecurrenceType(int, Enum):  # Também int, pois será armazenado como inteiro no banco
    DAILY = 1
    WEEKLY = 2
    MONTHLY = 3
    YEARLY = 4
    ONCE = 5