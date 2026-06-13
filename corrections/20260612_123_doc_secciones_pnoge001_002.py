from markupsafe import Markup

Doc = env['amunet.documento']

# ─── PNOGE-001 v03 (borrador) ───────────────────────────────────────────────
d1 = Doc.search([('codigo', '=', 'PNOGE-001'), ('state', '=', 'borrador')], limit=1, order='id desc')
print('Actualizando PNOGE-001 id=%d v%s' % (d1.id, d1.version_actual))

d1.with_context(amunet_documento_workflow_write=True).write({

'seccion_responsabilidades': Markup('''
<h3>Elaborador</h3>
<p>Cualquier persona del equipo AMUNET que identifique la necesidad de crear o actualizar
un documento del SGC. Es responsable de:</p>
<ul>
  <li>Redactar el contenido en Odoo con claridad, veracidad y lenguaje técnico apropiado.</li>
  <li>Asignar al revisor y autorizador en la pestaña "Firmas".</li>
  <li>Enviar el documento a revisión una vez completo.</li>
  <li>Corregir las observaciones que devuelva el revisor.</li>
</ul>

<h3>Revisor</h3>
<p>Persona designada con conocimiento técnico del proceso documentado. Es responsable de:</p>
<ul>
  <li>Leer el documento en Odoo y verificar que el contenido sea técnicamente correcto,
      completo y coherente con otros documentos del SGC.</li>
  <li>Aprobar mediante firma electrónica (PIN) si el documento está conforme.</li>
  <li>Devolver a borrador con observaciones escritas si requiere correcciones.</li>
</ul>

<h3>Autorizador (Responsable Sanitario o Dirección General)</h3>
<p>Persona con autoridad para publicar documentos del SGC. Es responsable de:</p>
<ul>
  <li>Verificar que el documento revisado sea pertinente y aplicable al SGC de AMUNET.</li>
  <li>Autorizar y publicar mediante firma electrónica (PIN). Al hacerlo, el sistema
      cambia el estado a <em>Vigente</em> y la versión anterior queda automáticamente como
      <em>Obsoleta</em>.</li>
  <li>Garantizar que el documento cumpla con ISO 13485, NOM-241-SSA1-2025 y Cofepris.</li>
</ul>

<h3>Área de Documentación</h3>
<p>Responsable de administrar el módulo de Documentación en Odoo. Sus funciones incluyen:</p>
<ul>
  <li>Mantener la lista de distribución actualizada en cada documento.</li>
  <li>Verificar que todos los documentos vigentes tengan fecha de revisión programada.</li>
  <li>Atender solicitudes de impresión controlada y de nueva versión.</li>
  <li>Coordinar el flujo de aprobación cuando alguna persona no esté disponible.</li>
  <li>Capacitar al personal en el uso del módulo de Documentación.</li>
</ul>

<h3>Todo el personal AMUNET</h3>
<ul>
  <li>Consultar únicamente la versión vigente del documento en Odoo.</li>
  <li>Firmar el acuse de conocimiento cuando el documento lo requiera.</li>
  <li>No reproducir, imprimir ni distribuir documentos fuera del sistema sin autorización.</li>
  <li>Notificar al área de Documentación si detecta inconsistencias o necesidad de actualización.</li>
</ul>
'''),

'seccion_terminos_definiciones': Markup('''
<table border="1" cellpadding="6" style="border-collapse:collapse;width:100%">
<thead style="background-color:#e9ecef">
  <tr><th style="width:30%">Término</th><th>Definición</th></tr>
</thead>
<tbody>
  <tr>
    <td><strong>Documento controlado</strong></td>
    <td>Documento del SGC gestionado en Odoo con código único, versión, estado y trazabilidad completa de cambios. La versión vigente en el sistema es la única oficial.</td>
  </tr>
  <tr>
    <td><strong>Firma electrónica con PIN</strong></td>
    <td>Mecanismo de autenticación personal que sustituye a la firma autógrafa en el entorno digital. Consiste en un número de identificación personal (PIN) de 4 dígitos, único por usuario, almacenado de forma cifrada en el sistema. Su uso vincula de manera trazable a una persona con una acción (revisar, autorizar, confirmar un registro).</td>
  </tr>
  <tr>
    <td><strong>Estado del documento</strong></td>
    <td>Condición en que se encuentra un documento dentro de su ciclo de vida. Los estados posibles son: <em>Borrador</em> (en elaboración), <em>En revisión</em> (pendiente de revisión técnica), <em>Vigente</em> (aprobado y en uso), <em>Obsoleto</em> (sustituido por versión más reciente o retirado).</td>
  </tr>
  <tr>
    <td><strong>Versión vigente</strong></td>
    <td>La versión del documento con estado "Vigente" en Odoo. Es la única de referencia para la operación. Las versiones anteriores quedan en estado "Obsoleto" y solo se consultan para trazabilidad histórica.</td>
  </tr>
  <tr>
    <td><strong>Historial de versiones</strong></td>
    <td>Registro automático que el sistema mantiene de todas las versiones anteriores de un documento, incluyendo contenido, fechas y firmas de cada versión publicada.</td>
  </tr>
  <tr>
    <td><strong>Lista de distribución</strong></td>
    <td>Relación de personas que deben ser notificadas al publicarse una nueva versión del documento. Se gestiona en la pestaña "Distribución" de cada documento en Odoo.</td>
  </tr>
  <tr>
    <td><strong>Copia no controlada</strong></td>
    <td>Impresión física o archivo descargado de un documento del SGC. No es la fuente oficial. Puede usarse como referencia temporal, pero siempre debe verificarse contra la versión vigente en Odoo antes de tomar decisiones críticas.</td>
  </tr>
  <tr>
    <td><strong>SGC</strong></td>
    <td>Sistema de Gestión de Calidad: conjunto de políticas, objetivos, procedimientos, instrucciones, registros y recursos que AMUNET implementa para asegurar que sus productos cumplen los requisitos de calidad y regulatorios aplicables (ISO 13485, NOM-241-SSA1-2025, Cofepris).</td>
  </tr>
  <tr>
    <td><strong>IVD</strong></td>
    <td>Dispositivo de diagnóstico in vitro (In Vitro Diagnostic). Producto médico destinado al diagnóstico de condiciones humanas mediante análisis de muestras biológicas. Las pruebas rápidas de AMUNET son dispositivos IVD sujetos a regulación sanitaria estricta.</td>
  </tr>
  <tr>
    <td><strong>Trazabilidad documental</strong></td>
    <td>Capacidad de reconstruir el historial completo de un documento: quién lo creó, quién lo revisó, quién lo autorizó, qué cambios se hicieron en cada versión y cuándo. Odoo garantiza esta trazabilidad de forma automática mediante el log de auditoría.</td>
  </tr>
  <tr>
    <td><strong>PNO</strong></td>
    <td>Procedimiento Normalizado de Operación. Documento del SGC que describe paso a paso cómo realizar una actividad, quién es responsable y qué registros se generan. Equivale al SOP (Standard Operating Procedure) en inglés.</td>
  </tr>
  <tr>
    <td><strong>Responsable Sanitario (RS)</strong></td>
    <td>Profesional de la salud responsable ante Cofepris del cumplimiento regulatorio de AMUNET. Su firma autoriza los documentos del SGC con carácter oficial ante las autoridades sanitarias.</td>
  </tr>
</tbody>
</table>
'''),

'seccion_referencias': Markup('''
<ul>
  <li>ISO 13485:2016 — Sistemas de gestión de la calidad para productos sanitarios. Apartados 4.2.3, 4.2.4 y 4.2.5.</li>
  <li>NOM-241-SSA1-2025 — Buenas prácticas de fabricación para establecimientos dedicados a la fabricación de dispositivos médicos. Apartado 5.2 (Documentación).</li>
  <li>Manual de Calidad AMUNET — versión vigente.</li>
  <li>PNOGE-002 — Buenas Prácticas de Documentación — versión vigente.</li>
  <li>PNODC-001 — Control de registros y retención — versión vigente.</li>
</ul>
'''),

'seccion_anexos': Markup('''
<h3>Anexo 1. Estructura documental del Sistema de Gestión de Calidad de AMUNET en Odoo</h3>
<p>La siguiente jerarquía representa cómo se organizan los documentos del SGC dentro del módulo de Documentación de Odoo:</p>

<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%;margin-bottom:16px">
<thead style="background-color:#1a5276;color:#ffffff">
  <tr><th colspan="2" style="text-align:center">NIVEL 1 — POLÍTICAS Y MANUAL</th></tr>
</thead>
<tbody>
  <tr>
    <td style="width:40%;background-color:#d6eaf8"><strong>Manual de Calidad (MACA)</strong></td>
    <td>Define el alcance del SGC, la política de calidad y los compromisos de la dirección. Referencia principal ante auditorías.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>Políticas corporativas</strong></td>
    <td>Declaraciones de compromiso de la dirección sobre temas específicos (calidad, inocuidad, seguridad de la información).</td>
  </tr>
</tbody>
</table>

<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%;margin-bottom:16px">
<thead style="background-color:#1f618d;color:#ffffff">
  <tr><th colspan="2" style="text-align:center">NIVEL 2 — PROCEDIMIENTOS NORMALIZADOS DE OPERACIÓN (PNO)</th></tr>
</thead>
<tbody>
  <tr>
    <td style="width:40%;background-color:#d6eaf8"><strong>PNOGE — Generales</strong></td>
    <td>Procedimientos transversales: control de documentos, BPD, control de cambios, formación, auditorías internas.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNOCC — Control de Calidad</strong></td>
    <td>Análisis de producto terminado, controles de calidad en proceso, estudios de estabilidad, no conformidades.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNOPR — Producción</strong></td>
    <td>Fabricación, ensamble, acondicionado, limpieza y desinfección de áreas.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNOAL — Almacén</strong></td>
    <td>Recepción, almacenamiento, control de lotes y distribución de materiales y producto terminado.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNORH — Recursos Humanos</strong></td>
    <td>Contratación, capacitación, evaluación de competencias, higiene del personal.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNOEST — Aseguramiento de Calidad</strong></td>
    <td>Revisión por la dirección, gestión de riesgos, CAPA, quejas y tecnovigilancia.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNOIN — Ingeniería / Mantenimiento</strong></td>
    <td>Mantenimiento de equipos, calibración, validaciones de proceso.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>PNOMA — Manual / Transversales</strong></td>
    <td>Documentos de referencia y lineamientos aplicables a toda la organización.</td>
  </tr>
</tbody>
</table>

<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%;margin-bottom:16px">
<thead style="background-color:#2874a6;color:#ffffff">
  <tr><th colspan="2" style="text-align:center">NIVEL 3 — INSTRUCTIVOS Y ESPECIFICACIONES</th></tr>
</thead>
<tbody>
  <tr>
    <td style="width:40%;background-color:#d6eaf8"><strong>Instructivos de trabajo</strong></td>
    <td>Descripciones detalladas de operaciones específicas que complementan un PNO (paso a paso de un equipo, proceso crítico, etc.).</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>Especificaciones técnicas</strong></td>
    <td>Definición de parámetros de calidad de materias primas, materiales de empaque y producto terminado.</td>
  </tr>
</tbody>
</table>

<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%">
<thead style="background-color:#2e86c1;color:#ffffff">
  <tr><th colspan="2" style="text-align:center">NIVEL 4 — REGISTROS Y FORMATOS</th></tr>
</thead>
<tbody>
  <tr>
    <td style="width:40%;background-color:#d6eaf8"><strong>Registros digitales en Odoo</strong></td>
    <td>Evidencia de actividades realizadas: lotes de producción, análisis, calibraciones, capacitaciones, no conformidades, CAPA. Generados y almacenados en el módulo correspondiente de Odoo.</td>
  </tr>
  <tr>
    <td style="background-color:#d6eaf8"><strong>Formatos descargables</strong></td>
    <td>Plantillas controladas (PDF) disponibles en Documentación → Formatos, para casos donde se requiere captura en papel. Su descarga e impresión requieren solicitud de impresión controlada.</td>
  </tr>
</tbody>
</table>

<p style="margin-top:12px;font-style:italic;color:#555">
  Todos los documentos del SGC se encuentran en el módulo <strong>Documentación → Documentos controlados</strong> de Odoo.
  La única versión oficial es la que aparece en estado <em>Vigente</em> dentro del sistema.
</p>
'''),

})
print('  PNOGE-001: 4 secciones actualizadas')

# ─── PNOGE-002 v04 (borrador) ───────────────────────────────────────────────
d2 = Doc.search([('codigo', '=', 'PNOGE-002'), ('state', '=', 'borrador')], limit=1, order='id desc')
print('Actualizando PNOGE-002 id=%d v%s' % (d2.id, d2.version_actual))

d2.with_context(amunet_documento_workflow_write=True).write({

'seccion_responsabilidades': Markup('''
<h3>Todo el personal AMUNET</h3>
<ul>
  <li>Ingresar al sistema Odoo exclusivamente con su cuenta personal (usuario y contraseña propios).</li>
  <li>Registrar la información en el momento en que ocurre la actividad, sin anticipar ni diferir el registro sin justificación.</li>
  <li>Capturar datos reales y verídicos. Queda prohibido estimar, redondear o inventar valores en registros del SGC.</li>
  <li>Firmar con su PIN personal cuando el sistema lo requiera. No firmar por cuenta de otra persona ni ceder el PIN.</li>
  <li>Reportar inmediatamente cualquier error en un registro ya firmado al área de Documentación para gestionar la corrección formal.</li>
  <li>Mantener la confidencialidad de su contraseña y PIN. Reportar a RRHH si sospecha de uso no autorizado.</li>
</ul>

<h3>Supervisores y responsables de área</h3>
<ul>
  <li>Verificar que el personal bajo su cargo registre la información en tiempo y forma en Odoo.</li>
  <li>Atender oportunamente las solicitudes de corrección de registros bajo su responsabilidad.</li>
  <li>Notificar al área de Documentación cuando detecten un patrón de registros incompletos o incorrectos en su área.</li>
</ul>

<h3>Área de Documentación</h3>
<ul>
  <li>Administrar el catálogo de firmas electrónicas: verificar que todos los usuarios activos que generan registros del SGC tengan PIN configurado.</li>
  <li>Gestionar las correcciones a registros ya firmados, asegurando trazabilidad completa.</li>
  <li>Capacitar al personal en las Buenas Prácticas de Documentación digital.</li>
  <li>Emitir los lineamientos de BPD y mantener este procedimiento actualizado.</li>
</ul>

<h3>Área de TI / Desarrollo</h3>
<ul>
  <li>Garantizar la disponibilidad y seguridad del sistema Odoo.</li>
  <li>Mantener la trazabilidad y los logs de auditoría del sistema.</li>
  <li>Gestionar los respaldos de la base de datos conforme al procedimiento de seguridad de la información.</li>
</ul>
'''),

'seccion_terminos_definiciones': Markup('''
<table border="1" cellpadding="6" style="border-collapse:collapse;width:100%">
<thead style="background-color:#e9ecef">
  <tr><th style="width:30%">Término</th><th>Definición</th></tr>
</thead>
<tbody>
  <tr>
    <td><strong>Buenas Prácticas de Documentación (BPD)</strong></td>
    <td>Conjunto de lineamientos que aseguran que los documentos y registros del SGC sean atribuibles, legibles, contemporáneos, originales, precisos, completos, consistentes, duraderos y disponibles (principios ALCOA+). En el entorno digital de AMUNET, estas prácticas se aplican al uso del sistema Odoo.</td>
  </tr>
  <tr>
    <td><strong>ALCOA+</strong></td>
    <td>Acrónimo de los principios de integridad de datos reconocidos por la FDA, EMA y WHO: <em>Attributable</em> (Atribuible), <em>Legible</em>, <em>Contemporaneous</em> (Contemporáneo), <em>Original</em>, <em>Accurate</em> (Preciso), más: <em>Completo</em>, <em>Consistente</em>, <em>Duradero</em> y <em>Disponible</em>.</td>
  </tr>
  <tr>
    <td><strong>Firma electrónica con PIN</strong></td>
    <td>Mecanismo de autenticación personal que sustituye a la firma autógrafa. El PIN (número de identificación personal de 4 dígitos) está vinculado a un único usuario en el sistema. Su uso en Odoo registra: usuario, fecha, hora y acción realizada, con la misma validez que una firma manuscrita para los efectos del SGC.</td>
  </tr>
  <tr>
    <td><strong>Registro digital</strong></td>
    <td>Evidencia generada y almacenada en Odoo que documenta la realización de una actividad del SGC. Incluye fecha y hora del sistema, usuario que lo creó y log de cualquier modificación posterior.</td>
  </tr>
  <tr>
    <td><strong>Trazabilidad</strong></td>
    <td>Capacidad de rastrear el historial, aplicación o localización de un registro o documento. En Odoo, la trazabilidad es automática: el sistema registra cada acción (creación, edición, aprobación) con fecha, hora y usuario.</td>
  </tr>
  <tr>
    <td><strong>Log de auditoría</strong></td>
    <td>Registro automático que el sistema genera de cada acción realizada sobre un documento o registro: quién hizo qué, cuándo y desde qué equipo. No puede ser editado ni eliminado por los usuarios.</td>
  </tr>
  <tr>
    <td><strong>Integridad de datos</strong></td>
    <td>Propiedad que asegura que los datos registrados son completos, consistentes y exactos durante todo su ciclo de vida. La integridad es un requisito regulatorio de ISO 13485 y la NOM-241-SSA1-2025.</td>
  </tr>
  <tr>
    <td><strong>Contemporáneo</strong></td>
    <td>Que el registro se realiza en el momento en que ocurre la actividad. En Odoo, la fecha y hora la asigna el sistema al guardar el registro; no son editables por el usuario, lo que garantiza la contemporaneidad.</td>
  </tr>
  <tr>
    <td><strong>Corrección de registro</strong></td>
    <td>Proceso formal para enmendar un error en un registro del SGC. Antes de firma: edición directa en Odoo (el log de auditoría registra el cambio). Después de firma: requiere un registro de corrección formal con justificación y firma del responsable, gestionado por el área de Documentación.</td>
  </tr>
  <tr>
    <td><strong>Registro original</strong></td>
    <td>El primer registro creado en Odoo es el original. Las impresiones o archivos exportados son copias. Si existe discrepancia entre el sistema y una copia impresa, prevalece el sistema.</td>
  </tr>
</tbody>
</table>
'''),

'seccion_referencias': Markup('''
<ul>
  <li>ISO 13485:2016 — Sistemas de gestión de la calidad para productos sanitarios. Apartado 4.2 (Requisitos de documentación).</li>
  <li>NOM-241-SSA1-2025 — Buenas prácticas de fabricación para dispositivos médicos. Apartado 5.2 (Documentación y registros).</li>
  <li>21 CFR Part 11 — FDA: Electronic Records; Electronic Signatures (referencia para BPD en entorno electrónico).</li>
  <li>GAMP 5 — Good Automated Manufacturing Practice (guía para sistemas informáticos regulados).</li>
  <li>Manual de Calidad AMUNET — versión vigente.</li>
  <li>PNOGE-001 — Elaboración, revisión y autorización de documentos controlados — versión vigente.</li>
</ul>
'''),

'seccion_anexos': Markup('<p>No aplica.</p>'),

})
print('  PNOGE-002: 4 secciones actualizadas')

env.cr.commit()
print('\nListo. Ambos borradores completados.')
