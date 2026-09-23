# -*- coding: utf-8 -*-
"""Rendimiento de lamina por almohadilla SPALMA — base para armar sus BoM.

Karla confirmo el 18-sep-2026 que las laminas llegan del proveedor en hojas
sueltas de 30 cm de largo, con estos anchos:

    MPAFV01  Almohadilla MDI          20.0 x 30 cm
    MPAFV02  Almohadilla Biotech      21.0 x 30 cm
    MPAAB01  Almohadilla Absorbente   19.9 x 30 cm
    MPAGR01  Filtro para sangre       25.0 x 30 cm

El proceso (explicado por Mery el 21-sep): se prepara la solucion en una charola,
se sumerge la LAMINA COMPLETA, se agita con el agitador orbital (equipo 88, en
Lectura y Pretratamiento) para impregnar parejo, se seca en el HORNO DE LAMINADO
(equipo 97, no el de Lectura) y ya seca se corta con la cortadora de hojas
(equipo 99) al tamano especifico.

Por eso el BoM va POR LAMINA (decision de Mery): produce N tiras y consume 1
lamina. Se pretrata y corta la lamina entera, no la tira suelta.

Este script SOLO CALCULA e imprime; no escribe nada. Sirve para armar los BoM
cuando Mery defina los tres datos que faltan:
  1. A9 y A10 ("intermedia P" y "intermedia s"): se pretratan o solo se cortan?
  2. SPSPA02 vs SPSPA03: las dos se llaman "para almohadilla de muestra".
  3. Ml de solucion por lamina (el minimo es 200 ml por charola, pero varia).
"""
LAMINA = {
    'MPAFV01': (20.0, 'Almohadilla MDI'),
    'MPAFV02': (21.0, 'Almohadilla Biotech'),
    'MPAAB01': (19.9, 'Almohadilla Absorbente'),
    'MPAGR01': (25.0, 'Filtro para sangre'),
}
# clave, alias, ancho de tira (cm), materia prima, objetivo, proceso
ALMOHADILLAS = [
    ('SPALMA01', 'A1',  0.7, 'MPAFV01', 'conjugado',  'pretrata'),
    ('SPALMA02', 'A2',  0.7, 'MPAFV01', 'conjugado',  'pretrata'),
    ('SPALMA03', 'A3',  0.5, 'MPAFV01', 'conjugado',  'pretrata'),
    ('SPALMA04', 'A4',  1.4, 'MPAFV01', 'muestra',    'pretrata'),
    ('SPALMA05', 'A5',  1.4, 'MPAFV01', 'muestra',    'pretrata'),
    ('SPALMA06', 'A6',  1.1, 'MPAFV02', 'muestra',    'pretrata'),
    ('SPALMA07', 'A7',  1.1, 'MPAFV02', 'muestra',    'pretrata'),
    ('SPALMA08', 'A8',  5.0, 'MPAFV02', 'muestra',    'pretrata'),
    ('SPALMA09', 'A9',  0.3, 'MPAFV01', 'intermedia', 'POR DEFINIR'),
    ('SPALMA10', 'A10', 3.0, 'MPAFV01', 'intermedia', 'POR DEFINIR'),
    ('SPALMA11', 'A11', 1.7, 'MPAAB01', 'absorbente', 'solo corta'),
    ('SPALMA12', 'A12', 3.0, 'MPAAB01', 'absorbente', 'solo corta'),
    ('SPALMA13', 'A13', 0.7, 'MPAGR01', 'filtracion', 'solo corta'),
]

def rendimiento(ancho_tira, ancho_lamina):
    """Tiras enteras que salen de una lamina, y el sobrante en cm."""
    tiras = int(ancho_lamina // ancho_tira)
    return tiras, round(ancho_lamina - tiras * ancho_tira, 2)

if __name__ == '__main__' or True:
    print('%-10s %-4s %-8s %-10s %-22s %8s %6s' % (
        'CLAVE', 'A', 'TIRA', 'GRANEL', 'MATERIA PRIMA', 'TIRAS', 'SOBRA'))
    for clave, alias, ancho, mp, objetivo, proceso in ALMOHADILLAS:
        lam, nombre = LAMINA[mp]
        tiras, sobra = rendimiento(ancho, lam)
        print('%-10s %-4s %5.1f cm %-10s %-22s %8d %5.2f cm   %s' % (
            clave, alias, ancho, mp, nombre, tiras, sobra, proceso))
