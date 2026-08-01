from django.db import connection


class TenantMiddleware:
    """
    Sets PostgreSQL search_path to the active tenant's schema on every request.
    Falls back to public schema if no business JWT is active.
    CRITICAL: Prevents all cross-tenant data leakage.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        active_business = getattr(request, 'active_business', None)

        if active_business and active_business.get('schema'):
            schema = active_business['schema']
            # Validate schema name format — SECURITY CRITICAL
            if self._is_valid_schema(schema):
                with connection.cursor() as cursor:
                    cursor.execute(
                        f"SET search_path TO {schema}, public"
                    )
        else:
            with connection.cursor() as cursor:
                cursor.execute("SET search_path TO public")

        response = self.get_response(request)

        # Reset to public after each request
        with connection.cursor() as cursor:
            cursor.execute("SET search_path TO public")

        return response

    def _is_valid_schema(self, schema: str) -> bool:
        """Only allow tenant_{uuid} format — no SQL injection possible."""
        import re
        pattern = r'^tenant_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, schema))
