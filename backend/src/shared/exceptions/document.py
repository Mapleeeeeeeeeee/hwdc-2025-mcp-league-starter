"""
Document-related business exceptions for HWDC 2025 MCP League Starter.

Contains exceptions specific to document management, processing, and sharing operations.
"""

from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError


class DocumentNotFoundError(NotFoundError):
    """
    Exception raised when a document cannot be found.

    Common usage: document management, search, processing, sharing
    """

    def __init__(self, document_id: str | None = None, **kwargs):
        detail = "Document not found"
        if document_id:
            detail = f"Document {document_id} not found"

        super().__init__(
            detail=detail,
            i18n_key="errors.document.not_found",
            i18n_params={"document_id": document_id} if document_id else {},
            context={"document_id": document_id} if document_id else None,
            **kwargs,
        )


class DocumentAccessDeniedError(ForbiddenError):
    """
    Exception raised when a user doesn't have permission to access a document.

    More specific than generic ForbiddenError for document access control.
    """

    def __init__(
        self,
        document_id: str | None = None,
        user_id: str | int | None = None,
        required_permission: str | None = None,
        **kwargs,
    ):
        detail = "Document access denied"
        if document_id:
            detail = f"Access denied to document {document_id}"

        super().__init__(
            detail=detail,
            i18n_key="errors.document.access_denied",
            i18n_params={
                "document_id": document_id,
                "user_id": str(user_id) if user_id else None,
                "required_permission": required_permission,
            },
            context={
                "document_id": document_id,
                "user_id": user_id,
                "required_permission": required_permission,
            },
            **kwargs,
        )


class DocumentLockedError(ConflictError):
    """
    Exception raised when a document is locked and cannot be modified.

    Common usage: concurrent editing, document processing workflows
    """

    def __init__(
        self,
        document_id: str | None = None,
        locked_by: str | None = None,
        lock_reason: str | None = None,
        **kwargs,
    ):
        detail = "Document is currently locked"
        if document_id:
            detail = f"Document {document_id} is currently locked"
        if locked_by:
            detail += f" by {locked_by}"

        super().__init__(
            detail=detail,
            i18n_key="errors.document.locked",
            i18n_params={
                "document_id": document_id,
                "locked_by": locked_by,
                "lock_reason": lock_reason,
            },
            context={
                "document_id": document_id,
                "locked_by": locked_by,
                "lock_reason": lock_reason,
            },
            **kwargs,
        )
