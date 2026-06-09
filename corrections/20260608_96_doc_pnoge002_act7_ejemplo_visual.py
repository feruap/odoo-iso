ej = 'style="background:#f5f5f5;border-left:3px solid #1976d2;padding:6px 12px;margin:4px 0;"'

act7 = (
    '<p>En caso de contar con espacios en blanco que no sean utilizados, '
    'cancelar de la siguiente forma:</p>'
    '<ul>'
    '<li>Trazar una línea que abarque el espacio en blanco.</li>'
    '<li>Colocar antefirma (inicial del nombre y primer apellido) de la persona '
    'que va a realizar la cancelación y fecha en que se realizó.</li>'
    '</ul>'
    '<p><strong>Ejemplo — cancelación de espacio en blanco:</strong></p>'
    '<table border="1" style="border-collapse:collapse;width:100%;font-size:inherit;">'
    '<tbody>'
    '<tr>'
    '<th style="padding:6px;background:#f0f0f0;text-align:center;">Campo con dato</th>'
    '<th style="padding:6px;background:#f0f0f0;text-align:center;">Campo en blanco (cancelado)</th>'
    '<th style="padding:6px;background:#f0f0f0;text-align:center;">Campo con dato</th>'
    '</tr>'
    '<tr>'
    '<td style="padding:6px;text-align:center;">23.04.24</td>'
    '<td style="padding:6px;text-align:center;">'
    '<span style="text-decoration:line-through;color:#aaa;">__________</span>'
    '<br/><small><strong>B. Jiménez &nbsp; 23.05.19</strong></small>'
    '</td>'
    '<td style="padding:6px;text-align:center;">35 mL</td>'
    '</tr>'
    '</tbody>'
    '</table>'
    '<p><em>La línea debe tachar todo el espacio en blanco. '
    'La antefirma y fecha se colocan junto a la línea de cancelación.</em></p>'
)

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']
doc = DocModel.search([('codigo', '=', 'PNOGE-002')], limit=1)
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')
acts[6].write({'descripcion': act7})
env.cr.commit()
print('OK — actividad 7 actualizada con ejemplo visual de cancelación')
