# -*- coding: utf-8 -*-
"""Dos cosas para SPCPR01 y sus hermanas de corrimiento.

1) SECUENCIA DE LOTE de SPCPR01. Las soluciones no llevan folio de orden
   (mo_sequence_id): se lotifican con una secuencia propia por producto, cuyo
   prefijo es la clave sin las dos primeras letras. SPLPT01 -> LPT01%(month)s%(y)s
   y da lotes como LPT01032601. Al calcar el producto no se copia la secuencia --
   no debe copiarse, cada uno necesita la suya -- y SPCPR01 se quedo con la
   generica "Serial Numbers".

2) "2.6 años" ERA UN ERROR DE CAPTURA. Son dos años y seis meses, o sea 2.5
   anos (Mery, 25-sep-2026). Escrito como 2.6 el sistema calculaba 31 meses
   (943 dias) en vez de 30 (912 dias): un mes de vigencia regalado en cada lote
   de solucion de corrimiento.
"""
P = env['product.product'].sudo()
SEQ = env['ir.sequence'].sudo()

# --- 1) secuencia de lote para SPCPR01 -------------------------------------
q = P.search([('default_code','=','SPCPR01')], limit=1)
assert q, 'no existe SPCPR01'
t = q.product_tmpl_id
pref = 'CPR01'
if t.lot_sequence_id and (t.lot_sequence_id.code or '').startswith('amunet.lot.'):
    print('   SPCPR01 ya tiene su secuencia: %s' % t.lot_sequence_id.prefix)
else:
    s = SEQ.create({
        'name': 'Lote %s - %s' % (pref, t.name),
        'code': 'amunet.lot.%s.%s' % (pref, t.id),
        'prefix': '%s%%(month)s%%(y)s' % pref,
        'padding': 2,
        'implementation': 'standard',
        'number_next': 1,
    })
    t.write({'lot_sequence_id': s.id})
    print('   secuencia creada: %s   prefijo=%s' % (s.name, s.prefix))
t.invalidate_recordset()
print('      prefijo que vera el usuario: %s' % (t.amunet_lot_prefix or '-'))
print('      ejemplo de lote: %s0926 01  -> %s092601' % (pref, pref))

# --- 2) corregir 2.6 -> 2.5 anos -------------------------------------------
print('')
print('   corrigiendo "2.6 años" a "2.5 años":')
malos = P.search([('product_tmpl_id.amunet_expiration_text','ilike','2.6')])
for p in malos.sorted(lambda x: x.default_code or ''):
    tt = p.product_tmpl_id
    viejo = tt.amunet_expiration_text
    tt.write({'amunet_expiration_text': '2.5 años'})
    print('      %-10s %-44s "%s" -> "2.5 años"' % (
        p.default_code, (p.name or '')[:44], viejo))
print('      total corregidos: %s' % len(malos))
env.flush_all(); env.cr.commit()
