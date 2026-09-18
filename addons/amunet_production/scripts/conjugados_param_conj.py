# Marca los 29 como conjugado y carga los parametros de receta de los 19 con datos.
Tmpl = env['product.template']
todos = Tmpl.search([('default_code', 'like', 'SPCDE%')])
todos.write({'amunet_es_conjugado': True, 'amunet_req_aforar': False})
print('Marcados como conjugado: %s (y Aforar apagado)' % len(todos))

# clave: (pH, bloqueo, horas_conj, min_bloqueo, DO objetivo, proceso)
P = {
    'SPCDE01': ('7.5', 'cas', 2.0,  30, 9.0,  'estandar'),
    'SPCDE02': ('8.5', 'cas', 2.0,  30, 8.0,  'estandar'),
    'SPCDE03': ('8.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE08': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE09': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE10': ('7.5', 'cas', 1.5,  30, 12.0, 'largo'),
    'SPCDE12': ('8.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE13': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE14': ('7.5', 'cas', 1.5,  15, 10.0, 'largo'),
    'SPCDE17': ('8.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE18': ('7.5', 'cas', 2.0,  30, 12.4, 'estandar'),
    'SPCDE19': ('7.5', 'bsa', 1.5,  30, 10.0, 'largo'),
    'SPCDE20': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE21': ('8.5', 'cb',  2.0,  30, 20.0, 'estandar'),
    'SPCDE22': ('7.5', 'bsa', 2.0,  30, 10.0, 'estandar'),
    'SPCDE23': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE24': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE26': ('7.5', 'cas', 2.0,  30, 10.0, 'estandar'),
    'SPCDE29': ('8.5', 'bsa', 2.0,  30, 10.0, 'estandar'),
}
for clave, (ph, bloq, hc, mb, do, proc) in P.items():
    t = Tmpl.search([('default_code', '=', clave)], limit=1)
    if not t:
        print('%s NO existe' % clave); continue
    t.write({
        'amunet_conj_ph_sab': ph,
        'amunet_conj_agente_bloqueo': bloq,
        'amunet_conj_horas_conjugacion': hc,
        'amunet_conj_min_bloqueo': float(mb),
        'amunet_conj_do_objetivo': do,
        'amunet_conj_proceso': proc,
        'amunet_conj_vol_resuspension': 30.0,
    })
print('Parametros cargados: %s conjugados' % len(P))
env.cr.commit()
print('COMMIT OK')
