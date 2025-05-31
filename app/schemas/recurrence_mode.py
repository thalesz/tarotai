


from enum import Enum

class RecurrenceMode(int, Enum):  # Int, pois vai ser armazenado como inteiro no banco
    CALENDAR = 1
    USER_BASED = 2
    EXPIRED_DATE = 3
