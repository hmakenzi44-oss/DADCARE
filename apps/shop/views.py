"""
shop/views.py — Shop mini-app API endpoints.
All routes require @require_business (active business JWT).
Raw SQL via shop/services.py — tenant schema set by TenantMiddleware.
"""
import json
import uuid
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from apps.core.permissions import (
    require_business, require_owner, require_manager_or_above,
    require_permission, require_role
)
from apps.core.audit_service import log_tenant_action
from apps.shop.services import (
    _fetchall, _fetchone, _exec,
    create_sale, void_sale, record_stock_movement,
    generate_order_number, generate_po_number,
)


# ─────────────────────────────────────────────
# PRODUCTS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def list_products(request):
    """GET /api/shop/products/ — All products (active + inactive for staff)."""
    role = request.active_business['role']
    where = "" if role in ('owner', 'manager') else "WHERE is_active = true"

    search = request.GET.get('search', '').strip()
    category = request.GET.get('category', '').strip()
    low_stock = request.GET.get('low_stock', '')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 50
    offset = (page - 1) * per_page

    conditions = []
    params = []

    if where:
        conditions.append("is_active = true")
    if search:
        conditions.append("(name ILIKE %s OR barcode = %s)")
        params += [f'%{search}%', search]
    if category:
        conditions.append("category = %s")
        params.append(category)
    if low_stock == '1':
        conditions.append("stock_quantity <= low_stock_threshold")

    where_clause = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    products = _fetchall(
        f"""SELECT id, name, category, barcode, cost_price, selling_price,
                   stock_quantity, low_stock_threshold, unit, images,
                   is_active, created_at
            FROM products {where_clause}
            ORDER BY name ASC
            LIMIT %s OFFSET %s""",
        params + [per_page, offset]
    )

    count = _fetchone(
        f"SELECT COUNT(*) as cnt FROM products {where_clause}", params
    )

    return JsonResponse({
        'products': [_serialize_product(p) for p in products],
        'total': count['cnt'] if count else 0,
        'page': page,
        'per_page': per_page,
    })


@require_http_methods(["GET"])
@require_business
def product_detail(request, product_id):
    product = _fetchone("SELECT * FROM products WHERE id = %s", [str(product_id)])
    if not product:
        return JsonResponse({'error': 'Bidhaa haipatikani'}, status=404)
    return JsonResponse(_serialize_product(product))


@csrf_exempt
@require_http_methods(["POST"])
@require_manager_or_above
def create_product(request):
    """POST /api/shop/products/create/"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    selling_price = data.get('selling_price')

    if not name:
        return JsonResponse({'error': 'Jina la bidhaa linahitajika'}, status=400)
    if selling_price is None:
        return JsonResponse({'error': 'Bei ya kuuza inahitajika'}, status=400)

    product_id = str(uuid.uuid4())
    user = request.global_user

    _exec("""
        INSERT INTO products
            (id, name, description, category, barcode, cost_price, selling_price,
             stock_quantity, low_stock_threshold, unit, images, is_active,
             created_by, created_at, updated_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,true,%s,NOW(),NOW())
    """, [
        product_id, name,
        data.get('description', ''),
        data.get('category', ''),
        data.get('barcode', ''),
        data.get('cost_price'),
        selling_price,
        data.get('stock_quantity', 0),
        data.get('low_stock_threshold', 10),
        data.get('unit', 'pcs'),
        json.dumps(data.get('images', [])),
        user['id'],
    ])

    log_tenant_action(
        action='PRODUCT_CREATED',
        target_type='product',
        target_id=product_id,
        new_value={'name': name, 'selling_price': str(selling_price)},
        user_id=user['id'],
        user_name=user['full_name'],
    )

    return JsonResponse({'success': True, 'product_id': product_id}, status=201)


@csrf_exempt
@require_http_methods(["PATCH"])
@require_manager_or_above
def update_product(request, product_id):
    """PATCH /api/shop/products/<id>/update/"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    product = _fetchone("SELECT * FROM products WHERE id = %s", [str(product_id)])
    if not product:
        return JsonResponse({'error': 'Bidhaa haipatikani'}, status=404)

    # Check price change permission
    if 'selling_price' in data or 'cost_price' in data:
        business = request.active_business
        if business['role'] not in ('owner',) and \
           not business['permissions'].get('can_change_prices'):
            return JsonResponse({'error': 'Huna ruhusa ya kubadilisha bei'}, status=403)

    allowed = [
        'name', 'description', 'category', 'barcode',
        'cost_price', 'selling_price', 'low_stock_threshold',
        'unit', 'images', 'is_active'
    ]
    set_parts = []
    params = []
    for field in allowed:
        if field in data:
            set_parts.append(f"{field} = %s")
            val = data[field]
            if field == 'images':
                val = json.dumps(val)
            params.append(val)

    if not set_parts:
        return JsonResponse({'error': 'Hakuna mabadiliko'}, status=400)

    set_parts.append("updated_at = NOW()")
    params.append(str(product_id))

    _exec(
        f"UPDATE products SET {', '.join(set_parts)} WHERE id = %s",
        params
    )

    log_tenant_action(
        action='PRODUCT_UPDATED',
        target_type='product',
        target_id=str(product_id),
        old_value={k: str(product.get(k)) for k in allowed if k in product},
        new_value=data,
        user_id=request.global_user['id'],
        user_name=request.global_user['full_name'],
    )

    return JsonResponse({'success': True})


@csrf_exempt
@require_http_methods(["POST"])
@require_permission('can_adjust_stock')
def adjust_stock(request, product_id):
    """
    POST /api/shop/products/<id>/adjust-stock/
    Body: { quantity_change, reason }
    Manual stock adjustment — recorded in stock_movements.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    product = _fetchone(
        "SELECT id, name FROM products WHERE id = %s", [str(product_id)]
    )
    if not product:
        return JsonResponse({'error': 'Bidhaa haipatikani'}, status=404)

    quantity_change = data.get('quantity_change')
    if quantity_change is None:
        return JsonResponse({'error': 'quantity_change inahitajika'}, status=400)

    user = request.global_user
    try:
        result = record_stock_movement(
            product_id=str(product_id),
            product_name=product['name'],
            movement_type='adjustment',
            quantity_change=int(quantity_change),
            performed_by=user['id'],
            performed_by_name=user['full_name'],
            notes=data.get('reason', ''),
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'success': True, **result})


# ─────────────────────────────────────────────
# POINT OF SALE
# ─────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
@require_business
def process_sale(request):
    """
    POST /api/shop/sales/
    Body: {
        items: [{product_id, quantity, unit_price?, discount?}],
        payment_method,
        customer_id?,
        discount?,
        payment_reference?,
        notes?
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    items = data.get('items', [])
    payment_method = data.get('payment_method', '')

    if not items:
        return JsonResponse({'error': 'Bidhaa lazima ziwepo'}, status=400)
    if not payment_method:
        return JsonResponse({'error': 'Njia ya malipo inahitajika'}, status=400)

    # Discount permission check
    if data.get('discount') and float(data.get('discount', 0)) > 0:
        business = request.active_business
        if business['role'] not in ('owner', 'manager') and \
           not business['permissions'].get('can_give_discounts'):
            return JsonResponse({'error': 'Huna ruhusa ya kutoa punguzo'}, status=403)

    # Fetch shop tax rate
    settings = _fetchone("SELECT tax_rate FROM shop_settings LIMIT 1")
    tax_rate = float(settings['tax_rate']) if settings else 0

    user = request.global_user
    try:
        result = create_sale(
            items=items,
            payment_method=payment_method,
            cashier_id=user['id'],
            cashier_name=user['full_name'],
            customer_id=data.get('customer_id'),
            discount=float(data.get('discount', 0)),
            tax_rate=tax_rate,
            payment_reference=data.get('payment_reference', ''),
            notes=data.get('notes', ''),
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'success': True, **result}, status=201)


@require_http_methods(["GET"])
@require_business
def sale_detail(request, sale_id):
    """GET /api/shop/sales/<id>/ — Sale + items (for receipt)."""
    sale = _fetchone("SELECT * FROM sales WHERE id = %s", [str(sale_id)])
    if not sale:
        return JsonResponse({'error': 'Mauzo hayapatikani'}, status=404)

    items = _fetchall("SELECT * FROM sale_items WHERE sale_id = %s", [str(sale_id)])
    settings = _fetchone("SELECT shop_name, whatsapp, receipt_footer, currency FROM shop_settings LIMIT 1")

    return JsonResponse({
        'sale': _serialize_sale(sale),
        'items': [_serialize_sale_item(i) for i in items],
        'shop': settings or {},
    })


@require_http_methods(["GET"])
@require_business
def list_sales(request):
    """GET /api/shop/sales/ — Sales history with filters."""
    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')
    status = request.GET.get('status', '')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 50
    offset = (page - 1) * per_page

    conditions = []
    params = []

    if date_from:
        conditions.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= %s")
        params.append(date_to + ' 23:59:59')
    if status:
        conditions.append("status = %s")
        params.append(status)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    sales = _fetchall(
        f"SELECT * FROM sales {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset]
    )
    count = _fetchone(f"SELECT COUNT(*) as cnt FROM sales {where}", params)

    return JsonResponse({
        'sales': [_serialize_sale(s) for s in sales],
        'total': count['cnt'] if count else 0,
        'page': page,
    })


@csrf_exempt
@require_http_methods(["POST"])
@require_permission('can_void_sales')
def void_sale_view(request, sale_id):
    """POST /api/shop/sales/<id>/void/ — Void a sale and restore stock."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    reason = data.get('reason', '').strip()
    if not reason:
        return JsonResponse({'error': 'Sababu ya kubatilisha inahitajika'}, status=400)

    user = request.global_user
    try:
        result = void_sale(
            sale_id=str(sale_id),
            voided_by=user['id'],
            voided_by_name=user['full_name'],
            reason=reason,
        )
    except ValueError as e:
        return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'success': True, **result})


# ─────────────────────────────────────────────
# CUSTOMERS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def list_customers(request):
    search = request.GET.get('search', '')
    params = []
    where = ""
    if search:
        where = "WHERE name ILIKE %s OR phone ILIKE %s"
        params = [f'%{search}%', f'%{search}%']
    customers = _fetchall(
        f"SELECT * FROM customers {where} ORDER BY name ASC LIMIT 100",
        params
    )
    return JsonResponse({'customers': [_serialize_customer(c) for c in customers]})


@csrf_exempt
@require_http_methods(["POST"])
@require_business
def create_customer(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Jina la mteja linahitajika'}, status=400)

    customer_id = str(uuid.uuid4())
    _exec("""
        INSERT INTO customers (id, name, phone, email, address, city, credit_limit, balance, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,0,NOW())
    """, [
        customer_id, name,
        data.get('phone', ''), data.get('email', ''),
        data.get('address', ''), data.get('city', ''),
        data.get('credit_limit', 0),
    ])
    return JsonResponse({'success': True, 'customer_id': customer_id}, status=201)


@csrf_exempt
@require_http_methods(["PATCH"])
@require_business
def update_customer(request, customer_id):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    allowed = ['name', 'phone', 'email', 'address', 'city', 'credit_limit']
    set_parts = []
    params = []
    for field in allowed:
        if field in data:
            set_parts.append(f"{field} = %s")
            params.append(data[field])

    if not set_parts:
        return JsonResponse({'error': 'Hakuna mabadiliko'}, status=400)

    params.append(str(customer_id))
    _exec(f"UPDATE customers SET {', '.join(set_parts)} WHERE id = %s", params)
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
# SUPPLIERS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def list_suppliers(request):
    suppliers = _fetchall("SELECT * FROM suppliers ORDER BY name ASC")
    return JsonResponse({'suppliers': [_serialize_supplier(s) for s in suppliers]})


@csrf_exempt
@require_http_methods(["POST"])
@require_manager_or_above
def create_supplier(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    name = data.get('name', '').strip()
    if not name:
        return JsonResponse({'error': 'Jina la msambazaji linahitajika'}, status=400)

    supplier_id = str(uuid.uuid4())
    _exec("""
        INSERT INTO suppliers (id, name, contact_person, phone, email, address, payment_terms, created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,NOW())
    """, [
        supplier_id, name,
        data.get('contact_person', ''), data.get('phone', ''),
        data.get('email', ''), data.get('address', ''),
        data.get('payment_terms', ''),
    ])
    return JsonResponse({'success': True, 'supplier_id': supplier_id}, status=201)


# ─────────────────────────────────────────────
# PURCHASE ORDERS (from supplier)
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def list_purchase_orders(request):
    orders = _fetchall("SELECT * FROM purchase_orders ORDER BY created_at DESC LIMIT 100")
    return JsonResponse({'purchase_orders': [_serialize_po(o) for o in orders]})


@csrf_exempt
@require_http_methods(["POST"])
@require_manager_or_above
def create_purchase_order(request):
    """
    POST /api/shop/purchase-orders/
    Body: { supplier_id?, items: [{product_id, product_name, quantity_ordered, unit_cost}], notes? }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    items = data.get('items', [])
    if not items:
        return JsonResponse({'error': 'Bidhaa lazima ziwepo'}, status=400)

    total = sum(float(i['unit_cost']) * int(i['quantity_ordered']) for i in items)
    po_id = str(uuid.uuid4())
    po_number = generate_po_number()
    user = request.global_user

    _exec("""
        INSERT INTO purchase_orders
            (id, order_number, supplier_id, status, total, notes, created_by, created_at)
        VALUES (%s,%s,%s,'draft',%s,%s,%s,NOW())
    """, [
        po_id, po_number, data.get('supplier_id'),
        total, data.get('notes', ''), user['id'],
    ])

    for item in items:
        _exec("""
            INSERT INTO purchase_order_items
                (id, order_id, product_id, product_name,
                 quantity_ordered, quantity_received, unit_cost, total_cost)
            VALUES (%s,%s,%s,%s,%s,0,%s,%s)
        """, [
            str(uuid.uuid4()), po_id,
            item.get('product_id'), item.get('product_name', ''),
            int(item['quantity_ordered']),
            float(item['unit_cost']),
            float(item['unit_cost']) * int(item['quantity_ordered']),
        ])

    return JsonResponse({'success': True, 'po_id': po_id, 'order_number': po_number}, status=201)


@csrf_exempt
@require_http_methods(["POST"])
@require_manager_or_above
def receive_purchase_order(request, po_id):
    """
    POST /api/shop/purchase-orders/<id>/receive/
    Body: { items: [{item_id, quantity_received}] }
    Adds stock for each received item.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    po = _fetchone("SELECT * FROM purchase_orders WHERE id = %s", [str(po_id)])
    if not po:
        return JsonResponse({'error': 'Oda haipatikani'}, status=404)
    if po['status'] == 'cancelled':
        return JsonResponse({'error': 'Oda imefutwa'}, status=400)

    user = request.global_user
    received_items = data.get('items', [])

    for item in received_items:
        poi = _fetchone(
            "SELECT * FROM purchase_order_items WHERE id = %s AND order_id = %s",
            [item['item_id'], str(po_id)]
        )
        if not poi or not poi.get('product_id'):
            continue

        qty = int(item.get('quantity_received', 0))
        if qty <= 0:
            continue

        _exec("""
            UPDATE purchase_order_items
            SET quantity_received = quantity_received + %s
            WHERE id = %s
        """, [qty, item['item_id']])

        record_stock_movement(
            product_id=str(poi['product_id']),
            product_name=poi['product_name'],
            movement_type='purchase',
            quantity_change=qty,
            performed_by=user['id'],
            performed_by_name=user['full_name'],
            reference_id=str(po_id),
            reference_type='purchase_order',
        )

    # Update PO status
    all_items = _fetchall(
        "SELECT quantity_ordered, quantity_received FROM purchase_order_items WHERE order_id = %s",
        [str(po_id)]
    )
    fully_received = all(i['quantity_received'] >= i['quantity_ordered'] for i in all_items)
    new_status = 'received' if fully_received else 'partial'

    _exec("UPDATE purchase_orders SET status = %s, received_at = NOW() WHERE id = %s",
          [new_status, str(po_id)])

    return JsonResponse({'success': True, 'status': new_status})


# ─────────────────────────────────────────────
# WHOLESALE ORDERS (to customers)
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def list_orders(request):
    status = request.GET.get('status', '')
    where = "WHERE status = %s" if status else ""
    params = [status] if status else []
    orders = _fetchall(
        f"SELECT * FROM orders {where} ORDER BY created_at DESC LIMIT 100", params
    )
    return JsonResponse({'orders': [_serialize_order(o) for o in orders]})


@csrf_exempt
@require_http_methods(["POST"])
@require_business
def create_order(request):
    """
    POST /api/shop/orders/
    Body: { customer_id?, items: [{product_id, quantity, unit_price}], discount?, notes? }
    Creates draft wholesale order.
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    items = data.get('items', [])
    if not items:
        return JsonResponse({'error': 'Bidhaa lazima ziwepo'}, status=400)

    subtotal = sum(
        float(i['unit_price']) * int(i['quantity']) for i in items
    )
    discount = float(data.get('discount', 0))
    total = subtotal - discount

    order_id = str(uuid.uuid4())
    order_number = generate_order_number()
    user = request.global_user

    _exec("""
        INSERT INTO orders
            (id, order_number, customer_id, status, subtotal, discount, total,
             payment_method, notes, created_by, created_at, updated_at)
        VALUES (%s,%s,%s,'draft',%s,%s,%s,%s,%s,%s,NOW(),NOW())
    """, [
        order_id, order_number, data.get('customer_id'),
        subtotal, discount, total,
        data.get('payment_method', ''),
        data.get('notes', ''), user['id'],
    ])

    for item in items:
        product = _fetchone("SELECT name FROM products WHERE id = %s", [item['product_id']])
        line_total = float(item['unit_price']) * int(item['quantity'])
        _exec("""
            INSERT INTO order_items
                (id, order_id, product_id, product_name, quantity, unit_price, total_price)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """, [
            str(uuid.uuid4()), order_id,
            item['product_id'],
            product['name'] if product else item.get('product_name', ''),
            int(item['quantity']),
            float(item['unit_price']),
            line_total,
        ])

    return JsonResponse({'success': True, 'order_id': order_id, 'order_number': order_number}, status=201)


@csrf_exempt
@require_http_methods(["PATCH"])
@require_business
def update_order_status(request, order_id):
    """PATCH /api/shop/orders/<id>/status/ — Advance order through workflow."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    new_status = data.get('status', '')
    valid_statuses = ['confirmed', 'packed', 'delivered', 'paid', 'cancelled']
    if new_status not in valid_statuses:
        return JsonResponse({'error': f'Hali lazima iwe: {", ".join(valid_statuses)}'}, status=400)

    # confirmed requires permission
    if new_status == 'confirmed':
        business = request.active_business
        if business['role'] not in ('owner', 'manager') and \
           not business['permissions'].get('can_approve_orders'):
            return JsonResponse({'error': 'Huna ruhusa ya kuthibitisha oda'}, status=403)

    _exec(
        "UPDATE orders SET status = %s, updated_at = NOW() WHERE id = %s",
        [new_status, str(order_id)]
    )
    return JsonResponse({'success': True, 'status': new_status})


# ─────────────────────────────────────────────
# STOCK MOVEMENTS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def list_stock_movements(request):
    product_id = request.GET.get('product_id', '')
    movement_type = request.GET.get('type', '')
    page = max(1, int(request.GET.get('page', 1)))
    per_page = 100
    offset = (page - 1) * per_page

    conditions = []
    params = []
    if product_id:
        conditions.append("product_id = %s")
        params.append(product_id)
    if movement_type:
        conditions.append("movement_type = %s")
        params.append(movement_type)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    movements = _fetchall(
        f"SELECT * FROM stock_movements {where} ORDER BY created_at DESC LIMIT %s OFFSET %s",
        params + [per_page, offset]
    )
    return JsonResponse({'movements': movements})


# ─────────────────────────────────────────────
# REPORTS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def dashboard_stats(request):
    """GET /api/shop/dashboard/ — KPIs for today and summary."""
    business = request.active_business
    can_see_profit = (
        business['role'] in ('owner', 'manager') or
        business['permissions'].get('can_view_financial_reports')
    )

    today_sales = _fetchone("""
        SELECT
            COUNT(*) as sale_count,
            COALESCE(SUM(total), 0) as revenue,
            COALESCE(SUM(discount), 0) as discounts
        FROM sales
        WHERE status = 'completed' AND created_at::date = CURRENT_DATE
    """)

    low_stock = _fetchone(
        "SELECT COUNT(*) as cnt FROM products WHERE stock_quantity <= low_stock_threshold AND is_active = true"
    )

    pending_orders = _fetchone(
        "SELECT COUNT(*) as cnt FROM orders WHERE status IN ('draft', 'confirmed', 'packed')"
    )

    stats = {
        'today': {
            'sale_count': today_sales['sale_count'] if today_sales else 0,
            'revenue': float(today_sales['revenue']) if today_sales else 0,
        },
        'low_stock_count': low_stock['cnt'] if low_stock else 0,
        'pending_orders': pending_orders['cnt'] if pending_orders else 0,
    }

    if can_see_profit:
        profit = _fetchone("""
            SELECT COALESCE(SUM(
                (si.unit_price - COALESCE(p.cost_price, 0)) * si.quantity
            ), 0) as gross_profit
            FROM sale_items si
            JOIN sales s ON s.id = si.sale_id
            LEFT JOIN products p ON p.id = si.product_id
            WHERE s.status = 'completed' AND s.created_at::date = CURRENT_DATE
        """)
        stats['today']['gross_profit'] = float(profit['gross_profit']) if profit else 0

    return JsonResponse(stats)


@require_http_methods(["GET"])
@require_business
def sales_report(request):
    """GET /api/shop/reports/sales/?from=&to= — Aggregated sales report."""
    business = request.active_business
    if business['role'] not in ('owner', 'manager') and \
       not business['permissions'].get('can_view_financial_reports'):
        return JsonResponse({'error': 'Huna ruhusa ya kuona ripoti'}, status=403)

    date_from = request.GET.get('from', '')
    date_to = request.GET.get('to', '')

    conditions = ["status = 'completed'"]
    params = []
    if date_from:
        conditions.append("created_at >= %s")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= %s")
        params.append(date_to + ' 23:59:59')

    where = "WHERE " + " AND ".join(conditions)

    summary = _fetchone(f"""
        SELECT
            COUNT(*) as total_sales,
            COALESCE(SUM(total), 0) as total_revenue,
            COALESCE(SUM(discount), 0) as total_discounts,
            COALESCE(SUM(tax), 0) as total_tax,
            COALESCE(AVG(total), 0) as avg_sale
        FROM sales {where}
    """, params)

    by_payment = _fetchall(f"""
        SELECT payment_method, COUNT(*) as count, COALESCE(SUM(total), 0) as total
        FROM sales {where}
        GROUP BY payment_method ORDER BY total DESC
    """, params)

    top_products = _fetchall(f"""
        SELECT si.product_name,
               SUM(si.quantity) as qty_sold,
               SUM(si.total_price) as revenue
        FROM sale_items si
        JOIN sales s ON s.id = si.sale_id
        {where.replace('WHERE', 'WHERE s.')}
        GROUP BY si.product_name
        ORDER BY revenue DESC
        LIMIT 10
    """, params)

    return JsonResponse({
        'summary': {k: float(v) if v else 0 for k, v in summary.items()} if summary else {},
        'by_payment_method': by_payment,
        'top_products': top_products,
    })


# ─────────────────────────────────────────────
# SHOP SETTINGS
# ─────────────────────────────────────────────

@require_http_methods(["GET"])
@require_business
def get_shop_settings(request):
    settings = _fetchone("SELECT * FROM shop_settings LIMIT 1")
    return JsonResponse(settings or {})


@csrf_exempt
@require_http_methods(["POST", "PATCH"])
@require_owner
def update_shop_settings(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    existing = _fetchone("SELECT id FROM shop_settings LIMIT 1")
    allowed = ['shop_name', 'logo_url', 'address', 'city', 'country_code',
               'phone', 'whatsapp', 'language', 'currency', 'tax_rate', 'receipt_footer']

    if existing:
        set_parts = []
        params = []
        for field in allowed:
            if field in data:
                set_parts.append(f"{field} = %s")
                params.append(data[field])
        if set_parts:
            set_parts.append("updated_at = NOW()")
            params.append(existing['id'])
            _exec(f"UPDATE shop_settings SET {', '.join(set_parts)} WHERE id = %s", params)
    else:
        settings_id = str(uuid.uuid4())
        _exec("""
            INSERT INTO shop_settings
                (id, shop_name, logo_url, address, city, country_code,
                 phone, whatsapp, language, currency, tax_rate, receipt_footer, updated_at)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """, [
            settings_id,
            data.get('shop_name', ''), data.get('logo_url', ''),
            data.get('address', ''), data.get('city', ''),
            data.get('country_code', ''), data.get('phone', ''),
            data.get('whatsapp', ''), data.get('language', 'sw'),
            data.get('currency', 'TZS'), data.get('tax_rate', 0),
            data.get('receipt_footer', ''),
        ])

    return JsonResponse({'success': True})


# ─────────────────────────────────────────────
# SERIALIZERS (dict → JSON-safe dict)
# ─────────────────────────────────────────────

def _serialize_product(p: dict) -> dict:
    return {
        'id': str(p['id']),
        'name': p['name'],
        'category': p.get('category', ''),
        'barcode': p.get('barcode', ''),
        'cost_price': float(p['cost_price']) if p.get('cost_price') else None,
        'selling_price': float(p['selling_price']),
        'stock_quantity': p['stock_quantity'],
        'low_stock_threshold': p.get('low_stock_threshold', 10),
        'is_low_stock': p['stock_quantity'] <= p.get('low_stock_threshold', 10),
        'unit': p.get('unit', 'pcs'),
        'images': p.get('images', []),
        'is_active': p.get('is_active', True),
        'created_at': p['created_at'].isoformat() if p.get('created_at') else None,
    }


def _serialize_sale(s: dict) -> dict:
    return {
        'id': str(s['id']),
        'sale_number': s['sale_number'],
        'subtotal': float(s['subtotal']),
        'discount': float(s.get('discount', 0)),
        'tax': float(s.get('tax', 0)),
        'total': float(s['total']),
        'payment_method': s['payment_method'],
        'payment_reference': s.get('payment_reference', ''),
        'status': s['status'],
        'notes': s.get('notes', ''),
        'created_at': s['created_at'].isoformat() if s.get('created_at') else None,
    }


def _serialize_sale_item(i: dict) -> dict:
    return {
        'id': str(i['id']),
        'product_id': str(i['product_id']) if i.get('product_id') else None,
        'product_name': i['product_name'],
        'quantity': i['quantity'],
        'unit_price': float(i['unit_price']),
        'discount': float(i.get('discount', 0)),
        'total_price': float(i['total_price']),
    }


def _serialize_customer(c: dict) -> dict:
    return {
        'id': str(c['id']),
        'name': c['name'],
        'phone': c.get('phone', ''),
        'email': c.get('email', ''),
        'city': c.get('city', ''),
        'credit_limit': float(c.get('credit_limit', 0)),
        'balance': float(c.get('balance', 0)),
        'created_at': c['created_at'].isoformat() if c.get('created_at') else None,
    }


def _serialize_supplier(s: dict) -> dict:
    return {
        'id': str(s['id']),
        'name': s['name'],
        'contact_person': s.get('contact_person', ''),
        'phone': s.get('phone', ''),
        'email': s.get('email', ''),
        'payment_terms': s.get('payment_terms', ''),
    }


def _serialize_po(o: dict) -> dict:
    return {
        'id': str(o['id']),
        'order_number': o['order_number'],
        'status': o['status'],
        'total': float(o['total']),
        'notes': o.get('notes', ''),
        'created_at': o['created_at'].isoformat() if o.get('created_at') else None,
    }


def _serialize_order(o: dict) -> dict:
    return {
        'id': str(o['id']),
        'order_number': o['order_number'],
        'status': o['status'],
        'subtotal': float(o['subtotal']),
        'discount': float(o.get('discount', 0)),
        'total': float(o['total']),
        'payment_method': o.get('payment_method', ''),
        'created_at': o['created_at'].isoformat() if o.get('created_at') else None,
    }
