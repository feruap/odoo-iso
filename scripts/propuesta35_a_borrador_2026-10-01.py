# Regresar la propuesta 35 a borrador (Mery, 1-oct-2026). El modelo no tiene
# boton para esto: solo enviar, aprobar, rechazar y crear producto. Una
# propuesta aprobada a la que le falta un dato -- como esta, sin categoria y
# sin decir si se inventaria -- no se puede corregir desde la pantalla.
prop = env['amunet.marketplace.product.proposal'].browse(35)
print('antes :', prop.name, '|', prop.state)
prop.with_context(marketplace_proposal_internal_write=True).write({'state': 'draft'})
prop.message_post(body=(
    'Regresada a <b>Borrador</b> a peticion de Mery para completar los datos '
    'que le faltan: la categoria, y marcar si se lleva en inventario. Es un '
    'articulo de limpieza, asi que probablemente no se inventaria y entonces '
    'no necesita clave.'))
env.cr.commit()
prop.invalidate_recordset()
print('ahora :', prop.name, '|', prop.state)
print()
print('lo que le falta para poder darla de alta:')
print('   categoria        :', prop.category_id.complete_name or 'FALTA')
print('   se inventaria    :', prop.amunet_inventariable)
print('   clave            :', prop.clave_propuesta or '(sin clave)')
