# -*- coding: utf-8 -*-
"""Diagnostico del Marketplace Interno contra el inventario real."""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

B = '/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/'

# propuesta, estado, veredicto, clave que ya existe, nombre en el sistema, publicado, que hacer
PROPUESTAS = [
    ('Triptona', 'submitted', 'YA EXISTE', 'MPREC94', 'Triptona', 'Sí', 'Cerrar la propuesta: ya está publicado'),
    ('Peptona de Caseína', 'submitted', 'YA EXISTE', 'MPREC67', 'Peptona de caseína', 'No', 'Publicar y cerrar la propuesta'),
    ('DTT', 'submitted', 'YA EXISTE', 'MPREC26', 'DTT (granel)', 'No', 'Publicar y cerrar la propuesta'),
    ('Inhibidor de proteasas', 'submitted', 'YA EXISTE', 'MPINP0101', 'Inhibidor de proteasas', 'No', 'Publicar y cerrar la propuesta'),
    ('IPTG', 'submitted', 'YA EXISTE', 'MPREC25', 'IPTG (granel)', 'No', 'Publicar y cerrar la propuesta'),
    ('Tris-HCl', 'submitted', 'YA EXISTE', 'MPREC04', 'Tris-HCl (granel)', 'No', 'Publicar y cerrar la propuesta'),
    ('Imidazol', 'submitted', 'YA EXISTE', 'MPREC53', 'Imidazol', 'No', 'Publicar y cerrar la propuesta'),
    ('Sulfato de Magnesio', 'submitted', 'YA EXISTE', 'MPREC65', 'Sulfato de magnesio', 'No', 'Publicar y cerrar la propuesta'),
    ('EDTA', 'submitted', 'YA EXISTE', 'MPREC98', 'EDTA', 'No', 'Publicar y cerrar la propuesta'),
    ('Sulfato de amonio', 'submitted', 'YA EXISTE', 'MPREC41', 'Sulfato de amonio', 'No', 'Publicar y cerrar la propuesta'),
    ('Ácido Acético', 'submitted', 'YA EXISTE', 'MPREC78', 'Ácido acético', 'No', 'Publicar y cerrar la propuesta'),
    ('NaCl', 'submitted', 'EXISTE CON OTRO NOMBRE', 'MPREC05', 'Cloruro de sodio', 'No', 'Publicar y cerrar; agregar "NaCl" como sinónimo en la ficha'),
    ('KH2PO4', 'submitted', 'EXISTE CON OTRO NOMBRE', 'MPREC33', 'Fosfato de Potasio Monobásico', 'No', 'Publicar y cerrar; agregar "KH2PO4" como sinónimo'),
    ('Bata desechable azul', 'submitted', 'EXISTE CON OTRO NOMBRE', 'COBDE01', 'Bata Desechable', 'No', 'Confirmar si el color importa; si no, publicar y cerrar'),
    ('Biotina', 'submitted', 'REVISAR', '', 'Hay SPHMT01 Hoja Maestra Biotina y MPANT27 anti-biotina, no el reactivo', '', 'Preguntar a quien la pide para qué la usa'),
    ('Metanol', 'submitted', 'SÍ ES NUEVO', '', 'Lo parecido es MPREC18 Etanol 96%, que es otra cosa', '', 'Dar de alta'),
    ('Etanol', 'submitted', 'REVISAR', 'MPREC18', 'Etanol 96%', 'No', 'Confirmar si sirve el de 96%; si sí, publicar y cerrar'),
    ('Acetato de potasio', 'submitted', 'SÍ ES NUEVO', '', 'Lo parecido es MPREC66 Acetato de plomo, que es otra cosa', '', 'Dar de alta'),
    ('NaOH', 'submitted', 'EXISTE CON OTRO NOMBRE', 'MPREC09', 'Hidróxido de sodio (NaOH)', 'No', 'Publicar y cerrar la propuesta'),
    ('Aceite para bomba de vacío', 'rejected', 'RECHAZADA', '', '', '', 'Ya rechazada, sin acción'),
    ('Perlas disruptivas CTR', 'rejected', 'RECHAZADA', '', '', '', 'Ya rechazada, sin acción'),
    ('Tinta solvente secado rápido', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta (le falta categoría)'),
    ('Perlas de vidrio para ebullición', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta'),
    ('Regulador de voltaje', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta'),
    ('Extracto de levadura', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta'),
    ('Glicerol', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta; ojo, la #28 es la misma'),
    ('Glicerol / Glicerina', 'submitted', 'DUPLICADA', '', 'Es la misma que la propuesta "Glicerol"', '', 'Cerrar una de las dos'),
    ('K2HPO4', 'submitted', 'SÍ ES NUEVO', '', 'Existe el monobásico MPREC33, no el dibásico', '', 'Dar de alta'),
    ('b-mercaptoetanol', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta'),
    ('Repetidor WiFi', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta'),
    ('Reloj para pared', 'submitted', 'SÍ ES NUEVO', '', '', '', 'Dar de alta'),
]

DUPLICADOS = [
    ('Control negativo', 'STCON01', 'sin categoría · 0 existencia · 3 movs',
     'STCNL01', 'Semiterminado/Control · 78 pz · 18 movs', 'DUPLICADO REAL',
     'STCON01 sobra: archivarlo (no borrar, tiene 3 movimientos)'),
    ('CHAPS', 'MPREC23', 'Materia prima / Reactivo (granel)', 'PTREC09', 'Producto terminado / Reactivo (reenvasado)', 'No es duplicado', 'Distinguir en el nombre: "(granel)" y "(reenvasado)"'),
    ('DTT', 'MPREC26', 'granel · 50 · en 2 recetas', 'PTREC13', 'reenvasado · 0 · sin uso', 'No es duplicado', 'Distinguir en el nombre'),
    ('Guanidine hydrochloride', 'MPREC24', 'granel', 'PTREC10', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('HEPES', 'MPREC20', 'granel', 'PTREC06', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('IPTG', 'MPREC25', 'granel', 'PTREC12', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('MES', 'MPREC22', 'granel', 'PTREC08', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('MOPS', 'MPREC21', 'granel', 'PTREC07', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('TCEP-HCl', 'MPREC27', 'granel · 0 · en 3 recetas de PTREC11', 'PTREC11', 'reenvasado · 0 · nunca vendido', 'No es duplicado', 'Distinguir en el nombre'),
    ('Tris base', 'MPREC10', 'granel', 'PTREC05', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('Tris-HCl', 'MPREC04', 'granel', 'PTREC04', 'reenvasado', 'No es duplicado', 'Distinguir en el nombre'),
    ('Probeta 1 L', 'COPRB05', 'Cristalería · EN CATÁLOGO · 1 mov', 'PTCRS03', 'Distribución · 0 · sin movimientos', 'REVISAR', 'Confirmar con Luis si el de Distribución se usa'),
    ('Probeta 250 ml', 'COPRB04', 'Cristalería · EN CATÁLOGO · 1 pz', 'PTCRS04', 'Distribución · 0 · sin movimientos', 'REVISAR', 'Confirmar con Luis si el de Distribución se usa'),
]

azul = PatternFill('solid', fgColor='1F4E78')
rojo = PatternFill('solid', fgColor='FCE4E4')
ambar = PatternFill('solid', fgColor='FFF2CC')
verde = PatternFill('solid', fgColor='E8F4E8')
gris = PatternFill('solid', fgColor='F2F2F2')
borde = Border(*[Side(style='thin', color='BFBFBF')] * 4)


def encabeza(ws, titulo, sub, cols):
    ws['A1'] = titulo
    ws['A1'].font = Font(size=14, bold=True, color='1F4E78')
    ws['A2'] = sub
    ws['A2'].font = Font(size=9, italic=True, color='808080')
    for i, (t, w) in enumerate(cols, start=1):
        c = ws.cell(row=4, column=i, value=t)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = azul
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = borde
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[4].height = 30
    ws.freeze_panes = 'A5'


def fila(ws, r, vals, relleno=None):
    for i, v in enumerate(vals, start=1):
        c = ws.cell(row=r, column=i, value=v)
        c.border = borde
        c.alignment = Alignment(vertical='center', wrap_text=True)
        if relleno:
            c.fill = relleno
    ws.row_dimensions[r].height = 26


wb = openpyxl.Workbook()

# 1 — resumen
ws = wb.active
ws.title = 'Resumen'
encabeza(ws, 'Marketplace Interno contra el inventario real',
         'Diagnóstico del 29-sep-2026, sobre datos de producción.',
         [('Hallazgo', 56), ('Cuántos', 12), ('Qué significa', 78)])
RES = [
    ('Productos publicados en el catálogo', '66', 'De 1,049 del catálogo total. Es una vitrina del 6%.'),
    ('De esos 66, SIN clave interna', '60', 'El catálogo no está montado sobre el inventario: son fichas de escaparate que Almacén no maneja.'),
    ('De esos 66, SIN existencia', '63', 'Se puede pedir del catálogo algo de lo que no hay una sola pieza.'),
    ('De esos 66, SIN precio de referencia', '66', 'Ninguno tiene el precio capturado. La columna existe y está vacía.'),
    ('Propuestas abiertas', '29', 'Más 2 rechazadas. Ninguna se ha convertido en producto todavía.'),
    ('Propuestas de algo QUE YA EXISTE', '14', 'La causa: 13 de esos 14 productos existen pero NO están publicados, así que nadie los encuentra.'),
    ('Propuestas genuinamente nuevas', '12', 'Estas sí hay que darlas de alta.'),
    ('Nombres repetidos en el inventario', '13', '1 duplicado real, 10 pares granel/reenvasado y 2 de cristalería por revisar.'),
]
for n, f in enumerate(RES):
    fila(ws, 5 + n, list(f), ambar if f[1] in ('60', '63', '66', '14') else None)

# 2 — propuestas
ws2 = wb.create_sheet('Las 31 propuestas')
encabeza(ws2, 'Las propuestas, cruzadas contra el inventario',
         'Rojo = ya existe, no hay que dar nada de alta. Verde = sí es nuevo.',
         [('Propuesta', 30), ('Estado', 11), ('Veredicto', 22), ('Clave que ya existe', 16),
          ('Cómo se llama en el sistema', 40), ('¿Publicado?', 12), ('Qué hacer', 46)])
for n, f in enumerate(PROPUESTAS):
    v = f[2]
    col = rojo if v in ('YA EXISTE', 'EXISTE CON OTRO NOMBRE', 'DUPLICADA') else (
        verde if v == 'SÍ ES NUEVO' else (gris if v == 'RECHAZADA' else ambar))
    fila(ws2, 5 + n, list(f), col)

# 3 — duplicados
ws3 = wb.create_sheet('Nombres repetidos')
encabeza(ws3, 'Los 13 nombres que aparecen dos veces en el inventario',
         'Solo uno es duplicado de verdad; diez son pares granel/reenvasado que comparten nombre.',
         [('Nombre repetido', 24), ('Clave A', 11), ('Qué es A', 34),
          ('Clave B', 11), ('Qué es B', 34), ('Veredicto', 17), ('Qué hacer', 46)])
for n, f in enumerate(DUPLICADOS):
    v = f[5]
    fila(ws3, 5 + n, list(f), rojo if v == 'DUPLICADO REAL' else (ambar if v == 'REVISAR' else None))

# 4 — los 66
ws4 = wb.create_sheet('Los 66 publicados')
encabeza(ws4, 'Los 66 productos publicados en el catálogo',
         'Ordenados por categoría. Fíjate en la columna de clave y existencia.',
         [('Clave interna', 15), ('Producto', 48), ('Categoría', 34),
          ('Flujo', 14), ('Existencia', 12), ('URL de compra', 16)])
r = 5
for ln in open(B + 'catalogo66.txt'):
    f = ln.rstrip('\n').split('~')
    if len(f) < 6:
        continue
    clave, nombre, cat, flujo, url, ex = f
    fila(ws4, r, [clave or '(sin clave)', nombre, cat or '(sin categoría)', flujo,
                  float(ex or 0), 'sí' if url else 'no'],
         ambar if not clave else None)
    r += 1

wb.save(B + 'Marketplace_vs_inventario_2026-09-29.xlsx')
print('OK: %d propuestas, %d duplicados, %d publicados' % (len(PROPUESTAS), len(DUPLICADOS), r - 5))
