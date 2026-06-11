# Crear 16 productos Control Negativo — contraparte de los Control Positivo
# Solicitud de Karla (almacen.mp) — almacenables, unidades, rastreo por lote

cat_ctrl = env['product.category'].search([('complete_name', '=', 'Semiprocesado / Control')], limit=1)
if not cat_ctrl:
    print("ERROR: No se encontró la categoría 'Semiprocesado / Control'")
else:
    uom_units = env['uom.uom'].search([('name', '=', 'Units')], limit=1)
    if not uom_units:
        uom_units = env['uom.uom'].search([('name', '=', 'Unidades')], limit=1)

    productos = [
        ('Control Negativo SARS-CoV-2',                'SPCNL01'),
        ('Control Negativo Influenza A+B',              'SPCNL02'),
        ('Control Negativo Tuberculosis',               'SPCNL03'),
        ('Control Negativo VPH',                        'SPCNL04'),
        ('Control Negativo K-RAS',                      'SPCNL05'),
        ('Control Negativo P/anticuerpos VIH tipo 1',   'SPCNL06'),
        ('Control Negativo P/anticuerpos VIH tipo 2',   'SPCNL07'),
        ('Control Negativo Tuberculosis TB',            'SPCNL08'),
        ('Control Negativo Tuberculosis RIF/INH',       'SPCNL09'),
        ('Control Negativo Isolister-ADN',              'SPCNL10'),
        ('Control Negativo AUREUS-ADN',                 'SPCNL11'),
        ('Control Negativo CAMPY-ADN',                  'SPCNL12'),
        ('Control Negativo ENTERONET-ADN',              'SPCNL13'),
        ('Control Negativo SALMONET-ADN',               'SPCNL14'),
        ('Control Negativo EcoHem-ADN',                 'SPCNL15'),
        ('Control Negativo VIHLAMP-ADN',                'SPCNL16'),
    ]

    creados = 0
    for nombre, clave in productos:
        existe = env['product.template'].search([('default_code', '=', clave)], limit=1)
        if existe:
            existe.write({
                'name': nombre,
                'categ_id': cat_ctrl.id,
                'uom_id': uom_units.id,
                'type': 'consu',
                'is_storable': True,
                'tracking': 'lot',
            })
            print("Actualizado: " + nombre + " (" + clave + ")")
        else:
            env['product.template'].create({
                'name': nombre,
                'default_code': clave,
                'categ_id': cat_ctrl.id,
                'uom_id': uom_units.id,
                'type': 'consu',
                'is_storable': True,
                'tracking': 'lot',
                'purchase_ok': True,
                'sale_ok': False,
            })
            print("Creado: " + nombre + " (" + clave + ")")
            creados += 1

    env.cr.commit()
    print("LISTO: " + str(creados) + " productos creados. COMMIT OK")
