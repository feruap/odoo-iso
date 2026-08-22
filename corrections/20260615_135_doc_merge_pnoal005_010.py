from markupsafe import Markup

Doc = env['amunet.documento']
Act = env['amunet.documento.actividad']

# ── Leer fuente: PNOAL-010 ───────────────────────────────────────────────────
src = Doc.search([('codigo', '=', 'PNOAL-010')], limit=1, order='id desc')
dst = Doc.search([('codigo', '=', 'PNOAL-005')], limit=1, order='id desc')

print('Fuente : %s v%s id=%d estado=%s' % (src.codigo, src.version_actual, src.id, src.state))
print('Destino: %s v%s id=%d estado=%s' % (dst.codigo, dst.version_actual, dst.id, dst.state))

# Leer todas las secciones del PNOAL-010
secciones = {
    'name':                        src.name.replace(' (PNOAL-010)', '').strip(),
    'seccion_objetivo':            src.seccion_objetivo,
    'seccion_alcance':             src.seccion_alcance,
    'seccion_responsabilidades':   src.seccion_responsabilidades,
    'seccion_terminos_definiciones': src.seccion_terminos_definiciones,
    'seccion_condiciones_generales': src.seccion_condiciones_generales,
    'seccion_formatos_derivados':  src.seccion_formatos_derivados,
    'seccion_referencias':         src.seccion_referencias,
    'seccion_anexos':              src.seccion_anexos,
    'seccion_introduccion':        src.seccion_introduccion,
}

# Leer actividades de PNOAL-010
acts_src = Act.search([('documento_id', '=', src.id)], order='sequence')
print('  Actividades a copiar: %d' % len(acts_src))

# ── Paso 1: devolver PNOAL-005 a borrador ───────────────────────────────────
dst._workflow_write({'state': 'borrador',
                     'firma_revisa_id': False,
                     'fecha_revisa': False})
env.cr.flush()
print('\nPNOAL-005 devuelto a borrador')

# ── Paso 2: reemplazar contenido de PNOAL-005 ───────────────────────────────
dst.with_context(amunet_documento_workflow_write=True).write(secciones)

# Borrar actividades viejas de PNOAL-005 y copiar las de PNOAL-010
Act.search([('documento_id', '=', dst.id)]).unlink()
for a in acts_src:
    Act.create({
        'documento_id':  dst.id,
        'sequence':      a.sequence,
        'actividad':     a.actividad,
        'descripcion':   a.descripcion,
        'responsable':   a.responsable,
        'registro':      a.registro,
    })
env.cr.flush()
print('PNOAL-005 actualizado con contenido de PNOAL-010')
print('  Secciones copiadas: %d' % len([v for v in secciones.values() if v]))
print('  Actividades copiadas: %d' % len(acts_src))

# ── Paso 3: eliminar PNOAL-010 ───────────────────────────────────────────────
# Primero devolver a borrador para poder eliminar
src._workflow_write({'state': 'borrador',
                     'firma_revisa_id': False,
                     'fecha_revisa': False})
env.cr.flush()

# Eliminar actividades y luego el documento
Act.search([('documento_id', '=', src.id)]).unlink()
src_id = src.id
src.unlink()
env.cr.flush()
print('\nPNOAL-010 (id=%d) eliminado' % src_id)

env.cr.commit()
print('\nListo. PNOAL-005 queda como borrador con el contenido de PNOAL-010.')
print('Revísalo y envíalo a revisión cuando estés lista.')
