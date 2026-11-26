from fastapi import Response
from kardex.tools import TimeTools

_TENANT_VARY_HEADERS = ("X-Servin", "x-tenant-nickname", "Authorization")


async def cache_header_response_midnight(response: Response):
    next_midnight_in_seconds = TimeTools.seconds_until_next_midnight()
    response.headers["Cache-Control"] = (
        f"private, max-age={next_midnight_in_seconds}"
    )

    existing_vary = response.headers.get("Vary", "")
    vary_items = [item.strip() for item in existing_vary.split(",") if item.strip()]
    existing_lower = {item.lower() for item in vary_items}

    for header in _TENANT_VARY_HEADERS:
        if header.lower() not in existing_lower:
            vary_items.append(header)
            existing_lower.add(header.lower())

    response.headers["Vary"] = ", ".join(vary_items)
