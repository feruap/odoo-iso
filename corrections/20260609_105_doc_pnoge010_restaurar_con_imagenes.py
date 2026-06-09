import zipfile, base64
from markupsafe import Markup

path = '/tmp/pnoge/PNOGE-010 Etiquetas de identificación.docx'

with zipfile.ZipFile(path) as zf:
    def img(filename):
        full = f'word/{filename}' if not filename.startswith('word/') else filename
        data = base64.b64encode(zf.read(full)).decode('ascii')
        return Markup(f'<p><img src="data:image/png;base64,{data}" style="max-width:100%;height:auto;display:block;margin:8px 0;" alt=""/></p>')

    desc = {
        1: Markup(
            '<p>Al inicio y durante el proceso de fabricación, insumos (prima y material de empaque), '
            'envases, equipos, instrumentos y áreas utilizadas, deben identificarse con etiquetas.</p>'
            '<p>Las etiquetas de identificación deben ser claras y su realización depende de las '
            'necesidades de aplicación. En el presente procedimiento se describen los lineamientos '
            'generales para la elaboración de etiquetas de identificación.</p>'
        ),
        2: (
            Markup(
                '<p><strong>IDENTIFICACIÓN DE ÁREAS Y/O MESAS DE TRABAJO</strong></p>'
                '<p>Todas las áreas y mesas de trabajo deben estar identificadas, mediante una etiqueta '
                'que indique un nombre alusivo al trabajo que se realiza.</p>'
                '<p>A continuación, se ejemplifican las etiquetas utilizadas para este fin:</p>'
            )
            + img('media/image1.png')
            + img('media/image2.png')
        ),
        3: (
            Markup(
                '<p><strong>IDENTIFICACIÓN DE MATERIA PRIMA Y MATERIAL DE EMPAQUE</strong></p>'
                '<p>Para identificar los insumos se usa la siguiente etiqueta:</p>'
                '<p><strong>Fig. 2</strong> Etiqueta usada para identificar los insumos en almacén</p>'
                '<p>Donde el personal de almacén debe colocar: Nombre del insumo, No. de catálogo, '
                'No. de lote, Fecha de caducidad (FC), Cantidad, Proveedor y Estado del insumo '
                '(Cuarentena, Aprobado o Rechazado).</p>'
            )
            + img('media/image3.png')
        ),
        4: (
            Markup(
                '<p><strong>IDENTIFICACIÓN DE SOLUCIONES Y REACTIVOS</strong></p>'
                '<p>Para identificar las soluciones realizadas en AMUNET es muy importante anotar '
                'además del nombre y número de lote correspondiente, la fecha de elaboración (FE) '
                'y de caducidad (FC), así como el nombre del analista responsable de su realización '
                'y el volumen o cantidad preparados.</p>'
            )
            + img('media/image4.png')
            + img('media/image5.png')
        ),
        5: (
            Markup(
                '<p><strong>IDENTIFICACIÓN DE EQUIPOS E INSTRUMENTOS</strong></p>'
                '<p>Todos los equipos e instrumentos deben contar con un código de identificación '
                'el cual es asignado por el área de Validación.</p>'
                '<p><strong>Donde:</strong></p>'
                '<ul>'
                '<li>Las primeras tres letras (puede ser números) \'BIO\' pueden corresponder al '
                'nombre del equipo o instrumento.</li>'
                '<li>Los siguientes tres dígitos \'001\' corresponden al número consecutivo del equipo.</li>'
                '</ul>'
            )
            + img('media/image6.png')
        ),
        6: (
            Markup(
                '<p><strong>Identificación de Carpetas de Documentación</strong></p>'
                '<p>El área de documentación debe identificar todas las carpetas (documentos) mediante '
                'una etiqueta la cual indique en forma general el tipo de documentos que integran la '
                'carpeta. Cuando aplique la etiqueta puede incluir datos más precisos.</p>'
            )
            + img('media/image7.png')
            + img('media/image8.png')
        ),
        7: Markup('<p><strong>FIN DE LA ACTIVIDAD</strong></p>'),
    }

    ActModel = env['amunet.documento.actividad']
    doc_obj = env['amunet.documento'].search([('codigo', '=', 'PNOGE-010')], limit=1)
    acts = {a.sequence: a for a in ActModel.search([('documento_id', '=', doc_obj.id)])}

    for seq, nueva_desc in desc.items():
        if seq in acts:
            acts[seq].write({'descripcion': nueva_desc})

env.cr.commit()
print('OK — PNOGE-010 texto restaurado con imágenes correctas')
