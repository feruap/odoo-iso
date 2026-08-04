# Ajusta la hoja maestra del BoM de Chagas IgG (DMCHA01) a hoja corta 0.3 cm
l = env['mrp.bom.line'].browse(384)
print("Antes:", l.product_id.default_code, l.product_qty, "cm | BoM de:", l.bom_id.product_tmpl_id.default_code)
if l.product_id.default_code == 'SPHMC05':
    l.sudo().write({'product_qty': 0.3})
    print("Después:", l.product_qty, "cm")
else:
    print("OJO: la línea 384 no es SPHMC05, no se cambió")
env.cr.commit()
