class DomainException(Exception):
    pass


class ValidationException(DomainException):
    pass


class AuthorizationException(DomainException):
    pass


class NotFoundException(DomainException):
    pass
