"""
Limpieza de ir.rules de stock.location generadas dinámicamente por amunet_warehouse_access.

Estas reglas bloquean la lectura de ubicaciones en vistas de forecast/ajuste de inventario.
El módulo ya fue corregido para no generarlas. Este script elimina las existentes en DB.

Uso:
    docker exec odoo-staging bash -c \
      'odoo shell -c /etc/odoo/odoo.conf -d amunet_prod --no-http' < fix_stock_location_irules.py
"""

import logging
_logger = logging.getLogger(__name__)

IrRule = env['ir.rule']
AmunetRule = env['amunet.warehouse.access.rule']

# Buscar reglas de amunet_warehouse_access que aplican sobre stock.location
location_rules = AmunetRule.search([('model_name', '=', 'stock.location')])

if not location_rules:
    print("No se encontraron reglas de stock.location. Nada que limpiar.")
else:
    print(f"Encontradas {len(location_rules)} reglas de stock.location para eliminar:")
    for rule in location_rules:
        print(f"  - ID {rule.id}: {rule.name} (ir.rule ID: {rule.rule_id.id if rule.rule_id else 'N/A'})")

    location_rules.sudo().unlink()
    env.cr.commit()
    print("Reglas eliminadas correctamente.")
