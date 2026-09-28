# -*- coding: utf-8 -*-
"""Que solucion de captura le toca a cada hoja maestra. Version al cierre
del 28-sep-2026, con los ajustes que devolvio Mery.

La membrana lleva hasta TRES lineas impresas: prueba, referencia y control.
La de control es la misma en las 15 hojas.
"""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

CONTROL = 'SPSCA25'

# hoja, nombre, producto terminado, linea(s) de prueba, linea de referencia, estado
LAMINADAS = [
    ('SPHMC01', 'Covinet Ag', 'Covinet, Covflu-Net, Combo respiratorio', 'SPSCA15', '', 'Completa'),
    ('SPHMC07', 'Hemoglobina', 'DMHBA01 Hemoglobina cualitativa', 'SPSCA20', '', 'Completa'),
    ('SPHMC09', 'Vitamina D', 'DMVID01 Vitaminet D', 'SPSCA30', '', 'Completa'),
    ('SPHMC15', 'Influenza A+B', 'Flunet, Covflu-Net, Combo respiratorio', 'SPSCA01 + SPSCA02', '', 'Completa'),
    ('SPHMC18', 'Dengue IgG/IgM', 'Dengue Net, DMDEN02', 'SPSCA13 + SPSCA14', '', 'Completa'),
    ('SPHMC19', 'Dengue NS1', 'Dengue Net', 'SPSCA16', '', 'Completa'),
    ('SPHMC20', 'RSV', 'RSV Net, Combo respiratorio', 'SPSCA24', '', 'Completa'),
    ('SPHMC22', 'Sífilis', 'Sifilinet, Combo Sífilis+VIH', 'SPSCA29', '', 'Completa'),
    ('SPHMC23', 'VIH p24', 'DMVIH02 VIH 4ta generación', 'SPSCA26', '', 'Completa'),
    ('SPHMC24', 'PSA cualitativa', 'DMPSA02 Prostatinet', 'SPSCA21', '', 'Completa'),
    ('SPHMC37', 'TSH cualitativa', 'DMTSH01', 'SPSCA27', '', 'Completa'),
    ('SPHMC38', 'PSA semicuantitativa', 'DMPSA01', 'SPSCA21', 'FALTA DEFINIR', 'Falta la línea de referencia'),
    ('SPHMC45', 'Salmonella typhi', 'DMSAT01, Combo Entamoeba+Salmonella', 'SPSCA28', '', 'Completa'),
    ('SPHMC52', 'TSH semicuantitativa', 'DMTSH02', 'SPSCA27', 'FALTA DEFINIR', 'Falta la línea de referencia'),
    ('SPHMT01', 'Biotina', 'Ecohem, Isolister, Salmonet, VPH Net (PCR)', 'SPSCA08', '', 'Completa'),
]

COBERTURA = [
    ('SPSCA03', 'THC', 'SPHMC10, SPHMC53, SPHMC76, SPHMT07', 'Sin anticuerpo: no se lamina aquí todavía'),
    ('SPSCA04', 'COC', 'SPHMC12, SPHMC54, SPHMC75, SPHMT09', 'Sin anticuerpo: no se lamina aquí todavía'),
    ('SPSCA05', 'AMP', 'SPHMC11, SPHMC54, SPHMC75, SPHMT08', 'Sin anticuerpo: no se lamina aquí todavía'),
    ('SPSCA06', 'MET', 'SPHMC13, SPHMC53, SPHMC76, SPHMT10', 'Sin anticuerpo: no se lamina aquí todavía'),
    ('SPSCA07', 'OPI', 'SPHMC14, SPHMC54, SPHMC76, SPHMT11', 'Sin anticuerpo: no se lamina aquí todavía'),
    ('SPSCA09', 'Mioglobina', 'SPHMC17 Cardiac combo', 'Hoja aún sin ruta de laminado'),
    ('SPSCA10', 'CK-MB', 'SPHMC17 Cardiac combo', 'Hoja aún sin ruta de laminado'),
    ('SPSCA11', 'cTnI', 'SPHMC17, SPHMC74', 'Hoja aún sin ruta de laminado'),
    ('SPSCA12', 'Chlamydia trachomatis', 'SPHMC03, SPHMC08', 'Hoja aún sin ruta de laminado'),
    ('SPSCA17', 'Alcohol', 'SPHMC67 Alcohol en saliva', 'Sin MP: la prueba es enzimática, no inmunológica'),
    ('SPSCA18', 'Ferritina', 'SPHMC25', 'Hoja aún sin ruta de laminado'),
    ('SPSCA19', 'hCG', 'SPHMC21, SPHMC65, SPHMT06', 'Hoja aún sin ruta de laminado'),
    ('SPSCA22', 'Rotavirus', 'SPHMC27', 'Hoja aún sin ruta de laminado'),
    ('SPSCA23', 'Adenovirus', 'SPHMC27', 'Hoja aún sin ruta de laminado'),
    ('SPSCA13', 'IgG humana', 'SPHMC18 y además SPHMC49, 62, 69, 70, 80, 85-88', 'Sirve a varias hojas'),
    ('SPSCA14', 'IgM humana', 'SPHMC18 y además SPHMC49, 62, 69, 70, 80, 85-88', 'Sirve a varias hojas'),
]

PENDIENTES = [
    ('Línea de referencia', 'SPHMC38 PSA semicuantitativa, SPHMC52 TSH semicuantitativa',
     'Solo las semicuantitativas la llevan. Falta decir qué anticuerpo y a qué '
     'concentración: si es el mismo de la línea de prueba a otra concentración, '
     'es clave aparte.'),
]

azul = PatternFill('solid', fgColor='1F4E78')
rojo = PatternFill('solid', fgColor='FCE4E4')
verde = PatternFill('solid', fgColor='E8F4E8')
ambar = PatternFill('solid', fgColor='FFF2CC')
borde = Border(*[Side(style='thin', color='BFBFBF')] * 4)


def encabeza(ws, titulo, subtitulo, cols):
    ws['A1'] = titulo
    ws['A1'].font = Font(size=14, bold=True, color='1F4E78')
    ws['A2'] = subtitulo
    ws['A2'].font = Font(size=9, italic=True, color='808080')
    for i, (t, w) in enumerate(cols, start=1):
        c = ws.cell(row=4, column=i, value=t)
        c.font = Font(bold=True, color='FFFFFF')
        c.fill = azul
        c.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        c.border = borde
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.row_dimensions[4].height = 34
    ws.freeze_panes = 'A5'


def pinta(ws, fila, valores, relleno=None):
    for i, v in enumerate(valores, start=1):
        c = ws.cell(row=fila, column=i, value=v)
        c.border = borde
        c.alignment = Alignment(vertical='center', wrap_text=True)
        if relleno:
            c.fill = relleno
    ws.row_dimensions[fila].height = 26


wb = openpyxl.Workbook()

ws = wb.active
ws.title = 'Hojas que se laminan aqui'
encabeza(ws, 'Las 15 hojas maestras que se laminan en Amunet',
         'La membrana lleva hasta tres líneas impresas. La de control es la misma en las 15.',
         [('Hoja', 11), ('Nombre', 24), ('Producto terminado', 38),
          ('Línea(s) de prueba', 20), ('Línea de referencia', 18),
          ('Línea de control', 16), ('Estado', 30)])
for n, f in enumerate(LAMINADAS):
    fila = [f[0], f[1], f[2], f[3], f[4], CONTROL, f[5]]
    pinta(ws, 5 + n, fila, rojo if f[4] else verde)

ws2 = wb.create_sheet('Lo que falta')
encabeza(ws2, 'Lo único que falta', 'Las 30 soluciones cubren todo lo demás.',
         [('Qué falta', 24), ('Hojas afectadas', 46), ('Nota', 70)])
for n, f in enumerate(PENDIENTES):
    pinta(ws2, 5 + n, list(f), ambar)

ws3 = wb.create_sheet('Soluciones en espera')
encabeza(ws3, 'Soluciones dadas de alta que ninguna hoja laminada ocupa todavía',
         'No sobran: esperan su hoja.',
         [('Solución', 12), ('Analito', 26), ('Hojas que la ocuparían', 44), ('Nota', 52)])
for n, f in enumerate(COBERTURA):
    pinta(ws3, 5 + n, list(f))

wb.save('/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/Hojas_maestras_vs_soluciones_captura.xlsx')
print('OK: %d hojas, %d pendientes, %d en espera' % (len(LAMINADAS), len(PENDIENTES), len(COBERTURA)))
