class QueryResult:
    def __init__(self, query: dict, offset: int, limit: int):
        self.query = query
        self.offset = offset
        self.limit = limit


def build_query(date_field: str, **kargs) -> QueryResult:
    query = {
        "clientId": kargs.get("clientId"),
        "supplierId": kargs.get("supplierId"),
        "branchId": kargs.get("branchId"),
        "status": kargs.get("status"),
    }

    offset = int(kargs["offset"])
    limit = int(kargs["limit"])
    if kargs.get("startDate") and kargs.get("endDate"):
        query[date_field] = {
            "$gte": kargs.get("startDate"),
            "$lte": kargs.get("endDate"),
        }

    if kargs.get("createdBy"):
        query["createdBy.id"] = kargs.get("createdBy")

    query = {k: v for k, v in query.items() if v is not None}

    return QueryResult(query, offset, limit)
