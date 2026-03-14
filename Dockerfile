FROM odoo:18.0

USER root

# Install fonts
RUN apt-get update && \
    apt-get install -y --no-install-recommends fontconfig libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*

COPY ./fonts /usr/share/fonts/truetype/custom/
RUN fc-cache -fv

USER odoo
