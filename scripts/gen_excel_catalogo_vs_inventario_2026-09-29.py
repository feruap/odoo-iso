# -*- coding: utf-8 -*-
"""Las 60 fichas del catalogo interno contra el inventario real."""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

B = '/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/'

# ficha, nombre en el catalogo, clave real, nombre real, existencia, movs, confianza, nota
GEMELAS = [
 ('2161','Agar bacteriológico 450 g','MPREC90','Agar bacteriológico','418.75','12','Idéntico',''),
 ('2177','Azul de bromofenol 5 g','MPREC60','Azul de bromofenol','3.98','3','Idéntico',''),
 ('2183','Agua peptonada amortiguada 100 g','MPREC28','Agua peptonada amortiguada','450','15','Idéntico','Dos fichas apuntan al mismo producto: esta y la 2149'),
 ('2149','Agua peptonada amortiguada 450 g McdLab','MPREC28','Agua peptonada amortiguada','450','15','Alto','¿Es la misma o es otra presentación/marca?'),
 ('2160','Agar sangre base 100 g','MPREC91','Base Agar Sangre','100','1','Alto','Mismo producto, nombre volteado'),
 ('2180','Agar Mueller Hinton 38 g para 1 L','MPREC88','Agar Mueller Hinton Mcolab','35','3','Alto','¿Misma marca? El real dice Mcolab'),
 ('2188','Azida de sodio 100 g','SPSAS01','Azida de sodio 20 %','0','5','REVISAR','El real es SOLUCIÓN al 20%, la ficha parece el reactivo puro'),
 ('2151','Autoclave esterilizador 24 L','EQEPV01','Autoclave (esterilizador a presión)','1','4','Alto','Ya hay una autoclave dada de alta como equipo'),
 ('2152','Rack de puntas amarillas estériles','CORAC01','Rack de puntas amarillas','22','11','Alto','¿El real también es estéril?'),
 ('2173','Colorante amarillo 5 laca alumínica 500 g','MPREC55','Colorante amarillo','500','0','Alto',''),
 ('2179','Gel refrigerante frigogel','STGEL01','Gel refrigerante','100','8','Alto',''),
 ('2154','Mechero o lámpara de alcohol de vidrio','EQLAA01','Lampara de alcohol (mechero) 400 mL','5','2','Alto','Mismo objeto, nombre volteado'),
 ('2186','Solución para electrodos pH 3M KCl','MPREC83','Solución de almacenamiento 3M KCl','471','3','Alto','Mismo uso, confirmar'),
 ('2171','Tubo para PCR 30 bolsas','COTUB01','Tubo de 0.2 ml','19000','27','REVISAR','El real es por pieza, la ficha por bolsa'),
 ('2166','Tubo de centrífuga 10 ml','COTUB05','Tubo de 10 ml','0','0','REVISAR','El de 10 ml existe pero en cero'),
 ('2174','Probeta plástico 10 ml graduada','COPRB04','Probeta 250 ml','1','2','NO ES','Distinta capacidad: 10 ml contra 250 ml'),
 ('2175','Jeringa de vidrio borosilicato','COJER03','Jeringa 3ml','0','0','REVISAR','El real no dice material ni capacidad'),
]

DESCARTADAS = [
 ('2198','Mesa de trabajo de acero inoxidable','MPREC22','MES','Coincidencia de siglas: MES es un reactivo, no una mesa'),
 ('2164','Cubrezapatos desechables','COBDE01','Bata Desechable','Son prendas distintas'),
 ('2155','Varilla agitadora magnética','EQAMC01','Agitador magnético con calefacción','La varilla es el accesorio, el agitador es el aparato'),
 ('2178','Microplaca ELISA 96 pozos','EQMIC01','Micropipeta','Solo comparten las letras "mic"'),
 ('2207','Centrífuga para laboratorio','COCEN01','Centricon 0.5','Centricon es un filtro, no una centrífuga'),
 ('2163','Tubo PCR 0.2 ml tapa plana','STTBT01','Tubo con tapa desecante','Son tubos distintos'),
]

gemelas_ids = {g[0] for g in GEMELAS}

azul = PatternFill('solid', fgColor='1F4E78')
rojo = PatternFill('solid', fgColor='FCE4E4')
ambar = PatternFill('solid', fgColor='FFF2CC')
verde = PatternFill('solid', fgColor='E8F4E8')
gris = PatternFill('solid', fgColor='F2F2F2')
borde = Border(*[Side(style='thin', color='BFBFBF')] * 4)


def encabeza(ws, t, sub, cols):
    ws['A1'] = t; ws['A1'].font = Font(size=14, bold=True, color='1F4E78')
    ws['A2'] = sub; ws['A2'].font = Font(size=9, italic=True, color='808080')
    for i, (h, w) in enumerate(cols, 1):
        c = ws.cell(row=4, column=i, value=h)
        c.font = Font(bold=True, color='FFFFFF'); c.fill = azul
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = borde
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[4].height = 32
    ws.freeze_panes = 'A5'


def fila(ws, r, vals, rell=None):
    for i, v in enumerate(vals, 1):
        c = ws.cell(row=r, column=i, value=v)
        c.border = borde
        c.alignment = Alignment(vertical='center', wrap_text=True)
        if rell: c.fill = rell
    ws.row_dimensions[r].height = 26


wb = openpyxl.Workbook()

ws = wb.active; ws.title = 'Empieza aqui'
encabeza(ws, 'Catálogo interno contra inventario — 60 fichas sin clave',
         'Ninguna de las 60 se ha usado nunca: 0 movimientos, 0 existencia, 0 recetas, 0 compras. Apagarlas no afecta al producto con clave.',
         [('Punto', 46), ('Cuántas', 11), ('Qué significa', 86)])
RES = [
 ('Fichas del catálogo SIN clave interna', '60', 'Las creó la carga inicial del 26-jul importando un CSV, no prendiendo la casilla en productos que ya existían.'),
 ('De esas, sin NINGÚN uso', '59', 'Sin movimientos, existencia, recetas, órdenes de compra ni solicitudes. Se pueden apagar sin riesgo.'),
 ('Con algo colgando', '1', 'Tablet uso rudo HOTWAV: tiene la solicitud SMP/26/00338 esperando autorización desde el 21-sep. Esa NO se toca.'),
 ('Tienen gemelo con clave (a fusionar)', '17', 'El producto bueno ya existe, con existencia e historial. La ficha del catálogo es la que sobra.'),
 ('Falsos parecidos, descartados', '6', 'Los revisé y no son lo mismo. Van en su propia pestaña con el porqué.'),
 ('Sin gemelo — sí hay que codificarlas', '37', 'Sillas, lámparas, hieleras, básculas. Amunet no las tenía dadas de alta.'),
]
for n, f in enumerate(RES):
    fila(ws, 5+n, list(f), ambar if f[1] in ('60','17') else (rojo if f[1]=='1' else None))

ws2 = wb.create_sheet('17 con gemelo')
encabeza(ws2, 'Fichas del catálogo que duplican un producto con clave',
         'Lo que hay que validar es si de verdad son el mismo producto. La columna Confianza dice qué tan seguro estoy.',
         [('Ficha', 8), ('Nombre en el catálogo', 42), ('Clave real', 12),
          ('Nombre del producto real', 36), ('Existencia', 11), ('Movs', 8),
          ('Confianza', 12), ('Qué revisar', 48), ('Tu decisión', 20)])
for n, g in enumerate(GEMELAS):
    conf = g[6]
    col = verde if conf == 'Idéntico' else (rojo if conf == 'NO ES' else (ambar if conf == 'REVISAR' else None))
    fila(ws2, 5+n, list(g) + [''], col)

ws3 = wb.create_sheet('Descartadas')
encabeza(ws3, 'Parecidos que revisé y NO son el mismo producto',
         'Los pongo para que quede constancia de que se miraron y por qué se descartaron.',
         [('Ficha', 8), ('Nombre en el catálogo', 40), ('Clave', 12), ('Con qué se parecía', 32), ('Por qué NO es', 60)])
for n, d in enumerate(DESCARTADAS):
    fila(ws3, 5+n, list(d), gris)

ws4 = wb.create_sheet('Las 60 completas')
encabeza(ws4, 'Las 60 fichas del catálogo, completas',
         'En ámbar las que tienen gemelo. En rojo la única con historial.',
         [('Ficha', 8), ('Nombre en el catálogo', 52), ('Flujo', 14),
          ('¿Tiene liga?', 12), ('¿Tiene gemelo?', 14), ('¿Tiene historial?', 15)])
r = 5
for ln in open(B + 'fichas60.txt'):
    f = ln.rstrip('\n').split('~')
    if len(f) < 5: continue
    fid, nom, flujo, url, hist = f
    gem = 'SÍ' if fid in gemelas_ids else 'no'
    fila(ws4, r, [fid, nom, flujo, 'sí' if url else 'no', gem, hist or 'no'],
         rojo if hist else (ambar if gem == 'SÍ' else None))
    r += 1

wb.save(B + 'Catalogo_interno_vs_inventario_2026-09-29.xlsx')
print('OK: %d gemelas, %d descartadas, %d fichas' % (len(GEMELAS), len(DESCARTADAS), r-5))
