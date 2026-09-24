# Goteros: nombres, notas y proveedores segun el archivo que devolvio Mery
# (Goteros_2026-09-24 MAOV.xlsx, subido a Discuss el 24-sep-2026 18:44).
#
# Tres cosas que pidio:
#  1. El nombre debe ser IGUAL en espanol y en ingles. Habia productos con un
#     nombre distinto por idioma (STGOT02 decia "Gotero de 5 ul" en es y
#     "Gotero capilar chico punta larga" en en) y eso impedia mapearlos.
#  2. Lo que antes vivia en el nombre en ingles pasa a ser NOTA. Se guarda en
#     product.template.description (Notas internas), campo NATIVO de Odoo que
#     ya usan 294 productos. No sale en ningun documento: ni orden de compra,
#     ni cotizacion, ni recepcion. Se escribe en los dos idiomas porque el
#     campo tambien es traducible.
#  3. Proveedores: quedan solo los verdaderos. Las claves de Tongzhou venian
#     juntas en una celda ("ORF-322, IZIC-425"); se separan en un renglon por
#     kit, que es como ya estaba STGOT01. Odoo lee product_code como UNA clave:
#     si se deja pegada, la orden sale pidiendo un codigo que no existe.
#
# STTCC01: solo se le quita el proveedor. No se usa en ninguna prueba que se
# fabrique, asi que no se contempla en el resto del trabajo.

SF = 'Cangzhou ShengFeng Plastic Product Co., Ltd.'
TZ = 'Hangzhou Tongzhou Biotechnology Co., Ltd.'

# clave: (nombre, nota, [(proveedor, codigo, nombre_de_ellos), ...])
PLAN = {
 'STGOT01': ('Gotero capilar', '', [
     (SF, 'DG013', 'DG013 / Transfer pipette XC-4, clear color, 10ul')]),
 'STGOT02': ('Gotero de 5 ul', 'Gotero capilar chico punta larga', [
     (TZ, 'ORF-322',  'Dropper for ORF-322'),
     (TZ, 'IZIC-425', '5uL dropper for IZIC-425')]),
 'STGOT03': ('Gotero de 20 ul', 'Gotero capilar grande punta larga', [
     (TZ, 'ITOGM-445', 'Dropper for ITOGM-445'),
     (TZ, 'IMO-422',   'Dropper for IMO-422')]),
 'STGOT04': ('Gotero de 25 µl', '', [
     (SF, 'DG005',   'DG005 / Transfer pipette AD-5, clear color, 25ul, 80mm'),
     (TZ, 'ITB-422', 'Dropper for ITB-422')]),
 'STGOT05': ('Gotero general de 40 µl', '', [
     (TZ, 'IGL-622', 'Dropper for IGL-622'),
     (SF, 'DG049',   'DG049 / Transfer pipette 0.3ml, clear color, 40ul, 75mm')]),
 'STGOT06': ('Gotero Antidoping SSP', 'Gotero Antidoping SSP tipo popote', [
     (TZ, 'DOA-455', '40ul Dropper for DOA-455')]),
 'STGOT07': ('Gotero con capilar', 'Gotero con capilar y marca a 20uL', [
     (TZ, 'OVD-422', 'Dropper for OVD-422')]),
 'STTCC01': (None, None, []),   # solo se le quitan los proveedores
}

T = env['product.template']
S = env['product.supplierinfo']
socios = {}
for n in (SF, TZ):
    p = env['res.partner'].search([('name', '=', n)], limit=1)
    assert p, 'no existe el proveedor %s' % n
    socios[n] = p

print('=== LO QUE SE BORRA (queda respaldado aqui por si hay que reponerlo) ===')
borrados = []
for clave in PLAN:
    t = T.search([('default_code', '=', clave)], limit=1)
    assert t, 'no existe %s' % clave
    for si in S.search([('product_tmpl_id', '=', t.id)]):
        borrados.append((clave, si.partner_id.name, si.product_code or '', si.product_name or ''))
        print('  - %-9s %-44s %-18s %s'
              % (clave, si.partner_id.name[:44], si.product_code or '(sin clave)',
                 (si.product_name or '')[:46]))
        si.unlink()

print('\n=== NOMBRES (se escriben en los DOS idiomas) ===')
for clave, (nombre, nota, _) in PLAN.items():
    if nombre is None:
        continue
    t = T.search([('default_code', '=', clave)], limit=1)
    antes_es = t.with_context(lang='es_MX').name
    antes_en = t.with_context(lang='en_US').name
    t.with_context(lang='es_MX').name = nombre
    t.with_context(lang='en_US').name = nombre
    cambio = '' if (antes_es == antes_en == nombre) else '   <-- cambio'
    print('  %-9s %r%s' % (clave, nombre, cambio))
    if antes_es != antes_en:
        print('            antes es=%r  en=%r' % (antes_es, antes_en))

print('\n=== NOTAS en description (Notas internas, no sale en documentos) ===')
for clave, (nombre, nota, _) in PLAN.items():
    if not nota:
        continue
    t = T.search([('default_code', '=', clave)], limit=1)
    html = '<p>%s</p>' % nota
    t.with_context(lang='es_MX').description = html
    t.with_context(lang='en_US').description = html
    print('  %-9s %r' % (clave, nota))

print('\n=== PROVEEDORES QUE QUEDAN ===')
for clave, (_, _, provs) in PLAN.items():
    t = T.search([('default_code', '=', clave)], limit=1)
    if not provs:
        print('  %-9s (sin proveedor)' % clave)
        continue
    for i, (prov, cod, nom) in enumerate(provs, 1):
        S.create({'product_tmpl_id': t.id, 'partner_id': socios[prov].id,
                  'sequence': i, 'product_code': cod, 'product_name': nom})
        print('  + %-9s %-2s %-44s %-12s %s' % (clave, i, prov[:44], cod, nom[:44]))

env.cr.commit()

print('\n=== VERIFICACION SOBRE LA BASE ===')
for clave in sorted(PLAN):
    t = T.search([('default_code', '=', clave)], limit=1)
    es = t.with_context(lang='es_MX').name
    en = t.with_context(lang='en_US').name
    nota = (t.with_context(lang='es_MX').description or '').replace('<p>', '').replace('</p>', '')
    n = S.search_count([('product_tmpl_id', '=', t.id)])
    print('  %-9s igual=%-3s  %-26s  provs=%-2s  nota=%r'
          % (clave, 'si' if es == en else 'NO', es, n, nota))
print('\nrenglones borrados: %s   creados: %s'
      % (len(borrados), sum(len(v[2]) for v in PLAN.values())))
