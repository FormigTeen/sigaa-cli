class Student:
    def __init__(self, institution: str) -> None:
        self.institution = institution
        self._name = None
        self._email = None

    def set_name(self, name: str) -> None:
        self._name = name

    def set_email(self, email: str) -> None:
        self._email = email

    def get_email(self) -> str:
        return self._email

    def get_name(self) -> str:
        return self._name