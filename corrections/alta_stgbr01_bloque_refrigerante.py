# -*- coding: utf-8 -*-
# Alta de producto nuevo pedido por Fernando 2026-07-14:
#   nombre: "Bloque refrigerante"  clave: STGBR01
# ST = Semiterminado. Se modela en su gemelo STGEL01 "Gel refrigerante"
# (mismo tipo de insumo de cadena de frio): consu, almacenable, lote, sin
# caducidad, compra si / venta no, UdM Units, categoria "Gel refrigerante".
Pt = env['product.template']
if Pt.search([('default_code', '=', 'STGBR01')], limit=1):
    print("STGBR01 YA existe, no se crea de nuevo")
else:
    g = Pt.search([('default_code', '=', 'STGEL01')], limit=1)
    if not g:
        raise Exception("No existe el gemelo STGEL01 para modelar el alta")
    p = Pt.create({
        'name': 'Bloque refrigerante',
        'default_code': 'STGBR01',
        'categ_id': g.categ_id.id,
        'type': g.type,
        'is_storable': g.is_storable,
        'tracking': g.tracking,
        'sale_ok': g.sale_ok,
        'purchase_ok': g.purchase_ok,
        'use_expiration_date': g.use_expiration_date,
        'uom_id': g.uom_id.id,
    })
    env.cr.commit()
    print("CREADO id=%s | %s | %s | categ=%s | tipo=%s storable=%s track=%s caduca=%s" % (
        p.id, p.default_code, p.name, p.categ_id.complete_name,
        p.type, p.is_storable, p.tracking, p.use_expiration_date))
print("LISTO")
