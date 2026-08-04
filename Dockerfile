# Extiende la imagen oficial de Odoo 19 y agrega fuentes personalizadas
FROM odoo:19.0

USER root

# Fuentes de las etiquetas (Cambria + Kollektif + Now). Kollektif/Now las usan
# las plantillas de etiquetas; sin ellas LibreOffice sustituye y el texto se
# desborda en la vista previa.
COPY fonts/cambria/ /usr/share/fonts/truetype/cambria/
COPY fonts/kollektif/ /usr/share/fonts/truetype/kollektif/
COPY fonts/now/ /usr/share/fonts/truetype/now/
RUN fc-cache -f

# python-pptx para el generador de etiquetas de caja (amunet_label / plan de empaque)
RUN pip install --no-cache-dir --break-system-packages python-pptx

# LibreOffice Impress (headless) para la vista previa de etiquetas (PPTX -> PNG).
RUN apt-get update && apt-get install -y --no-install-recommends \
        libreoffice-impress libreoffice-core \
    && rm -rf /var/lib/apt/lists/*

# Copiar addons y configuracion para evitar errores de montaje de volumenes de Git en Portainer
COPY addons/ /opt/amunet-addons/
COPY odoo_server.conf /etc/odoo/odoo.conf
RUN chown -R odoo:odoo /opt/amunet-addons /etc/odoo

# Patch mail module description to prevent docutils RST crash during odoo -u all
RUN python3 -c "\
import re, glob;\
paths = glob.glob('/usr/lib/python3/dist-packages/*/addons/mail/__manifest__.py') + \
        glob.glob('/usr/lib/python3/dist-packages/addons/mail/__manifest__.py');\
target = \"'description': 'Chat, email gateway and private channel.',\";\
[(lambda c: open(p,'w').write(re.sub(r\"'description'\\s*:\\s*\\\"\\\"\\\"[\\s\\S]*?\\\"\\\"\\\"\\s*,\", target, c)))(open(p).read()) for p in paths];\
print(f'Patched {len(paths)} mail manifest(s)');\
"

USER odoo
