-- Script para corregir caracteres corruptos en Odoo19
-- Campos VARCHAR (no JSONB)

-- ============================================
-- 1. RES_PARTNER - Nombres
-- ============================================
SELECT id, name FROM res_partner WHERE name ~ E'\\?\\?' LIMIT 10;
