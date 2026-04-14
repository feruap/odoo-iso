# Extiende la imagen oficial de Odoo 19 y agrega fuentes personalizadas
FROM odoo:19.0

USER root

# Instalar fuente Cambria (necesaria para generar PDFs con la misma tipografía que los documentos Word)
COPY fonts/cambria/ /usr/share/fonts/truetype/cambria/
RUN fc-cache -f

# Copiar addons y configuracion para evitar errores de montaje de volumenes de Git en Portainer
COPY addons/ /opt/amunet-addons/
COPY odoo_server.conf /etc/odoo/odoo.conf
RUN chown -R odoo:odoo /opt/amunet-addons /etc/odoo

# Patch mail module description to prevent docutils RST crash during odoo -u all
RUN python3 -c "\
import re, glob;\
paths = glob.glob('/usr/lib/python3/dist-packages/*/addons/mail/__manifest__.py') + \
        glob.glob('/usr/lib/python3/dist-packages/addons/mail/__manifest__.py');\
target = 'Chat, email gateway and private channel.';\
[open(p,'w').write(re.sub(r\"'description'\\s*:\\s*\\\"\\\"\\\"[^\\\"]*\\\"\\\"\\\"\", f\"'description': '{target}'\", open(p).read(), flags=re.DOTALL)) for p in paths];\
print(f'Patched {len(paths)} mail manifest(s)');\
"

USER odoo
