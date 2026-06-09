import zipfile, base64, html as html_mod

path = '/tmp/pnoge/PNOGE-009 GESTION DE RIESGOS ver02.docx'

with zipfile.ZipFile(path) as zf:
    def img_b64(filename):
        data = base64.b64encode(zf.read(f'word/media/{filename}')).decode('ascii')
        return f'data:image/png;base64,{data}'

    img1 = img_b64('image1.png')
    img2 = img_b64('image2.png')
    img3 = img_b64('image3.png')

def img_tag(src, alt=''):
    return (f'<img src="{src}" '
            f'style="max-width:100%;height:auto;display:block;margin:8px 0;" '
            f'alt="{html_mod.escape(alt)}"/>')

hdr = lambda n: (
    f'<div style="background:#e8f4fd;border-left:4px solid #1565c0;'
    f'padding:10px 14px;margin:24px 0 8px 0;border-radius:0 4px 4px 0;">'
    f'<strong style="font-size:1.05em;color:#0d47a1;">Anexo {n}.</strong></div>'
)

tabla_anexo3 = (
    '<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">'
    '<tr><th style="padding:4px;">Severidad</th><th style="padding:4px;">Ocurrencia</th>'
    '<th style="padding:4px;">Detectabilidad</th>'
    '<th style="padding:4px;">Número de prioridad de riesgo (NPR)</th>'
    '<th style="padding:4px;">Tipo de Riesgo</th>'
    '<th style="padding:4px;">Impacto del Efecto</th></tr>'
    '<tr><td style="padding:4px;">Grado</td><td style="padding:4px;">Valor</td>'
    '<td style="padding:4px;">Grado</td><td style="padding:4px;">Valor</td>'
    '<td style="padding:4px;">Grado</td><td style="padding:4px;">Valor</td>'
    '<td style="padding:4px;">Calificación</td><td style="padding:4px;">Valor</td>'
    '<td style="padding:4px;">Identificación</td><td style="padding:4px;">Severidad</td>'
    '<td style="padding:4px;">→</td><td style="padding:4px;">Efecto</td></tr>'
    '<tr><td style="padding:4px;">Severidad muy baja</td><td style="padding:4px;">1</td>'
    '<td style="padding:4px;">Altamente improbable</td><td style="padding:4px;">1</td>'
    '<td style="padding:4px;">Alta probabilidad</td><td style="padding:4px;">1</td>'
    '<td style="padding:4px;">Alto riesgo de falla</td><td style="padding:4px;">64 a 125</td>'
    '<td style="padding:4px;">A</td><td style="padding:4px;">Ocurrencia</td>'
    '<td style="padding:4px;">→</td><td style="padding:4px;">Causa</td></tr>'
    '<tr><td style="padding:4px;">Severidad baja</td><td style="padding:4px;">2</td>'
    '<td style="padding:4px;">Muy baja probabilidad</td><td style="padding:4px;">2</td>'
    '<td style="padding:4px;">Prob. medianamente alta</td><td style="padding:4px;">2</td>'
    '<td style="padding:4px;">Prob. media de riesgo</td><td style="padding:4px;">9 a 63</td>'
    '<td style="padding:4px;">B</td><td style="padding:4px;">Detectbilidad</td>'
    '<td style="padding:4px;">→</td><td style="padding:4px;">Modo</td></tr>'
    '<tr><td style="padding:4px;">Severidad promedio</td><td style="padding:4px;">3</td>'
    '<td style="padding:4px;">Probabilidad media</td><td style="padding:4px;">3</td>'
    '<td style="padding:4px;">Probabilidad media</td><td style="padding:4px;">3</td>'
    '<td style="padding:4px;">Bajo riesgo de falla</td><td style="padding:4px;">1 a 8</td>'
    '<td style="padding:4px;">C</td><td style="padding:4px;"></td>'
    '<td style="padding:4px;"></td><td style="padding:4px;"></td></tr>'
    '<tr><td style="padding:4px;">Severidad alta</td><td style="padding:4px;">4</td>'
    '<td style="padding:4px;">Alta probabilidad</td><td style="padding:4px;">4</td>'
    '<td style="padding:4px;">Muy baja probabilidad</td><td style="padding:4px;">4</td>'
    '<td style="padding:4px;">No existe riesgo</td><td style="padding:4px;">0</td>'
    '<td style="padding:4px;">N/A</td><td style="padding:4px;"></td>'
    '<td style="padding:4px;"></td><td style="padding:4px;"></td></tr>'
    '<tr><td style="padding:4px;">Severidad muy alta</td><td style="padding:4px;">5</td>'
    '<td style="padding:4px;">Muy alta probabilidad</td><td style="padding:4px;">5</td>'
    '<td style="padding:4px;">Altamente improbable</td><td style="padding:4px;">5</td>'
    '<td style="padding:4px;"></td><td style="padding:4px;"></td>'
    '<td style="padding:4px;"></td><td style="padding:4px;"></td>'
    '<td style="padding:4px;"></td><td style="padding:4px;"></td></tr>'
    '</table>'
)

nuevo_anexos = (
    hdr(1) + f'<p>{img_tag(img1, "Anexo 1")}</p>'
    + hdr(2) + f'<p>{img_tag(img2, "Anexo 2")}</p>'
    + hdr(3) + tabla_anexo3
    + hdr(4) + f'<p>{img_tag(img3, "Anexo 4")}</p>'
)

doc = env['amunet.documento'].search([('codigo', '=', 'PNOGE-009')], limit=1)
doc.write({'seccion_anexos': nuevo_anexos})
env.cr.commit()
print('OK — imágenes agregadas a Anexos 1, 2 y 4 de PNOGE-009')
