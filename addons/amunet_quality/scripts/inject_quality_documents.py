import re
import json
import logging

_logger = logging.getLogger(__name__)

def parse_spanish_date(date_str):
    """
    Convierte 'Ago.2025' → '2025-08-01' para Odoo Date forest
    """
    months = {
        'Ene': 1, 'Feb': 2, 'Mar': 3, 'Abr': 4,
        'May': 5, 'Jun': 6, 'Jul': 7, 'Ago': 8,
        'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dic': 12
    }
    date_str = date_str.replace('.', ' ')
    parts = date_str.split()
    
    if len(parts) == 2:
        month_abbr, year = parts
        month = months.get(month_abbr, 1)
        # Odoo fields.Date expected string format 'YYYY-MM-DD'
        return f"{year}-{month:02d}-01"
    return False

def extract_table_data(text, section_title):
    data = {}
    section_match = re.search(rf'{section_title}.*?(?=####|\Z)', text, re.DOTALL)
    if not section_match:
        return data
        
    section_text = section_match.group(0)
    
    code_match = re.search(r'\|\s*\*\*Código\*\*\s*\|\s*([^|\n]+)\s*\|', section_text)
    elaboracion_match = re.search(r'\|\s*\*\*Fecha de Elaboración\*\*\s*\|\s*([^|\n]+)\s*\|', section_text)
    vigencia_match = re.search(r'\|\s*\*\*Fecha de Vigencia\*\*\s*\|\s*([^|\n]+)\s*\|', section_text)
    version_match = re.search(r'\|\s*\*\*Versión\*\*\s*\|\s*([^|\n]+)\s*\|', section_text)
    sustituye_match = re.search(r'\|\s*\*\*Sustituye\*\*\s*\|\s*([^|\n]+)\s*\|', section_text)
    
    if code_match:
        c = code_match.group(1).strip()
        if c: data['code'] = c
    if elaboracion_match:
        e = elaboracion_match.group(1).strip()
        if e: data['effective_date'] = parse_spanish_date(e)
    if vigencia_match:
        v_date = vigencia_match.group(1).strip()
        if v_date: data['expiry_date'] = parse_spanish_date(v_date)
    if version_match:
        v = version_match.group(1).strip()
        if v and v != '-': data['version'] = int(float(v))
    if sustituye_match:
        sv = sustituye_match.group(1).strip()
        if sv and sv != '-': data['replaces_version'] = int(float(sv))
    
    return data

def extract_references(text):
    ref_match = re.search(r'\*\*Referencias.*?\*\*.*?\n```[a-z]*\n(.*?)\n```', text, re.DOTALL)
    if ref_match:
        return ref_match.group(1).strip()
    return ""

def parse_markdown(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    products = {}
    product_sections = re.split(r'### Producto:\s*', content)
    
    for section in product_sections[1:]:
        lines = section.split('\n')
        product_code = lines[0].strip()
        
        report_data = extract_table_data(section, r'#### 📋 Reporte de Análisis')
        cert_data = extract_table_data(section, r'#### 📜 Certificado de Análisis')
        references = extract_references(section)
        
        if product_code:
            products[product_code] = {
                'report': report_data,
                'cert': cert_data,
                'references': references
            }
            
    return products

def inject_in_odoo(env, parsed_data, target_products=None):
    count_updated = 0
    count_not_found = 0
    
    for code, data in parsed_data.items():
        if target_products and code not in target_products:
            continue
            
        print(f"Buscando producto: {code}")
        # Intentar buscar por Ref interna primero
        templates = env['product.template'].search([('default_code', '=', code)])
        
        if not templates:
            print(f"  [!] Producto {code} no encontrado por Referencia Interna.")
            count_not_found += 1
            continue
            
        for template in templates:
            vals = {}
            
            # Reporte
            r_data = data.get('report', {})
            if 'code' in r_data: vals['report_document_code'] = r_data['code']
            if 'effective_date' in r_data and r_data['effective_date']: vals['report_effective_date'] = r_data['effective_date']
            if 'expiry_date' in r_data and r_data['expiry_date']: vals['report_expiry_date'] = r_data['expiry_date']
            if 'version' in r_data: vals['report_version'] = r_data['version']
            if 'replaces_version' in r_data: vals['report_replaces_version'] = r_data['replaces_version']
            
            if data.get('references'):
                vals['report_references'] = data['references']
                
            # Certificado
            c_data = data.get('cert', {})
            if 'code' in c_data: vals['certificate_document_code'] = c_data['code']
            if 'effective_date' in c_data and c_data['effective_date']: vals['certificate_effective_date'] = c_data['effective_date']
            if 'expiry_date' in c_data and c_data['expiry_date']: vals['certificate_expiry_date'] = c_data['expiry_date']
            if 'version' in c_data: vals['certificate_version'] = c_data['version']
            if 'replaces_version' in c_data: vals['certificate_replaces_version'] = c_data['replaces_version']
            
            if vals:
                try:
                    template.write(vals)
                    print(f"  [\u2713] Producto {code} (ID: {template.id}) actualizado correctamente con: {vals}")
                    count_updated += 1
                except Exception as e:
                    print(f"  [X] Error actualizando {code} (ID: {template.id}): {e}")
                    
    print(f"\nResumen: {count_updated} actualizados, {count_not_found} no encontrados.")
    if count_updated > 0:
        env.cr.commit()
        print("Cambios confirmados (commit).")
    else:
        env.cr.rollback()

if __name__ == '__main__':
    # El script se debe ejecutar con odoo-bin shell
    # env está inyectado por Odoo
    if 'env' in locals():
        file_path = r'/mnt/extra-addons/amunet_quality/quality documents/Catálogos/catalogo_documentos_calidad.md'
        print("Parseando el catálogo...")
        parsed_data = parse_markdown(file_path)
        
        print("Iniciando inyección de datos para todo el catálogo...")
        inject_in_odoo(env, parsed_data)
    else:
        print("Por favor, ejecuta este script desde odoo-bin shell.")
