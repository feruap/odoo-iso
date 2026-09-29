"""PCR rapida: fuera caducidad corta y cortesia. Un solo corte a 2 meses.

Decision de Mery el 28-sep-2026, sobre la propuesta de Luis del 10-sep:

    "Para la PCR rapida no debe existir la regla de caducidad corta y cortesia, ya
     que son pruebas que unicamente tienen seis meses de vida. Entonces cuando
     tenga solo ya dos meses, que se pase a dar de baja."

ANTES (lo que Mery y Fernando habian propuesto y Luis no acepto): los tres tramos
encogidos -- corta a 2 meses, cortesia a 1 mes, retiro a 10 dias.

AHORA: un solo corte. Normal hasta que le quedan 2 meses; por debajo de eso, sale
de venta.

COMO SE LOGRA: los tres umbrales en 2 meses. La condicion se evalua en este orden
-- retiro, cortesia, corta -- asi que poniendo retiro=2 todo lo que baje de 2 meses
cae en 'retirar' y los otros dos tramos nunca se alcanzan. No hace falta tocar
codigo: los umbrales por categoria son un parametro.

    {"Producto terminado / Pruebas PCR rapida": {"corta": 2, "cortesia": 2, "retiro": 2}}

Las pruebas rapidas INMUNOLOGICAS no cambian: siguen con sus tres tramos (6 / 4 /
1 meses), porque viven 24 meses y ahi el recorrido de promocion si tiene sentido.

LO QUE NO SE HACE, porque no existe todavia: Luis pidio que ese material pase a un
apartado de CAPACITACION en vez de a retenidos. Ese anaquel no esta creado. Con
este cambio el material cae en el anaquel de RETENIDOS, que es lo que hay hoy.
Queda planteado a Mery y Fernando.

Idempotente.
"""
import json

Param = env['ir.config_parameter'].sudo()
CLAVE = 'amunet_caducidad.umbrales_por_categoria'
CATEG_PCR = 'Producto terminado / Pruebas PCR rápida'
NUEVO = {'corta': 2, 'cortesia': 2, 'retiro': 2}

actual_txt = Param.get_param(CLAVE) or ''
print('valor guardado en la base: %s' % (actual_txt or '(no hay: usa el del codigo)'))
try:
    actual = json.loads(actual_txt) if actual_txt else {}
except (ValueError, TypeError):
    print('   el valor guardado no es un JSON valido, se reescribe')
    actual = {}

if actual.get(CATEG_PCR) == NUEVO:
    print('[ya] la PCR rapida ya tiene el corte unico a 2 meses')
else:
    antes = actual.get(CATEG_PCR)
    actual[CATEG_PCR] = NUEVO
    Param.set_param(CLAVE, json.dumps(actual, ensure_ascii=False))
    print('[ok] PCR rapida: %s -> %s' % (antes or '(los del codigo: 2/1/10 dias)', NUEVO))

# --- comprobacion: que devuelve el sistema para cada tramo
Lot = env['stock.lot'].sudo()
print('\n=== como queda una PCR rapida, dia por dia ===')
import datetime
hoy = datetime.date.today()
for dias in (200, 90, 70, 61, 59, 45, 31, 20, 9, 1, -1):
    cond, d = Lot._amunet_condicion(hoy + datetime.timedelta(days=dias),
                                    hoy=hoy, categoria=CATEG_PCR)
    print('   le quedan %4s dias (%4.1f meses) -> %s' % (dias, dias / 30.0, cond))

print('\n=== y una prueba rapida inmunologica (no debe cambiar) ===')
CATEG_INM = 'Producto terminado / Pruebas rápidas inmunológicas'
for dias in (400, 200, 150, 100, 45, 20, 5):
    cond, d = Lot._amunet_condicion(hoy + datetime.timedelta(days=dias),
                                    hoy=hoy, categoria=CATEG_INM)
    print('   le quedan %4s dias (%4.1f meses) -> %s' % (dias, dias / 30.0, cond))
env.cr.commit()
