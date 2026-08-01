import json
import threading

_audit_context = threading.local()


class AuditMiddleware:
    """
    Makes request context available globally for audit logging.
    Actual audit writes happen in views/services — this just stores context.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _audit_context.user_id = getattr(request.global_user, 'get', lambda x: None)('id') \
            if request.global_user else None
        _audit_context.tenant_id = getattr(request.active_business, 'get', lambda x: None)('tenant_id') \
            if request.active_business else None
        _audit_context.ip_address = self._get_client_ip(request)
        _audit_context.user_agent = request.META.get('HTTP_USER_AGENT', '')

        response = self.get_response(request)
        return response

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


def get_audit_context():
    return {
        'user_id': getattr(_audit_context, 'user_id', None),
        'tenant_id': getattr(_audit_context, 'tenant_id', None),
        'ip_address': getattr(_audit_context, 'ip_address', ''),
        'user_agent': getattr(_audit_context, 'user_agent', ''),
    }
