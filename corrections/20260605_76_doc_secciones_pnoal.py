import os, re, zipfile, html as html_mod
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
BASE = '/tmp/pnoal'

DOCS = [
    'PNOAL-001','PNOAL-002','PNOAL-003','PNOAL-004','PNOAL-005',
    'PNOAL-006','PNOAL-007','PNOAL-008','PNOAL-010','PNOAL-011',
]

# Mapa de encabezados del cuerpo → campo Odoo
SECTION_MAP = {
    'OBJETIVO':                  'seccion_objetivo',
    'ALCANCE':                   'seccion_alcance',
    'RESPONSABILIDADES':         'seccion_responsabilidades',
    'TÉRMINOS Y DEFINICIONES':   'seccion_terminos_definiciones',
    'TERMINOS Y DEFINICIONES':   'seccion_terminos_definiciones',
    'CONDICIONES GENERALES':     'seccion_condiciones_generales',
    'FORMATOS DERIVADOS':        'seccion_formatos_derivados',
    'REFERENCIAS BIBLIOGRÁFICAS':'seccion_referencias',
    'REFERENCIAS BIBLIOGRAFICAS':'seccion_referencias',
    'ANEXOS':                    'seccion_anexos',
}

# Secciones que marcan el fin de contenido que nos importa
END_SECTIONS = {'CONTROL DE CAMBIOS', 'FIRMAS DE CONOCIMIENTO', 'DESARROLLO DEL PROCESO'}


def run_to_html(r):
    rpr = r.find('w:rPr', NS)
    text = html_mod.escape(''.join((t.text or '') for t in r.findall('w:t', NS)))
    if not text:
        return ''
    if rpr is not None:
        if rpr.find('w:b', NS) is not None and rpr.find('w:bCs', NS) is None:
            text = f'<strong>{text}</strong>'
        if rpr.find('w:i', NS) is not None:
            text = f'<em>{text}</em>'
    return text


def para_to_html(p):
    runs = ''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
    if not runs.strip():
        return ''
    # Detectar si es item de lista
    ppr = p.find('w:pPr', NS)
    if ppr is not None and ppr.find('w:numPr', NS) is not None:
        return f'<li>{runs}</li>'
    return f'<p>{runs}</p>'


def table_to_html(tbl):
    rows = tbl.findall('w:tr', NS)
    if not rows:
        return ''
    html_rows = []
    for i, row in enumerate(rows):
        cells = row.findall('w:tc', NS)
        tag = 'th' if i == 0 else 'td'
        cell_html = ''.join(
            f'<{tag} style="padding:4px;">' +
            ' '.join(
                ''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
                for p in cell.findall('.//w:p', NS)
            ).strip() +
            f'</{tag}>'
            for cell in cells
        )
        html_rows.append(f'<tr>{cell_html}</tr>')
    return (
        '<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">'
        + ''.join(html_rows) + '</table>'
    )


def extract_sections(path):
    with zipfile.ZipFile(path) as zf:
        root = ET.fromstring(zf.read('word/document.xml'))

    body = root.find('.//w:body', NS)
    children = list(body)

    sections = {}
    current_field = None
    current_buf = []
    in_list = False

    def flush():
        nonlocal in_list, current_buf
        if in_list:
            current_buf.append('</ul>')
            in_list = False
        if current_field and current_buf:
            sections[current_field] = ''.join(current_buf).strip()

    for child in children:
        tag = child.tag.split('}')[-1]

        if tag == 'p':
            text = ''.join(t.text or '' for t in child.findall('.//w:t', NS)).strip()
            text_upper = text.upper()

            # ¿Es encabezado de sección?
            matched_field = SECTION_MAP.get(text_upper)
            if matched_field:
                flush()
                current_field = matched_field
                current_buf = []
                in_list = False
                continue

            if text_upper in END_SECTIONS:
                flush()
                current_field = None
                current_buf = []
                in_list = False
                continue

            if current_field is None:
                continue

            h = para_to_html(child)
            if not h:
                continue

            if h.startswith('<li>'):
                if not in_list:
                    current_buf.append('<ul>')
                    in_list = True
                current_buf.append(h)
            else:
                if in_list:
                    current_buf.append('</ul>')
                    in_list = False
                current_buf.append(h)

        elif tag == 'tbl':
            if current_field is None:
                continue
            if in_list:
                current_buf.append('</ul>')
                in_list = False
            th = table_to_html(child)
            if th:
                current_buf.append(th)

    flush()
    return sections


DocModel = env['amunet.documento']

for codigo in DOCS:
    doc = DocModel.search([('codigo', '=', codigo)], limit=1)
    if not doc:
        print(f'NO ENCONTRADO: {codigo}')
        continue

    path = os.path.join(BASE, f'{codigo}.docx')
    if not os.path.exists(path):
        print(f'FALTA DOCX: {path}')
        continue

    try:
        sections = extract_sections(path)
    except Exception as e:
        print(f'ERROR {codigo}: {e}')
        continue

    if sections:
        doc.write(sections)
        env.cr.commit()
        filled = [k.replace('seccion_','') for k in sections if sections[k]]
        print(f'OK {codigo} | secciones: {", ".join(filled)}')
    else:
        print(f'SIN SECCIONES {codigo}')

print('DONE')
