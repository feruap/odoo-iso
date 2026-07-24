# MO 69 (0726/01/HBC): re-corre preflight, verifica que el unico bloqueo sea el
# vial STBHB01 (en fabricacion), acepta el preflight como EXCEPCION DOCUMENTADA
# y confirma la orden. Instructivo MIMAN01 ya salio del BOM.
# Autorizado por Fernando 2026-07-20.
from odoo import fields
mo = env['mrp.production'].browse(69)
pf = mo.pilot_preflight_ids[:1]
assert pf, 'MO 69 sin preflight'
pf.action_run_checks()
blocks = pf.line_ids.filtered(lambda l: l.status == 'block')
otros = blocks.filtered(lambda l: 'STBHB01' not in (l.detail or ''))
assert not otros, 'Hay bloqueos distintos a STBHB01: %s' % otros.mapped('detail')
pf.write({'state': 'accepted', 'accepted_by_id': env.user.id, 'accepted_date': fields.Datetime.now()})
pf.message_post(body=(
    'Preflight ACEPTADO con excepcion documentada. Unico faltante: vial '
    'STBHB01 (1156 de 3650), actualmente EN FABRICACION. Instructivo MIMAN01 '
    'retirado del BOM por Direccion. Autorizado por Fernando 2026-07-20.'))
print('Preflight', pf.id, '->', pf.state, '| MO preflight_accepted:', mo.amunet_preflight_accepted)
env.cr.commit()
