# -*- coding: utf-8 -*-
# Migracion Almacen MP -> produccion: Cristaleria (16) + Esponja (1).
# Origen: cargado en staging por el agente 'almacenmp'. Autorizado por Fernando
# el 2026-07-09. Decision: SIN control de caducidad (la cristaleria no caduca;
# la caducidad de hoy en staging era un artefacto de use_expiration_date).
# Idempotente: si una clave/lote/categoria ya existe, no la duplica.

LOC_ID = 5  # AMP/Existencias en amunet_prod
UOM_UNITS = 1  # Units

# (clave, nombre, categoria_key, sale_ok)
PRODUCTOS = [
    ("COFDU01", "Frasco DURAN 100 ml",          "crist", False),
    ("COFDU02", "Frasco DURAN 250 ml",          "crist", False),
    ("COFDU03", "Frasco DURAN 1 L",             "crist", False),
    ("COFDU04", "Frasco DURAN 2 L",             "crist", False),
    ("COMAF01", "Matraz aforado 10 ml",         "crist", False),
    ("COMAF02", "Matraz aforado 500 ml",        "crist", False),
    ("COMEL01", "Matraz Erlenmeyer 500 ml",     "crist", False),
    ("COMEL02", "Matraz Erlenmeyer 2 L",        "crist", False),
    ("COPRB01", "Probeta 25 ml",                "crist", False),
    ("COPRB02", "Probeta 100 ml",               "crist", False),
    ("COPRB03", "Probeta 500 ml",               "crist", False),
    ("COPRB04", "Probeta 250 ml",               "crist", False),
    ("COVPR01", "Vaso de precipitados 250 ml",  "crist", False),
    ("COVPR02", "Vaso de precipitados 600 ml",  "crist", False),
    ("COVPR03", "Vaso de precipitados 1 L",     "crist", False),
    ("COVPR04", "Vaso de precipitados 2 L",     "crist", False),
    ("STESP01", "Esponja para toma de muestra", "sumin", True),
]

# clave -> [(lote, cantidad), ...]
LOTES = {
    "COFDU01": [("FDU01072601", 2)],
    "COFDU02": [("FDU02072601", 3)],
    "COFDU03": [("FDU03072601", 5), ("FDU03122401", 1)],
    "COFDU04": [("FDU04122401", 1)],
    "COMAF01": [("MAF01122401", 1)],
    "COMAF02": [("MAF02122401", 1)],
    "COMEL01": [("MEL01072601", 4), ("MEL01122401", 2)],
    "COMEL02": [("MEL02122401", 2)],
    "COPRB01": [("PRB01072601", 1)],
    "COPRB02": [("PRB02072601", 1)],
    "COPRB03": [("PRB03072601", 1)],
    "COPRB04": [("PRB04072601", 1)],
    "COVPR01": [("VPR01122401", 1)],
    "COVPR02": [("VPR02072601", 2), ("VPR02122401", 1)],
    "COVPR03": [("VPR03122401", 1)],
    "COVPR04": [("VPR04122401", 1)],
    "STESP01": [("ESP01072601", 12)],
}

Categ = env['product.category']
Tmpl = env['product.template']
Prod = env['product.product']
Lot = env['stock.lot']
Quant = env['stock.quant']

# 1) Categorias
crist = Categ.search([('complete_name', '=', 'Consumible / Cristalería')], limit=1)
if not crist:
    parent = Categ.search([('complete_name', '=', 'Consumible')], limit=1)
    if not parent:
        raise Exception("No existe la categoria padre 'Consumible' en prod")
    crist = Categ.create({'name': 'Cristalería', 'parent_id': parent.id})
    print("  [CATEG] creada 'Consumible / Cristalería' id=%s" % crist.id)
else:
    print("  [CATEG] ya existia 'Consumible / Cristalería' id=%s" % crist.id)

sumin = Categ.search([('complete_name', '=', 'Semiterminado / Suministros')], limit=1)
if not sumin:
    raise Exception("No existe 'Semiterminado / Suministros' en prod")
print("  [CATEG] 'Semiterminado / Suministros' id=%s" % sumin.id)

CATEG_MAP = {'crist': crist.id, 'sumin': sumin.id}

# 2) Productos
n_prod = 0
for clave, nombre, ck, sale_ok in PRODUCTOS:
    existe = Tmpl.search([('default_code', '=', clave)], limit=1)
    if existe:
        print("  [PROD] ya existia %s (%s)" % (clave, nombre))
        continue
    Tmpl.create({
        'name': nombre,
        'default_code': clave,
        'type': 'consu',
        'is_storable': True,
        'tracking': 'lot',
        'uom_id': UOM_UNITS,
        'categ_id': CATEG_MAP[ck],
        'sale_ok': sale_ok,
        'purchase_ok': True,
        'use_expiration_date': False,
    })
    n_prod += 1
    print("  [PROD] creado %s (%s)" % (clave, nombre))

# 3) Lotes + 4) Existencias (ajuste de inventario auditable)
n_lot = 0
n_adj = 0
for clave, lotes in LOTES.items():
    variant = Prod.search([('default_code', '=', clave)], limit=1)
    if not variant:
        print("  [WARN] sin variante para %s, salto lotes" % clave)
        continue
    for lote_name, qty in lotes:
        lot = Lot.search([('name', '=', lote_name),
                          ('product_id', '=', variant.id)], limit=1)
        if not lot:
            lot = Lot.create({
                'name': lote_name,
                'product_id': variant.id,
                'company_id': env.company.id,
            })
            n_lot += 1
            print("  [LOTE] creado %s para %s" % (lote_name, clave))
        # Existencia actual de este lote en AMP/Existencias
        actual = sum(Quant.search([
            ('product_id', '=', variant.id),
            ('lot_id', '=', lot.id),
            ('location_id', '=', LOC_ID),
        ]).mapped('quantity'))
        if abs(actual - qty) < 0.0001:
            print("  [EXIST] %s/%s ya tiene %s, ok" % (clave, lote_name, qty))
            continue
        q = Quant.with_context(inventory_mode=True).create({
            'product_id': variant.id,
            'location_id': LOC_ID,
            'lot_id': lot.id,
            'inventory_quantity': qty,
        })
        q.action_apply_inventory()
        n_adj += 1
        print("  [EXIST] %s/%s ajustado a %s (antes %s)" % (clave, lote_name, qty, actual))

env.cr.commit()
print("RESUMEN: productos_nuevos=%s lotes_nuevos=%s ajustes_inventario=%s" % (n_prod, n_lot, n_adj))
