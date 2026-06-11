# Crear categoría Semiprocesado/Control y 16 productos Control Positivo
# Solicitud de Karla (almacen.mp) — almacenables, unidades
# Los productos de prueba STCOP01/STCON01 ya fueron eliminados

# --- 1. Categoría Semiprocesado / Control ---
cat_semi = env['product.category'].search([('complete_name', '=', 'Semiprocesado')], limit=1)
if not cat_semi:
    print("ERROR: No se encontró la categoría 'Semiprocesado'")
else:
    cat_ctrl = env['product.category'].search([('complete_name', '=', 'Semiprocesado / Control')], limit=1)
    if not cat_ctrl:
        cat_ctrl = env['product.category'].create({
            'name': 'Control',
            'parent_id': cat_semi.id,
        })
        print("Categoría creada: Semiprocesado / Control (id=" + str(cat_ctrl.id) + ")")
    else:
        print("Categoría ya existe: Semiprocesado / Control (id=" + str(cat_ctrl.id) + ")")

    # --- 2. UdM Unidades ---
    uom_units = env['uom.uom'].search([('name', '=', 'Units')], limit=1)
    if not uom_units:
        uom_units = env['uom.uom'].search([('name', '=', 'Unidades')], limit=1)
    if not uom_units:
        print("ERROR: No se encontró UdM Units/Unidades")
    else:
        # --- 3. Productos ---
        productos = [
            ('Control Positivo SARS-CoV-2',                'SPCPL01'),
            ('Control Positivo Influenza A+B',              'SPCPL02'),
            ('Control Positivo Tuberculosis',               'SPCPL03'),
            ('Control Positivo VPH',                        'SPCPL04'),
            ('Control Positivo K-RAS',                      'SPCPL05'),
            ('Control Positivo P/anticuerpos VIH tipo 1',   'SPCPL06'),
            ('Control Positivo P/anticuerpos VIH tipo 2',   'SPCPL07'),
            ('Control Positivo Tuberculosis TB',            'SPCPL08'),
            ('Control Positivo Tuberculosis RIF/INH',       'SPCPL09'),
            ('Control Positivo Isolister-ADN',              'SPCPL10'),
            ('Control Positivo AUREUS-ADN',                 'SPCPL11'),
            ('Control Positivo CAMPY-ADN',                  'SPCPL12'),
            ('Control Positivo ENTERONET-ADN',              'SPCPL13'),
            ('Control Positivo SALMONET-ADN',               'SPCPL14'),
            ('Control Positivo EcoHem-ADN',                 'SPCPL15'),
            ('Control Positivo VIHLAMP-ADN',                'SPCPL16'),
        ]

        creados = 0
        actualizados = 0
        for nombre, clave in productos:
            existe = env['product.template'].search([('default_code', '=', clave)], limit=1)
            if existe:
                existe.write({
                    'name': nombre,
                    'categ_id': cat_ctrl.id,
                    'uom_id': uom_units.id,
                    'type': 'consu',
                    'is_storable': True,
                })
                print("Actualizado: " + nombre + " (" + clave + ")")
                actualizados += 1
            else:
                env['product.template'].create({
                    'name': nombre,
                    'default_code': clave,
                    'categ_id': cat_ctrl.id,
                    'uom_id': uom_units.id,
                    'type': 'consu',
                    'is_storable': True,
                    'purchase_ok': True,
                    'sale_ok': False,
                })
                print("Creado: " + nombre + " (" + clave + ")")
                creados += 1

        print("LISTO: " + str(creados) + " creados, " + str(actualizados) + " actualizados.")

        # --- 4. Eliminar categoría Semiterminado / Control (vacía) ---
        cat_vieja = env['product.category'].search([('complete_name', '=', 'Semiterminado / Control')], limit=1)
        if cat_vieja:
            productos_en_vieja = env['product.template'].search([('categ_id', '=', cat_vieja.id)])
            if productos_en_vieja:
                print("AVISO: La categoría 'Semiterminado / Control' aún tiene " + str(len(productos_en_vieja)) + " productos. No se eliminó.")
            else:
                cat_vieja.unlink()
                print("Categoría 'Semiterminado / Control' eliminada.")
        else:
            print("La categoría 'Semiterminado / Control' no existe (ya fue eliminada o nunca existió).")
env.cr.commit()
print('COMMIT OK')

# --- Rastreo por lote en los 16 productos Control Positivo ---
refs = ['SPCPL%02d' % i for i in range(1, 17)]
productos_ctrl = env['product.template'].search([('default_code', 'in', refs)])
productos_ctrl.write({'tracking': 'lot'})
env.cr.commit()
print("Rastreo por lote activado en " + str(len(productos_ctrl)) + " productos.")
