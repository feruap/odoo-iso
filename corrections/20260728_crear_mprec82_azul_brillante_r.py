"""
Corrección Azul Brillante — separación G-250 y R.

Situación encontrada en staging:
  MPREC17 tenía dos lotes mezclados de distintos compuestos:
  - REC17032501 (prov. MKBS9408V)   → Azul Brillante R    (producto diferente)
  - REC17032502 (prov. 6697.102119A) → Azul Brillante G-250 (el correcto para MPREC17)

Acciones:
  1. Crear MPREC82 "Azul Brillante R" con su secuencia.
  2. Mover el lote REC17032501 (MKBS9408V) a MPREC82, renombrarlo REC82032501.
  3. Renombrar REC17032502 → REC17032501 (queda como único lote de MPREC17).

Autorizado por: Karla Fernanda Palma Ramos (almacen.mp@amunet.com.mx)
Fecha: 2026-07-28
"""

loc = env['stock.location'].search([('complete_name', 'ilike', 'AMP/Existencias')], limit=1)
categ = env['product.category'].browse(18)   # Materia prima / Reactivo
uom_g = env['uom.uom'].browse(14)

# ── 1. Crear MPREC82 Azul Brillante R ────────────────────────────────────────
existe82 = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPREC82')], limit=1)
if existe82:
    print(f"⚠️  MPREC82 ya existe: {existe82.name}")
    tmpl82 = existe82
else:
    tmpl82 = env['product.template'].with_context(amunet_alta_autorizada=True).sudo().create({
        'name': 'Azul Brillante R',
        'default_code': 'MPREC82',
        'categ_id': categ.id,
        'type': 'consu',
        'is_storable': True,
        'tracking': 'lot',
        'uom_id': uom_g.id,
        'purchase_ok': True,
        'sale_ok': False,
        'use_expiration_date': True,
        'amunet_requires_quarantine': False,
    })
    prefix_base = 'REC82'
    seq_code   = f'amunet.lot.{prefix_base}.{tmpl82.id}'
    seq_prefix = f'{prefix_base}%(month)s%(y)s'
    seq = env['ir.sequence'].sudo().search([('code', '=', seq_code)], limit=1)
    if not seq:
        seq = env['ir.sequence'].sudo().create({
            'name': 'Lote Amunet — Azul Brillante R',
            'code': seq_code,
            'prefix': seq_prefix,
            'padding': 2,
            'implementation': 'no_gap',
        })
    tmpl82.product_variant_ids[:1].sudo().write({'lot_sequence_id': seq.id})
    print(f"✅ MPREC82 creado — Azul Brillante R | seq: {seq_prefix}01")

prod82 = tmpl82.product_variant_ids[:1]

# ── 2. Mover lote REC17032501 (MKBS9408V) a MPREC82 ──────────────────────────
tmpl17 = env['product.template'].with_context(active_test=False).search([
    ('default_code', '=', 'MPREC17')], limit=1)
prod17 = tmpl17.product_variant_ids[:1]

lote_r = env['stock.lot'].search([
    ('name', '=', 'REC17032501'), ('product_id', '=', prod17.id)], limit=1)

if not lote_r:
    print("⚠️  Lote REC17032501 no encontrado en MPREC17")
else:
    # Ajustar quant: quitar de MPREC17
    qty_r = 0
    quant_r = env['stock.quant'].search([
        ('lot_id', '=', lote_r.id), ('location_id', '=', loc.id)], limit=1)
    if quant_r:
        qty_r = quant_r.quantity
        env['stock.quant']._update_available_quantity(prod17, loc, -qty_r, lot_id=lote_r)

    # Cambiar producto y nombre del lote
    lote_r.sudo().write({
        'product_id': prod82.id,
        'name': 'REC82032501',
    })

    # Agregar quant en MPREC82
    if qty_r:
        env['stock.quant']._update_available_quantity(prod82, loc, qty_r, lot_id=lote_r)

    print(f"✅ Lote movido: REC17032501 → REC82032501 (MPREC82) | qty={qty_r} g")

# ── 3. Renombrar REC17032502 → REC17032501 en MPREC17 ────────────────────────
lote_g = env['stock.lot'].search([
    ('name', '=', 'REC17032502'), ('product_id', '=', prod17.id)], limit=1)

if not lote_g:
    print("⚠️  Lote REC17032502 no encontrado en MPREC17")
else:
    lote_g.sudo().write({'name': 'REC17032501'})
    print(f"✅ Lote renombrado: REC17032502 → REC17032501 (MPREC17 G-250) | prov={lote_g.factory_lot_id.name}")

env.cr.commit()
print("\n✓ Listo — Azul Brillante G-250 (MPREC17) y R (MPREC82) separados correctamente")
