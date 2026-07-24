# Valida el traslado interno AMP/STOR/00080 (Control de calidad -> AMP/Existencias,
# 55.50 u del lote HMC59072601, SPHMC59 Hoja Maestra NT-proBNP). El lote ya esta
# liberado; el traslado quedo pendiente por el bug de re-enrutado (ya corregido de
# raiz). Autorizado por Fernando 2026-07-22.
p = env['stock.picking'].sudo().search([('name', '=', 'AMP/STOR/00080')], limit=1)
assert p, 'no existe AMP/STOR/00080'
print('picking:', p.name, '| estado antes:', p.state)
lotes = set(p.move_line_ids.mapped('lot_id.name'))
print('lotes:', lotes)
assert lotes <= {'HMC59072601'}, 'ATENCION: el picking tiene otros lotes, abortar'

# asegurar cantidad hecha = reservada
for ml in p.move_line_ids:
    if not ml.quantity:
        ml.quantity = ml.reserved_uom_qty if hasattr(ml, 'reserved_uom_qty') else ml.quantity

res = p.with_context(skip_backorder=True, picking_label_report=False).button_validate()
if isinstance(res, dict):
    print('button_validate devolvio un wizard/accion:', res.get('res_model'))
env.cr.commit()
print('estado despues:', p.state)

# verificar existencias del lote
env.cr.execute("""
    SELECT sl.complete_name, sq.quantity
    FROM stock_quant sq JOIN stock_lot l ON l.id=sq.lot_id JOIN stock_location sl ON sl.id=sq.location_id
    WHERE l.name='HMC59072601' AND sq.quantity<>0 ORDER BY sl.complete_name
""")
print('existencias HMC59072601:')
for row in env.cr.fetchall():
    print('  ', row)
print('LISTO')
