# Ajuste de la caducidad en el ANALISIS (QC) para que coincida con la del lote,
# corregida antes en la recepcion. El QC guarda su propia caducidad y no se
# actualizo. Cartucho CAC08072601 -> 2030-07-01; vial BPR01072601 -> 2028-05-01.
# Autorizado por Fernando 2026-07-17.
from datetime import datetime
QC = env['amunet.quality.check'].sudo()
razon = ('Ajuste de caducidad del analisis para coincidir con la del lote '
         '(corregida en recepcion). Autorizado por Fernando 2026-07-17.')
fixes = [('CAC08072601', datetime(2030, 7, 1)), ('BPR01072601', datetime(2028, 5, 1))]
for lname, exp in fixes:
    qc = QC.search([('lot_id.name', '=', lname), ('active', '=', True)], limit=1)
    if not qc:
        print('SIN QC:', lname); continue
    antes = qc.expiration_date
    qc.write({'expiration_date': exp, 'change_reason': razon})
    print('%s QC %s: %s -> %s' % (lname, qc.id, antes, qc.expiration_date))
env.cr.commit()
