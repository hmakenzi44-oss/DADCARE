"""
tenants/schema_service.py — Provisions a new PostgreSQL schema per tenant.
Called once during business registration. Never called again.
"""
import os
from pathlib import Path
from django.db import connection
import logging

logger = logging.getLogger(__name__)

SQL_FILE = Path(__file__).parent / 'sql' / 'create_tenant_schema.sql'


def provision_tenant_schema(tenant_id: str) -> bool:
    """
    Creates a new PostgreSQL schema for a tenant.
    Schema name: tenant_{uuid}
    Returns True on success, raises on failure.
    """
    schema_name = f"tenant_{tenant_id}"

    # Security: validate format before touching DB
    import re
    pattern = r'^tenant_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(pattern, schema_name):
        raise ValueError(f"Invalid schema name format: {schema_name}")

    sql_template = SQL_FILE.read_text()
    sql = sql_template.replace('{schema_name}', schema_name)

    try:
        with connection.cursor() as cursor:
            # Execute the full schema creation script
            cursor.execute(sql)
        logger.info(f"Tenant schema created: {schema_name}")
        return True
    except Exception as e:
        logger.error(f"Failed to create tenant schema {schema_name}: {e}")
        raise


def drop_tenant_schema(tenant_id: str) -> bool:
    """
    Drops a tenant schema. DESTRUCTIVE — only for Super Admin use.
    Requires explicit confirmation in calling code.
    """
    schema_name = f"tenant_{tenant_id}"

    import re
    pattern = r'^tenant_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if not re.match(pattern, schema_name):
        raise ValueError(f"Invalid schema name: {schema_name}")

    with connection.cursor() as cursor:
        cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')

    logger.warning(f"Tenant schema DROPPED: {schema_name}")
    return True
