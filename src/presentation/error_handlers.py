"""
Error Handlers

Middleware para tratamento de erros.
Converte exceções em respostas HTTP apropriadas.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handler para ValueError.
    
    Usado para validações de negócio.
    """
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": "validation_error",
            "message": str(exc),
            "detail": "Request validation failed"
        }
    )


async def not_found_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler para recursos não encontrados.
    """
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "not_found",
            "message": str(exc),
            "detail": "Resource not found"
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """
    Handler para erros de integridade do banco.
    
    Ex: constraint violations, duplicates, etc.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": "integrity_error",
            "message": "Database integrity constraint violated",
            "detail": str(exc.orig) if hasattr(exc, 'orig') else str(exc)
        }
    )


async def database_error_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """
    Handler genérico para erros de banco.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "database_error",
            "message": "Database operation failed",
            "detail": str(exc)
        }
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handler para erros de validação do FastAPI/Pydantic.
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validation_error",
            "message": "Request validation failed",
            "detail": exc.errors()
        }
    )


async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handler genérico para qualquer exceção não tratada.
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
            "detail": str(exc)
        }
    )


def register_error_handlers(app):
    """
    Registra todos os error handlers no app.
    
    Usage:
        app = FastAPI()
        register_error_handlers(app)
    """
    app.add_exception_handler(ValueError, value_error_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(SQLAlchemyError, database_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_error_handler)