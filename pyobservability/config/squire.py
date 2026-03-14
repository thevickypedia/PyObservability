from typing import Any, Dict, Optional
from urllib.parse import urlencode


def urljoin(*args, params: Optional[Dict[str, Any]] = None) -> str:
    """Joins given arguments into a URL and optionally adds query parameters.

    Args:
        *args: URL parts to join.
        params: Optional dictionary of query parameters.

    Returns:
        str: Joined URL with optional query string.
    """
    base_url = "/".join(str(x).rstrip("/").lstrip("/") for x in args)

    if params:
        query_string = urlencode(params)
        return f"{base_url}?{query_string}"

    return base_url
