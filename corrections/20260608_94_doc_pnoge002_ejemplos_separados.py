DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']

doc = DocModel.search([('codigo', '=', 'PNOGE-002')], limit=1)
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')

# Estilo para cajas de ejemplo
ej = 'style="background:#f5f5f5;border-left:3px solid #1976d2;padding:6px 12px;margin:4px 0;font-family:monospace;"'

# ── Actividad 2: Formato de fecha - Opción 1 ──────────────────────────────────
act2 = (
    '<p><strong>Formato de fecha — Opción 1</strong></p>'
    '<p>Esta opción deberá ser usada en bitácoras, reportes, certificados y demás '
    'donde sea necesario colocar la fecha completa.</p>'
    '<p>Se podrá usar la siguiente estructura:</p>'
    '<ul>'
    '<li>Día: 2 dígitos</li>'
    '<li>Mes: 2 dígitos</li>'
    '<li>Año: 2 últimos dígitos</li>'
    '</ul>'
    '<p>Entre datos deberá existir puntos que separen la información.</p>'
    '<p><strong>Ejemplo:</strong></p>'
    f'<p {ej}>25.12.24</p>'
)

# ── Actividad 3: Formato de fecha - Opción 2 ──────────────────────────────────
act3 = (
    '<p><strong>Formato de fecha — Opción 2</strong></p>'
    '<p>Esta opción deberá ser usada en documentos ya sea como encabezado, vigencias '
    'o próximas revisiones.</p>'
    '<p>Se podrá usar la siguiente estructura:</p>'
    '<ul>'
    '<li>Mes: 3 primeras letras</li>'
    '<li>Año: 4 dígitos o 2 últimos dígitos</li>'
    '</ul>'
    '<p>Entre datos deberá existir puntos o un espacio que separe la información.</p>'
    '<p><strong>Ejemplos:</strong></p>'
    f'<p {ej}>Ene 2024 &nbsp; o &nbsp; Ene 24</p>'
    f'<p {ej}>Ene.2024 &nbsp; o &nbsp; Ene.24</p>'
)

# ── Actividad 4: Formato de fecha carta/memorándum ────────────────────────────
act4 = (
    '<p><strong>Formato de fecha (carta/memorándum)</strong></p>'
    '<p>Para esta opción se inicia indicando municipio, estado seguido de dos dígitos '
    'para el día seguido del mes y año sin abreviaturas; como se muestra a continuación:</p>'
    '<ul>'
    '<li>Municipio, Estado seguido de la preposición "a"</li>'
    '<li>Día (2 dígitos) seguido de la preposición "de"</li>'
    '<li>Mes (nombre completo en minúscula) seguido de la preposición "de"</li>'
    '<li>Año (4 dígitos)</li>'
    '</ul>'
    '<p><strong>Ejemplo:</strong></p>'
    f'<p {ej}>Puebla, Puebla a 28 de mayo de 2024</p>'
)

# ── Actividad 5: Formato de horas ─────────────────────────────────────────────
act5 = (
    '<p>Escribir horas en formato de 12 horas:</p>'
    '<p><strong>Ejemplos:</strong></p>'
    f'<p {ej}>03:02 pm</p>'
    f'<p {ej}>08:30 am</p>'
    f'<p {ej}>11:59 pm</p>'
    '<p>Cuando se registren tiempos menores a una hora se utiliza la palabra MIN, min.</p>'
    '<p><strong>Ejemplo:</strong></p>'
    f'<p {ej}>10 MIN &nbsp; / &nbsp; 15 min</p>'
)

acts[1].write({'descripcion': act2})
acts[2].write({'descripcion': act3})
acts[3].write({'descripcion': act4})
acts[4].write({'descripcion': act5})
env.cr.commit()
print('OK — actividades 2/3/4/5 de PNOGE-002 corregidas')
