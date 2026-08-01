"""
shop/services.py — Business logic layer for the Shop mini-app.
All DB writes go through here — views stay thin.
Handles: sale number generation, stock deduction, stock movement recording.
"""
import uuid
from datetime import date
from django.db import connection, transaction
from django.utils import timezone
from apps.core.audit_service import log_tenant_action


def _exec(sql: str, params=None):
    """Execute raw SQL against the current tenant schema (set by middleware)."""
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        return cur


def _fetchall(sql: str, params=None) -> list[dict]:
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _fetchone(sql: str, params=None) -> dict | None:
    with connection.cursor() as cur:
        cur.execute(sql, params or [])
        if not cur.description:
            return None
        cols = [c[0] for c in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None


def generate_sale_number() -> str:
    today = date.today().strftime('%Y%m%d')
    result = _fetchone(
        "SELECT COUNT(*) as cnt FROM sales WHERE created_at::date = CURRENT_DATE"
    )
    seq = (result['cnt'] or 0) + 1
    return f"SL-{today}-{seq:04d}"


def generate_order_number(prefix='ORD') -> str:
    today = date.today().strftime('%Y%m%d')
    result = _fetchone(
        "SELECT COUNT(*) as cnt FROM orders WHERE created_at::date = CURRENT_DATE"
    )
    seq = (result['cnt'] or 0) + 1
    return f"{prefix}-{today}-{seq:04d}"


def generate_po_number() -> str:
    today = date.today().strftime('%Y%m%d')
    result = _fetchone(
        "SELECT COUNT(*) as cnt FROM purchase_orders WHERE created_at::date = CURRENT_DATE"
    )
    seq = (result['cnt'] or 0) + 1
    return f"PO-{today}-{seq:04d}"


def record_stock_movement(
    product_id: str,
    product_name: str,
    movement_type: str,
    quantity_change: int,
    performed_by: str,
    performed_by_name: str,
    reference_id: str = None,
    reference_type: str = '',
    notes: str = '',
) -> dict:
    """
    Records a stock movement and updates product stock_quantity atomically.
    quantity_change: positive = increase, negative = decrease.
    """
    product = _fetchone("SELECT stock_quantity FROM products WHERE id = %s", [product_id])
    if not product:
        raise ValueError(f"Product {product_id} not found")

    qty_before = product['stock_quantity']
    qty_after = qty_before + quantity_change

    if qty_after < 0:
        raise ValueError(
            f"Stoo haitoshi. Iliyopo: {qty_before}, Inayohitajika: {abs(quantity_change)}"
        )

    movement_id = str(uuid.uuid4())

    _exec("""
        INSERT INTO stock_movements
            (id, product_id, product_name, movement_type,
             quantity_before, quantity_change, quantity_after,
             reference_id, reference_type, notes,
             performed_by, performed_by_name, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
    """, [
        movement_id, product_id, product_name, movement_type,
        qty_before, quantity_change, qty_after,
        reference_id, reference_type, notes,
        performed_by, performed_by_name,
    ])

    _exec(
        "UPDATE products SET stock_quantity = %s, updated_at = NOW() WHERE id = %s",
        [qty_after, product_id]
    )

    return {
        'movement_id': movement_id,
        'quantity_before': qty_before,
        'quantity_after': qty_after,
    }


def create_sale(
    items: list[dict],
    payment_method: str,
    cashier_id: str,
    cashier_name: str,
    customer_id: str = None,
    discount: float = 0,
    tax_rate: float = 0,
    payment_reference: str = '',
    notes: str = '',
) -> dict:
    """
    Creates a complete sale atomically:
    1. Validates all products and stock
    2. Calculates totals
    3. Creates sale record
    4. Creates sale_items
    5. Deducts stock + records movements
    6. Writes audit log
    """
    if not items:
        raise ValueError("Bidhaa lazima ziwepo angalau moja")

    # Validate and enrich items
    enriched = []
    subtotal = 0

    for item in items:
        product = _fetchone(
            "SELECT id, name, selling_price, stock_quantity, is_active FROM products WHERE id = %s",
            [item['product_id']]
        )
        if not product:
            raise ValueError(f"Bidhaa haipatikani: {item['product_id']}")
        if not product['is_active']:
            raise ValueError(f"Bidhaa imefungwa: {product['name']}")

        qty = int(item['quantity'])
        if qty <= 0:
            raise ValueError(f"Idadi lazima iwe zaidi ya 0: {product['name']}")

        unit_price = float(item.get('unit_price', product['selling_price']))
        item_discount = float(item.get('discount', 0))
        line_total = (unit_price * qty) - item_discount
        subtotal += line_total

        enriched.append({
            'product_id': str(product['id']),
            'product_name': product['name'],
            'stock_quantity': product['stock_quantity'],
            'quantity': qty,
            'unit_price': unit_price,
            'discount': item_discount,
            'total_price': line_total,
        })

    discount = float(discount)
    tax = round((subtotal - discount) * (tax_rate / 100), 2)
    total = round(subtotal - discount + tax, 2)
    sale_number = generate_sale_number()
    sale_id = str(uuid.uuid4())

    with transaction.atomic():
        _exec("""
            INSERT INTO sales
                (id, sale_number, customer_id, cashier_id, subtotal,
                 discount, tax, total, payment_method, payment_reference,
                 status, notes, created_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'completed',%s,NOW())
        """, [
            sale_id, sale_number, customer_id, cashier_id,
            subtotal, discount, tax, total,
            payment_method, payment_reference, notes,
        ])

        for item in enriched:
            item_id = str(uuid.uuid4())
            _exec("""
                INSERT INTO sale_items
                    (id, sale_id, product_id, product_name,
                     quantity, unit_price, discount, total_price)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, [
                item_id, sale_id,
                item['product_id'], item['product_name'],
                item['quantity'], item['unit_price'],
                item['discount'], item['total_price'],
            ])

            record_stock_movement(
                product_id=item['product_id'],
                product_name=item['product_name'],
                movement_type='sale',
                quantity_change=-item['quantity'],
                performed_by=cashier_id,
                performed_by_name=cashier_name,
                reference_id=sale_id,
                reference_type='sale',
            )

        log_tenant_action(
            action='SALE_CREATED',
            target_type='sale',
            target_id=sale_id,
            new_value={'sale_number': sale_number, 'total': total, 'items': len(enriched)},
            user_id=cashier_id,
            user_name=cashier_name,
        )

    return {
        'sale_id': sale_id,
        'sale_number': sale_number,
        'subtotal': subtotal,
        'discount': discount,
        'tax': tax,
        'total': total,
        'items': enriched,
    }


def void_sale(sale_id: str, voided_by: str, voided_by_name: str, reason: str) -> dict:
    """
    Voids a completed sale and restores stock.
    Requires can_void_sales permission (checked in view).
    """
    sale = _fetchone("SELECT * FROM sales WHERE id = %s", [sale_id])
    if not sale:
        raise ValueError("Mauzo hayapatikani")
    if sale['status'] == 'voided':
        raise ValueError("Mauzo haya tayari yamebatilishwa")

    items = _fetchall("SELECT * FROM sale_items WHERE sale_id = %s", [sale_id])

    with transaction.atomic():
        _exec("""
            UPDATE sales
            SET status='voided', voided_by=%s, voided_at=NOW(), void_reason=%s
            WHERE id=%s
        """, [voided_by, reason, sale_id])

        for item in items:
            record_stock_movement(
                product_id=str(item['product_id']),
                product_name=item['product_name'],
                movement_type='return',
                quantity_change=item['quantity'],
                performed_by=voided_by,
                performed_by_name=voided_by_name,
                reference_id=sale_id,
                reference_type='void',
                notes=f"Void: {reason}",
            )

        log_tenant_action(
            action='SALE_VOIDED',
            target_type='sale',
            target_id=sale_id,
            old_value={'status': 'completed'},
            new_value={'status': 'voided', 'reason': reason},
            user_id=voided_by,
            user_name=voided_by_name,
        )

    return {'sale_id': sale_id, 'status': 'voided'}
