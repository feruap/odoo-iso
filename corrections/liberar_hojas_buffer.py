# -*- coding: utf-8 -*-
# Liberacion de lote reflejada en sistema: Calidad YA liberó estos lotes EN PAPEL,
# pero el modulo de Calidad aun no permite liberar en sistema. Fernando autoriza
# (2026-07-16) registrar la liberacion. Solo HOJAS MAESTRAS (SPHMC75/76) y el
# BUFFER/vial (STBPR01). El cartucho MPCAC08 NO se libera.
# Se pone amunet_lot_release_state='released' (igual que _action_release_lot, que
# solo cambia el estado; no mueve stock). Se documenta en las notas y el chatter.
from odoo import fields

Lot = env['stock.lot'].sudo()
Prod = env['product.product']
diana = env['res.users'].search([('login', '=', 's.controldecalidad@amunet.com.mx')], limit=1)
nota = ('Liberado EN PAPEL por Calidad; registrado en sistema por Desarrollo '
        'porque el modulo de Calidad aun no permite liberar en sistema. '
        'Autorizado por Fernando 2026-07-16.')

for code, lname in [('SPHMC75', 'HMC75072601'),
                    ('SPHMC76', 'HMC76072601'),
                    ('STBPR01', 'BPR01072601')]:
    prod = Prod.search([('default_code', '=', code)], limit=1)
    lot = Lot.search([('product_id', '=', prod.id), ('name', '=', lname)], limit=1)
    if not lot:
        print('SIN lote:', code, lname); continue
    if lot.amunet_lot_release_state == 'released':
        print('ya liberado:', code, lname); continue
    lot.with_context(skip_lot_release_lock=True).write({
        'amunet_lot_release_state': 'released',
        'amunet_lot_released_by_id': (diana.id if diana else env.user.id),
        'amunet_lot_released_date': fields.Datetime.now(),
        'amunet_lot_release_notes': nota,
    })
    try:
        lot.message_post(body=nota)
    except Exception:
        pass
    print('LIBERADO:', code, lname, '->', lot.amunet_lot_release_state,
          '| por:', lot.amunet_lot_released_by_id.name)
env.cr.commit()
