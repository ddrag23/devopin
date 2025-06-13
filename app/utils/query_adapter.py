from typing import List, Optional, Tuple, Dict, Any, Callable
from fastapi import Request
from sqlalchemy.orm import Query
from sqlalchemy.sql import or_


class QueryAdapter:
    def __init__(
        self,
        model,
        request: Optional[Request] = None,
        allowed_search_fields: Optional[List[str]] = None,
        query_params: Optional[Dict[str, str]] = None,
        max_limit: int = 1000,
        is_soft_delete: bool = False,
    ):
        self.model = model
        self.request = request
        # Support for request-based or direct dictionary-based query params
        self.query_params = query_params or (request.query_params if request else {})
        self.allowed_search_fields = allowed_search_fields or []
        self.max_limit = max_limit
        self.is_soft_delete = is_soft_delete

    LOOKUP_MAP: Dict[str, Callable[[Any, Any], Any]] = {
        "eq": lambda col, val: col == val,
        "neq": lambda col, val: col != val,
        "lt": lambda col, val: col < val,
        "lte": lambda col, val: col <= val,
        "gt": lambda col, val: col > val,
        "gte": lambda col, val: col >= val,
        "like": lambda col, val: col.like(f"%{val}%"),
        "ilike": lambda col, val: col.ilike(f"%{val}%"),
        "in": lambda col, val: col.in_(val.split(",")),
    }

    def __resolve_column(self, attr_path: str):
        attrs = attr_path.split(".")
        current = self.model
        for attr in attrs:
            current = getattr(current, attr)
        return current

    def __apply_filters(self, query: Query) -> Query:
        filters = []

        for key, val in self.query_params.items():
            # Skip if the parameter is a search or pagination-related
            if key == "search" or key in ["page", "limit"]:
                continue
            if "__" in key:
                field_path, lookup = key.split("__", 1)
                try:
                    col = self.__resolve_column(field_path)
                    if lookup in self.LOOKUP_MAP:
                        filters.append(self.LOOKUP_MAP[lookup](col, val))
                except Exception:
                    continue

        if filters:
            query = query.filter(*filters)
        return query

    def __apply_search(self, query: Query) -> Query:
        search_val = self.query_params.get("search")
        if search_val and self.allowed_search_fields:
            conditions = []
            for field in self.allowed_search_fields:
                try:
                    col = self.__resolve_column(field)
                    conditions.append(col.ilike(f"%{search_val}%"))
                except Exception:
                    continue
            if conditions:
                query = query.filter(or_(*conditions))
        return query

    def __apply_soft_delete(self, query: Query) -> Query:
        if self.is_soft_delete:
            return query.filter(self.model.deleted_at is None)
        return query

    def __apply_pagination(
        self, query: Query
    ) -> Tuple[Query, Optional[int], Optional[int]]:
        try:
            page = int(self.query_params.get("page", 1))
            limit = int(self.query_params.get("limit", self.max_limit))
            limit = min(limit, self.max_limit)  # Ensure limit doesn't exceed max
            offset = (page - 1) * limit

            # Apply pagination only if page and limit are valid numbers
            if page > 0 and limit > 0:
                query = query.offset(offset).limit(limit)
                return query, page, limit
        except (ValueError, TypeError):
            pass

        # No pagination applied, return all data
        return query, None, None

    def adapt(self, query: Query) -> Tuple[Query, Optional[int], Optional[int], int]:
        query = self.simple_adapt(query)
        count = query.count()
        query, page, limit = self.__apply_pagination(query)
        return query, page, limit, count

    def simple_adapt(self, query: Query) -> Query:
        query = self.__apply_filters(query)
        query = self.__apply_search(query)
        query = self.__apply_soft_delete(query)
        return query
