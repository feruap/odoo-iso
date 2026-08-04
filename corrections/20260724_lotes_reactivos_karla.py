"""
Carga 13 lotes históricos de reactivos capturados por Karla Fernanda Palma Ramos.
Fecha de registro: 2026-07-24.
Formato de nombre: REC{nn}{MM}{YY}{seq} usando mes/año de entrada del material.
"""

# Ubicación: AMP/Existencias
loc = env['stock.location'].search([
    ('complete_name', 'ilike', 'AMP/Existencias')
], limit=1)
if not loc:
    loc = env['stock.location'].search([
        ('name', 'ilike', 'Existencias'), ('usage', '=', 'internal')
    ], limit=1)
print(f"Ubicación destino: {loc.complete_name} (id={loc.id})\n")

def get_product(codigo):
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', codigo)
    ], limit=1)
    return tmpl.product_variant_ids[:1]

def get_or_create_factory(prov_lot):
    f = env['amunet.lot.factory'].search([('name', '=', prov_lot)], limit=1)
    if not f:
        f = env['amunet.lot.factory'].create({'name': prov_lot})
    return f

def crear_lote(codigo, lot_name, prov_lot, expiry_str, qty):
    prod = get_product(codigo)
    if not prod:
        print(f"  ⚠️  {codigo} no encontrado, omitido")
        return
    existe = env['stock.lot'].search([
        ('name', '=', lot_name), ('product_id', '=', prod.id)
    ], limit=1)
    if existe:
        print(f"  ⚠️  {lot_name} ya existe, omitido")
        return
    factory = get_or_create_factory(prov_lot)
    lote = env['stock.lot'].create({
        'name': lot_name,
        'product_id': prod.id,
        'company_id': 1,
        'factory_lot_id': factory.id,
        'expiration_date': expiry_str,
    })
    env['stock.quant']._update_available_quantity(
        product_id=prod,
        location_id=loc,
        quantity=qty,
        lot_id=lote,
    )
    print(f"  ✅ {lot_name} | Prov: {prov_lot} | Cad: {expiry_str} | Cant: {qty}")

# ── Corregir caducidad de MPREC37 existente ─────────────────────────────────
prod37 = get_product('MPREC37')
lote37 = env['stock.lot'].search([
    ('name', '=', 'REC37032301'), ('product_id', '=', prod37.id)
], limit=1)
if lote37:
    lote37.sudo().write({'expiration_date': '2027-08-01 00:00:00'})
    print("✅ MPREC37 (HCl) — caducidad corregida a 2027-08-01")
    print(f"   Lote: {lote37.name} | Prov: {lote37.factory_lot_id.name}\n")

# ── Crear lotes ──────────────────────────────────────────────────────────────
lotes = [
    # (codigo,    lot_name,         prov_lot,           expiry,              qty)
    ('MPREC04', 'REC04082301', '020151217',       '2028-08-24 00:00:00', 3000),  # Tris HCl, 3 kg → g
    ('MPREC46', 'REC46082301', '260123',          '2028-01-01 00:00:00',   96),  # Cloruro Férrico lote 1
    ('MPREC46', 'REC46082201', '100921',          '2026-09-01 00:00:00',   96),  # Cloruro Férrico lote 2
    ('MPREC48', 'REC48082201', '27.08.22',        '2027-08-01 00:00:00',   26),  # Molibdato de sodio
    ('MPREC12', 'REC12062301', '260422',          '2027-04-01 00:00:00',  400),  # Tween 20
    ('MPREC50', 'REC50082101', '0091593',         '2027-09-11 00:00:00',  350),  # Agar dextrosa y papa
    ('MPREC51', 'REC51062301', '002367',          '2028-06-12 00:00:00',  170),  # Agarosa
    ('MPREC61', 'REC61032301', 'SLBX5528',        '2028-03-29 00:00:00',  150),  # Glicina (nuevo lote)
    ('MPREC19', 'REC19072101', '310320',          '2027-05-01 00:00:00',  250),  # Ácido fosfórico
    ('MPREC52', 'REC52082301', '120823',          '2028-08-01 00:00:00',  250),  # Etilenglicol
    ('MPREC53', 'REC53022101', 'M7128670XA',      '2027-02-28 00:00:00',  400),  # Imidazol
    ('MPREC55', 'REC55062501', 'LAA5SC-25D-069L', '2030-06-12 00:00:00',  500),  # Colorante amarillo
]

print("Creando lotes:\n")
for row in lotes:
    crear_lote(*row)

env.cr.commit()
print("\n✓ Todos los lotes procesados")
