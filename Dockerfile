# Extiende la imagen oficial de Odoo 19 y agrega fuentes personalizadas
FROM odoo:19.0

USER root

# Instalar fuente Cambria (necesaria para generar PDFs con la misma tipografía que los documentos Word)
COPY fonts/cambria/ /usr/share/fonts/truetype/cambria/
RUN fc-cache -f

USER odoo
