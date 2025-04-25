class TypeOfUser:
    """
    Class to define user types.
    """

    ADM = 187
    STANDARD = 1
    PREMIUM = 987

    def __init__(self, type_of_user: int):
        if type_of_user not in {self.ADM, self.STANDARD, self.PREMIUM}:
            raise ValueError("Invalid user type")
        self.type_of_user = type_of_user

    def __str__(self):
        return str(self.type_of_user)
