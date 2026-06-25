"""
Corrige las actividades del Desarrollo del proceso de PNOGE-009 (Gestión de Riesgos).
Las 4 actividades anteriores eran descripciones de metodología (APR, AMEF, HACCP,
Mapeo de proceso) tomadas de Condiciones Generales — no el flujo real del proceso.
Este script las reemplaza por las 24 actividades correctas del Word ver02.

Ejecutar en producción DESPUÉS del deploy del módulo amunet_documentos.
"""
import psycopg2

conn = psycopg2.connect(host="localhost", dbname="Amunet", user="odoo", password="odoo_prod_password")
cur = conn.cursor()

cur.execute("SELECT id FROM amunet_documento WHERE codigo = 'PNOGE-009'")
row = cur.fetchone()
if not row:
    print("ERROR: PNOGE-009 no encontrado en la base de datos")
    conn.close()
    raise SystemExit(1)

doc_id = row[0]
print(f"PNOGE-009 encontrado: id={doc_id}")

cur.execute("DELETE FROM amunet_documento_actividad WHERE documento_id = %s", (doc_id,))
print(f"Actividades anteriores eliminadas: {cur.rowcount}")

actividades = [
    (10,  '1',  'Una vez definido el proceso objeto de Gestión de Riesgos el cual se define como: técnica o proceso científico y analítico que tiene como proceso identificar, evaluar y controlar los posibles riesgos que puedan surgir de la toma de decisiones o en un proceso que puede afectar a la continuidad de un negocio, avisar al Área de Calidad para la conformación del Comité Técnico.', 'Documentación', 'No aplica'),
    (20,  '2',  'Convocar a los supervisores de las áreas correspondientes, así como al personal con conocimientos en los procesos de gestión de riesgos, por ejemplo: Riesgo en sistemas críticos: Validación, Sistemas críticos, Mantenimiento, ingeniería, regulatorios, etc. / Riesgo en cadena de suministro: Almacén, Operaciones, Validación, ventas, regulatorios, etc. Una vez integrado el Comité Técnico realizar un memorándum donde se indique a los integrantes de Comité Técnico de Amunet S.A. de C.V. y difundir en las áreas correspondientes.', 'Documentación / Responsable Sanitario o Aux. de Responsable Sanitario', 'No aplica'),
    (30,  '3',  'Solicitar de forma impresa y/o electrónica los formatos correspondientes para realizar la Gestión de Riesgos correspondiente al Área de Calidad.', 'Personal solicitante', 'No aplica'),
    (40,  '4',  'Entregar de forma impresa y/o electrónica los siguientes formatos en su versión vigente: F-GE-009/001 "Matriz de Gestión de Riesgos Análisis de Modo y Efectos de Fallas (A.M.E.F.)" e F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F.", al personal solicitante.', 'Documentación', 'F-GE-009/001 "Matriz de Gestión de Riesgos A.M.E.F" / F-GE-009/002 "Informe de Análisis de Riesgos (A.M.E.F)"'),
    (50,  '5',  'Colocar la siguiente información en la Sección I. Datos Generales del formato F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente: Área, Nombre del Responsable (Personal que elabora Análisis de Riesgo), Fecha, Proceso (Identificar con claridad los procesos, funciones, sistemas, equipos, instalaciones, que requieren o sobre los que se realiza la Matriz de Gestión de Riesgos).', 'Personal solicitante', 'F-GE-009/002 "Informe de Análisis de Riesgos (A.M.E.F)" versión vigente'),
    (60,  '6',  'Solicitar el Folio AR (folio de análisis de riesgo) al Área de Documentación.', 'Personal solicitante', 'No aplica'),
    (70,  '7',  'Asignar y registrar el número de Folio AR (folio de análisis de riesgo) correspondiente al consecutivo en la bitácora electrónica formato F-GE-009/003 "Reporte de Análisis de Riesgos" versión vigente, de la siguiente manera: Análisis de Riesgo (AR) seguido de un guion (-), el año en curso a dos cifras (00) y el consecutivo que sigue en la bitácora mencionada a tres dígitos (000). Folio AR (ejemplo): AR-23-001.', 'Documentación', 'F-GE-009/003 "Reporte de Análisis de Riesgos" versión vigente'),
    (80,  '8',  'Colocar el Folio AR (folio de análisis de riesgo) asignado en la Sección I. Datos Generales del formato F-GE-009/003 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente.', 'Personal solicitante', 'F-GE-009/003 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (90,  '9',  'Realizar el diagrama de Ishikawa (también llamado Diagrama de Causa y Efecto, Diagrama de Espina de Pescado o Diagrama de los 6Ms — Ver Anexo 2) del proceso objeto de la Gestión de Riesgos en la Sección II. Diagrama causa y efecto del formato F-GR-009/003 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente.', 'Personal solicitante', 'F-GR-009/003 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (100, '10', 'Realizar el formato F-GE-009/001 "Matriz de Gestión de Riesgos Análisis de Modo y Efecto de Fallas A.M.E.F." versión vigente del proceso, equipo, sistema etc. en la Sección III. Análisis de Riesgos del formato F-GE-009/003 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente. Campos: Proceso, Función, Modo de la Falla, Efecto de la Falla, Causa de la Falla, Control Actual, Severidad (escala 1-5), Ocurrencia (escala 1-5), Detectabilidad (escala 1-5), NPR = S×O×D (rango 1-125), Acciones Recomendadas (Ver Anexo 3 y 4).', 'Personal solicitante', 'F-GE-009/001 "Matriz de Gestión de Riesgos A.M.E.F." / F-GE-009/003 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (110, '11', 'Realizar el análisis de los valores de NPR de mayor a menor en la Sección VI. Análisis de NPR y plan de mitigación de riesgos: referencial al control de cambios/CAPAs del formato F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente.', 'Personal solicitante', 'F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (120, '12', 'Solicitar la aprobación del Comité Técnico, los cuales deben revisar junto con el elaborador el análisis y el plan de mitigación de riesgo, exponiendo argumentos técnicos a favor o en contra de la efectividad del análisis, requisitos adicionales y resultado del análisis; registrando fecha, nombre, firma y observaciones en la Sección V. Aprobación del Comité Técnico del formato F-GE-009/002 versión vigente.', 'Personal solicitante / Comité técnico', 'F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (130, '13', 'Evaluar las Acciones Recomendadas en el formato F-GE-009/001 A.M.E.F., estimar los nuevos valores (Nueva Severidad S, Nueva Ocurrencia O, Nueva Detección D) y calcular el Nuevo Número de Prioridad de Riesgo (NNPR) en la Sección VI. Re-Análisis de Riesgo del formato F-GE-009/002 versión vigente.', 'Personal solicitante / Comité técnico', 'F-GE-009/001 Matriz de Gestión de Riesgos A.M.E.F. / F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (140, '14', 'Realizar un análisis técnico del nivel de riesgo inicial contra el nuevo nivel probable de riesgo, evaluando si el NNPR es aceptable; si no, proponer e implantar nuevas acciones de mitigación hasta que el NNPR sea menor al NPR y aceptable para el Comité Técnico, en la Sección VII. Análisis de Riesgo NPR vs NNPR del formato F-GE-009/002 versión vigente.', 'Personal solicitante', 'F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (150, '15', 'Indicar las referencias de los documentos modificados, implementados, capacitaciones, distribuciones, comunicados y evidencias en la Sección VIII. Referencias Documentales de las Acciones del formato F-GE-009/002 versión vigente.', 'Personal solicitante', 'F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (160, '16', 'Solicitar una junta con la Dirección de la empresa, Área de Documentación y Comité Técnico para revisar el Informe de Análisis de Riesgo A.M.E.F. correspondiente: análisis, plan de mitigación ejecutado, evidencias y evaluación del nuevo impacto.', 'Dirección general / Documentación / Comité técnico', 'No aplica'),
    (170, '17', 'Si es requerido, establecer acciones y recursos para completar las tareas establecidas del Informe de Análisis de Riesgo A.M.E.F. correspondiente.', 'Dirección general / Documentación / Comité técnico', 'No aplica'),
    (180, '18', 'El Comité Técnico, de estar en cumplimiento, firman la Sección IX. Autorización y Cierre del formato F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente.', 'Comité técnico', 'F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (190, '19', 'Entregar el F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente junto con su evidencia al Área de Calidad.', 'Personal solicitante', 'F-GE-009/002 "Informe de Análisis de Riesgos: A.M.E.F." versión vigente'),
    (200, '20', 'Verificar la correcta integración de la evidencia, la congruencia de la información, el efecto esperado y que todas las actividades han sido completadas correctamente.', 'Documentación', 'No aplica'),
    (210, '21', 'Una vez cerrado el análisis de riesgos, actualizar la bitácora electrónica conforme al formato F-GE-009/004 "Registro de Análisis de Riesgos" versión vigente: identificar el Folio AR y registrar en la fila correspondiente el No. de control de cambios generado y/o el folio de las CAPAs.', 'Documentación', 'F-GE-009/004 "Registro de Análisis de Riesgos" versión vigente'),
    (220, '22', 'Seguimiento al Sistema de Gestión de Riesgos de Calidad: registrar en el formato F-GE-009/004 "Seguimiento al Sistema de Gestión de Riesgos" versión vigente los campos: Fecha (seguimiento 3 meses a partir de la última tarea asignada), Folio AR, Área, Fecha Programada, Fecha Reprogramada (si aplica), Efectividad y Fecha de Cierre.', 'Documentación / Dirección general', 'F-GE-009/004 "Seguimiento al Sistema de Gestión de Riesgos" versión vigente'),
    (230, '23', 'Archivar la documentación generada en este procedimiento en la carpeta correspondiente.', 'Documentación', 'No aplica'),
    (240, '24', 'FIN DE LA ACTIVIDAD', 'No aplica', 'No aplica'),
]

for seq, act, desc, resp, reg in actividades:
    cur.execute("""
        INSERT INTO amunet_documento_actividad
            (documento_id, sequence, actividad, descripcion, responsable, registro)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (doc_id, seq, act, f'<p>{desc}</p>', resp, reg))

print(f"OK: {len(actividades)} actividades correctas insertadas en PNOGE-009 (id={doc_id})")
conn.commit()
conn.close()
