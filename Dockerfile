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

USER odoo
