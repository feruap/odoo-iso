import re

def txt(html, limit=120):
    t = re.sub(r'<[^>]+>', ' ', html or '')
    return re.sub(r'\s+', ' ', t).strip()[:limit]

Doc = env['amunet.documento']
Act = env['amunet.documento.actividad']

for codigo in ['PNOAL-005', 'PNOAL-010']:
    docs = Doc.search([('codigo', '=', codigo)], order='id desc')
    print('\n=== %s ===' % codigo)
    for d in docs:
        print('  id=%-4d  v%s  estado=%-10s  nombre: %s' % (d.id, d.version_actual, d.state, d.name))
    vigente = docs.filtered(lambda x: x.state == 'vigente')
    if not vigente:
        vigente = docs[0] if docs else False
    if vigente:
        print('  >> Usando: v%s id=%d estado=%s' % (vigente.version_actual, vigente.id, vigente.state))
        campos = [
            ('seccion_objetivo', 'Objetivo'),
            ('seccion_alcance', 'Alcance'),
            ('seccion_responsabilidades', 'Responsabilidades'),
            ('seccion_terminos_definiciones', 'Terminos'),
            ('seccion_condiciones_generales', 'Condiciones'),
            ('seccion_formatos_derivados', 'Formatos derivados'),
            ('seccion_referencias', 'Referencias'),
            ('seccion_anexos', 'Anexos'),
        ]
        for fname, label in campos:
            val = getattr(vigente, fname, None) or ''
            estado = 'OK(%d)' % len(val) if val.strip() else 'VACIO'
            print('    %-22s %s' % (label+':', estado))
        acts = Act.search([('documento_id', '=', vigente.id)], order='sequence')
        print('    Actividades: %d' % len(acts))
        for a in acts:
            print('      %s. %s' % (a.sequence, txt(a.actividad, 80)))
