from __future__ import annotations

from ..constants import PROVIDER_NAMES
from .beike_like import BeikeLikeProvider


class KeProvider(BeikeLikeProvider):
    name = "ke"
    display_name = PROVIDER_NAMES["ke"]
    host = "m.ke.com"
