import os, re, zipfile, html as html_mod
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
BASE = '/tmp/pnocc'

DOCS = {
    'PNOCC-001': ('PNOCC-001.docx', 'CC', 'PRODUCTO NO CONFORME / FUERA DE ESPECIFICACIONES'),
    'PNOCC-002': ('PNOCC-002.docx', 'CC', 'INSPECCIÓN DE INSUMOS'),
    'PNOCC-003': ('PNOCC-003.docx', 'CC', 'RE-ANÁLISIS DE MATERIA PRIMA'),
    'PNOCC-004': ('PNOCC-004.docx', 'CC', 'INSPECCIÓN Y LIBERACIÓN DE PRODUCTO A GRANEL Y TERMINADO'),
    'PNOCC-005': ('PNOCC-005.docx', 'CC', 'MÉTODO DE MUESTREO DE ACUERDO A LA NORMA ANSI'),
    'PNOCC-006': ('PNOCC-006.docx', 'CC', 'LIMPIEZA DEL ÁREA DE CONTROL DE CALIDAD'),
    'PNOCC-007': ('PNOCC-007.docx', 'CC', 'ASEGURAMIENTO DE TRAZABILIDAD'),
    'PNOCC-008': ('PNOCC-008.docx', 'CC', 'INSPECCIÓN DE REACTIVOS'),
    'PNOCC-009': ('PNOCC-009.docx', 'CC', 'CONTROL DE TEMPERATURA Y HUMEDAD'),
}

MESES = {'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,'sep':9,'oct':10,'nov':11,'dic':12}

def parse_iso(s):
    s = (s or '').strip()
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s): return s
    m = re.match(r'^([A-Za-záéíóúñ]+)[\.\s]+(\d{4})$', s)
    if m:
        mes = MESES.get(m.group(1)[:3].lower())
        if mes: return f'{m.group(2)}-{mes:02d}-01'
    return None

def get_header_vals(zf):
    headers = sorted(n for n in zf.namelist() if n.startswith('word/header') and n.endswith('.xml'))
    texts = []
    for h in headers:
        root = ET.fromstring(zf.read(h))
        for para in root.findall('.//w:p', NS):
            t = ''.join(r.text or '' for r in para.findall('.//w:t', NS)).strip()
            if t: texts.append(t)
    version = fe = fv = ''
    for i, t in enumerate(texts):
        tl = t.lower()
        nxt = texts[i+1] if i+1 < len(texts) else ''
        if re.match(r'^\d{2}$', t) and not version: version = t
        if re.search(r'vigente\s+a\s+partir', tl):
            after = re.split(r':\s*', t, 1)
            cand = after[1].strip() if len(after)>1 and after[1].strip() else nxt
            fe = parse_iso(cand) or ''
        if re.search(r'pr[oó]xima\s+revis', tl):
            after = re.split(r':\s*', t, 1)
            cand = after[1].strip() if len(after)>1 and after[1].strip() else nxt
            fv = parse_iso(cand) or ''
    return version or '01', fe or '2024-07-01', fv or '2026-07-01'

# ── Helpers HTML ─────────────────────────────────────────────────────────────
def run_to_html(r):
    rpr = r.find('w:rPr', NS)
    text = html_mod.escape(''.join((t.text or '') for t in r.findall('w:t', NS)))
    if not text: return ''
    if rpr is not None:
        if rpr.find('w:b', NS) is not None: text = f'<strong>{text}</strong>'
        if rpr.find('w:i', NS) is not None: text = f'<em>{text}</em>'
    return text

def para_to_html(p):
    runs = ''.join(run_to_html(r) for r in p.findall('.//w:r', NS))
    if not runs.strip(): return ''
    ppr = p.find('w:pPr', NS)
    if ppr is not None and ppr.find('w:numPr', NS) is not None:
        return f'<li>{runs}</li>'
    return f'<p>{runs}</p>'

def table_to_html(tbl):
    rows = tbl.findall('w:tr', NS)
    if not rows: return ''
    html_rows = []
    for i, row in enumerate(rows):
        cells = row.findall('w:tc', NS)
        tag = 'th' if i == 0 else 'td'
        cell_html = ''.join(
            f'<{tag} style="padding:4px;">' +
            ' '.join(''.join(run_to_html(r) for r in p.findall('.//w:r', NS)) for p in cell.findall('.//w:p', NS)).strip() +
            f'</{tag}>'
            for cell in cells
        )
        html_rows.append(f'<tr>{cell_html}</tr>')
    return '<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">' + ''.join(html_rows) + '</table>'

def para_text(p):
    return ''.join(t.text or '' for t in p.findall('.//w:t', NS)).strip()

# ── Parsers ───────────────────────────────────────────────────────────────────
SECTION_MAP = {
    'OBJETIVO': 'seccion_objetivo',
    'ALCANCE': 'seccion_alcance',
    'RESPONSABILIDADES': 'seccion_responsabilidades',
    'TÉRMINOS Y DEFINICIONES': 'seccion_terminos_definiciones',
    'TERMINOS Y DEFINICIONES': 'seccion_terminos_definiciones',
    'CONDICIONES GENERALES': 'seccion_condiciones_generales',
    'FORMATOS DERIVADOS': 'seccion_formatos_derivados',
    'REFERENCIAS BIBLIOGRÁFICAS': 'seccion_referencias',
    'REFERENCIAS BIBLIOGRAFICAS': 'seccion_referencias',
    'ANEXOS': 'seccion_anexos',
}
END_SECTIONS = {'CONTROL DE CAMBIOS', 'FIRMAS DE CONOCIMIENTO', 'DESARROLLO DEL PROCESO'}

def extract_all(zf):
    root = ET.fromstring(zf.read('word/document.xml'))
    body = root.find('.//w:body', NS)
    children = list(body)

    sections = {}
    actividades = []
    responsabilidades = []
    terminos = []
    historial = []

    current_field = None
    current_buf = []
    in_list = False
    in_actividades = False

    def flush_section():
        nonlocal in_list, current_buf
        if in_list:
            current_buf.append('</ul>')
            in_list = False
        if current_field and current_buf:
            sections[current_field] = ''.join(current_buf).strip()

    # ── Actividades from tables ──────────────────────────────────────────────
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2: continue
        header_text = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if not any(k in header_text for k in ('ACTIVIDAD','DESCRIPCI','RESPONSABLE','PASO')): continue
        col_headers = [''.join(t.text or '' for t in cell.findall('.//w:t', NS)).upper()
                       for cell in rows[0].findall('w:tc', NS)]
        idx_act = next((i for i,h in enumerate(col_headers) if 'ACTIVIDAD' in h or 'PASO' in h), 0)
        idx_desc = next((i for i,h in enumerate(col_headers) if 'DESCRIPCI' in h or 'PROCEDIM' in h), 1)
        idx_resp = next((i for i,h in enumerate(col_headers) if 'RESPONSABLE' in h), -1)
        idx_reg  = next((i for i,h in enumerate(col_headers) if 'REGISTRO' in h or 'EVIDENCIA' in h), -1)
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            def ch(idx):
                if idx<0 or idx>=len(cells): return ''
                return '<br/>'.join(filter(None, [para_to_html(p) for p in cells[idx].findall('w:p', NS)]))
            act, desc = ch(idx_act), ch(idx_desc)
            if act or desc:
                actividades.append({'actividad':act,'descripcion':desc,'responsable':ch(idx_resp),'registro':ch(idx_reg)})

    # ── Responsabilidades & Términos from tables ─────────────────────────────
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if not rows: continue
        header_text = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if any(k in header_text for k in ('RESPONSABILIDAD','ROL','PUESTO')):
            for row in rows[1:]:
                cells = row.findall('w:tc', NS)
                if len(cells) >= 2:
                    rol = ''.join(t.text or '' for t in cells[0].findall('.//w:t', NS)).strip()
                    desc = ''.join(t.text or '' for t in cells[1].findall('.//w:t', NS)).strip()
                    if rol: responsabilidades.append({'rol':rol,'descripcion':desc})
        elif any(k in header_text for k in ('TÉRMINO','TERMINO','CONCEPTO','DEFINICI','GLOSARIO')):
            for row in rows[1:]:
                cells = row.findall('w:tc', NS)
                if len(cells) >= 2:
                    concepto = ''.join(t.text or '' for t in cells[0].findall('.//w:t', NS)).strip()
                    definicion = ''.join(t.text or '' for t in cells[1].findall('.//w:t', NS)).strip()
                    if concepto: terminos.append({'concepto':concepto,'definicion':definicion})

    # ── Responsabilidades párrafo (De/Del...) si no hay tabla ────────────────
    if not responsabilidades:
        all_texts = [''.join(t.text or '' for t in p.findall('.//w:t', NS)).strip()
                     for p in root.findall('.//w:p', NS)]
        start = next((i+1 for i,t in enumerate(all_texts) if t == 'RESPONSABILIDADES'), None)
        if start:
            ROL_RE = re.compile(r'^(De |Del |De la )', re.I)
            STOP = re.compile(r'^(TÉRMINOS|TERMINOS|CONDICIONES|OBJETIVO|ALCANCE)', re.I)
            current_rol = current_desc_list = None
            for t in all_texts[start:]:
                if STOP.match(t): break
                if not t: continue
                is_rol = ROL_RE.match(t) and len(t) <= 60
                if is_rol:
                    if current_rol:
                        responsabilidades.append({'rol':current_rol,'descripcion':' '.join(current_desc_list)})
                    current_rol = t; current_desc_list = []
                elif current_rol:
                    current_desc_list.append(t)
                elif ROL_RE.match(t):  # línea larga De/Del = rol+desc juntos
                    parts = re.split(r',\s*', t, 1)
                    responsabilidades.append({'rol':parts[0],'descripcion':parts[1] if len(parts)>1 else ''})
            if current_rol:
                responsabilidades.append({'rol':current_rol,'descripcion':' '.join(current_desc_list)})

    # ── Historial de versiones ───────────────────────────────────────────────
    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if not rows: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if 'VERSIÓN' not in hdr and 'VERSION' not in hdr: continue
        if 'DESCRIPCIÓN' not in hdr and 'DESCRIPCION' not in hdr: continue
        col_h = [''.join(t.text or '' for t in c.findall('.//w:t', NS)).upper() for c in rows[0].findall('w:tc', NS)]
        iv = next((i for i,h in enumerate(col_h) if 'VERSIÓN' in h or 'VERSION' in h), 0)
        id_ = next((i for i,h in enumerate(col_h) if 'DESCRIPCIÓN' in h or 'DESCRIPCION' in h), 2)
        ij = next((i for i,h in enumerate(col_h) if 'JUSTIFIC' in h), -1)
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            def ct(idx): return ''.join(t.text or '' for t in cells[idx].findall('.//w:t', NS)).strip() if 0<=idx<len(cells) else ''
            ver = ct(iv)
            if re.match(r'^\d', ver):
                historial.append({'version':ver.zfill(2),'descripcion':ct(id_),'justificacion':ct(ij)})
        break

    # ── Secciones de texto ───────────────────────────────────────────────────
    for child in children:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            text = para_text(child)
            text_upper = text.upper()
            matched_field = SECTION_MAP.get(text_upper)
            if matched_field:
                flush_section(); current_field = matched_field; current_buf = []; in_list = False; continue
            if text_upper in END_SECTIONS:
                flush_section(); current_field = None; current_buf = []; in_list = False; continue
            if current_field is None: continue
            h = para_to_html(child)
            if not h: continue
            if h.startswith('<li>'):
                if not in_list: current_buf.append('<ul>'); in_list = True
                current_buf.append(h)
            else:
                if in_list: current_buf.append('</ul>'); in_list = False
                current_buf.append(h)
        elif tag == 'tbl':
            if current_field is None: continue
            if in_list: current_buf.append('</ul>'); in_list = False
            th = table_to_html(child)
            if th: current_buf.append(th)
    flush_section()

    return sections, actividades, responsabilidades, terminos, historial


# ── Migración ─────────────────────────────────────────────────────────────────
DocModel  = env['amunet.documento']
ActModel  = env['amunet.documento.actividad']
RespModel = env['amunet.documento.responsabilidad']
TermModel = env['amunet.documento.termino']
VerModel  = env['amunet.documento.version']

for codigo, (fname, area, titulo) in DOCS.items():
    if DocModel.search([('codigo','=',codigo)]):
        print(f'YA EXISTE {codigo}, omitiendo'); continue

    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f'FALTA: {path}'); continue

    with zipfile.ZipFile(path) as zf:
        version, fe, fv = get_header_vals(zf)
        sections, actividades, responsabilidades, terminos, historial = extract_all(zf)

    doc = DocModel.create({
        'codigo': codigo, 'name': titulo, 'tipo': 'pno', 'area': area,
        'version_actual': version, 'state': 'borrador',
        'elabora_id': 1, 'company_id': 1,
        'fecha_emision': fe, 'fecha_vigencia': fv,
        **sections,
    })

    for seq, a in enumerate(actividades, 1):
        ActModel.create({'documento_id':doc.id,'sequence':seq,**a})
    for seq, r in enumerate(responsabilidades, 1):
        RespModel.create({'documento_id':doc.id,'sequence':seq,**r})
    for seq, t in enumerate(terminos, 1):
        TermModel.create({'documento_id':doc.id,'sequence':seq,**t})

    version_actual = version
    for h in historial:
        state_h = 'vigente' if h['version'] == version_actual else 'obsoleto'
        VerModel.create({
            'documento_id':doc.id,'version':h['version'],
            'fecha':'2024-01-01','cambios':h['descripcion'] or 'Ver documento',
            'descripcion_cambio':h['descripcion'],'justificacion':h['justificacion'],
            'state_historico':state_h,
        })

    env.cr.commit()
    secciones_ok = [k.replace('seccion_','') for k in sections if sections.get(k)]
    print(f'OK {codigo} | v{version} | {len(actividades)} acts | {len(responsabilidades)} resp | {len(terminos)} terms | {len(historial)} hist | secs: {len(secciones_ok)}')

print('DONE')
