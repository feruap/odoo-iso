# MO 81 (0726/01/CAL) de 70 -> 93 piezas: se usa toda la hoja SPHMC55 (28 cm) que
# a 0.3 cm/pieza alcanza para 93. Escala los componentes por-pieza a 93.
# Autorizado por Fernando 2026-07-29.
mo=env['mrp.production'].sudo().browse(81)
NEW=93.0
TARGET={'SPHMC55':28.0,'MPCAR55':NEW,'STBPR03':NEW,'STDSC01':NEW,'STGOT05':NEW,'MPBOL01':NEW}
mo.write({'product_qty':NEW})
for m in mo.move_raw_ids:
    c=m.product_id.default_code
    if c not in TARGET: continue
    t=TARGET[c]
    m._do_unreserve()
    m.product_uom_qty=t
    m._action_assign()
    resv=sum(m.move_line_ids.mapped('quantity'))
    if 'amunet_qty_supplied' in m._fields: m.amunet_qty_supplied=resv
for f in mo.move_finished_ids.filtered(lambda x: x.product_id==mo.product_id):
    f.product_uom_qty=NEW
env.cr.commit()
print('MO 81 product_qty:', mo.product_qty)
for m in mo.move_raw_ids.sorted(lambda x:x.product_id.default_code):
    print('  %-8s demanda=%s reservado=%s supplied=%s'%(m.product_id.default_code, m.product_uom_qty, sum(m.move_line_ids.mapped('quantity')), getattr(m,'amunet_qty_supplied','n/a')))
print('LISTO')
