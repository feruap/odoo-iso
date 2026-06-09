import json

with open('/tmp/circulos_b64.json') as f:
    circs = json.load(f)

def circulo(color_b64, alt):
    return (f'<img src="data:image/png;base64,{color_b64}" '
            f'style="width:28px;height:28px;vertical-align:middle;margin:0 5px;" '
            f'alt="{alt}"/>')

c_amarillo = circulo(circs['amarillo'], 'cuarentena')
c_verde    = circulo(circs['verde'],    'aprobado')
c_rojo     = circulo(circs['rojo'],     'rechazado')

act3 = (
    '<p><strong>Identificación de producto</strong></p>'
    '<p>Colocar etiquetas de identificación a los empaques o contenedores de cada lote '
    'de insumos. Ver anexo 1</p>'
    '<p>Adicional a la etiqueta de identificación colocar una etiqueta circular color '
    'amarillo ' + c_amarillo + ', la cual indica que el insumo se encuentra en cuarentena.</p>'
)

act7 = (
    '<p>La etiqueta circular color rojo, de insumos rechazados, no debe contener alguna '
    'marca o indicación. ' + c_rojo + '</p>'
    '<p>La etiqueta circular color verde, de insumos aprobados, debe marcarse de acuerdo '
    'al siguiente sistema: ' + c_verde + '</p>'
    '<p><strong>1.1 | 1.1</strong></p>'
    '<p>Donde:</p>'
    '<p>El primer número indica el número de lote ingresado, este número es consecutivo '
    'para cada lote aprobado, de cada insumo.</p>'
    '<p>El segundo número corresponde a la cantidad de bolsas o paquetes que conforman '
    'el lote, de ser el caso.</p>'
    '<p>El orden para marcar las bolsas o paquetes de los insumos ingresados al resguardo '
    'de producto aprobado se debe realizar de acuerdo al siguiente ejemplo:</p>'
    '<p>Si ya se encuentran resguardados lotes del insumo, las bolsas o paquetes '
    'ingresados se deben numerar y colocar de manera consecutiva. Suponiendo que existan '
    'paquetes de lotes con la siguiente numeración en la etiqueta: 5.1, 6.1, 6.2, 6.3 y '
    '7.1; y suponiendo que se van a ingresar dos paquetes de un nuevo lote, los paquetes '
    'nuevos se identifican de la siguiente forma: 8.1 y 8.2.</p>'
)

DocModel = env['amunet.documento']
ActModel = env['amunet.documento.actividad']
doc = DocModel.search([('codigo', '=', 'PNOAL-002')], limit=1)
acts = ActModel.search([('documento_id', '=', doc.id)], order='sequence')
acts[2].write({'descripcion': act3})
acts[6].write({'descripcion': act7})
env.cr.commit()
print('OK — imágenes de etiquetas eliminadas de actividades 3 y 7')
