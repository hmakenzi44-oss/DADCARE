"""
core/audit_service.py — Write to the immutable audit log.
Never call AuditLog.objects.update() or .delete() — the DB trigger will reject it.
"""
from middleware.audit_middleware import get_audit_context
import logging

logger = logging.getLogger(__name__)


def log_action(
    action: str,
    target_type: str = '',
    target_id=None,
    old_value=None,
    new_value=None,
    user_id=None,
    user_name: str = '',
    tenant_id=None,
) -> None:
    """
    Write one immutable audit record.
    Context (ip, user_agent, user_id, tenant_id) auto-filled from middleware
    unless explicitly overridden.
    """
    from apps.core.models import AuditLog

    ctx = get_audit_context()

    try:
        AuditLog.objects.create(
            tenant_id=tenant_id or ctx.get('tenant_id'),
            user_id=user_id or ctx.get('user_id'),
            user_name=user_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ctx.get('ip_address') or None,
            user_agent=ctx.get('user_agent', ''),
        )
    except Exception as e:
        # Audit failures must NEVER break the main request
        logger.error(f"Audit log write failed: {e}")


def log_tenant_action(
    action: str,
    target_type: str = '',
    target_id=None,
    old_value=None,
    new_value=None,
    user_id=None,
    user_name: str = '',
) -> None:
    """Write to tenant_audit_log (tenant schema). Called from shop views."""
    from apps.shop.models import TenantAuditLog
    ctx = get_audit_context()

    try:
        TenantAuditLog.objects.create(
            user_id=user_id or ctx.get('user_id'),
            user_name=user_name,
            action=action,
            target_type=target_type,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ctx.get('ip_address') or None,
        )
    except Exception as e:
        logger.error(f"Tenant audit log write failed: {e}")
