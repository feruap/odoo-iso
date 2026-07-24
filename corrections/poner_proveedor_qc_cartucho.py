# Registra el proveedor faltante en el analisis 005170726-01 (QC 681, cartucho
# MPCAC08 lote CAC08072601 / DOA-455). Quedo vacio porque la recepcion
# AMP/IN/00190 se creo sin proveedor. Proveedor confirmado por Fernando:
# Cangzhou ShengFeng Plastic Product. Autorizado 2026-07-17.
QC = env['amunet.quality.check'].sudo()
qc = QC.search([('analysis_number', '=', '005170726-01')], limit=1)
assert qc, 'no se encontro el analisis 005170726-01'
partner = env['res.partner'].search([('name', 'ilike', 'Cangzhou ShengFeng')], limit=1)
assert partner, 'no se encontro el proveedor Cangzhou ShengFeng'
razon = ('Registro del proveedor faltante en el analisis: la recepcion '
         'AMP/IN/00190 se creo sin proveedor y el QC lo heredo vacio. '
         'Autorizado por Fernando 2026-07-17.')
antes = qc.partner_id.name
qc.write({'partner_id': partner.id, 'change_reason': razon})
print('QC %s (%s): proveedor %s -> %s' % (qc.id, qc.analysis_number, antes or '(vacio)', qc.partner_id.name))
env.cr.commit()
