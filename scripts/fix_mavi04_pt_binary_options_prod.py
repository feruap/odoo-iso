"""
CORRECCIÓN: binary_option_pass/fail vacíos en MAVI-04 de PT (producción)
=========================================================================
Problema: 222 spec configs en 85 PT tienen evaluation_type=binary_selection
          pero binary_option_pass y binary_option_fail vacíos. El módulo no
          puede mostrar los botones de aprobado/rechazado y bloquea cerrar
          el análisis.

Causa: scripts previos que agregaron specs nuevas no incluían las opciones.

Mapa de correcciones (por nombre de spec):
  Polvo                            → Sin polvo / Con polvo
  Manchas y/o suciedad             → Sin manchas y/o suciedad / Con manchas y/o suciedad
  Rasgaduras — Empaque             → Sin rasgaduras / Con rasgaduras
  Rasgaduras — Prueba              → Sin rasgaduras / Con rasgaduras
  Deformidad o deterioro — Empaque → Sin deformidad o deterioro / Con deformidad o deterioro
  Deformidad o deterioro — Prueba  → Sin deformidad o deterioro / Con deformidad o deterioro
  Letra adecuada — Empaque         → Letra adecuada / Letra inadecuada

Aplica SOLO a parameter_id=145 (Aspectos Visuales, PT).
Solicitado por: Diana Flores — Control de Calidad, 2026-09-23
"""

OPCIONES = {
    'Polvo':                               ('Sin polvo',                       'Con polvo'),
    'Manchas y/o suciedad':               ('Sin manchas y/o suciedad',        'Con manchas y/o suciedad'),
    'Rasgaduras — Empaque':               ('Sin rasgaduras',                   'Con rasgaduras'),
    'Rasgaduras — Prueba':                ('Sin rasgaduras',                   'Con rasgaduras'),
    'Deformidad o deterioro — Empaque':   ('Sin deformidad o deterioro',       'Con deformidad o deterioro'),
    'Deformidad o deterioro — Prueba':    ('Sin deformidad o deterioro',       'Con deformidad o deterioro'),
    'Letra adecuada — Empaque':           ('Letra adecuada',                   'Letra inadecuada'),
}

Config = env['amunet.quality.parameter.specification.config']
Rel    = env['amunet.quality.parameter.product.rel']

rels_pt = Rel.search([('parameter_id', '=', 145), ('active', '=', True)])
cfgs    = Config.search([
    ('product_parameter_rel_id', 'in', rels_pt.ids),
    ('active', '=', True),
    ('evaluation_type', '=', 'binary_selection'),
    ('binary_option_pass', 'in', [False, '']),
])

print(f"Configs sin opciones encontradas: {len(cfgs)}")

corregidas = 0
sin_mapa   = []
for cfg in cfgs:
    nombre = cfg.specification_name or ''
    if nombre in OPCIONES:
        pass_val, fail_val = OPCIONES[nombre]
        cfg.write({
            'binary_option_pass': pass_val,
            'binary_option_fail': fail_val,
        })
        corregidas += 1
    else:
        sin_mapa.append(f"  cfg_id={cfg.id}, spec='{nombre}'")

env.cr.commit()
print(f"✓ Corregidas: {corregidas}")
if sin_mapa:
    print(f"Sin mapa ({len(sin_mapa)}):")
    for s in sin_mapa:
        print(s)
else:
    print("✓ Todas las specs tenían mapa definido.")
