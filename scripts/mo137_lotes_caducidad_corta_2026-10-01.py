# 0926/01/CCF (MO 137): sacar de la orden el material que caduca en menos de
# dos anios. Ese material NO lo eligio nadie: entro solo cuando la orden
# crecio de 3,600 a 3,750 (30-sep 22:47) y cuando se dio de baja el lote
# BTR122502 (1-oct 16:45). Odoo cubre la diferencia tomando por caducidad y
# parte el renglon en varios lotes.
#
# Criterio (Mery, 1-oct-2026): el insumo debe durar al menos 2 anios, porque
# el producto terminado lleva esa caducidad.
CAMBIOS = [
    ('STDSC01', 'DSC01032501', 'DSC01092601'),   # 31.01.28 -> 01.08.29
    ('STHIS01', 'HIS01122301', 'HIS01082601'),   # 31.05.28 -> 02.08.29
]
mo = env['mrp.production'].search([('name', '=', '0926/01/CCF')])
for clave, viejo, nuevo in CAMBIOS:
    lineas = mo.move_raw_ids.move_line_ids.filtered(
        lambda l: l.product_id.default_code == clave and l.lot_id.name == viejo)
    if not lineas:
        print(clave, ': ya no tiene', viejo); continue
    lote_nuevo = env['stock.lot'].search([
        ('name', '=', nuevo), ('product_id', '=', lineas[0].product_id.id)], limit=1)
    for l in lineas:
        cant = l.quantity
        l.sudo().with_context(amunet_supply_internal=True).write(
            {'lot_id': lote_nuevo.id})
        print('%-8s %s piezas: %s (%s) -> %s (%s)' % (
            clave, cant, viejo, l.lot_id.expiration_date.date() if False else '',
            nuevo, lote_nuevo.expiration_date.date()))
mo.message_post(body=(
    'Se sacaron de la orden dos lotes que caducan en menos de dos anios y se '
    'cambiaron por material con vida larga: los <b>522 desecantes</b> del '
    'DSC01032501 (31.01.28) pasan al DSC01092601 (01.08.29), y los <b>75 '
    'hisopos</b> del HIS01122301 (31.05.28, un lote de diciembre 2023) pasan al '
    'HIS01082601 (02.08.29). Ese material no lo habia elegido nadie: entro solo '
    'cuando la orden crecio de 3,600 a 3,750 piezas y el sistema cubrio la '
    'diferencia tomando por caducidad.<br/><br/>'
    '<b>Queda pendiente el buffer:</b> los 210 viales del BTR01032601 caducan el '
    '30.09.28 y no hay con que cambiarlos -- solo hay 121 libres con vida larga. '
    'Los 3,526 del BTR02092603 (17.03.29) siguen retenidos en Control de calidad '
    'con su analisis QC/2026/00512 sin arrancar.'))
env.cr.commit()

print()
print('=== como queda la orden ===')
for l in mo.move_raw_ids.move_line_ids.sorted(
        lambda x: (x.product_id.default_code or '', x.lot_id.name or '')):
    cad = l.lot_id.expiration_date
    corto = ''
    if cad:
        from datetime import timedelta
        corto = '  <-- menos de 2 anios' if cad < fields.Datetime.now() + timedelta(days=730) else ''
    print('   %-9s %-13s %-11s %9s%s' % (
        l.product_id.default_code, l.lot_id.name or '-',
        cad.date() if cad else 'sin caducidad', l.quantity, corto))
