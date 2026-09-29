# -*- coding: utf-8 -*-
"""Las 45 fichas del catalogo sin clave: propuesta de codificacion."""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
B='/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/'

filas=[]
for ln in open(B+'propuesta_claves.txt'):
    f=ln.rstrip('\n').split('~')
    while len(f)<5: f.append('')
    filas.append(f)   # id, grupo, clave, nombre, nota

ligas={}
for ln in open(B+'fichas45.txt'):
    g=ln.rstrip('\n').split('~')
    if len(g)>=5: ligas[g[0]]=(g[2], g[4], g[5])   # flujo, url, historial

azul=PatternFill('solid',fgColor='1F4E78'); ambar=PatternFill('solid',fgColor='FFF2CC')
verde=PatternFill('solid',fgColor='E8F4E8'); rojo=PatternFill('solid',fgColor='FCE4E4')
borde=Border(*[Side(style='thin',color='BFBFBF')]*4)

def enc(ws,t,sub,cols):
    ws['A1']=t; ws['A1'].font=Font(size=14,bold=True,color='1F4E78')
    ws['A2']=sub; ws['A2'].font=Font(size=9,italic=True,color='808080')
    for i,(h,w) in enumerate(cols,1):
        c=ws.cell(row=4,column=i,value=h); c.font=Font(bold=True,color='FFFFFF'); c.fill=azul
        c.alignment=Alignment(horizontal='center',vertical='center',wrap_text=True); c.border=borde
        ws.column_dimensions[get_column_letter(i)].width=w
    ws.row_dimensions[4].height=32; ws.freeze_panes='A5'

def fila(ws,r,v,rell=None):
    for i,x in enumerate(v,1):
        c=ws.cell(row=r,column=i,value=x); c.border=borde
        c.alignment=Alignment(vertical='center',wrap_text=True)
        if rell: c.fill=rell
    ws.row_dimensions[r].height=26

wb=openpyxl.Workbook()
ws=wb.active; ws.title='Empieza aqui'
enc(ws,'Las 45 fichas del catálogo que sí hay que codificar',
    'Ya no duplican nada: las 15 que duplicaban se fusionaron el 29-sep. Estas son altas de verdad.',
    [('Punto',44),('Cuántas',11),('Qué significa',88)])
RES=[
 ('Con clave propuesta','21','Encajan en las abreviaturas que Amunet ya usa: CO consumible, EQ equipo, MP materia prima.'),
 ('SIN casa en la normativa','24','Mobiliario, cómputo, instalaciones y mantenimiento. Las 5 clasificaciones oficiales (MP, MI, SP, ST, PT) son todas de producto sanitario.'),
 ('Abreviaturas nuevas que haría falta crear','10','COBOT, COHIE, COESP, COESC, COTIJ, COPLA, COCZP, COMIP, EQCEN, EQTHI, EQVAG.'),
 ('MPREC ya llegó a 99','1','Base caldo Half Fraser sería MPREC100, y la normativa dice consecutivo de DOS dígitos. Esa serie está llena.'),
 ('Quién libera las claves','—','Documentación (Stacy). Esta propuesta es para que ella la valide, no para aplicarla directo.'),
]
for n,f in enumerate(RES): fila(ws,5+n,list(f), ambar if f[1] in ('24','1') else None)

ws2=wb.create_sheet('21 con clave propuesta')
enc(ws2,'Las que sí encajan en la codificación actual',
    'La clave sale de: clasificación (2 letras) + abreviatura (3) + consecutivo (2), continuando el máximo existente.',
    [('Ficha',8),('Grupo',24),('Clave propuesta',15),('Nombre propuesto',46),('De dónde sale el consecutivo',26),('Liga',8),('Tu visto bueno',16)])
r=5
for f in filas:
    if not f[2]: continue
    fl=ligas.get(f[0],('','',''))
    fila(ws2,r,[f[0],f[1],f[2],f[3],f[4],'sí' if fl[1] else 'no',''],
         ambar if 'nueva' in f[4] else verde)
    r+=1

ws3=wb.create_sheet('24 sin casa')
enc(ws3,'Las que no encajan en ninguna clasificación de la normativa',
    'No son producto sanitario: son activos y consumo de oficina. Hace falta decidir qué clasificación les toca.',
    [('Ficha',8),('Grupo',20),('Nombre',52),('Liga',8),('¿Tiene historial?',16),('Qué clasificación le ponemos',30)])
r=5
for f in filas:
    if f[2]: continue
    fl=ligas.get(f[0],('','',''))
    fila(ws3,r,[f[0],f[1],f[3],'sí' if fl[1] else 'no', fl[2] or 'no',''],
         rojo if fl[2] else None)
    r+=1

wb.save(B+'Fichas_sin_clave_propuesta_2026-09-29.xlsx')
print('OK: %d con clave, %d sin casa' % (sum(1 for f in filas if f[2]), sum(1 for f in filas if not f[2])))
