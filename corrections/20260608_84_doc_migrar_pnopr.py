import os, re, zipfile, html as html_mod
import xml.etree.ElementTree as ET

env = env  # noqa

NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
BASE = '/tmp/pnopr'

DOCS = {
    'PNOPR-001': ('PNOPR-001.docx', 'PR', 'DESPEJE DEL ÁREA O LÍNEA DE FABRICACIÓN'),
    'PNOPR-002': ('PNOPR-002.docx', 'PR', 'ORDEN DE PRODUCCIÓN, LOTIFICADO Y ACONDICIONADO'),
    'PNOPR-003': ('PNOPR-003.docx', 'PR', 'LIMPIEZA DEL ÁREA DE PRODUCCIÓN'),
    'PNOPR-004': ('PNOPR-004.docx', 'PR', 'ENTRADA DE INSUMOS A LAS ÁREAS DE PRODUCCIÓN'),
    'PNOPR-005': ('PNOPR-005.docx', 'PR', 'MANTENIMIENTO DURANTE LA FABRICACIÓN Y USO DE COMPONENTES'),
    'PNOPR-006': ('PNOPR-006.docx', 'PR', 'PREPARACIÓN DE SOLUCIONES GENERALES'),
    'PNOPR-007': ('PNOPR-007.docx', 'PR', 'CONTROL DE TEMPERATURA Y HUMEDAD'),
}

MESES = {'ene':1,'feb':2,'mar':3,'abr':4,'may':5,'jun':6,'jul':7,'ago':8,'sep':9,'oct':10,'nov':11,'dic':12}

def parse_iso(s):
    s = (s or '').strip().replace('\xa0', ' ')
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
    version = fe = fv = sustituye = ''
    for i, t in enumerate(texts):
        tl = t.lower(); nxt = texts[i+1] if i+1 < len(texts) else ''
        if re.match(r'^\d{2}$', t) and not version: version = t
        if re.search(r'sustituye\s+a', tl):
            after = re.split(r':\s*', t, 1)
            cand = after[1].strip() if len(after)>1 and after[1].strip() else nxt
            if re.match(r'^\d{1,3}$', cand): sustituye = cand.zfill(2)
        if re.search(r'vigente\s+a\s+partir', tl):
            after = re.split(r':\s*', t, 1)
            cand = after[1].strip() if len(after)>1 and after[1].strip() else nxt
            fe = parse_iso(cand) or ''
        if re.search(r'pr[oó]xima\s+revis', tl):
            after = re.split(r':\s*', t, 1)
            cand = after[1].strip() if len(after)>1 and after[1].strip() else nxt
            fv = parse_iso(cand) or ''
    return version or '01', fe or '2024-07-01', fv or '2026-07-01', sustituye

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
    if ppr is not None and ppr.find('w:numPr', NS) is not None: return f'<li>{runs}</li>'
    return f'<p>{runs}</p>'

def table_to_html(tbl):
    rows = tbl.findall('w:tr', NS)
    if not rows: return ''
    html_rows = []
    for i, row in enumerate(rows):
        cells = row.findall('w:tc', NS); tag = 'th' if i == 0 else 'td'
        html_rows.append('<tr>' + ''.join(
            f'<{tag} style="padding:4px;">' +
            ' '.join(''.join(run_to_html(r) for r in p.findall('.//w:r', NS)) for p in cell.findall('.//w:p', NS)).strip() +
            f'</{tag}>' for cell in cells) + '</tr>')
    return '<table border="1" style="width:100%;border-collapse:collapse;font-size:inherit;">' + ''.join(html_rows) + '</table>'

def cell_to_html(cell):
    result = []; in_list = False
    for child in cell:
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            h = para_to_html(child)
            if not h: continue
            if h.startswith('<li>'):
                if not in_list: result.append('<ul>'); in_list = True
                result.append(h)
            else:
                if in_list: result.append('</ul>'); in_list = False
                result.append(h)
        elif tag == 'tbl':
            if in_list: result.append('</ul>'); in_list = False
            th = table_to_html(child)
            if th: result.append(th)
    if in_list: result.append('</ul>')
    return ''.join(result)

def cell_plain(cell):
    return ''.join(t.text or '' for t in cell.findall('.//w:t', NS)).strip()

def para_text(p):
    return ''.join(t.text or '' for t in p.findall('.//w:t', NS)).strip()

SECTION_MAP = {
    'OBJETIVO': 'seccion_objetivo', 'ALCANCE': 'seccion_alcance',
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
    sections = {}; actividades = []; responsabilidades = []; terminos = []; historial = []
    current_field = None; current_buf = []; in_list = False

    def flush():
        nonlocal in_list, current_buf
        if in_list: current_buf.append('</ul>'); in_list = False
        if current_field and current_buf:
            sections[current_field] = ''.join(current_buf).strip()

    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if len(rows) < 2: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if 'VERSIÓN' in hdr or 'VERSION' in hdr: continue
        if not any(k in hdr for k in ('ACTIVIDAD','DESCRIPCI','PASO')): continue
        col_hdrs = [''.join(t.text or '' for t in c.findall('.//w:t', NS)).upper() for c in rows[0].findall('w:tc', NS)]
        idx_act  = next((i for i,h in enumerate(col_hdrs) if 'ACTIVIDAD' in h or 'PASO' in h), 0)
        idx_desc = next((i for i,h in enumerate(col_hdrs) if 'DESCRIPCI' in h or 'PROCEDIM' in h), 1)
        idx_resp = next((i for i,h in enumerate(col_hdrs) if 'RESPONSABLE' in h), -1)
        idx_reg  = next((i for i,h in enumerate(col_hdrs) if 'REGISTRO' in h or 'EVIDENCIA' in h), -1)
        seq = 0
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            if not cells: continue
            def ch(idx):
                if idx < 0 or idx >= len(cells): return ''
                return cell_to_html(cells[idx])
            desc_html = ch(idx_desc)
            if not desc_html: continue
            act_text = cell_plain(cells[idx_act]) if idx_act < len(cells) else ''
            seq += 1
            actividades.append({'actividad': act_text if act_text else str(seq),
                                 'descripcion': desc_html, 'responsable': ch(idx_resp), 'registro': ch(idx_reg)})
        if actividades: break

    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if not rows: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if any(k in hdr for k in ('RESPONSABILIDAD','ROL','PUESTO')):
            for row in rows[1:]:
                cells = row.findall('w:tc', NS)
                if len(cells) >= 2:
                    rol = cell_plain(cells[0]); desc = cell_plain(cells[1])
                    if rol: responsabilidades.append({'rol':rol,'descripcion':desc})
        elif any(k in hdr for k in ('TÉRMINO','TERMINO','CONCEPTO','DEFINICI','GLOSARIO')):
            for row in rows[1:]:
                cells = row.findall('w:tc', NS)
                if len(cells) >= 2:
                    c = cell_plain(cells[0]); d = cell_plain(cells[1])
                    if c: terminos.append({'concepto':c,'definicion':d})

    if not responsabilidades:
        all_texts = [para_text(p) for p in root.findall('.//w:p', NS)]
        start = next((i+1 for i,t in enumerate(all_texts) if t == 'RESPONSABILIDADES'), None)
        if start:
            ROL_RE = re.compile(r'^(De |Del |De la )', re.I)
            STOP   = re.compile(r'^(TÉRMINOS|TERMINOS|CONDICIONES|OBJETIVO|ALCANCE)', re.I)
            cur_rol = cur_desc = None
            for t in all_texts[start:]:
                if STOP.match(t): break
                if not t: continue
                if ROL_RE.match(t) and len(t) <= 60:
                    if cur_rol: responsabilidades.append({'rol':cur_rol,'descripcion':' '.join(cur_desc)})
                    cur_rol = t; cur_desc = []
                elif cur_rol: cur_desc.append(t)
                elif ROL_RE.match(t):
                    parts = re.split(r',\s*', t, 1)
                    responsabilidades.append({'rol':parts[0],'descripcion':parts[1] if len(parts)>1 else ''})
            if cur_rol: responsabilidades.append({'rol':cur_rol,'descripcion':' '.join(cur_desc)})

    for tbl in root.findall('.//w:tbl', NS):
        rows = tbl.findall('w:tr', NS)
        if not rows: continue
        hdr = ''.join(t.text or '' for t in rows[0].findall('.//w:t', NS)).upper()
        if ('VERSIÓN' not in hdr and 'VERSION' not in hdr): continue
        if ('DESCRIPCIÓN' not in hdr and 'DESCRIPCION' not in hdr): continue
        col_h = [''.join(t.text or '' for t in c.findall('.//w:t', NS)).upper() for c in rows[0].findall('w:tc', NS)]
        iv  = next((i for i,h in enumerate(col_h) if 'VERSIÓN' in h or 'VERSION' in h), 0)
        id_ = next((i for i,h in enumerate(col_h) if 'DESCRIPCIÓN' in h or 'DESCRIPCION' in h), 2)
        ij  = next((i for i,h in enumerate(col_h) if 'JUSTIFIC' in h), -1)
        for row in rows[1:]:
            cells = row.findall('w:tc', NS)
            def ct(idx): return cell_plain(cells[idx]) if 0<=idx<len(cells) else ''
            ver = ct(iv)
            if re.match(r'^\d', ver):
                historial.append({'version':ver.zfill(2),'descripcion':ct(id_),'justificacion':ct(ij)})
        break

    for child in list(body):
        tag = child.tag.split('}')[-1]
        if tag == 'p':
            text = para_text(child); tu = text.upper()
            mf = SECTION_MAP.get(tu)
            if mf:
                flush(); current_field = mf; current_buf = []; in_list = False; continue
            if tu in END_SECTIONS:
                flush(); current_field = None; current_buf = []; in_list = False; continue
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
    flush()
    return sections, actividades, responsabilidades, terminos, historial

DocModel  = env['amunet.documento']
ActModel  = env['amunet.documento.actividad']
RespModel = env['amunet.documento.responsabilidad']
TermModel = env['amunet.documento.termino']
VerModel  = env['amunet.documento.version']

for codigo, (fname, area, titulo) in DOCS.items():
    if DocModel.search([('codigo','=',codigo)]):
        print(f'YA EXISTE {codigo}'); continue
    path = os.path.join(BASE, fname)
    if not os.path.exists(path):
        print(f'FALTA: {path}'); continue
    with zipfile.ZipFile(path) as zf:
        version, fe, fv, sustituye = get_header_vals(zf)
        sections, actividades, responsabilidades, terminos, historial = extract_all(zf)
    doc = DocModel.create({
        'codigo': codigo, 'name': titulo, 'tipo': 'pno', 'area': area,
        'version_actual': version, 'state': 'borrador',
        'elabora_id': 1, 'company_id': 1,
        'fecha_emision': fe, 'fecha_vigencia': fv,
        'sustituye_version': sustituye, **sections,
    })
    for seq, a in enumerate(actividades, 1): ActModel.create({'documento_id':doc.id,'sequence':seq,**a})
    for seq, r in enumerate(responsabilidades, 1): RespModel.create({'documento_id':doc.id,'sequence':seq,**r})
    for seq, t in enumerate(terminos, 1): TermModel.create({'documento_id':doc.id,'sequence':seq,**t})
    for h in historial:
        VerModel.create({'documento_id':doc.id,'version':h['version'],'fecha':'2024-01-01',
                         'cambios':h['descripcion'] or 'Ver documento',
                         'descripcion_cambio':h['descripcion'],'justificacion':h['justificacion'],
                         'state_historico':'vigente' if h['version']==version else 'obsoleto'})
    env.cr.commit()
    secs = [k.replace('seccion_','') for k in sections if sections.get(k)]
    print(f'OK {codigo} | v{version} | sust={sustituye} | fe={fe} | {len(actividades)} acts | {len(responsabilidades)} resp | {len(terminos)} terms | {len(historial)} hist | secs:{len(secs)}')

print('DONE')
