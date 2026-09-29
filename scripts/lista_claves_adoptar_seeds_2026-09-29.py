"""Destraba los seeds de amunet_lista_claves: adopta las claves que ya existen.

Autorizado por Mery el 29-sep-2026.

EL SINTOMA: `odoo -u <cualquier modulo>` en staging sale con exit 255. El error real,
escondido en el logfile, es un ParseError al cargar
amunet_lista_claves/data/seeds_semiprocesado.xml en el registro de SPMRL01. Eso bloquea
la validacion con -u de CUALQUIER modulo en staging, no solo de este.

LA CAUSA, y no es un duplicado en el XML como parecia al principio: el catalogo de claves
se cargo a la base por otra via -386 de los 562 registros no tienen ni create_date, que es
la huella de un INSERT por SQL directo- y quedaron SIN xml_id. El modelo tiene
UNIQUE(clave), asi que cuando el seed intenta crear su registro, choca con el que ya esta
ahi y revienta. No es un caso: son 507 de las 553 claves del seed.

EL ARREGLO: darle a cada registro existente el xml_id que su seed espera. Con eso el seed
deja de intentar crearlo y pasa a actualizarlo, que es como debio estar desde el
principio. No se borra ni se duplica nada, y los registros conservan su id -importante,
porque otros modulos pueden estar apuntando a ellos.

Se lee el par (xml_id, clave) de los propios archivos del modulo, no de una lista escrita
a mano: si manana agregan claves al seed, este script sigue sirviendo.

Idempotente.
"""
import glob
import re

Clave = env['amunet.clave'].sudo()
IMD = env['ir.model.data'].sudo()
RUTA = '/opt/amunet-addons/amunet_lista_claves/data/*.xml'

# <record id="clave_XXX" model="amunet.clave"> ... <field name="clave">XXX</field>
patron = re.compile(
    r'<record\s+id="([^"]+)"\s+model="amunet\.clave"\s*>\s*'
    r'<field\s+name="clave">([^<]+)</field>', re.S)

pares = {}
archivos = sorted(glob.glob(RUTA))
for ruta in archivos:
    with open(ruta, encoding='utf-8') as fh:
        for xid, clave in patron.findall(fh.read()):
            pares[clave.strip()] = xid.strip()
print('archivos de seed leidos: %d   claves encontradas: %d' % (len(archivos), len(pares)))

adoptadas = ya_tenian = sin_registro = conflicto = 0
for clave, xid in sorted(pares.items()):
    rec = Clave.search([('clave', '=', clave)], limit=1)
    if not rec:
        # el seed la creara solo cuando corra; no hay nada que adoptar
        sin_registro += 1
        continue
    existente = IMD.search([('model', '=', 'amunet.clave'), ('res_id', '=', rec.id)], limit=1)
    if existente:
        if existente.module == 'amunet_lista_claves' and existente.name == xid:
            ya_tenian += 1
        else:
            # apunta a otro xml_id: se deja como esta y se reporta
            conflicto += 1
            print('   [ojo] %s (id %s) ya tiene xml_id %s.%s, el seed espera '
                  'amunet_lista_claves.%s' % (clave, rec.id, existente.module,
                                              existente.name, xid))
        continue
    ocupado = IMD.search([('module', '=', 'amunet_lista_claves'), ('name', '=', xid)], limit=1)
    if ocupado:
        conflicto += 1
        print('   [ojo] el xml_id %s ya lo usa el registro %s; %s (id %s) se queda sin '
              'adoptar' % (xid, ocupado.res_id, clave, rec.id))
        continue
    IMD.create({'module': 'amunet_lista_claves', 'name': xid,
                'model': 'amunet.clave', 'res_id': rec.id, 'noupdate': False})
    adoptadas += 1

print()
print('   adoptadas ahora:            %d' % adoptadas)
print('   ya tenian su xml_id:        %d' % ya_tenian)
print('   el seed las creara el solo: %d' % sin_registro)
print('   conflictos (sin tocar):     %d' % conflicto)

faltan = Clave.search_count([]) - IMD.search_count([('model', '=', 'amunet.clave')])
print('   claves en la base sin xml_id despues de esto: %d' % faltan)
env.cr.commit()

# ---------------------------------------------------------------------------
# SEGUNDA PARTE: los xml_id huerfanos.
#
# Adoptar los 504 no basto: el -u seguia reventando con
# "duplicate key value violates unique constraint amunet_clave_clave_unique".
#
# La causa: 49 xml_id apuntan a registros que YA NO EXISTEN. El caso que lo
# destapo fue clave_STSSP01, que apunta al registro 97 -borrado- mientras la
# clave STSSP01 vive hoy en el 58. Cuando el seed carga ese registro, Odoo ve el
# xml_id, no encuentra su res_id, crea uno nuevo, y choca con el que ya tiene esa
# clave.
#
# El arreglo es RE-APUNTARLOS al registro que hoy tiene esa clave, no borrarlos:
# un xml_id borrado se vuelve a crear en el siguiente -u y el problema regresa.
# Se re-apunta solo cuando hay exactamente un registro con esa clave, para no
# adivinar.
# ---------------------------------------------------------------------------
print('\n=== xml_id huerfanos (apuntan a registros borrados) ===')
huerfanos = IMD.search([('model', '=', 'amunet.clave')]).filtered(
    lambda d: not Clave.browse(d.res_id).exists())
print('   encontrados: %d' % len(huerfanos))
reapuntados = sin_destino = 0
for d in huerfanos:
    # el nombre del xml_id lleva la clave: clave_STSSP01 -> STSSP01, pt_diam_002 -> DIAM-002
    candidatos = [c for c, x in pares.items() if x == d.name]
    clave = candidatos[0] if candidatos else None
    if not clave:
        print('   [ojo] %s no corresponde a ninguna clave de los seeds; se deja' % d.name)
        sin_destino += 1
        continue
    rec = Clave.search([('clave', '=', clave)])
    if len(rec) != 1:
        print('   [ojo] %s -> %s tiene %d registros; no se adivina' % (d.name, clave, len(rec)))
        sin_destino += 1
        continue
    viejo = d.res_id
    d.write({'res_id': rec.id})
    reapuntados += 1
    print('   [ok] %-16s %s -> %s  (clave %s)' % (d.name, viejo, rec.id, clave))
print('   re-apuntados: %d   sin destino claro: %d' % (reapuntados, sin_destino))
env.cr.commit()
