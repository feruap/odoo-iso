FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    wkhtmltopdf \
    python3 \
    curl \
    fonts-liberation \
    fontconfig \
    libfontconfig1 \
    && rm -rf /var/lib/apt/lists/*

# Download the local Odoo 19 deb file via host network
RUN curl -o /tmp/odoo.deb http://host.docker.internal:8085/odoo_19.0.20260316_all.deb
RUN apt-get update && apt-get install -y /tmp/odoo.deb \
    && rm -rf /var/lib/apt/lists/* \
    && rm /tmp/odoo.deb

# Copy custom fonts if any exist in the repository
COPY ./fonts /usr/share/fonts/truetype/custom/
RUN fc-cache -fv || true

USER odoo

EXPOSE 8069

CMD ["odoo"]
