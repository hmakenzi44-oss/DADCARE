-- ============================================================
-- DADCARE Public Schema Bootstrap
-- Run once: psql $DATABASE_URL -f public_schema.sql
-- ============================================================

-- Shared immutable audit trigger (used by all schemas)
CREATE OR REPLACE FUNCTION prevent_audit_modification()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'Audit log is immutable - modifications not allowed';
END;
$$ LANGUAGE plpgsql;

-- Protect public audit_log
DROP TRIGGER IF EXISTS audit_log_immutable ON audit_log;
CREATE TRIGGER audit_log_immutable
BEFORE UPDATE OR DELETE ON audit_log
FOR EACH ROW EXECUTE FUNCTION prevent_audit_modification();

-- Seed mini-apps
INSERT INTO mini_apps (id, name, slug, icon, version, is_active, is_coming_soon, display_order)
VALUES
  (gen_random_uuid(), 'Shop',        'shop',        '🛒', '1.0.0', true,  false, 1),
  (gen_random_uuid(), 'Marketplace', 'marketplace', '🌐', '1.0.0', true,  false, 2),
  (gen_random_uuid(), 'School',      'school',      '🏫', '1.0.0', false, true,  3),
  (gen_random_uuid(), 'Pharmacy',    'pharmacy',    '💊', '1.0.0', false, true,  4),
  (gen_random_uuid(), 'Gym',         'gym',         '🏋', '1.0.0', false, true,  5)
ON CONFLICT (slug) DO NOTHING;
