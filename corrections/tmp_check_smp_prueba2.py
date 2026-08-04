"""Busca los SMP de prueba directamente en el modelo."""
try:
    for nombre in ['SMP/26/00159', 'SMP/26/00160']:
        smp = env['amunet.solicitud.material'].search([('name','=',nombre)], limit=1)
        if not smp:
            print(f"{nombre}: no encontrado en amunet.solicitud.material")
            continue
        print(f"\n{nombre} | estado={smp.state} | area={smp.area_id.name if smp.area_id else '-'}")
        for line in smp.line_ids:
            print(f"  [{line.product_id.default_code}] {line.product_id.name} | qty={line.product_qty} | lote={line.lot_id.name if line.lot_id else 'sin lote'}")
except Exception as e:
    print(f"Error: {e}")

# También buscar pickings con SMP en el nombre
picks = env['stock.picking'].search([
    ('origin','in',['SMP/26/00159','SMP/26/00160'])
])
print(f"\nPickings ligados: {len(picks)}")
for p in picks:
    print(f"  {p.name} | origen={p.origin} | estado={p.state}")
    for mv in p.move_ids:
        print(f"    [{mv.product_id.default_code}] {mv.product_id.name} | qty={mv.product_uom_qty} | hecho={mv.quantity_done} | estado={mv.state}")
