"""Typed failures returned by the deterministic core."""


class SteadyFolioError(Exception):
    """Base exception for expected SteadyFolio failures."""


class ValidationError(SteadyFolioError):
    """Input data violates a documented schema or domain invariant."""


class DuplicateIdentifierError(ValidationError):
    """A collection contains a duplicate stable identifier."""


class MissingPriceError(ValidationError):
    """A required dated market price is unavailable."""


class MissingFxRateError(ValidationError):
    """A required dated currency conversion is unavailable."""


class StorageSafetyError(SteadyFolioError):
    """A requested file operation would cross the private workspace boundary."""


class ProviderUnavailableError(SteadyFolioError):
    """An explicitly selected research provider cannot return data."""
