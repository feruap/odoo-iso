# Renombra la MO 70 (Dimero D) al folio codificado 0726/01/DMD y sube el
# consecutivo. La orden se creo antes de la secuencia. Autorizado Fernando 2026-07-21.
mo = env['mrp.production'].browse(70)
assert mo.exists() and mo.product_id.default_code == 'DMDMD01' and mo.state == 'draft', 'MO inesperada'
old = mo.name
mo.sudo().write({'name': '0726/01/DMD'})
seq = env['ir.sequence'].search([('suffix', '=', '/DMD')], limit=1)
if seq and seq.number_next < 2:
    seq.number_next = 2
env.cr.commit()
print('Folio:', old, '->', mo.name, '| secuencia next:', seq.number_next if seq else '?')
