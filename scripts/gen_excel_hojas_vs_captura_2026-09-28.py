# -*- coding: utf-8 -*-
"""Que solucion de captura le toca a cada hoja maestra, y cuales faltan."""
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

# hoja, nombre, producto terminado, linea de prueba, solucion, estado
LAMINADAS = [
    ('SPHMC01', 'Covinet Ag', 'Covinet, Covflu-Net, Combo respiratorio', 'Proteína N SARS-CoV-2', 'SPSCA15', 'OK'),
    ('SPHMC07', 'Hemoglobina', 'DMHBA01 Hemoglobina cualitativa', 'Hemoglobina humana (sangre oculta)', '', 'FALTA SOLUCIÓN Y MP'),
    ('SPHMC09', 'Vitamina D', 'DMVID01 Vitaminet D', '25 (OH) D', 'SPSAN01', 'OK'),
    ('SPHMC15', 'Influenza A+B', 'Flunet, Covflu-Net, Combo respiratorio', 'Influenza A / Influenza B (2 líneas)', 'SPSCA01 + SPSCA02', 'OK'),
    ('SPHMC18', 'Dengue IgG/IgM', 'Dengue Net, DMDEN02', 'IgG humana / IgM humana (2 líneas)', 'SPSCA13 + SPSCA14', 'OK'),
    ('SPHMC19', 'Dengue NS1', 'Dengue Net', 'NS1 de Dengue', 'SPSCA16', 'OK'),
    ('SPHMC20', 'RSV', 'RSV Net, Combo respiratorio', 'RSV', 'SPSCA24', 'OK'),
    ('SPHMC22', 'Sífilis', 'Sifilinet, Combo Sífilis+VIH', 'Antígeno Treponema pallidum', 'SPSPC01', 'OK (clave con Documentación)'),
    ('SPHMC23', 'VIH p24', 'DMVIH02 VIH 4ta generación', 'p24', '', 'FALTA SOLUCIÓN (MP sí hay: MPANT41)'),
    ('SPHMC24', 'PSA cualitativa', 'DMPSA02 Prostatinet', 'PSA', 'SPSCA21', 'OK'),
    ('SPHMC37', 'TSH cualitativa', 'DMTSH01, DMTSH02', 'TSH', '', 'FALTA SOLUCIÓN (MP sí hay: MPANT55)'),
    ('SPHMC38', 'PSA semicuantitativa', 'DMPSA01', 'PSA', 'SPSCA21', 'OK (la misma que SPHMC24)'),
    ('SPHMC45', 'Salmonella typhi', 'DMSAT01, Combo Entamoeba+Salmonella', 'Salmonella typhi', '', 'FALTA SOLUCIÓN (MP sí hay: MPANT49)'),
    ('SPHMC52', 'TSH semicuantitativa', '(ninguno la usa)', 'TSH', '', 'FALTA SOLUCIÓN + hoja sin producto'),
    ('SPHMT01', 'Biotina', 'Ecohem, Isolister, Salmonet, VPH Net (PCR)', 'Biotina', 'SPSCA08', 'OK'),
]

# solucion, analito, hojas que la ocuparian, estado
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
    ('SPSCA20', 'Hemoglobina glicada', '(ninguna)', 'NO HAY hoja maestra de HbA1c'),
    ('SPSCA22', 'Rotavirus', 'SPHMC27', 'Hoja aún sin ruta de laminado'),
    ('SPSCA23', 'Adenovirus', 'SPHMC27', 'Hoja aún sin ruta de laminado'),
    ('SPSCA13', 'IgG humana', 'SPHMC18 y además SPHMC49, 62, 69, 70, 80, 85-88', 'Sirve a varias hojas'),
    ('SPSCA14', 'IgM humana', 'SPHMC18 y además SPHMC49, 62, 69, 70, 80, 85-88', 'Sirve a varias hojas'),
]

# que falta dar de alta
FALTANTES = [
    ('Línea de control', 'MPANT03 Anticuerpo policlonal anti-ratón (línea control)',
     'TODAS las 15 hojas', 'La tira lleva línea de prueba Y línea de control. Hoy no hay solución para la de control.'),
    ('anti-p24', 'MPANT41 Anticuerpo de captura anti-p24', 'SPHMC23', 'El MP ya existe.'),
    ('anti-TSH', 'MPANT55 Anticuerpo de captura anti-TSH', 'SPHMC37, SPHMC52', 'El MP ya existe.'),
    ('anti-Salmonella', 'MPANT49 Anticuerpo de captura anti-Salmonella', 'SPHMC45', 'El MP ya existe.'),
    ('anti-hemoglobina humana', '(no existe el MP)', 'SPHMC07',
     'Es hemoglobina cualitativa (sangre oculta), NO glicada. Falta el anticuerpo en el catálogo.'),
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
    ws.row_dimensions[4].height = 30
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
         'Qué solución de captura se imprime en la membrana de cada una.',
         [('Hoja', 11), ('Nombre', 26), ('Producto terminado', 40),
          ('Línea de prueba', 34), ('Solución de captura', 20), ('Estado', 34)])
for n, f in enumerate(LAMINADAS):
    pinta(ws, 5 + n, list(f), rojo if f[5].startswith('FALTA') else verde)

ws2 = wb.create_sheet('Faltan por dar de alta')
encabeza(ws2, 'Soluciones de captura que faltan',
         'Cinco huecos. Cuatro tienen el anticuerpo ya en el catálogo; uno no.',
         [('Solución que falta', 26), ('Anticuerpo / antígeno', 46),
          ('Hojas afectadas', 24), ('Nota', 62)])
for n, f in enumerate(FALTANTES):
    pinta(ws2, 5 + n, list(f), ambar)

ws3 = wb.create_sheet('Las otras 17 soluciones')
encabeza(ws3, 'Soluciones ya dadas de alta que ninguna hoja laminada ocupa todavía',
         'Son para hojas que hoy no se laminan aquí. No sobran: esperan su hoja.',
         [('Solución', 12), ('Analito', 26), ('Hojas que la ocuparían', 44), ('Nota', 52)])
for n, f in enumerate(COBERTURA):
    pinta(ws3, 5 + n, list(f))

wb.save('/tmp/claude-1001/-home-agentia-odoo-odoo-workspace/40e1928e-dd87-4d8e-b8a3-401e8c22dfcd/scratchpad/Hojas_maestras_vs_soluciones_captura.xlsx')
print('OK: %d laminadas, %d faltantes, %d cobertura' % (len(LAMINADAS), len(FALTANTES), len(COBERTURA)))
