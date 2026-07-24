"""
Carga lotes de los batches 2 y 3 capturados por Karla Fernanda Palma Ramos.
Todos con fecha de entrada 03/03/2025. Fecha de registro: 2026-07-24.
"""
loc = env['stock.location'].search([('complete_name','ilike','AMP/Existencias')], limit=1)
print(f"Ubicación: {loc.complete_name}\n")

def get_product(codigo):
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code','=',codigo)], limit=1)
    return tmpl.product_variant_ids[:1]

def get_or_create_factory(prov_lot):
    f = env['amunet.lot.factory'].search([('name','=',prov_lot)], limit=1)
    if not f:
        f = env['amunet.lot.factory'].create({'name': prov_lot})
    return f

def crear_lote(codigo, lot_name, prov_lot, expiry_str, qty):
    prod = get_product(codigo)
    if not prod:
        print(f"  ⚠️  {codigo} no encontrado")
        return
    existe = env['stock.lot'].search([
        ('name','=',lot_name), ('product_id','=',prod.id)], limit=1)
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
        product_id=prod, location_id=loc, quantity=qty, lot_id=lote)
    print(f"  ✅ {lot_name} | Prov: {prov_lot} | Cad: {expiry_str[:10]} | Cant: {qty}")

# ── BATCH 2 (entrada 03/03/2025) ────────────────────────────────────────────
print("=== BATCH 2 ===")
lotes_b2 = [
    ('MPREC56', 'REC56032501', '270124',     '2029-02-01 00:00:00',  498),   # Cloruro de calcio
    ('MPREC65', 'REC65032501', '161022',     '2027-01-01 00:00:00',  250),   # Sulfato de magnesio
    ('MPREC66', 'REC66032501', '140523',     '2028-04-01 00:00:00',   94),   # Acetato de plomo
    ('MPREC61', 'REC61032501', '190721',     '2027-08-01 00:00:00',   80),   # Glicina (ác. aminoacético)
    ('MPREC09', 'REC09032501', '311222',     '2027-11-01 00:00:00',  500),   # Hidróxido de sodio
]
for row in lotes_b2:
    crear_lote(*row)

# ── BATCH 3 (entrada 03/03/2025) ────────────────────────────────────────────
print("\n=== BATCH 3 ===")
lotes_b3 = [
    ('MPREC21', 'REC21032501', 'M1254',        '2030-03-03 00:00:00',   10),  # MOPS
    ('MPREC20', 'REC20032501', 'H3375',        '2030-03-03 00:00:00',   15),  # HEPES
    ('MPREC32', 'REC32032501', '7558-80-7',    '2030-03-03 00:00:00',  500),  # Fosfato sodio monobásico 1
    ('MPREC67', 'REC67032501', 'N10G017',      '2030-03-03 00:00:00',  400),  # Peptona de caseína
    ('MPREC63', 'REC63032501', '1B70102',      '2030-03-03 00:00:00',  100),  # N,N-Metilenbis(Acrilamida)
    ('MPREC70', 'REC70032501', '090223',       '2028-01-01 00:00:00', 1000),  # Ácido sulfúrico
    ('MPREC17', 'REC17032501', 'MKBS9408V',    '2027-07-06 00:00:00',    5),  # Azul brillante Coomassie
    ('MPREC32', 'REC32032502', 'S186',         '2030-03-03 00:00:00', 2000),  # Fosfato sodio monobásico 2
    ('MPREC73', 'REC73032501', '131903',       '2030-03-03 00:00:00',   25),  # Ortosilicato de tetraetilo
]
for row in lotes_b3:
    crear_lote(*row)

env.cr.commit()
print("\n✓ Todos los lotes procesados")
