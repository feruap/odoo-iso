"""
Carga 7 lotes con entrada 03/03/2025, capturados por Karla Fernanda Palma Ramos.
Fecha de registro: 2026-07-28.
"""
loc = env['stock.location'].search([('complete_name','ilike','AMP/Existencias')], limit=1)
print(f"Ubicación: {loc.complete_name}\n")

def get_product(codigo):
    tmpl = env['product.template'].with_context(active_test=False).search([
        ('default_code', '=', codigo)], limit=1)
    return tmpl.product_variant_ids[:1]

def get_or_create_factory(prov_lot):
    f = env['amunet.lot.factory'].search([('name', '=', prov_lot)], limit=1)
    if not f:
        f = env['amunet.lot.factory'].create({'name': prov_lot})
    return f

def crear_lote(codigo, lot_name, prov_lot, expiry_str, qty):
    prod = get_product(codigo)
    if not prod:
        print(f"  ⚠️  {codigo} no encontrado")
        return
    existe = env['stock.lot'].search([
        ('name', '=', lot_name), ('product_id', '=', prod.id)], limit=1)
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

lotes = [
    # (codigo,    lot_name,         prov_lot,          expiry,               qty)
    ('MPREC89', 'REC89032501', '108750-13-6',    '2030-03-03 00:00:00',   10),  # Calceína
    ('MPREC66', 'REC66032502', '215902',          '2030-03-03 00:00:00',   25),  # Acetato de plomo (2do lote)
    ('MPREC74', 'REC74032501', '05507JD',         '2030-03-03 00:00:00',   90),  # Ácido nitriloacético
    ('MPREC17', 'REC17032502', '6697.102119A',    '2030-03-03 00:00:00',   15),  # Azul brillante (2do lote)
    ('MPREC31', 'REC31032501', 'RA102301',        '2029-02-01 00:00:00',    5),  # Fosfato sodio dibásico
    ('MPREC79', 'REC79032501', '300523',          '2028-05-02 00:00:00',  250),  # Hidróxido de amonio
    ('MPREC80', 'REC80032501', 'SIN-LOTE',        '2030-03-03 00:00:00',  696),  # SDS (sin lote proveedor)
]

print("Creando lotes:\n")
for row in lotes:
    crear_lote(*row)

env.cr.commit()
print("\n✓ Todos los lotes procesados")
