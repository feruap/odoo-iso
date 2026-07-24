# Elimina el adjunto de campo (.docx) de PNOGE-014. Es un attachment con
# res_field='archivo', que el ORM oculta en search/unlink; por eso se borra por
# SQL. archivo_filename ya quedo en NULL. El documento controlado real vive en
# Nextcloud (Documentacion confirmo el criterio); aqui solo se limpia el adjunto
# erroneo para dejar PNOGE-014 igual que los otros 70 PNOs. Documento sigue vigente.
doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-014')], limit=1)
assert doc, 'PNOGE-014 no encontrado'

env.cr.execute("""
    DELETE FROM ir_attachment
    WHERE res_model='amunet.documento' AND res_id=%s AND res_field='archivo'
""", (doc.id,))
borrados = env.cr.rowcount
env.cr.commit()

env.cr.execute("""
    SELECT count(*) FROM ir_attachment
    WHERE res_model='amunet.documento' AND res_id=%s
""", (doc.id,))
restantes = env.cr.fetchone()[0]
print('adjuntos borrados:', borrados, '| restantes:', restantes)
print('archivo_filename :', doc.archivo_filename, '| state:', doc.state)
