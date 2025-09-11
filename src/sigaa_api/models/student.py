class Student:
    def __init__(self, institution: str) -> None:
        self.institution = institution
        self._name = None
        self._email = None
        self._registration = None
        self._profile_picture_url = None

    def set_name(self, name: str) -> None:
        self._name = name

    def set_email(self, email: str) -> None:
        self._email = email

    def get_email(self) -> str:
        return self._email

    def get_name(self) -> str:
        return self._name

    # Registration (Matrícula)
    def set_registration(self, registration: str | None) -> None:
        self._registration = registration

    def get_registration(self) -> str | None:
        return self._registration

    # Profile picture URL
    def set_profile_picture_url(self, url: str | None) -> None:
        self._profile_picture_url = url

    def get_profile_picture_url(self) -> str | None:
        return self._profile_picture_url
