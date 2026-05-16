from fastapi import Request, Response


class NotModified(Exception):
    pass


async def not_modified_exception_handler(request: Request, exc: Exception):
    return Response(status_code=304)
