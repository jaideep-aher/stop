"""Errors shared by the vision backends."""


class GenerationError(RuntimeError):
    """A backend could not return a completion. Not a scored answer."""


class QuotaError(GenerationError):
    """The account is out of quota. Callers stop and keep rows already stored."""
