from __future__ import annotations


class ZufangCliError(Exception):
    pass


class FetchError(ZufangCliError):
    pass


class ParseError(ZufangCliError):
    pass


class ProviderBlockedError(ZufangCliError):
    pass


class CacheMissError(ZufangCliError):
    pass


def error_code_for_exception(exc: Exception) -> str:
    if isinstance(exc, ProviderBlockedError):
        return "provider_blocked"
    if isinstance(exc, ParseError):
        return "parse_error"
    if isinstance(exc, CacheMissError):
        return "cache_miss"
    if isinstance(exc, FetchError):
        return "fetch_error"
    return "internal_error"

