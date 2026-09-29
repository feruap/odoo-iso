"""Genera el analisis de la hoja de Dengue del combo mosquito.

Autorizado por Mery el 29-sep-2026. Se le pidio a Calidad el 28-sep a las 00:32, lo
leyeron y no lo generaron; las 900 cm siguen detenidas en cuarentena y sin analisis
el combo terminado no se puede fabricar, porque su receta consume las CUATRO hojas.

    SPHMC86   HMC86092601   900 cm   QC/2026/00503  en proceso
    SPHMC87   HMC87092601   900 cm   QC/2026/00504  en proceso
    SPHMC88   HMC88092601   900 cm   QC/2026/00505  borrador
    SPHMC85   HMC85092601   900 cm   <-- este

SE COPIA EL PATRON DE SU HERMANA QC/2026/00503: misma recepcion de origen
(AMP/IN/00347, la del combo), misma unidad de muestreo y la misma cantidad a
muestrear. Las fechas de fabricacion y caducidad se toman del lote si las tiene, y si
no, de su hermana: las cuatro hojas vienen del MISMO combo, asi que comparten fechas.

QUEDA EN BORRADOR. Solo se crea el registro con sus parametros cargados; capturar los
resultados y liberar el lote es de Calidad, no nuestro.

Idempotente: si ya existe un analisis para ese lote, no crea otro.
"""
from markupsafe import Markup

Check = env['amunet.quality.check'].sudo()
Lot = env['stock.lot'].sudo()
Prod = env['product.product'].sudo()

prod = Prod.search([('default_code', '=', 'SPHMC85')], limit=1)
assert prod, 'no existe SPHMC85'
lote = Lot.search([('name', '=', 'HMC85092601'), ('product_id', '=', prod.id)], limit=1)
assert lote, 'no existe el lote HMC85092601 de SPHMC85'
assert prod.product_tmpl_id.qc_required, 'SPHMC85 tiene qc_required apagado'

ya = Check.search([('lot_id', '=', lote.id)])
if ya:
    print('[ya] el lote %s ya tiene analisis: %s' % (
        lote.name, ', '.join('%s (%s)' % (c.name, c.state) for c in ya)))
else:
    hermana = Check.search([('name', '=', 'QC/2026/00503')], limit=1)
    vals = {
        'product_id': prod.id,
        'lot_id': lote.id,
        'lot_amunet': lote.name,
        'sampling_uom_id': prod.uom_id.id,
    }
    if hermana:
        vals['sampling_uom_id'] = hermana.sampling_uom_id.id or prod.uom_id.id
        if hermana.qty_sampling:
            vals['qty_sampling'] = hermana.qty_sampling
        if hermana.picking_id:
            vals['picking_id'] = hermana.picking_id.id
        if hermana.partner_id:
            vals['partner_id'] = hermana.partner_id.id
    # las fechas: del lote si las trae, si no las de la hermana (mismo combo)
    for campo in ('expiration_date', 'manufacturing_date'):
        valor = getattr(lote, campo, False) or (getattr(hermana, campo, False) if hermana else False)
        if valor:
            vals[campo] = valor
    qc = Check.create(vals)
    qc._load_product_parameters()
    print('[ok] %s creado para %s lote %s' % (qc.name, prod.default_code, lote.name))
    print('     renglones cargados: %s' % sum(len(tl.detail_line_ids) for tl in qc.test_line_ids))
    if not qc.test_line_ids:
        print('     OJO: nacio SIN parametros, revisar la configuracion del producto')
    qc.message_post(body=Markup(
        'Analisis generado por Desarrollo el 29-sep-2026, autorizado por Mery.<br/><br/>'
        'Son las <b>900 cm de la hoja de Dengue</b> que llegaron en el combo mosquito '
        'el 17-sep: en la recepcion AMP/IN/00347 se pidio el combo de TRES hojas '
        '(I204-4025) y el proveedor mando el de CUATRO (I163-4045), que incluye esta. '
        'Se registro el que se pidio, asi que la conversion CONV/00010 genero solo tres '
        'hojas y esta quedo sin dar de alta hasta el 28-sep.<br/><br/>'
        'Mery acepto el material como llego. <b>No es material de sobra:</b> la receta '
        'del Combo Mosquito terminado (DMDCZ01) consume las cuatro hojas, 0.40 cm de '
        'cada una, asi que sin esta no se fabrica el producto.<br/><br/>'
        'Se copio el patron de su hermana QC/2026/00503: misma recepcion de origen y '
        'misma cantidad a muestrear. <b>Queda en borrador:</b> capturar los resultados y '
        'liberar el lote es de Calidad.'))

print('\n=== las cuatro hojas del combo ===')
for clave, nombre_lote in (('SPHMC85', 'HMC85092601'), ('SPHMC86', 'HMC86092601'),
                           ('SPHMC87', 'HMC87092601'), ('SPHMC88', 'HMC88092601')):
    p = Prod.search([('default_code', '=', clave)], limit=1)
    l = Lot.search([('name', '=', nombre_lote), ('product_id', '=', p.id)], limit=1)
    cs = Check.search([('lot_id', '=', l.id)]) if l else Check.browse()
    ren = sum(sum(len(tl.detail_line_ids) for tl in c.test_line_ids) for c in cs)
    print('   %-9s %-13s %s  %s renglones' % (
        clave, nombre_lote,
        ', '.join('%s (%s)' % (c.name, c.state) for c in cs) or 'SIN ANALISIS', ren))
env.cr.commit()
