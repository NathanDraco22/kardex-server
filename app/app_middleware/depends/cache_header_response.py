from fastapi import Response
from kardex.tools import TimeTools


async def cache_header_response_midnight(response: Response):
    next_midnight_in_seconds = TimeTools.seconds_until_next_midnight()
    response.headers["Cache-Control"] = "public, max-age=" + str(
        next_midnight_in_seconds
    )
