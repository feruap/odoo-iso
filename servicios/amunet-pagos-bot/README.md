# amunet-pagos-bot

Visto bueno de compras generales por Telegram.

    Odoo (jefe autoriza) -> 'por_enviar'
      -> bot manda DM a Fernando con botones Si/No
        -> Si + transferencia -> orden de pago en el grupo "depositos mk"
        -> Si + tarjeta       -> Claude prepara la compra y la confirma antes de pagar
        -> No                 -> no se publica nada, queda registrado

- Servicio: `systemctl status amunet-pagos-bot`  ·  log `/var/log/amunet-pagos-bot.log`
- Config: `.env` (600). `ORIGEN_CON_FACTURA` y `ORIGEN_SIN_FACTURA` son los
  textos de "transferencia desde ..." y se pueden cambiar sin redesplegar.
- Bot: @Transferfzbot. **Usa getUpdates, no webhook**, a proposito: el bot de
  depositos (@Controldepositosbot) sí tiene webhook en produccion y un
  `setWebhook` con su token lo tumbaria. Aqui no se toca ese bot.
- El secreto HMAC vive en `ir_config_parameter` clave
  `amunet_compras_general.hmac_secret`. Lo crea el modulo al instalarse.
- Solo `from.id == TELEGRAM_DM_DUENO` puede resolver un boton; la firma es de
  un solo uso por solicitud y el estado hace la operacion idempotente.

Pruebas: siempre al DM de Fernando, nunca al grupo. Para probar sin riesgo,
usa una solicitud con forma de pago `tarjeta`: un "Si" no publica nada.
