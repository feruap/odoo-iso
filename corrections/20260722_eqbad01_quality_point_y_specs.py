"""
Crea el punto de control y especificaciones de EQBAD01 (Balanza electrónica de precisión).
Correr UNA VEZ después del deploy a producción.
"""
env = env  # noqa: F821 — Odoo shell

Product = env['product.product']
QualityPoint = env['amunet.quality.point']
ParamRel = env['amunet.quality.parameter.product.rel']
SpecConfig = env['amunet.quality.parameter.specification.config']
Spec = env['amunet.quality.check.parameter.specification']
Param = env['amunet.quality.check.parameter']

product = Product.search([('default_code', '=', 'EQBAD01')], limit=1)
if not product:
    print("ERROR: producto EQBAD01 no encontrado")
else:
    # Verificar si ya existe el punto de control
    existing = QualityPoint.search([('name', '=', 'Balanza electrónica de precisión')])
    if existing:
        print(f"El punto de control ya existe (id={existing.id}), no se crea duplicado.")
    else:
        # 1. Crear punto de control
        qp = QualityPoint.create({
            'name': 'Balanza electrónica de precisión',
            'product_ids': [(4, product.id)],
        })
        print(f"Punto de control creado: id={qp.id}")

    # 2. Parámetros: 147=Apariencia física, 149=Cumplimiento de la funcionalidad
    param_apariencia = Param.browse(147)
    param_exactitud  = Param.browse(149)

    tmpl = product.product_tmpl_id

    existing_rels = ParamRel.search([('product_tmpl_id', '=', tmpl.id)])
    if existing_rels:
        print(f"Relaciones parámetro-producto ya existen ({len(existing_rels)}), no se crean duplicados.")
    else:
        rel_ap = ParamRel.create({'product_tmpl_id': tmpl.id, 'parameter_id': param_apariencia.id, 'sequence': 10})
        rel_ex = ParamRel.create({'product_tmpl_id': tmpl.id, 'parameter_id': param_exactitud.id,  'sequence': 20})
        print(f"Relaciones creadas: Apariencia id={rel_ap.id}, Exactitud id={rel_ex.id}")

        # 3. Specs de Apariencia
        spec_polvo    = Spec.search([('parameter_id', '=', 147), ('name', '=', 'Polvo')], limit=1)
        spec_manchas  = Spec.search([('parameter_id', '=', 147), ('name', '=', 'Manchas y/o suciedad')], limit=1)
        spec_rasgrad  = Spec.search([('parameter_id', '=', 147), ('name', 'ilike', 'Rasgaduras')], limit=1)
        spec_deform   = Spec.search([('parameter_id', '=', 147), ('name', '=', 'Deformidad o deterioro')], limit=1)

        SpecConfig.create({'product_parameter_rel_id': rel_ap.id, 'specification_id': spec_polvo.id,
            'sequence': 10, 'evaluation_type': 'binary_selection',
            'specification_name': 'Polvo', 'acceptance_criteria': 'Sin polvo',
            'binary_option_pass': 'Sin polvo', 'binary_option_fail': 'Con polvo'})
        SpecConfig.create({'product_parameter_rel_id': rel_ap.id, 'specification_id': spec_manchas.id,
            'sequence': 20, 'evaluation_type': 'binary_selection',
            'specification_name': 'Manchas y/o suciedad', 'acceptance_criteria': 'Sin manchas y/o suciedad',
            'binary_option_pass': 'Sin manchas y/o suciedad', 'binary_option_fail': 'Con manchas y/o suciedad'})
        SpecConfig.create({'product_parameter_rel_id': rel_ap.id, 'specification_id': spec_rasgrad.id,
            'sequence': 30, 'evaluation_type': 'binary_selection',
            'specification_name': 'Rasgaduras y/o fisuras', 'acceptance_criteria': 'Sin rasgaduras y/o fisuras',
            'binary_option_pass': 'Sin rasgaduras y/o fisuras', 'binary_option_fail': 'Con rasgaduras y/o fisuras'})
        SpecConfig.create({'product_parameter_rel_id': rel_ap.id, 'specification_id': spec_deform.id,
            'sequence': 40, 'evaluation_type': 'binary_selection',
            'specification_name': 'Deformidad o deterioro', 'acceptance_criteria': 'Sin deformidad o deterioro',
            'binary_option_pass': 'Sin deformidad o deterioro', 'binary_option_fail': 'Con deformidad o deterioro'})

        # 4. Spec de Exactitud — crear si no existe
        spec_exactitud = Spec.search([('parameter_id', '=', 149), ('name', 'ilike', 'Exactitud')], limit=1)
        if not spec_exactitud:
            spec_exactitud = Spec.create({'parameter_id': 149, 'name': 'Exactitud (±2d)',
                'evaluation_type': 'binary_selection',
                'acceptance_criteria': 'Las lecturas coinciden con las pesas patrón dentro de la tolerancia (±2d)'})
        SpecConfig.create({'product_parameter_rel_id': rel_ex.id, 'specification_id': spec_exactitud.id,
            'sequence': 10, 'evaluation_type': 'binary_selection',
            'specification_name': 'Exactitud (±2d)',
            'acceptance_criteria': 'Las lecturas coinciden con las pesas patrón dentro de la tolerancia (±2d)',
            'binary_option_pass': 'Las lecturas coinciden con las pesas patrón (±2d)',
            'binary_option_fail': 'Las lecturas NO coinciden con las pesas patrón (±2d)'})

        print("Specs de Apariencia (4) y Exactitud (1) creados correctamente.")

    env.cr.commit()
    print("LISTO — EQBAD01 configurado.")
