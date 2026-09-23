#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""amunet-pagos-bot

Une Odoo con Telegram para el visto bueno de compras generales.

Dos trabajos en el mismo proceso:

  1. Cada POLL_ODOO segundos busca solicitudes en 'por_enviar' (las que el
     jefe acaba de autorizar) y le manda a Fernando un mensaje con dos
     botones a su privado. Un mensaje por solicitud y nada mas: si no
     responde, no se insiste.

  2. Escucha getUpdates en long-polling. Cuando llega un callback_query de
     sus propios botones lo valida y lo resuelve.

Por que long-polling y no webhook: @Transferfzbot no tiene webhook, y
montarle uno obligaria a exponer un endpoint. getUpdates no toca nada
externo. El bot de depositos (@Controldepositosbot) SI tiene webhook en
produccion y aqui no se le toca.

Seguridad del boton (el callback_data viaja por el cliente):
  * solo se atiende a from.id == DM_DUENO
  * callback_data firmado con HMAC-SHA256 contra un secreto en
    ir_config_parameter, que incluye un token propio de esa solicitud
  * idempotente: solo resuelve si el estado sigue en 'pendiente', asi que
    un segundo clic no publica dos veces
"""

import hashlib
import hmac
import html
import json
import logging
import os
import subprocess
import time
import zoneinfo
import urllib.error
import urllib.parse
import urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))


def cargar_env():
    cfg = {}
    with open(os.path.join(BASE, '.env'), encoding='utf-8') as fh:
        for linea in fh:
            linea = linea.strip()
            if not linea or linea.startswith('#') or '=' not in linea:
                continue
            k, v = linea.split('=', 1)
            cfg[k.strip()] = v.strip().strip('"').strip("'")
    return cfg


CFG = cargar_env()
TOKEN = CFG['TELEGRAM_PAGOS_BOT_TOKEN']
DM_DUENO = str(CFG['TELEGRAM_DM_DUENO'])
GRUPO = str(CFG['TELEGRAM_GRUPO_DEPOSITOS_MK'])
ORIGEN_CON_FACTURA = CFG.get('ORIGEN_CON_FACTURA', 'la cuenta de Amunet')
ORIGEN_SIN_FACTURA = CFG.get('ORIGEN_SIN_FACTURA', 'RB')
DB = CFG.get('ODOO_DB', 'amunet_prod')
DB_CONTENEDOR = CFG.get('ODOO_DB_CONTENEDOR', 'odoo-production-db')
POLL_ODOO = int(CFG.get('POLL_ODOO', '20'))
# Corte de pagos: las ordenes autorizadas no salen una por una, se juntan y
# salen todas a esta hora, de lunes a viernes.
CORTE_HORA = int(CFG.get('CORTE_HORA', '15'))
ZONA = CFG.get('ZONA_HORARIA', 'America/Mexico_City')
# Quien recibe y ordena los comprobantes. Vacio = no se reenvian.
ARCHIVISTA = str(CFG.get('TELEGRAM_ARCHIVISTA', '') or '')
COMPROBANTES = os.path.join(BASE, 'comprobantes')

# Interruptor unico de pruebas. Con MODO_PRUEBA=1 TODO lo que saldria al
# grupo de pagos y al archivista se desvia al privado de Fernando. Es un
# solo cambio para salir a produccion, en vez de acordarse de dos ids.
MODO_PRUEBA = CFG.get('MODO_PRUEBA', '0') == '1'
GRUPO_REAL, ARCHIVISTA_REAL = GRUPO, ARCHIVISTA
if MODO_PRUEBA:
    GRUPO = ARCHIVISTA = DM_DUENO

API = 'https://api.telegram.org/bot%s/' % TOKEN

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('pagos-bot')


def sql(consulta):
    """Lista de dicts. Se habla con Postgres por docker exec: el contenedor
    de la base no publica puerto y este servicio corre en el mismo host."""
    salida = subprocess.run(
        ['docker', 'exec', DB_CONTENEDOR, 'psql', '-U', 'odoo', '-d', DB, '-At', '-c', consulta],
        capture_output=True, text=True, timeout=30,
    )
    if salida.returncode != 0:
        raise RuntimeError('psql fallo: %s' % salida.stderr.strip()[:300])
    return [json.loads(l) for l in salida.stdout.strip().splitlines() if l.strip()]


def escapar(valor):
    return str(valor).replace("'", "''")


def secreto_hmac():
    filas = sql("select row_to_json(t) from (select value from ir_config_parameter "
                "where key='amunet_compras_general.hmac_secret') t")
    if not filas:
        raise RuntimeError('no hay secreto HMAC todavia en ir_config_parameter')
    return filas[0]['value']


def firma(solicitud_id, token, respuesta):
    mensaje = '%s|%s|%s' % (solicitud_id, token or '', respuesta)
    return hmac.new(secreto_hmac().encode(), mensaje.encode(), hashlib.sha256).hexdigest()[:16]

CONSULTA_SOLICITUD = """
select row_to_json(t) from (
  select r.id, r.name, r.amunet_forma_pago, r.amunet_proveedor_factura,
         r.amunet_monto, r.amunet_banco, r.amunet_clabe, r.amunet_titular,
         r.amunet_referencia_pago, r.amunet_concepto_pago,
         r.amunet_autorizacion_estado, r.amunet_autorizacion_token,
         r.amunet_telegram_msg_id,
         coalesce(c.name, 'MXN') as moneda,
         coalesce(ps.name, '?') as solicitante,
         coalesce(pj.name, '') as jefe,
         (select string_agg(coalesce(pt.default_code,'') || ' ' ||
                 coalesce(pt.name->>'es_MX', pt.name->>'en_US', l.name, '') ||
                 ' x' || trim(to_char(l.qty,'FM999999.99')), ', ')
            from amunet_solicitud_compra_line l
            left join product_product pp on pp.id = l.product_id
            left join product_template pt on pt.id = pp.product_tmpl_id
           where l.request_id = r.id) as productos
    from amunet_solicitud_compra r
    left join res_currency c on c.id = r.amunet_currency_id
    left join res_users us on us.id = r.requester_id
    left join res_partner ps on ps.id = us.partner_id
    left join res_users uj on uj.id = r.amunet_autorizada_por_id
    left join res_partner pj on pj.id = uj.partner_id
   where %s
) t
"""


def solicitudes_por_enviar():
    return sql(CONSULTA_SOLICITUD % (
        "r.amunet_autorizacion_estado = 'por_enviar' "
        "and r.state not in ('cancelled', 'closed')"))


def solicitud(solicitud_id):
    filas = sql(CONSULTA_SOLICITUD % ('r.id = %d' % int(solicitud_id)))
    return filas[0] if filas else None


def marcar(solicitud_id, estado, msg_id=None, con_fecha=False):
    partes = ["amunet_autorizacion_estado = '%s'" % escapar(estado)]
    if msg_id is not None:
        partes.append("amunet_telegram_msg_id = '%s'" % escapar(msg_id))
    if con_fecha:
        partes.append("amunet_autorizacion_fecha = (now() at time zone 'utc')")
    sql("with u as (update amunet_solicitud_compra set %s where id = %d returning id) "
        "select row_to_json(u) from u" % (', '.join(partes), int(solicitud_id)))


def tg(metodo, **datos):
    cuerpo = urllib.parse.urlencode(
        {k: (json.dumps(v) if isinstance(v, (dict, list)) else v)
         for k, v in datos.items() if v is not None}).encode()
    peticion = urllib.request.Request(API + metodo, data=cuerpo)
    try:
        with urllib.request.urlopen(peticion, timeout=70) as respuesta:
            return json.loads(respuesta.read().decode())
    except urllib.error.HTTPError as error:
        # Telegram dice el motivo real en el cuerpo de la respuesta. urllib lo
        # descarta si uno deja escapar la excepcion, y el log queda en un
        # inutil "400 Bad Request". Aqui se lee y se registra.
        try:
            detalle = json.loads(error.read().decode())
        except Exception:
            detalle = {'ok': False, 'description': 'HTTP %s' % error.code}
        log.error('Telegram %s -> %s', metodo, detalle.get('description'))
        return detalle


def importe(sol):
    monto = sol.get('amunet_monto')
    if monto in (None, ''):
        return None
    return '%s %s' % ('{:,.2f}'.format(float(monto)), sol.get('moneda') or 'MXN')


def texto_para_fernando(sol):
    lineas = [
        '<b>VISTO BUENO DE COMPRA</b>', '',
        '<b>%s</b>' % html.escape(sol['name']),
        'Pide: %s' % html.escape(sol.get('solicitante') or '?'),
        'Autorizo el jefe: %s' % html.escape(sol.get('jefe') or '?'), '',
        html.escape((sol.get('productos') or 'sin lineas')[:400]), '',
    ]
    imp = importe(sol)
    lineas.append('Importe: <b>%s</b>' % html.escape(imp) if imp else 'Importe: <i>sin capturar</i>')
    forma = sol.get('amunet_forma_pago')
    if forma == 'transferencia':
        lineas.append('Pago: transferencia%s' % (
            ' (CON factura)' if sol.get('amunet_proveedor_factura') else ' (SIN factura)'))
        lineas.append('A: %s - %s' % (html.escape(sol.get('amunet_titular') or '?'),
                                      html.escape(sol.get('amunet_banco') or '?')))
        lineas.append('Si autorizas, se publica la orden de pago en "depositos mk".')
    elif forma == 'tarjeta':
        lineas.append('Pago: tarjeta en tienda')
        lineas.append('Si autorizas, se prepara la compra y te la confirmo antes de pagar.')
    else:
        lineas.append('Pago: por definir')
    return '\n'.join(lineas)


def texto_para_grupo(sol):
    origen = ORIGEN_CON_FACTURA if sol.get('amunet_proveedor_factura') else ORIGEN_SIN_FACTURA
    imp = importe(sol) or 'IMPORTE SIN CAPTURAR'
    lineas = [
        '<b>ORDEN DE PAGO (Odoo)</b> - no es un aviso de deposito', '',
        'Favor de hacer una transferencia desde <b>%s</b> por la cantidad de <b>%s</b>'
        % (html.escape(origen), html.escape(imp)),
        'A nombre de: <b>%s</b>' % html.escape(sol.get('amunet_titular') or '?'),
        'CLABE: <code>%s</code>' % html.escape(sol.get('amunet_clabe') or '?'),
        'Banco: %s' % html.escape(sol.get('amunet_banco') or '?'),
    ]
    if sol.get('amunet_referencia_pago'):
        lineas.append('Referencia: %s' % html.escape(sol['amunet_referencia_pago']))
    if sol.get('amunet_concepto_pago'):
        lineas.append('Concepto: %s' % html.escape(sol['amunet_concepto_pago']))
    lineas += ['',
               'Cuando este pagado, <b>responde a este mensaje</b> con la foto '
               'del comprobante.']
    return '\n'.join(lineas)


def botones(sol):
    tok = sol.get('amunet_autorizacion_token')
    return {'inline_keyboard': [[
        {'text': 'Si, autorizo', 'callback_data': 'ap:%s:s:%s' % (sol['id'], firma(sol['id'], tok, 's'))},
        {'text': 'No', 'callback_data': 'ap:%s:n:%s' % (sol['id'], firma(sol['id'], tok, 'n'))},
    ]]}

# ---------------------------------------------------------- corte de pagos
def _ahora_local():
    return __import__('datetime').datetime.now(zoneinfo.ZoneInfo(ZONA))


def _marca_corte(valor=None):
    """Ultimo dia en que ya se hizo el corte, guardado en disco para que un
    reinicio del servicio no dispare un segundo corte el mismo dia."""
    ruta = os.path.join(BASE, '.ultimo_corte')
    if valor is None:
        try:
            with open(ruta, encoding='utf-8') as fh:
                return fh.read().strip()
        except FileNotFoundError:
            return ''
    with open(ruta, 'w', encoding='utf-8') as fh:
        fh.write(valor)
    return valor


def toca_corte():
    ahora = _ahora_local()
    if ahora.weekday() > 4:          # sabado y domingo no hay corte
        return False
    if ahora.hour < CORTE_HORA:
        return False
    return _marca_corte() != ahora.strftime('%Y-%m-%d')


def publicar_corte():
    """Publica juntas todas las ordenes de pago autorizadas y no publicadas."""
    hoy = _ahora_local()
    pendientes = sql(CONSULTA_SOLICITUD % (
        "r.amunet_autorizacion_estado = 'autorizado' "
        "and r.amunet_forma_pago = 'transferencia' "
        "and r.amunet_pago_publicado is null "
        "and r.state not in ('cancelled', 'closed')"))
    if not pendientes:
        _marca_corte(hoy.strftime('%Y-%m-%d'))
        log.info('corte %s: nada que pagar', hoy.strftime('%Y-%m-%d'))
        return

    total = sum(float(x.get('amunet_monto') or 0) for x in pendientes)
    encabezado = tg('sendMessage', chat_id=GRUPO, parse_mode='HTML', text=(
        '<b>CORTE DE PAGOS %s</b>\n'
        '%d transferencia(s) por un total de <b>%s MXN</b>\n\n'
        'Cada pago va en su propio mensaje abajo. Al pagarlo, responde a ESE '
        'mensaje con la foto del comprobante.'
        % (hoy.strftime('%d/%m/%Y'), len(pendientes), '{:,.2f}'.format(total))))
    if not encabezado.get('ok'):
        log.error('no se pudo abrir el corte; no se publica nada')
        return

    for sol in pendientes:
        publicado = tg('sendMessage', chat_id=GRUPO, parse_mode='HTML',
                       text=texto_para_grupo(sol))
        if not publicado.get('ok'):
            log.error('no se publico %s', sol['name'])
            continue
        sql("with u as (update amunet_solicitud_compra set "
            "amunet_pago_publicado = (now() at time zone 'utc'), "
            "amunet_telegram_grupo_msg_id = '%s' where id = %d returning id) "
            "select row_to_json(u) from u"
            % (escapar(publicado['result']['message_id']), int(sol['id'])))
        log.info('publicado en el corte: %s', sol['name'])
    _marca_corte(hoy.strftime('%Y-%m-%d'))


# ------------------------------------------------------------ comprobantes
def por_mensaje_de_grupo(msg_id):
    filas = sql(CONSULTA_SOLICITUD % (
        "r.amunet_telegram_grupo_msg_id = '%s'" % escapar(msg_id)))
    return filas[0] if filas else None


def registrar_privado(mensaje):
    """Deja constancia de quien le escribe al bot en privado.

    Telegram no deja que un bot escriba primero a una persona: esa persona
    tiene que mandarle algo antes. El id con el que hay que configurarlo solo
    aparece en ese mensaje, y si el bot lo descarta en silencio no hay forma
    de recuperarlo despues. Por eso se registra aqui."""
    chat = mensaje.get('chat') or {}
    if chat.get('type') != 'private':
        return
    quien = mensaje.get('from') or {}
    if str(quien.get('id')) == DM_DUENO:
        return
    nombre = ' '.join(filter(None, [quien.get('first_name'), quien.get('last_name')])) or '?'
    log.info('PRIVADO de %s (@%s) id=%s: %r', nombre, quien.get('username') or '-',
             quien.get('id'), (mensaje.get('text') or '')[:60])


def guardar_comprobante(mensaje):
    """Quien paga responde a la orden con la foto. Esa respuesta es lo unico
    que el bot ve del grupo (modo privacidad activo), y ademas dice a que
    pago pertenece la imagen sin que nadie tenga que escribirlo."""
    respondido = (mensaje.get('reply_to_message') or {}).get('message_id')
    if not respondido:
        return
    sol = por_mensaje_de_grupo(respondido)
    if not sol:
        return

    fotos = mensaje.get('photo') or []
    documento = mensaje.get('document')
    file_id = fotos[-1]['file_id'] if fotos else (documento or {}).get('file_id')
    if not file_id:
        return

    quien = mensaje.get('from', {})
    nombre_quien = ' '.join(filter(None, [quien.get('first_name'), quien.get('last_name')])) or '?'

    ruta = ''
    try:
        info = tg('getFile', file_id=file_id)
        if info.get('ok'):
            origen = info['result']['file_path']
            os.makedirs(COMPROBANTES, exist_ok=True)
            destino = os.path.join(COMPROBANTES, '%s-%s%s' % (
                sol['name'].replace('/', '-'),
                _ahora_local().strftime('%Y%m%d-%H%M%S'),
                os.path.splitext(origen)[1] or '.jpg'))
            url = 'https://api.telegram.org/file/bot%s/%s' % (TOKEN, origen)
            with urllib.request.urlopen(url, timeout=60) as r, open(destino, 'wb') as fh:
                fh.write(r.read())
            ruta = destino
    except Exception:
        log.exception('no se pudo descargar el comprobante de %s', sol['name'])

    sql("with u as (update amunet_solicitud_compra set "
        "amunet_comprobante_fecha = (now() at time zone 'utc'), "
        "amunet_comprobante_archivo = '%s' where id = %d returning id) "
        "select row_to_json(u) from u" % (escapar(ruta), int(sol['id'])))

    if ARCHIVISTA:
        pie = ('COMPROBANTE DE PAGO\n%s\n%s\nA nombre de: %s\nBanco: %s\n'
               'Pago subido por: %s el %s'
               % (sol['name'], importe(sol) or 'sin importe',
                  sol.get('amunet_titular') or '?', sol.get('amunet_banco') or '?',
                  nombre_quien, _ahora_local().strftime('%d/%m/%Y %H:%M')))
        enviado = tg('copyMessage', chat_id=ARCHIVISTA, from_chat_id=GRUPO,
                     message_id=mensaje['message_id'], caption=pie[:1020])
        if not enviado.get('ok'):
            log.error('no se pudo reenviar el comprobante de %s: %s',
                      sol['name'], enviado.get('description'))
    log.info('comprobante recibido de %s (%s)', sol['name'], nombre_quien)


def enviar_pendientes():
    for sol in solicitudes_por_enviar():
        try:
            resultado = tg('sendMessage', chat_id=DM_DUENO, parse_mode='HTML',
                           text=texto_para_fernando(sol), reply_markup=botones(sol))
            if not resultado.get('ok'):
                log.error('no se pudo avisar de %s: %s', sol['name'], resultado.get('description'))
                continue
            marcar(sol['id'], 'pendiente', msg_id=str(resultado['result']['message_id']))
            log.info('aviso enviado: %s', sol['name'])
        except Exception:
            log.exception('fallo al avisar de %s', sol.get('name'))


def resolver(callback):
    datos = callback.get('data') or ''
    quien = str(callback.get('from', {}).get('id'))
    cb_id = callback['id']

    if quien != DM_DUENO:
        tg('answerCallbackQuery', callback_query_id=cb_id,
           text='Solo Fernando puede autorizar.', show_alert=True)
        log.warning('clic de un tercero: uid=%s data=%s', quien, datos)
        return

    partes = datos.split(':')
    if len(partes) != 4 or partes[0] != 'ap':
        tg('answerCallbackQuery', callback_query_id=cb_id, text='Boton no reconocido.')
        return
    _, sid, respuesta, firma_recibida = partes

    sol = solicitud(sid)
    if not sol:
        tg('answerCallbackQuery', callback_query_id=cb_id, text='Esa solicitud ya no existe.')
        return
    esperada = firma(sol['id'], sol.get('amunet_autorizacion_token'), respuesta)
    if not hmac.compare_digest(firma_recibida, esperada):
        tg('answerCallbackQuery', callback_query_id=cb_id,
           text='Firma invalida. No se hizo nada.', show_alert=True)
        log.warning('firma invalida en %s', sol['name'])
        return
    if sol.get('amunet_autorizacion_estado') != 'pendiente':
        tg('answerCallbackQuery', callback_query_id=cb_id,
           text='Ya se habia atendido (%s).' % sol.get('amunet_autorizacion_estado'))
        return

    tg('answerCallbackQuery', callback_query_id=cb_id,
       text='Autorizando...' if respuesta == 's' else 'Rechazando...')

    if respuesta == 's':
        marcar(sol['id'], 'autorizado', con_fecha=True)
        cierre = '\n\n<b>AUTORIZADO</b>'
        if sol.get('amunet_forma_pago') == 'transferencia':
            cierre += ('\nEntra al corte de pagos de las %02d:00 '
                       '(lunes a viernes).' % CORTE_HORA)
        else:
            cierre += '\nClaude preparara la compra y te la confirmara antes de pagar.'
    else:
        marcar(sol['id'], 'rechazado', con_fecha=True)
        cierre = '\n\n<b>RECHAZADO</b> - no se publico nada.'

    editado = tg('editMessageText', chat_id=DM_DUENO,
                 message_id=sol.get('amunet_telegram_msg_id'),
                 parse_mode='HTML', text=texto_para_fernando(sol) + cierre,
                 reply_markup={'inline_keyboard': []})
    if not editado.get('ok'):
        # Si no se puede editar, al menos que quede claro en el chat que se
        # resolvio; un mensaje sin cerrar invita a volver a picarle.
        tg('sendMessage', chat_id=DM_DUENO, parse_mode='HTML',
           text='%s%s' % (html.escape(sol['name']), cierre))
    log.info('%s -> %s', sol['name'], 'autorizado' if respuesta == 's' else 'rechazado')


def main():
    log.info('arranca amunet-pagos-bot (db=%s) %s', DB,
             'MODO PRUEBA: todo va al privado de Fernando' if MODO_PRUEBA
             else 'EN VIVO: grupo=%s archivista=%s' % (GRUPO, ARCHIVISTA or 'sin configurar'))
    offset = None
    ultimo_scan = 0.0
    while True:
        try:
            if time.time() - ultimo_scan > POLL_ODOO:
                enviar_pendientes()
                ultimo_scan = time.time()
            if toca_corte():
                publicar_corte()
            respuesta = tg('getUpdates', offset=offset, timeout=25,
                           allowed_updates=['callback_query', 'message'])
            for update in respuesta.get('result', []):
                offset = update['update_id'] + 1
                if 'callback_query' in update:
                    try:
                        resolver(update['callback_query'])
                    except Exception:
                        log.exception('fallo al resolver un boton')
                elif 'message' in update:
                    try:
                        registrar_privado(update['message'])
                        guardar_comprobante(update['message'])
                    except Exception:
                        log.exception('fallo al guardar un comprobante')
        except Exception:
            log.exception('ciclo con error; reintento en 10 s')
            time.sleep(10)


if __name__ == '__main__':
    main()