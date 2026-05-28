# Idempotente: crea presentaciones Caja 5 y Caja 10 para DMICR01
# Requiere amunet_packaging_planning instalado
if 'amunet.packaging.presentation' not in env:
    print("  amunet_packaging_planning NO instalado - skip")
else:
    dmicr = env['product.template'].search([('default_code','=','DMICR01')], limit=1)
    if not dmicr:
        print("  DMICR01 no encontrado en BD - skip")
    else:
        for qty, sku, nm in [(10,'DMICR01.10-R','Caja con 10 pruebas'),
                              (5,'DMICR01.05-R','Caja con 5 pruebas')]:
            pres = env['amunet.packaging.presentation'].search([
                ('product_tmpl_id','=',dmicr.id),('package_qty','=',qty)
            ], limit=1)
            if not pres:
                pres = env['amunet.packaging.presentation'].create({
                    'name':nm,'product_tmpl_id':dmicr.id,
                    'product_id':dmicr.product_variant_id.id,
                    'package_qty':qty,'woo_sku':sku,
                    'woo_name':f'Prueba rapida combo respiratorio - {nm}',
                    'authorization_source':'woocommerce','is_authorized':True,
                })
                print(f"  CREADA presentacion {nm} id={pres.id}")
            else:
                print(f"  YA OK presentacion {nm} id={pres.id}")
            existing = {c.product_id.default_code: c for c in pres.component_ids}
            for code, q in [('MICAJ02',1.0),('MIMAN01',1.0),('MIEBP01',1.0),('MIECP01',1.0)]:
                if code in existing: continue
                prod = env['product.product'].search([('default_code','=',code)], limit=1)
                if prod:
                    env['amunet.packaging.presentation.component'].create({
                        'presentation_id':pres.id,'product_id':prod.id,'qty_per_box':q,
                    })
        env.cr.commit()
        print("  Componentes secundarios asegurados")
