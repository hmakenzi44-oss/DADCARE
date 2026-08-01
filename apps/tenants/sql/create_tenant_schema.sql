-- ============================================================
-- DADCARE — Tenant Schema Creation Script
-- Executed once per new business registration
-- Schema: tenant_{uuid}
-- ============================================================

-- Create schema
CREATE SCHEMA IF NOT EXISTS "tenant_{schema_name}";
SET search_path TO "tenant_{schema_name}";

-- Shop settings
CREATE TABLE shop_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    shop_name VARCHAR(255) NOT NULL,
    logo_url VARCHAR(500),
    address TEXT,
    city VARCHAR(100),
    country_code VARCHAR(5),
    phone VARCHAR(50),
    whatsapp VARCHAR(50),
    language VARCHAR(5) DEFAULT 'sw',
    currency VARCHAR(10) DEFAULT 'TZS',
    tax_rate DECIMAL(5,2) DEFAULT 0,
    receipt_footer TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories
CREATE TABLE categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Products
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    barcode VARCHAR(100),
    cost_price DECIMAL(15,2),
    selling_price DECIMAL(15,2) NOT NULL,
    stock_quantity INT DEFAULT 0,
    low_stock_threshold INT DEFAULT 10,
    unit VARCHAR(50) DEFAULT 'pcs',
    images JSONB DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Customers
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    city VARCHAR(100),
    credit_limit DECIMAL(15,2) DEFAULT 0,
    balance DECIMAL(15,2) DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Suppliers
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    payment_terms TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sales
CREATE TABLE sales (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID,
    cashier_id UUID NOT NULL,
    subtotal DECIMAL(15,2) NOT NULL,
    discount DECIMAL(15,2) DEFAULT 0,
    tax DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    payment_reference VARCHAR(255),
    status VARCHAR(20) DEFAULT 'completed',
    voided_by UUID,
    voided_at TIMESTAMPTZ,
    void_reason TEXT,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Sale items
CREATE TABLE sale_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sale_id UUID REFERENCES sales(id) ON DELETE CASCADE,
    product_id UUID,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    discount DECIMAL(15,2) DEFAULT 0,
    total_price DECIMAL(15,2) NOT NULL
);

-- Stock movements
CREATE TABLE stock_movements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_id UUID NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    movement_type VARCHAR(20) NOT NULL,
    quantity_before INT NOT NULL,
    quantity_change INT NOT NULL,
    quantity_after INT NOT NULL,
    reference_id UUID,
    reference_type VARCHAR(50),
    notes TEXT,
    performed_by UUID NOT NULL,
    performed_by_name VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Purchase orders
CREATE TABLE purchase_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id UUID,
    status VARCHAR(20) DEFAULT 'draft',
    total DECIMAL(15,2) NOT NULL,
    notes TEXT,
    created_by UUID NOT NULL,
    approved_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    received_at TIMESTAMPTZ
);

CREATE TABLE purchase_order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES purchase_orders(id) ON DELETE CASCADE,
    product_id UUID,
    product_name VARCHAR(255) NOT NULL,
    quantity_ordered INT NOT NULL,
    quantity_received INT DEFAULT 0,
    unit_cost DECIMAL(15,2) NOT NULL,
    total_cost DECIMAL(15,2) NOT NULL
);

-- Wholesale orders
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id UUID,
    status VARCHAR(20) DEFAULT 'draft',
    subtotal DECIMAL(15,2) NOT NULL,
    discount DECIMAL(15,2) DEFAULT 0,
    total DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50),
    notes TEXT,
    created_by UUID NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID,
    product_name VARCHAR(255) NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    total_price DECIMAL(15,2) NOT NULL
);

-- HR employee applications
CREATE TABLE employee_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invite_token VARCHAR(255) UNIQUE NOT NULL,
    invited_by UUID NOT NULL,
    applicant_email VARCHAR(255) NOT NULL,
    applicant_name VARCHAR(255),
    position VARCHAR(100),
    role_to_assign VARCHAR(20),
    custom_permissions JSONB DEFAULT '{}',
    status VARCHAR(20) DEFAULT 'pending',
    full_name VARCHAR(255),
    phone VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20),
    nationality VARCHAR(100),
    disability_status VARCHAR(50) DEFAULT 'none',
    disability_details TEXT,
    passport_photo_url VARCHAR(500),
    cv_url VARCHAR(500),
    national_id_url VARCHAR(500),
    certificates_urls JSONB DEFAULT '[]',
    work_experience TEXT,
    education TEXT,
    skills TEXT,
    languages_spoken TEXT,
    digital_signature_url VARCHAR(500),
    hr_notes TEXT,
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    submitted_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '7 days')
);

-- Stock counts
CREATE TABLE stock_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    counted_by UUID,
    count_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'in_progress',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE stock_count_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    stock_count_id UUID REFERENCES stock_counts(id),
    product_id UUID,
    product_name VARCHAR(255) NOT NULL,
    system_quantity INT NOT NULL,
    actual_quantity INT,
    variance INT,
    variance_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tenant audit log (immutable)
CREATE TABLE tenant_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    action VARCHAR(100) NOT NULL,
    target_type VARCHAR(50),
    target_id UUID,
    old_value JSONB,
    new_value JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Protect tenant audit log from modification
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is immutable - modifications not allowed';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tenant_audit_log_immutable
BEFORE UPDATE OR DELETE ON tenant_audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- Reset search_path
SET search_path TO public;
