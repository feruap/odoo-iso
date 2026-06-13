from markupsafe import Markup

Doc = env['amunet.documento']
Act = env['amunet.documento.actividad']

# ─────────────────────────────────────────────
# PNOGE-001 — ELABORACIÓN DE DOCUMENTOS
# ─────────────────────────────────────────────
doc1 = Doc.search([('codigo', '=', 'PNOGE-001')], limit=1)
doc1.with_context(amunet_documento_workflow_write=True).write({
    'descripcion_cambio_pendiente': 'Actualización del procedimiento al sistema Odoo: flujo digital, firmas electrónicas, distribución y resguardo en el sistema de gestión de calidad.',
    'justificacion_pendiente': 'Transición a operación paperless conforme al Manual de Calidad versión vigente. Eliminación de copias físicas y firma autógrafa; adopción de firma electrónica con PIN en Odoo.',
})
doc1.with_context(amunet_documento_workflow_write=True).action_nueva_version()
env.cr.flush()

# Tomamos el nuevo borrador (la acción crea un nuevo registro con version_actual incrementada)
nuevo1 = Doc.search([('codigo', '=', 'PNOGE-001'), ('state', '=', 'borrador')], limit=1, order='id desc')
print(f'Nueva versión PNOGE-001 creada: v{nuevo1.version_actual} id={nuevo1.id}')

nuevo1.with_context(amunet_documento_workflow_write=True).write({
    'seccion_objetivo': Markup('''
<p>Establecer los lineamientos para la elaboración, revisión, autorización y gestión
del ciclo de vida de los documentos que integran el Sistema de Gestión de Calidad (SGC)
de AMUNET, utilizando el sistema Odoo como plataforma oficial de control documental,
en cumplimiento con la NOM-241-SSA1-2025 e ISO 13485.</p>
'''),
    'seccion_alcance': Markup('''
<p>Aplica a todos los documentos del SGC de AMUNET: manuales, procedimientos normalizados
de operación (PNO), instructivos, políticas, especificaciones y formatos. Abarca desde
la identificación de la necesidad hasta la obsolescencia del documento, gestionados
íntegramente en el módulo de Documentación de Odoo.</p>
'''),
    'seccion_condiciones_generales': Markup('''
<h3>Sistema oficial de control documental</h3>
<p>El módulo <strong>Documentación</strong> de Odoo (ruta: Documentación → Documentos controlados)
es el repositorio único y oficial del SGC. La versión vigente de cualquier documento es
exclusivamente la que aparece en estado <em>Vigente</em> dentro del sistema.
No se reconocen como controladas las copias impresas ni los archivos descargados fuera del sistema.</p>

<h3>Estructura del documento en Odoo</h3>
<p>Cada documento en el sistema contiene: código único, título, área, tipo, versión,
responsable, fecha de vigencia, secciones estructuradas (objetivo, alcance, desarrollo
del proceso, formatos derivados, referencias, anexos) e historial de versiones anteriores.</p>

<h3>Codificación</h3>
<p>El código se asigna al crear el documento en Odoo con la nomenclatura establecida en
el Anexo de codificación. El sistema impide duplicar códigos existentes.</p>

<h3>Vigencia</h3>
<p>La vigencia de los documentos es de <strong>3 años</strong> o antes si surgiera una
modificación en la actividad, una observación de auditoría o un cambio regulatorio.
El sistema envía alertas automáticas al responsable cuando la fecha de revisión se acerca.</p>

<h3>Firmas electrónicas</h3>
<p>Las firmas de elaboración, revisión y autorización se realizan mediante PIN personal
en Odoo. Una misma persona no puede firmar dos roles en el mismo documento. El sistema
registra usuario, fecha y hora de cada firma en el historial de auditoría.</p>

<h3>Distribución y conocimiento</h3>
<p>Al publicarse una nueva versión, el sistema notifica automáticamente a las personas
registradas en la lista de distribución del documento. El acceso al documento vigente
en Odoo equivale a la distribución controlada. No se emiten copias físicas controladas.</p>

<h3>Documentos obsoletos</h3>
<p>Al publicar una nueva versión, la anterior pasa automáticamente a estado
<em>Obsoleto</em> y queda resguardada en el historial del sistema. No se destruye
el registro digital; permanece accesible para consulta histórica y auditorías.</p>

<h3>Restricción</h3>
<p>Ningún documento del SGC puede modificarse fuera del flujo establecido en Odoo.
Queda prohibido editar archivos descargados y reintroducirlos al sistema como si fueran
versiones vigentes. Toda modificación debe iniciar con el botón
<strong>"Publicar nueva versión"</strong> dentro del sistema.</p>
'''),
    'seccion_formatos_derivados': Markup('''
<p>Los siguientes registros y reportes de este procedimiento se generan directamente
en Odoo y no requieren formato en papel:</p>
<ul>
  <li><strong>Lista maestra de documentos vigentes</strong> — Documentación → Lista maestra (vigentes)</li>
  <li><strong>Historial de versiones</strong> — Pestaña "Historial" dentro de cada documento</li>
  <li><strong>Lista de distribución</strong> — Pestaña "Distribución" dentro de cada documento</li>
  <li><strong>Registro de firmas</strong> — Pestaña "Firmas" dentro de cada documento</li>
</ul>
'''),
})

# Actualizar actividades del PNOGE-001
actividades_001 = [
    (10, 'Identificar la necesidad del documento',
     Markup('''<p>Identificar si se requiere crear un documento nuevo o actualizar uno existente, con base en:</p>
<ul>
  <li>Cambio en un proceso o actividad operativa.</li>
  <li>Observación de auditoría interna o externa.</li>
  <li>Actualización de la normatividad aplicable (NOM-241, ISO 13485, Cofepris).</li>
  <li>Mejora continua del SGC.</li>
</ul>
<p>El responsable notifica al área de Documentación para iniciar el proceso en Odoo.</p>'''),
     Markup('<p>No aplica</p>')),

    (20, 'Crear o abrir el documento en Odoo',
     Markup('''<p><strong>Documento nuevo:</strong></p>
<ol>
  <li>Ingresar a Odoo → Documentación → Documentos controlados → <em>Nuevo</em>.</li>
  <li>Asignar código conforme a la nomenclatura del SGC.</li>
  <li>Seleccionar tipo, área y responsable.</li>
  <li>Capturar el título del documento.</li>
</ol>
<p><strong>Actualización de documento existente:</strong></p>
<ol>
  <li>Localizar el documento vigente en Odoo.</li>
  <li>Hacer clic en <em>"Publicar nueva versión"</em>. El sistema crea automáticamente un borrador con la versión incrementada.</li>
  <li>La versión vigente permanece activa hasta que la nueva sea autorizada.</li>
</ol>'''),
     Markup('<p>No aplica</p>')),

    (30, 'Elaborar el contenido del documento',
     Markup('''<p>Redactar el contenido en las secciones correspondientes dentro de Odoo:</p>
<ul>
  <li><strong>Objetivo</strong> — Qué se busca lograr con el documento.</li>
  <li><strong>Alcance</strong> — A quién y qué aplica.</li>
  <li><strong>Responsabilidades</strong> — Roles y sus obligaciones.</li>
  <li><strong>Términos y definiciones</strong> — Glosario.</li>
  <li><strong>Desarrollo del proceso</strong> — Actividades paso a paso con responsable y registro.</li>
  <li><strong>Formatos derivados</strong> — Lista de formatos que se generan con este PNO.</li>
  <li><strong>Referencias</strong> — Normatividad y documentos relacionados.</li>
  <li><strong>Anexos</strong> — Información complementaria.</li>
</ul>
<p>El sistema guarda automáticamente los cambios. No se requiere archivo externo (Word, PDF) para documentos nuevos; la fuente oficial es el editor de Odoo.</p>'''),
     Markup('<p>No aplica</p>')),

    (40, 'Asignar revisor y autorizador',
     Markup('''<p>En la pestaña <strong>"Firmas controladas"</strong> del documento:</p>
<ol>
  <li>Seleccionar el <em>Revisor</em> (persona que verificará el contenido técnico).</li>
  <li>Seleccionar el <em>Autorizador</em> (Responsable Sanitario o quien corresponda por nivel jerárquico).</li>
</ol>
<p>Una misma persona no puede ocupar dos roles en el mismo documento.</p>'''),
     Markup('<p>No aplica</p>')),

    (50, 'Enviar a revisión',
     Markup('''<p>El elaborador hace clic en <strong>"Enviar a revisión"</strong>. El sistema:</p>
<ul>
  <li>Cambia el estado del documento a <em>En revisión</em>.</li>
  <li>Notifica al revisor asignado con un aviso en Odoo.</li>
  <li>Bloquea la edición del contenido durante la revisión.</li>
</ul>'''),
     Markup('<p>No aplica</p>')),

    (60, 'Revisar el documento',
     Markup('''<p>El revisor asignado:</p>
<ol>
  <li>Recibe la notificación en Odoo (o en su correo).</li>
  <li>Abre el documento y lee el contenido en cada pestaña.</li>
  <li>Si el documento cumple: hace clic en <strong>"Aprobar revisión"</strong> e ingresa su PIN de firma.</li>
  <li>Si requiere correcciones: escribe el motivo en el campo <em>"Motivo de devolución"</em> y hace clic en <strong>"Devolver a borrador"</strong>. El elaborador recibe la notificación y corrige desde el paso 3.</li>
</ol>'''),
     Markup('<p>No aplica</p>')),

    (70, 'Autorizar y publicar',
     Markup('''<p>El autorizador asignado:</p>
<ol>
  <li>Recibe la notificación de que el documento ya fue revisado.</li>
  <li>Lee el documento y verifica que sea correcto.</li>
  <li>Hace clic en <strong>"Aprobar y publicar"</strong> e ingresa su PIN de firma.</li>
  <li>El sistema cambia el estado a <em>Vigente</em>, registra la fecha de publicación y marca la versión anterior como <em>Obsoleta</em>.</li>
</ol>'''),
     Markup('<p>No aplica</p>')),

    (80, 'Difusión y toma de conocimiento',
     Markup('''<p>Al publicarse el documento:</p>
<ul>
  <li>El sistema notifica automáticamente a las personas registradas en la lista de distribución.</li>
  <li>El personal puede leer el documento en Odoo (Documentación → Documentos controlados).</li>
  <li>La capacitación sobre el nuevo procedimiento se registra en el módulo de Competencias de Odoo (cuando aplique).</li>
</ul>
<p>No se emiten copias físicas controladas. El acceso al sistema es la distribución oficial.</p>'''),
     Markup('<p>No aplica</p>')),

    (90, 'Resguardo y trazabilidad',
     Markup('''<p>El sistema Odoo resguarda automáticamente:</p>
<ul>
  <li>El contenido de todas las versiones del documento (pestaña <em>Historial</em>).</li>
  <li>Fecha, hora y usuario de cada acción (elaboración, revisión, autorización).</li>
  <li>Los documentos obsoletos permanecen en el sistema para consulta histórica y auditorías.</li>
</ul>
<p>No se requiere archivo físico de originales ni destrucción de copias obsoletas;
el sistema garantiza que solo aparezca la versión vigente como activa.</p>'''),
     Markup('<p>No aplica</p>')),

    (100, 'FIN DE LA ACTIVIDAD', Markup('<p><strong>FIN DE LA ACTIVIDAD</strong></p>'), Markup('<p>No aplica</p>')),
]

# Borrar actividades anteriores del borrador y crear nuevas
Act.search([('documento_id', '=', nuevo1.id)]).unlink()
for seq, actividad, desc, reg in actividades_001:
    Act.create({
        'documento_id': nuevo1.id,
        'sequence': seq,
        'actividad': actividad,
        'descripcion': desc,
        'registro': reg,
    })
print(f'  PNOGE-001: {len(actividades_001)} actividades creadas')

# ─────────────────────────────────────────────
# PNOGE-002 — BUENAS PRÁCTICAS DE DOCUMENTACIÓN
# ─────────────────────────────────────────────
doc2 = Doc.search([('codigo', '=', 'PNOGE-002')], limit=1)
doc2.with_context(amunet_documento_workflow_write=True).write({
    'descripcion_cambio_pendiente': 'Actualización de Buenas Prácticas de Documentación al entorno digital Odoo: principios ALCOA+, correcciones en sistema, firma electrónica con PIN y eliminación de reglas de documentación en papel.',
    'justificacion_pendiente': 'Transición a operación paperless conforme al Manual de Calidad versión vigente. Las reglas de escritura con tinta azul, cancelación de espacios y archivo físico ya no aplican en el entorno Odoo.',
})
doc2.with_context(amunet_documento_workflow_write=True).action_nueva_version()
env.cr.flush()

nuevo2 = Doc.search([('codigo', '=', 'PNOGE-002'), ('state', '=', 'borrador')], limit=1, order='id desc')
print(f'Nueva versión PNOGE-002 creada: v{nuevo2.version_actual} id={nuevo2.id}')

nuevo2.with_context(amunet_documento_workflow_write=True).write({
    'seccion_objetivo': Markup('''
<p>Establecer las reglas de Buenas Prácticas de Documentación (BPD) aplicables al registro
de información en el Sistema de Gestión de Calidad de AMUNET, operado mediante la
plataforma Odoo, garantizando que todos los registros sean legibles, verídicos,
rastreables, contemporáneos, originales y precisos (principios ALCOA+).</p>
'''),
    'seccion_alcance': Markup('''
<p>Aplica a todo el personal de AMUNET que genere, edite, revise o autorice registros
o documentos dentro del SGC a través del sistema Odoo, así como a cualquier registro
en soporte físico que por excepción justificada no pueda capturarse en el sistema.</p>
'''),
    'seccion_condiciones_generales': Markup('''
<h3>Principios ALCOA+ en Odoo</h3>
<p>Todos los registros del SGC deben cumplir los principios ALCOA+:</p>
<ul>
  <li><strong>Atribuible:</strong> el sistema registra automáticamente el usuario que crea o modifica cada registro. No se comparten cuentas de usuario ni contraseñas.</li>
  <li><strong>Legible:</strong> los registros capturados en Odoo son siempre legibles. Para registros en papel (cuando aplique por excepción), se escribe con letra clara.</li>
  <li><strong>Contemporáneo:</strong> el registro se captura en el momento en que se realiza la actividad. La fecha y hora las asigna el sistema automáticamente y no son editables.</li>
  <li><strong>Original:</strong> el registro en Odoo es el original. Las impresiones son copias no controladas.</li>
  <li><strong>Preciso:</strong> la información capturada refleja exactamente lo ocurrido, sin omisiones ni alteraciones.</li>
  <li><strong>+Completo, Consistente, Duradero y Disponible:</strong> Odoo garantiza la integridad, consistencia y disponibilidad de los registros durante su periodo de retención.</li>
</ul>

<h3>Correcciones en registros digitales</h3>
<p>Si un registro digital requiere corrección <strong>antes</strong> de ser firmado o aprobado, el usuario puede editarlo directamente en Odoo. El sistema registra la fecha y hora del cambio en el log de auditoría.</p>
<p>Si el registro ya fue <strong>firmado o aprobado</strong>, no puede modificarse. Para corregir un error se debe generar una nueva versión del documento o un registro de corrección, según indique el procedimiento específico.</p>
<p>Queda <strong>prohibido</strong>:</p>
<ul>
  <li>Modificar registros firmados sin seguir el flujo de corrección establecido.</li>
  <li>Usar la cuenta de otra persona para registrar o firmar.</li>
  <li>Antedatar o postdatar registros (la fecha la asigna el sistema).</li>
  <li>Eliminar registros del sistema (los registros obsoletos se marcan, no se borran).</li>
</ul>

<h3>Registros excepcionales en papel</h3>
<p>Cuando por razones operativas un registro deba iniciarse en papel (por ejemplo, en ausencia de conexión a internet), debe transferirse al sistema Odoo en la misma jornada de trabajo, indicando la razón de la captura diferida en el campo de observaciones. El papel original debe resguardarse físicamente hasta que el registro digital sea confirmado.</p>

<h3>Campos en blanco</h3>
<p>Si un campo del formulario en Odoo no aplica para el registro en cuestión, se selecciona la opción "No aplica" o se deja en blanco según lo permita el sistema. No se completan campos con información inventada o aproximada.</p>

<h3>Idioma</h3>
<p>Todos los registros del SGC se capturan en idioma español, salvo términos técnicos o científicos de uso internacional que no tengan equivalente en español.</p>
'''),
})

actividades_002 = [
    (10, 'Acceder al sistema con credenciales propias',
     Markup('''<p>Todo el personal que genere registros en el SGC debe:</p>
<ul>
  <li>Ingresar a Odoo con su <strong>usuario y contraseña personales</strong>.</li>
  <li>Tener configurado su <strong>PIN de firma electrónica</strong> antes de operar (el área de RRHH gestiona el alta en el sistema).</li>
  <li>Cerrar sesión al finalizar su turno o al alejarse de la estación de trabajo.</li>
  <li>Notificar inmediatamente a RRHH o al administrador del sistema si detecta acceso no autorizado con su cuenta.</li>
</ul>
<p><strong>Prohibido:</strong> compartir usuario, contraseña o PIN con cualquier otra persona, incluyendo compañeros de área o superiores.</p>'''),
     Markup('<p>No aplica</p>')),

    (20, 'Capturar el registro en el momento de la actividad',
     Markup('''<p>El registro debe capturarse en Odoo <strong>al momento</strong> en que se realiza la actividad, no antes ni después de manera injustificada.</p>
<ul>
  <li>La fecha y hora del registro las asigna el sistema automáticamente y <strong>no son editables</strong>.</li>
  <li>Si se captura un dato numérico (temperatura, peso, cantidad), debe reflejar el valor real medido, no un estimado.</li>
  <li>Los campos marcados como obligatorios en el formulario deben completarse antes de guardar.</li>
  <li>Si un campo no aplica para el caso en cuestión, escribir <em>"No aplica"</em> o dejar en blanco según lo permita el formulario.</li>
</ul>'''),
     Markup('<p>No aplica</p>')),

    (30, 'Formato de fechas y horas',
     Markup('''<p>En Odoo, las fechas y horas se capturan mediante el selector de fecha del sistema, que garantiza el formato correcto de manera automática.</p>
<p>Para referencias textuales dentro de campos de texto libre, usar:</p>
<ul>
  <li><strong>Fecha completa:</strong> DD/MM/AAAA (ej. 12/06/2026)</li>
  <li><strong>Mes y año:</strong> MM/AAAA (ej. 06/2026)</li>
  <li><strong>Hora:</strong> formato de 24 horas — HH:MM (ej. 14:30)</li>
</ul>'''),
     Markup('<p>No aplica</p>')),

    (40, 'Corregir un error en un registro',
     Markup('''<p><strong>Antes de firmar o aprobar el registro:</strong></p>
<ol>
  <li>Editar directamente el campo incorrecto en Odoo.</li>
  <li>Guardar el cambio. El sistema registra la modificación en el log de auditoría (usuario, fecha, hora).</li>
</ol>
<p><strong>Después de que el registro fue firmado o aprobado:</strong></p>
<ol>
  <li>No es posible modificar el registro directamente.</li>
  <li>El responsable debe notificar al área de Documentación indicando el error y el valor correcto.</li>
  <li>Documentación genera un registro de corrección vinculado al registro original, con el valor corregido, la justificación y la firma del responsable.</li>
  <li>El registro original permanece en el sistema con una nota que lo vincula a la corrección.</li>
</ol>
<p><strong>Prohibido:</strong> eliminar, sobrescribir o alterar registros ya firmados sin seguir este proceso.</p>'''),
     Markup('<p>No aplica</p>')),

    (50, 'Firmar registros y documentos con PIN',
     Markup('''<p>Cuando un registro o documento requiere firma electrónica:</p>
<ol>
  <li>Localizar el botón de acción correspondiente (ej. "Aprobar revisión", "Confirmar", "Liberar").</li>
  <li>El sistema solicita el <strong>PIN personal de firma</strong>.</li>
  <li>Ingresar el PIN y confirmar. El sistema registra: usuario, fecha, hora y acción realizada.</li>
</ol>
<p><strong>Prohibido:</strong> firmar a nombre de otra persona, aunque sea por indicación de un superior. En ausencia del firmante designado, se sigue el procedimiento de sustitución establecido en el SGC.</p>'''),
     Markup('<p>No aplica</p>')),

    (60, 'Resguardo y retención de registros',
     Markup('''<p>El sistema Odoo resguarda automáticamente todos los registros del SGC:</p>
<ul>
  <li>Los registros son accesibles durante todo el período de retención definido en el maestro de registros.</li>
  <li>Los registros obsoletos o sustituidos se marcan como tales en el sistema pero <strong>nunca se eliminan</strong>.</li>
  <li>El respaldo del sistema lo gestiona el área de TI según el procedimiento de resguardo de datos.</li>
</ul>
<p>Para registros en papel que por excepción deban resguardarse físicamente, se aplica lo indicado en el procedimiento PNODC-001 "Control de documentos" versión vigente.</p>'''),
     Markup('<p>No aplica</p>')),

    (70, 'FIN DE LA ACTIVIDAD', Markup('<p><strong>FIN DE LA ACTIVIDAD</strong></p>'), Markup('<p>No aplica</p>')),
]

Act.search([('documento_id', '=', nuevo2.id)]).unlink()
for seq, actividad, desc, reg in actividades_002:
    Act.create({
        'documento_id': nuevo2.id,
        'sequence': seq,
        'actividad': actividad,
        'descripcion': desc,
        'registro': reg,
    })
print(f'  PNOGE-002: {len(actividades_002)} actividades creadas')

env.cr.commit()
print('\nListo — ambos borradores creados. Pendientes de revisión y autorización.')
print(f'  PNOGE-001 v{nuevo1.version_actual} → id {nuevo1.id}')
print(f'  PNOGE-002 v{nuevo2.version_actual} → id {nuevo2.id}')
