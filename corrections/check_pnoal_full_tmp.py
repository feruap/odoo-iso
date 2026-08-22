import re

def txt(html, limit=300):
    t = re.sub(r'<[^>]+>', ' ', html or '')
    return re.sub(r'\s+', ' ', t).strip()[:limit]

Doc = env['amunet.documento']
Act = env['amunet.documento.actividad']

for codigo in ['PNOAL-005', 'PNOAL-010']:
    d = Doc.search([('codigo', '=', codigo)], limit=1, order='id desc')
    print('\n' + '='*60)
    print('%s  |  v%s  |  %s  |  id=%d' % (codigo, d.version_actual, d.state, d.id))
    print('Nombre: %s' % d.name)
    print('\n[OBJETIVO]')
    print(txt(d.seccion_objetivo))
    print('\n[ALCANCE]')
    print(txt(d.seccion_alcance))
    print('\n[CONDICIONES GENERALES]')
    print(txt(d.seccion_condiciones_generales))
    print('\n[ACTIVIDADES]')
    acts = Act.search([('documento_id', '=', d.id)], order='sequence')
    for a in acts:
        print('  Act %s: %s' % (a.sequence, txt(a.actividad, 100)))
        print('    Desc: %s' % txt(a.descripcion, 150))
        print('    Resp: %s' % (a.responsable or ''))
        print('    Reg:  %s' % txt(a.registro, 80))
