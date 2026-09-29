"""Archiva QC/2026/00509: analisis duplicado que quedo sin objeto.

Autorizado por Mery el 29-sep-2026. Diana (msg 18:12) pidio que no lo cerrara Calidad,
para que no pareciera que aprobo material ficticio. Archivarlo no aprueba nada: el
analisis nunca se capturo ni se firmo.

QUE PASO. El 28-sep se genero un analisis para SPHMC56 lote HMC56072602 a partir de la
recepcion AMP/IN/00159. La clave estaba mal: el material era SPHMC87.

DONDE ESTA HOY:
    - El material vive en SPHMC87, lote HMC56072602 (conserva su nombre de lote
      original), con 117.6 cm en AMP/Existencias. Almacen ya hizo la correccion.
    - Ese material YA SE ANALIZO Y SE LIBERO bajo la clave correcta: QC/2026/00340,
      mismo lote, estado Finalizado. Su gemelo del otro lote es QC/2026/00330.
    - SPHMC56 quedo con 0 cm de existencia interna. No hay saldo negativo que corregir;
      a diferencia del caso STREX, aqui el inventario ya cuadra.

POR QUE SE ARCHIVA Y NO SE "CANCELA": el modelo no tiene estado 'cancel' (draft,
in_progress, pending, awaiting_reception, done). Archivar conserva el registro completo
para el expediente y lo saca de las listas. El analisis se queda en 'Por realizar', sin
firma de nadie, que es exactamente lo que Diana pidio evitar.

Idempotente.
"""
from markupsafe import Markup

Check = env['amunet.quality.check'].sudo().with_context(active_test=False)
qc = Check.search([('name', '=', 'QC/2026/00509')], limit=1)

if not qc:
    print('[ojo] no existe QC/2026/00509')
elif not qc.active:
    print('[ya] QC/2026/00509 ya esta archivado')
else:
    capturados = 0
    for l in qc.test_line_ids:
        for d in l.detail_line_ids:
            if any(getattr(d, f, False) for f in
                   ('binary_result', 'numeric_value', 'text_value', 'result')):
                capturados += 1
    print('QC/2026/00509  id %s  %s  lote %s  estado %s  renglones capturados %d' % (
        qc.id, qc.product_id.default_code, qc.lot_id.name, qc.state, capturados))
    if capturados:
        # si alguien capturo algo entre ayer y hoy, este script NO es el camino
        print('[ALTO] tiene %d renglones capturados; no se archiva sin revisar' % capturados)
    else:
        qc.message_post(body=Markup(
            'Analisis archivado el 29-sep-2026, autorizado por Mery, a peticion de '
            'Calidad.<br/><br/>'
            '<b>Analisis duplicado sin objeto.</b> Se genero el 28-sep para la clave '
            'SPHMC56 a partir de la recepcion AMP/IN/00159, pero el material recibido '
            'era <b>SPHMC87</b>, no SPHMC56.<br/><br/>'
            'Ese material ya se analizo y se libero bajo la clave correcta: '
            '<b>QC/2026/00340</b>, mismo lote HMC56072602, estado Finalizado. Hoy vive '
            'en SPHMC87 con 117.6 cm en AMP/Existencias, despues de la correccion de '
            'Almacen.<br/><br/>'
            'Este analisis se queda en <b>Por realizar</b>, sin captura y sin firma de '
            'nadie: no hubo aprobacion de material. SPHMC56 no tiene existencia ni saldo '
            'negativo que corregir.'))
        qc.write({'active': False,
                  'change_reason': ('Analisis duplicado sin objeto: la clave de la '
                                    'recepcion estaba mal (era SPHMC87) y el material ya '
                                    'se libero en QC/2026/00340. Autorizado por Mery el '
                                    '29-sep-2026 a peticion de Calidad.')})
        print('[ok] QC/2026/00509 archivado')

print('\n=== como queda ===')
qc = Check.search([('name', '=', 'QC/2026/00509')], limit=1)
print('   QC/2026/00509  activo=%s  estado=%s' % (qc.active, qc.state))
print('   el que si corresponde: QC/2026/00340  %s' % Check.search(
    [('name', '=', 'QC/2026/00340')], limit=1).state)
env.cr.commit()
