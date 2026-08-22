import re

def texto(html):
    t = re.sub(r'<[^>]+>', ' ', html or '')
    return re.sub(r'\s+', ' ', t).strip()[:80]

Doc = env['amunet.documento']
Act = env['amunet.documento.actividad']

for codigo in ['PNOGE-001', 'PNOGE-002']:
    d = Doc.search([('codigo', '=', codigo), ('state', '=', 'borrador')], limit=1, order='id desc')
    if not d:
        print('%s — SIN BORRADOR' % codigo)
        continue
    print('\n=== %s v%s id=%d (borrador) ===' % (codigo, d.version_actual, d.id))
    campos = [
        ('seccion_objetivo', 'Objetivo'),
        ('seccion_alcance', 'Alcance'),
        ('seccion_responsabilidades', 'Responsabilidades'),
        ('seccion_terminos_definiciones', 'Terminos'),
        ('seccion_condiciones_generales', 'Condiciones generales'),
        ('seccion_formatos_derivados', 'Formatos derivados'),
        ('seccion_referencias', 'Referencias'),
        ('seccion_anexos', 'Anexos'),
    ]
    for fname, label in campos:
        val = getattr(d, fname, None) or ''
        tiene = 'OK(%d)' % len(val) if val.strip() else 'VACIO'
        print('  %-22s %s' % (label + ':', tiene))
    acts = Act.search([('documento_id', '=', d.id)], order='sequence')
    print('  Actividades:          %d' % len(acts))
    for a in acts:
        print('    %s. %s' % (a.sequence, (a.actividad or '')[:60]))
