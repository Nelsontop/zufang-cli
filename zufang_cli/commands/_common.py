from __future__ import annotations

from collections.abc import Callable
from typing import Optional, TypeVar

from ..exceptions import ZufangCliError
from ..output import print_error, print_structured

T = TypeVar("T")


def run_command(
    fn: Callable[[], T],
    *,
    render: Optional[Callable[[T], None]] = None,
    as_json: bool = False,
    as_yaml: bool = False,
) -> Optional[T]:
    try:
        data = fn()
        if as_json or as_yaml:
            payload = data.to_dict() if hasattr(data, "to_dict") else data
            print_structured(payload, as_json=as_json, as_yaml=as_yaml)
            return data
        if render:
            render(data)
        return data
    except ZufangCliError as exc:
        print_error(exc, as_json=as_json, as_yaml=as_yaml)
        return None
