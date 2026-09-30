"""PTBWP01 y PTESP01: su folio de orden pasa al formato Amunet (MMAA/NN/ABR).

Pedido por Mery el 30-sep-2026: su orden de bolsas salio con el folio generico
AMP/MO/00039 en vez del folio de Amunet con las tres letras.

LA CAUSA: el folio Amunet lo da el campo mo_sequence_id del producto. Si lo tiene, create()
de mrp.production toma el folio de esa secuencia (formato MMAA/NN/ABR) en vez del generico
del tipo de operacion. PTBWP01 y PTESP01 no lo tenian, asi que cayeron en la secuencia
AMP/MO/ del almacen.

EL PATRON, copiado de los productos que ya lo usan:

    DMCRD01   prefijo "%(month)s%(y)s/"  sufijo "/CRD"  padding 2   ->  0926/01/CRD
    DLVPH01   prefijo "%(month)s%(y)s/"  sufijo "/VPL"  padding 2   ->  0926/01/VPL

Las tres letras las dio Mery: BWE para las bolsas Whirl-Pak. Para el kit de esponjas se
usa ESP, siguiendo el mismo criterio de tomarlas del producto.

El consecutivo se reinicia cada mes por _amunet_next_folio_mensual, que compara el periodo
guardado en la secuencia con el mes actual.

LA ORDEN QUE YA EXISTE se renombra: Mery la quiere ver con su folio bueno. Es la unica de
estos dos productos y esta en confirmado, sin material consumido todavia. Se deja nota en
su historial con el folio anterior, porque el numero de una orden aparece en documentos y
hay que poder rastrearlo.

Idempotente.
"""
Seq = env['ir.sequence'].sudo()
T = env['product.template'].sudo()

CASOS = [
    ('PTBWP01', 'BWE', 'Lote kit terminado - Paquete bolsas Whirl-Pak'),
    ('PTESP01', 'ESP', 'Lote kit terminado - Kit de esponjas'),
]

for clave, letras, nombre in CASOS:
    t = T.search([('default_code', '=', clave)], limit=1)
    if not t:
        print('[ojo] no existe %s' % clave); continue
    if t.mo_sequence_id:
        s = t.mo_sequence_id
        print('[ya] %-9s ya tiene secuencia "%s" sufijo "%s"' % (clave, s.name, s.suffix))
        continue
    s = Seq.create({
        'name': nombre,
        'implementation': 'standard',
        'prefix': '%(month)s%(y)s/',
        'suffix': '/%s' % letras,
        'padding': 2,
        'number_next': 1,
        'number_increment': 1,
        'company_id': env.company.id,
    })
    t.write({'mo_sequence_id': s.id})
    print('[ok] %-9s secuencia %s: prefijo "%s" sufijo "%s" -> proxima orden %s01/%s' % (
        clave, s.id, s.prefix, s.suffix, __import__('datetime').date.today().strftime('%m%y/'), letras))

# ---- la orden que ya salio con el folio generico -------------------------
print('\n=== la orden que ya existe ===')
MO = env['mrp.production'].sudo()
for clave, letras, _n in CASOS:
    t = T.search([('default_code', '=', clave)], limit=1)
    genericas = MO.search([('product_id.product_tmpl_id', '=', t.id),
                           ('name', 'like', 'AMP/MO/')])
    for mo in genericas:
        if mo.state in ('done', 'cancel'):
            print('   %-16s %s: no se renombra una orden %s' % (mo.name, clave, mo.state))
            continue
        viejo = mo.name
        nuevo = t.mo_sequence_id._amunet_next_folio_mensual()
        mo.write({'name': nuevo})
        mo.message_post(body=(
            'Folio corregido: esta orden salio con el folio genérico del almacén '
            '<b>%s</b> porque %s no tenía configurada su secuencia de Amunet. Ahora '
            'tiene su folio propio <b>%s</b>.<br/><br/>'
            'Si el folio anterior aparece en algún documento impreso o en una etiqueta, '
            'corresponde a esta misma orden.' % (viejo, clave, nuevo)))
        print('   %-9s %s  ->  %s' % (clave, viejo, nuevo))

print('\n=== como queda ===')
for clave, _l, _n in CASOS:
    t = T.search([('default_code', '=', clave)], limit=1)
    s = t.mo_sequence_id
    print('   %-9s secuencia "%s"  sufijo %s  siguiente %s' % (
        clave, s.name if s else '-', s.suffix if s else '-', s.number_next_actual if s else '-'))
    for mo in MO.search([('product_id.product_tmpl_id', '=', t.id)], order='id desc', limit=3):
        print('        %-16s %s' % (mo.name, mo.state))
env.cr.commit()
