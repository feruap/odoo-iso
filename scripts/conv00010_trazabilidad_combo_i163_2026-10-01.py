# -*- coding: utf-8 -*-
"""CONV/00010: dejar por escrito que el combo recibido fue I163-4045.

QUE PASO (reconstruido el 01-oct-2026)
  17-sep  AMP/IN/00347 recibe 30 pz del combo I204-4025 (3 hojas: Zika, Chik IgG,
          Chik IgM).
  28-sep  CONV/00010 convierte esos 30 combos en 900 piezas de cada una de esas
          TRES hojas.
  29-sep  Entran 900 hojas de Dengue (SPHMC85, lote HMC85092601) a cuarentena de
          Calidad por "Ajuste de inventario", sin documento que las explique.

Ese ajuste delata el error: el combo que llego fisicamente es el I163-4045, que
trae CUATRO hojas -- las tres anteriores mas la de Dengue-. Karla lo reporto el
30-sep: se confundio entre dos claves parecidas al validar.

QUE SE CORRIGE Y QUE NO
El inventario fisico esta CORRECTO: las cuatro hojas existen con sus 900 piezas.
No falta ni sobra nada, asi que no se mueve una sola pieza.

Lo que estaba mal es el papel: 900 piezas de producto aparecian de un ajuste de
inventario sin explicacion, y en una auditoria eso es lo que no se puede defender.
Este script deja la explicacion escrita en los cuatro registros donde un auditor
la buscaria: la recepcion, la conversion, el lote de Dengue y el lote del combo.

POR QUE NO SE REHACE LA CONVERSION
Habria que revertir el ajuste de las 900 hojas de Dengue, y sobre ese lote hay un
analisis en proceso (QC/2026/00513) que se romperia; ademas toca una recepcion ya
cerrada con cuarentena de Calidad. El inventario acabaria igual que hoy. Decision
de Mery el 01-oct-2026.

El combo I204-4025 NO se archiva: el proveedor si lo vende (confirmado por Mery).

Idempotente: no repite la nota si ya esta puesta.
"""

MARCA = '[CONV/00010 - combo corregido a I163-4045]'

NOTA = """%s

<p>El combo que llego fisicamente en esta operacion fue el <b>I163-4045</b>
(COMBO MOSQUITO, cuatro hojas: Dengue + Zika + Chikungunya IgG + Chikungunya IgM),
<b>no el I204-4025</b> (tres hojas, sin Dengue) que quedo capturado.</p>

<p>Karla lo reporto el 30-sep-2026: se confundio entre las dos claves al validar.</p>

<p><b>Como se ve el error en los registros:</b> CONV/00010 genero 900 piezas de
SPHMC86, SPHMC87 y SPHMC88 -- las tres hojas del combo equivocado-, y el 29-sep
entraron 900 piezas de SPHMC85 (Dengue, lote HMC85092601) por un ajuste de
inventario, porque faltaban. Esas 900 de Dengue <b>pertenecen a este mismo combo</b>:
no son un ajuste de conteo.</p>

<p><b>El inventario fisico esta correcto</b> y no se movio ninguna pieza. Las cuatro
hojas existen con sus 900 unidades cada una.</p>

<p><b>Por que no se rehizo la conversion:</b> habria que revertir el ajuste de las
900 hojas de Dengue, y sobre ese lote hay un analisis en proceso (QC/2026/00513)
que se romperia; ademas obliga a reabrir una recepcion ya cerrada con cuarentena de
Calidad. El resultado en inventario seria identico al actual. Se opto por dejar la
trazabilidad documentada (decision de Mery, 01-oct-2026).</p>

<p>El combo I204-4025 sigue activo en el catalogo: el proveedor si lo vende.</p>""" % MARCA


def anotar(rec, etiqueta):
    if not rec:
        print('  [!] no se encontro %s' % etiqueta)
        return 0
    rec.ensure_one()
    previas = env['mail.message'].search([('model', '=', rec._name), ('res_id', '=', rec.id),
                                          ('body', 'ilike', MARCA)], limit=1)
    if previas:
        print('  ya tenia la nota: %s' % etiqueta)
        return 0
    rec.sudo().message_post(body=NOTA)
    print('  anotado: %s' % etiqueta)
    return 1


puestas = 0
recep = env['stock.picking'].search([('name', '=', 'AMP/IN/00347')], limit=1)
puestas += anotar(recep, 'recepcion AMP/IN/00347')

conv = env['stock.picking'].search([('name', '=', 'CONV/00010')], limit=1)
puestas += anotar(conv, 'conversion CONV/00010')

lote_dengue = env['stock.lot'].search([('name', '=', 'HMC85092601')], limit=1)
puestas += anotar(lote_dengue, 'lote de Dengue HMC85092601 (las 900 del ajuste)')

combo_tmpl = env['product.template'].search([('default_code', '=', 'I204-4025')], limit=1)
lote_combo = env['stock.lot'].search([('name', '=', '0000001'),
                                      ('product_id.product_tmpl_id', '=', combo_tmpl.id)], limit=1)
puestas += anotar(lote_combo, 'lote del combo 0000001 (I204-4025)')

env.cr.commit()

print('\n=== COMPROBACION ===')
for mod, ident, etq in [('stock.picking', 'AMP/IN/00347', 'recepcion'),
                        ('stock.picking', 'CONV/00010', 'conversion'),
                        ('stock.lot', 'HMC85092601', 'lote Dengue'),
                        ('stock.lot', '0000001', 'lote combo')]:
    rec = env[mod].search([('name', '=', ident)], limit=1)
    n = env['mail.message'].search_count([('model', '=', mod), ('res_id', '=', rec.id),
                                          ('body', 'ilike', MARCA)]) if rec else 0
    print('  %-12s %-14s nota presente: %s' % (etq, ident, 'si' if n else 'NO'))
print('\nnotas puestas en esta corrida: %s' % puestas)
print('inventario: no se movio ninguna pieza (este script solo escribe en el historial)')
