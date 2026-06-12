# Extiende la imagen oficial de Odoo 19 y agrega fuentes personalizadas
# Ordenado para maximizar reuso de cache: capas estables ANTES de capas que cambian seguido.
FROM odoo:19.0

USER root

# Capa estable 1: Fuente Cambria (rara vez cambia)
COPY fonts/cambria/ /usr/share/fonts/truetype/cambria/
RUN fc-cache -f

# Capa estable 2: Patch mail manifest. NO depende de addons,
# se mueve aqui para que el cambio de addons NO invalide esta capa.
RUN python3 -c "\
import re, glob;\
paths = glob.glob('/usr/lib/python3/dist-packages/*/addons/mail/__manifest__.py') + \
        glob.glob('/usr/lib/python3/dist-packages/addons/mail/__manifest__.py');\
target = \"'description': 'Chat, email gateway and private channel.',\";\
[(lambda c: open(p,'w').write(re.sub(r\"'description'\\s*:\\s*\\\"\\\"\\\"[\\s\\S]*?\\\"\\\"\\\"\\s*,\", target, c)))(open(p).read()) for p in paths];\
print(f'Patched {len(paths)} mail manifest(s)');\
"

# Capa volatil 3: addons (cambia casi cada commit). --chown integrado evita
# un RUN chown -R posterior que tomaba ~37s sobre 90MB de archivos.
COPY --chown=odoo:odoo addons/ /opt/amunet-addons/
COPY --chown=odoo:odoo odoo_server.conf /etc/odoo/odoo.conf

USER odoo
