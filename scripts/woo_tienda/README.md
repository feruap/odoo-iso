# Cambios en la tienda WooCommerce (www.amunet.com.mx) que no tienen git propio

Servidor 89.117.21.3, docroot /home/amunet/htdocs/www.amunet.com.mx. La tienda NO esta en git;
aqui se guarda copia de lo que Claude cambio para que quede versionado junto a Odoo.

- `amunet-agente-backorder.php` -> wp-content/mu-plugins/. Agentes SalesKing comprando como
  cliente pueden pedir sin existencia; la partida queda "Pendiente de produccion: N pz"
  (meta `_amunet_pendiente`). Odoo lo lee (amunet_production_plan, amunet.woo.pending.line).
- `crms_posible_vs_inventario_20260903.patch` -> parche a
  wp-content/plugins/custom-raw-material-stock-display/custom-raw-material-stock-display.php:
  productos administrados por Odoo (`_amunet_inv_raiz`) ignoran el stock virtual del APT y
  leen la existencia del filtro de amunet-inventario.
- Opciones cambiadas: `apt_expiration_movement_enabled` = no (04-sep-2026).

IMPORTANTE: el servidor tiene opcache.validate_timestamps=0. Tras cambiar PHP:
`systemctl reload php8.3-fpm` y purgar WP Rocket (`rm -rf wp-content/cache/wp-rocket/www.amunet.com.mx*/`).
