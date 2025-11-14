"""
Shared exceptions used across microservices.
"""


class MicroserviceException(Exception):
    """Base exception for microservices."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(MicroserviceException):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class AuthorizationException(MicroserviceException):
    """Raised when user lacks required permissions."""
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403)


class ResourceNotFoundException(MicroserviceException):
    """Raised when a resource is not found."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationException(MicroserviceException):
    """Raised when validation fails."""
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status_code=422)


class ServiceUnavailableException(MicroserviceException):
    """Raised when a dependent service is unavailable."""
    def __init__(self, service_name: str):
        message = f"Service '{service_name}' is unavailable"
        super().__init__(message, status_code=503)
