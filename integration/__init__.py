"""AWS/integration-owner components. Importing the package performs no I/O."""


def record_review(case_id: str, decision: str) -> dict:
    """Application-only review write; never register this as an AI tool."""
    from .reviews import record_review as persist_review

    return persist_review(case_id, decision)


__all__ = ["record_review"]
