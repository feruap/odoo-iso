# -*- coding: utf-8 -*-
"""Ajusta los candados del tipo de operacion "Ingreso de produccion".

POR QUE HACE FALTA UN SCRIPT Y NO BASTA CON PROMOVER EL MODULO

El tipo de operacion se creo el 21-sep-2026, antes de que Mery definiera las
reglas el 22-sep. Su data.xml es `noupdate="1"`, asi que Odoo respeta el registro
que ya existe y NO reescribe los campos: promover amunet_production deja los
valores viejos tal cual.

Estado al 22-sep-2026:
    produccion   use_create_lots=True   create_backorder=ask     <- mal
    staging      use_create_lots=False  create_backorder=never   <- bien

LAS DOS REGLAS (Mery, 22-sep-2026)

  use_create_lots = False
      El lote viene de la orden de fabricacion. Si Almacen puede inventar uno al
      validar, se rompe la trazabilidad: quedarian dos lotes para el mismo
      material fabricado y ninguno amarrado a su orden.

  create_backorder = never
      O llego o no llego. Si Almacen recibe menos, corrige la cantidad y valida;
      sin pendiente fantasma arrastrandose.

Idempotente: si ya estan bien, no toca nada.

  docker cp fix_ingreso_produccion_candados.py odoo-production:/tmp/x.py
  docker exec odoo-production bash -c 'odoo shell -c /etc/odoo/odoo.conf \
    -d amunet_prod --no-http --db_host $HOST --db_port $PORT \
    --db_user $USER --db_password $PASSWORD < /tmp/x.py'
"""
ESPERADO = {
    'use_create_lots': False,
    'use_existing_lots': True,
    'create_backorder': 'never',
    'show_operations': False,
}

tipo = env.ref('amunet_production.picking_type_ingreso_produccion',
               raise_if_not_found=False)
if not tipo:
    print('   El tipo de operacion no existe todavia: corre primero el -u de '
          'amunet_production, que lo crea.')
else:
    print('   %s' % tipo.display_name)
    cambios = {}
    for campo, valor in ESPERADO.items():
        actual = tipo[campo]
        estado = 'ok' if actual == valor else 'SE CORRIGE -> %s' % valor
        print('        %-20s %-8s %s' % (campo, actual, estado))
        if actual != valor:
            cambios[campo] = valor
    if cambios:
        tipo.sudo().write(cambios)
        # stock.picking.type no lleva chatter, asi que el rastro va al log del
        # servidor y en el commit de este script.
        import logging
        logging.getLogger(__name__).info(
            'amunet_production: candados del ingreso de produccion ajustados: %s',
            ', '.join('%s=%s' % (k, v) for k, v in cambios.items()))
        env.flush_all()
        env.cr.commit()
        print('   CORREGIDOS: %s' % ', '.join(cambios))
    else:
        print('   Nada que corregir, ya estaba bien.')
