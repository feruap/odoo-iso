# Amunet - Conector WooCommerce

Sincroniza el inventario de producto terminado de Odoo hacia la tienda
WooCommerce (`www.amunet.com.mx` / `tst.amunet.com.mx`) mediante la API REST
`wc/v3`. Odoo es la fuente de verdad de las existencias; WooCommerce las recibe.

## Que hace

- **Tiendas conectadas** (`Inventario > WooCommerce > Tiendas conectadas`):
  URL de la tienda + consumer key/secret de la API REST de WooCommerce.
- **Importar catalogo Woo**: descarga productos y variaciones de WooCommerce
  y los empareja con productos de Odoo por SKU (`default_code`).
- **Publicar existencias**: envia la cantidad disponible (configurable:
  disponible sin reservas, a la mano o pronosticado, por almacen) a
  `stock_quantity` de cada producto/variacion Woo, en lotes de 100.
- **Cron cada 30 minutos** (opcional, campo "Sincronizacion automatica"):
  publica solo los productos cuya cantidad cambio desde el ultimo envio.
- **Bitacora auditable**: cada corrida queda registrada con totales,
  fallos y detalle (trazabilidad ISO 13485).

## Puesta en marcha (primero en staging)

1. En WordPress **tst.amunet.com.mx**: WooCommerce > Ajustes > Avanzado >
   API REST > "Agregar clave", permiso **Lectura/Escritura**. Copiar
   consumer key y consumer secret (el secret solo se muestra una vez).
2. Si un plugin de seguridad bloquea la API REST (error
   `rest_cannot_access`), permitir el espacio de nombres `wc/v3` para
   peticiones autenticadas de WooCommerce.
3. En Odoo staging: instalar `amunet_woocommerce` (Aplicaciones >
   Actualizar lista) y asignar el grupo "WooCommerce / Responsable".
4. Crear la tienda con entorno "Staging (tst)", capturar llaves y
   **Probar conexion**.
5. **Importar catalogo Woo** y revisar los mapeos: corregir SKU sin
   emparejar y desactivar los que no deban sincronizarse.
6. **Publicar existencias ahora** y verificar cantidades en la tienda tst.
7. Solo despues de validar en staging, repetir con www.amunet.com.mx.

## Consideraciones

- Los SKU deben coincidir entre Odoo (`default_code`) y WooCommerce.
- Cantidades negativas se publican como 0; WooCommerce maneja enteros.
- El envio activa `manage_stock` en cada producto Woo sincronizado.
- Pendiente validar convivencia con el plugin de WordPress
  "AlmacenPT - Producto Terminado": si ese plugin tambien escribe stock,
  definir cual manda antes de activar la sincronizacion automatica.
- Modulo nuevo: `odoo -u all` no lo instala; instalar desde Aplicaciones.
