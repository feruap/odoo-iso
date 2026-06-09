import zipfile, base64, html as html_mod

path = '/tmp/pnoge/PNOGE-001  ELABORACION DE  DOCs listo.docx'

with zipfile.ZipFile(path) as zf:
    def img_b64(filename):
        data = base64.b64encode(zf.read(f'word/media/{filename}')).decode('ascii')
        return f'data:image/png;base64,{data}'
    img_anexo3 = img_b64('image1.png')
    img_anexo4 = img_b64('image2.png')

def img_tag(src, alt=''):
    return (f'<img src="{src}" '
            f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
            f'alt="{html_mod.escape(alt)}"/>')

hdr = lambda n, titulo='': (
    '<div style="background:#e8f4fd;border-left:4px solid #1565c0;'
    'padding:10px 14px;margin:24px 0 8px 0;border-radius:0 4px 4px 0;">'
    f'<strong style="font-size:1.05em;color:#0d47a1;">Anexo {n}. {titulo}</strong></div>'
)

# Anexo 1 — Pirámide documental
anexo1 = hdr(1, 'Estructura documental del Sistema de Gestión de Calidad')
anexo1 += '''
<table border="0" style="width:100%;border-collapse:collapse;margin:12px 0;">
  <tr>
    <td style="background:#1565c0;color:#fff;text-align:center;padding:10px 8px;font-weight:bold;width:50%;border:1px solid #ccc;">
      ¿Hacia dónde vamos con la aplicación del Sistema de Gestión de Calidad?
    </td>
    <td style="background:#e3f2fd;padding:10px 8px;border:1px solid #ccc;">
      <strong>Políticas, Manuales</strong>
    </td>
  </tr>
  <tr>
    <td style="background:#1976d2;color:#fff;text-align:center;padding:10px 8px;font-weight:bold;border:1px solid #ccc;">
      ¿Cuál es el compromiso de la organización?
    </td>
    <td style="background:#e8f5e9;padding:10px 8px;border:1px solid #ccc;">
      <strong>Procedimientos Normalizados de Operación</strong>
    </td>
  </tr>
  <tr>
    <td style="background:#1e88e5;color:#fff;text-align:center;padding:10px 8px;font-weight:bold;border:1px solid #ccc;">
      ¿Cómo se realizan las actividades?
    </td>
    <td style="background:#fff9c4;padding:10px 8px;border:1px solid #ccc;">
      <strong>Instructivos, Especificaciones, Métodos de prueba</strong>
    </td>
  </tr>
  <tr>
    <td style="background:#42a5f5;color:#fff;text-align:center;padding:10px 8px;font-weight:bold;border:1px solid #ccc;">
      En ellos se asienta las evidencias objetivas, por eso son la base
    </td>
    <td style="background:#fce4ec;padding:10px 8px;border:1px solid #ccc;">
      <strong>Registros y Formatos</strong>
    </td>
  </tr>
</table>
<p>Se le conoce también como pirámide documental, y es la forma en que jerárquicamente están organizados los documentos del Sistema de Gestión de Calidad.</p>
<p>Los documentos libres podrán ser emitidos con base a las necesidades de cada área.</p>
'''

# Anexo 2 — Estructura de los documentos
anexo2 = hdr(2, 'Estructura de los documentos')
anexo2 += '''
<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">
  <tr>
    <th style="padding:6px;background:#e3f2fd;">Contenido del documento</th>
    <th style="padding:6px;background:#e3f2fd;">Manual</th>
    <th style="padding:6px;background:#e3f2fd;">Procedimiento Normalizado de Operación</th>
    <th style="padding:6px;background:#e3f2fd;">Instructivo</th>
  </tr>
  <tr><td style="padding:6px;">Objetivo</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Alcance</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Introducción</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">N/A</td><td style="padding:6px;text-align:center;">N/A</td></tr>
  <tr><td style="padding:6px;">Misión, Visión</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">N/A</td><td style="padding:6px;text-align:center;">N/A</td></tr>
  <tr><td style="padding:6px;">Responsabilidades</td><td style="padding:6px;text-align:center;">N/A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Organigrama</td><td style="padding:6px;text-align:center;">O</td><td style="padding:6px;text-align:center;">N/A</td><td style="padding:6px;text-align:center;">N/A</td></tr>
  <tr><td style="padding:6px;">Términos y definiciones</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Condiciones generales</td><td style="padding:6px;text-align:center;">O</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">O</td></tr>
  <tr><td style="padding:6px;">Desarrollo del proceso</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Formatos derivados</td><td style="padding:6px;text-align:center;">N/A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Referencias bibliográficas</td><td style="padding:6px;text-align:center;">O</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Anexos</td><td style="padding:6px;text-align:center;">O</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">O</td></tr>
  <tr><td style="padding:6px;">Control de cambios</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td style="padding:6px;">Firmas de conocimiento</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td><td style="padding:6px;text-align:center;">A</td></tr>
  <tr><td colspan="4" style="padding:6px;background:#f5f5f5;"><em>A: Aplica &nbsp;&nbsp; N/A: No aplica &nbsp;&nbsp; O: Opcional</em></td></tr>
</table>
<p>Si se requiere realizar otro documento para el Sistema de Gestión de la Calidad, solicitar el tipo de documento y su estructura al área de Documentación.</p>
<ul>
  <li><strong>Objetivo:</strong> Describe el propósito y/o la razón de ser del documento.</li>
  <li><strong>Alcance:</strong> Describe las áreas donde se aplica el documento.</li>
  <li><strong>Introducción:</strong> En las primeras páginas del documento se describe de forma general su contenido.</li>
  <li><strong>Misión:</strong> Es una declaración o manifestación duradera del objeto, propósito o razón de ser de una empresa.</li>
  <li><strong>Visión:</strong> Es una declaración o manifestación que indica hacia dónde se dirige una empresa a largo plazo.</li>
  <li><strong>Responsabilidades:</strong> Describen las obligaciones generales que son competencia de un cargo o área.</li>
  <li><strong>Organigrama:</strong> Representación gráfica de la estructura de una empresa o institución.</li>
  <li><strong>Términos y definiciones:</strong> Palabras o siglas que requieran de una aclaración dentro del documento.</li>
  <li><strong>Condiciones generales:</strong> Indicaciones necesarias aplicables al documento.</li>
  <li><strong>Contenido:</strong> Describe de forma ordenada todas las actividades a desarrollar (quién, qué, cómo, cuándo).</li>
  <li><strong>Formatos derivados:</strong> Formatos mencionados en la descripción del documento.</li>
  <li><strong>Control de cambios:</strong> Es la acción de controlar los cambios que tiene un documento a través de su historial.</li>
  <li><strong>Referencias bibliográficas:</strong> Material consultado como libros, revistas científicas, normas, leyes, reglamentos, etc.</li>
  <li><strong>Anexos:</strong> Información que complementa el contenido del documento como tablas, diagramas, imágenes, etc.</li>
</ul>
<p>Si durante la elaboración del documento no aplica alguno de los apartados de la estructura, se debe indicar "No aplica" o "N/A".</p>
'''

# Anexo 3 — Encabezado con imagen
anexo3 = hdr(3, 'Encabezados: Se muestra un ejemplo de un encabezado el cual se puede modificar según las necesidades del área')
anexo3 += f'<p>{img_tag(img_anexo3, "Ejemplo de encabezado")}</p>'
anexo3 += '''<p><strong>Donde:</strong></p>
<ul>
  <li><strong>Logotipo de la empresa</strong></li>
  <li><strong>Nombre de la empresa</strong></li>
  <li><strong>Área al que pertenece el documento</strong></li>
  <li><strong>Tipo y nombre del documento:</strong> Identificación del documento según corresponda, ya sea Manual, PNO, Instructivo, Especificación, etc.</li>
  <li><strong>Código:</strong> Clave alfanumérica proporcionado por el área de Sistema de Gestión de Calidad.</li>
  <li><strong>Versión:</strong> Concierne al número de veces que el documento ha sido revisado y actualizado.</li>
  <li><strong>Sustituye:</strong> Se escribe la versión del documento a remplazar.</li>
  <li><strong>Página:</strong> Numeración consecutiva con relación al total de páginas. Ejemplo: Pagina 1 de 5.</li>
  <li><strong>Fecha de emisión:</strong> Es la fecha en la cual se indica a partir de cuándo el documento entra en vigor.</li>
  <li><strong>Próxima revisión:</strong> Es la fecha en la cual se indica cuándo se debe revisar el documento para verificar su vigencia.</li>
</ul>'''

# Anexo 4 — Sección de firmas con imagen
anexo4 = hdr(4, 'Sección de firmas: Colocar únicamente en la primera página del documento')
anexo4 += '<p>Colocar el siguiente recuadro en Manuales y/o Procedimientos Normalizados de Operación:</p>'
anexo4 += f'<p>{img_tag(img_anexo4, "Sección de firmas")}</p>'

nuevo_anexos = anexo1 + anexo2 + anexo3 + anexo4

doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-001')], limit=1)
doc.write({'seccion_anexos': nuevo_anexos})
env.cr.commit()
print('OK — PNOGE-001 anexos 3 y 4 actualizados con imágenes')
