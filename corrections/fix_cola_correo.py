# Arregla la cola de correo de Odoo (reportado por agente RRHH):
#  1. Descarta (cancel) los mails outgoing viejos con create_date <= 2026-07-01
#     (incluye el lote de 54 del 1-jul y stragglers de junio).
#  2. Limpia (cancel) los 47 mails en 'exception' (fallos viejos feb-jun).
#  3. Reactiva el cron "Mail: Email Queue Manager" (estaba desactivado desde ~enero)
#     y dispara el envio de la cola restante (recientes >= 8-jul).
# SMTP (Mailcow mail.amunet.com.mx:465) verificado OK. Autorizado Fernando 2026-07-23.
Mail = env['mail.mail'].sudo()

viejos = Mail.search([('state', '=', 'outgoing'), ('create_date', '<', '2026-07-02 00:00:00')])
print('Outgoing viejos a descartar:', len(viejos))
viejos.write({'state': 'cancel'})

errores = Mail.search([('state', '=', 'exception')])
print('Errores (exception) a limpiar:', len(errores))
errores.write({'state': 'cancel'})

recientes = Mail.search([('state', '=', 'outgoing')])
print('Outgoing recientes que quedan (se enviaran):', len(recientes))

from odoo import fields as _f
cron = env['ir.cron'].sudo().with_context(active_test=False).search([('cron_name', '=', 'Mail: Email Queue Manager')], limit=1)
assert cron, 'no existe el cron Email Queue Manager'
cron.write({'active': True, 'nextcall': _f.Datetime.now()})
print('Cron reactivado:', cron.cron_name, '| active:', cron.active)

env.cr.commit()

# disparar el envio de la cola ahora para verificar
Mail.process_email_queue()
env.cr.commit()

# estado final
env.cr.execute("SELECT state, count(*) FROM mail_mail GROUP BY state ORDER BY count DESC")
print('Estado final de la cola:', env.cr.fetchall())
print('LISTO')
