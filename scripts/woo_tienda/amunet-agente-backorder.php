<?php
/**
 * Plugin Name: Amunet - Agentes pueden vender sin existencia (pedido pendiente)
 * Description: Cuando un agente SalesKing compra "como cliente" (Purchase as customer), la tienda permite pedir producto aunque no haya existencia. Lo que falta queda marcado en el pedido como pendiente de produccion; el APT ya descuenta lo fisico y registra el faltante (_apt_fulfillment_needs). Instruccion de Fernando 04-sep-2026.
 * Author: Amunet / Claude
 * Version: 1.0.1
 */
if (!defined('ABSPATH')) { exit; }

function amunet_ab_activo() {
    $activo = false;
    if (is_admin() && !wp_doing_ajax()) { return false; }
    if (!is_user_logged_in() || empty($_COOKIE['salesking_switch_cookie'])) { return false; }
    // SalesKing inicia sesion COMO EL CLIENTE al hacer "purchase as customer";
    // la cookie guarda "<cliente>_<agente>_<fecha registro agente>" (misma regla que
    // salesking_switched_to()). Aplica si el usuario actual es ese cliente y el
    // agente de la cookie es agente real (y su fecha de registro coincide).
    $partes = explode('_', sanitize_text_field(wp_unslash($_COOKIE['salesking_switch_cookie'])));
    if (count($partes) < 2) { return false; }
    $cliente = intval($partes[0]);
    $agente  = intval($partes[1]);
    $actual  = get_current_user_id();
    if ($actual !== $cliente && $actual !== $agente) { return false; }
    $grupo = get_user_meta($agente, 'salesking_group', true);
    if (empty($grupo) || $grupo === 'none') { return false; }
    if (isset($partes[2])) {
        $u = get_userdata($agente);
        if (!$u || $u->user_registered !== $partes[2]) { return false; }
    }
    $activo = true;
    return apply_filters('amunet_agente_backorder_activo', $activo, $agente);
}

function amunet_ab_aplica($producto) {
    // Solo productos que manejan existencias (los mapeados a Odoo o cualquiera con manage_stock).
    return is_object($producto) && method_exists($producto, 'get_manage_stock') && $producto->get_manage_stock();
}

// Permitir pedidos pendientes (backorder con aviso) mientras el agente compra como cliente.
// Prioridad 2000: despues de amunet-inventario (1000), que es quien calcula la existencia.
add_filter('woocommerce_product_get_backorders', 'amunet_ab_backorders', 2000, 2);
add_filter('woocommerce_product_variation_get_backorders', 'amunet_ab_backorders', 2000, 2);
function amunet_ab_backorders($valor, $producto) {
    if (amunet_ab_activo() && amunet_ab_aplica($producto)) { return 'notify'; }
    return $valor;
}

add_filter('woocommerce_product_get_stock_status', 'amunet_ab_estado', 2000, 2);
add_filter('woocommerce_product_variation_get_stock_status', 'amunet_ab_estado', 2000, 2);
function amunet_ab_estado($valor, $producto) {
    if (!amunet_ab_activo() || $valor === 'instock') { return $valor; }
    if (!amunet_ab_aplica($producto)) {
        // Producto variable (padre): si alguna variacion maneja stock, se muestra comprable
        if (is_object($producto) && method_exists($producto, 'is_type') && $producto->is_type('variable')) {
            return 'onbackorder';
        }
        return $valor;
    }
    return 'onbackorder';
}

add_filter('woocommerce_product_is_in_stock', 'amunet_ab_en_stock', 2000, 2);
function amunet_ab_en_stock($valor, $producto) {
    if (amunet_ab_activo() && (amunet_ab_aplica($producto)
        || (is_object($producto) && method_exists($producto, 'is_type') && $producto->is_type('variable')))) {
        return true;
    }
    return $valor;
}

// Texto que ve el agente en vez de "Agotado".
add_filter('woocommerce_get_availability_text', 'amunet_ab_texto', 2000, 2);
function amunet_ab_texto($texto, $producto) {
    if (!amunet_ab_activo() || !amunet_ab_aplica($producto)) { return $texto; }
    $qty = (float) $producto->get_stock_quantity();
    if ($qty <= 0) { return 'Sin existencia: se puede pedir, queda pendiente de produccion'; }
    return sprintf('%s disponibles; lo demas queda pendiente de produccion', wc_format_stock_quantity_for_display($qty, $producto));
}

// Al crear el pedido: dejar constancia de cuanto quedo pendiente por partida.
add_action('woocommerce_checkout_create_order_line_item', 'amunet_ab_partida', 20, 4);
function amunet_ab_partida($item, $cart_item_key, $values, $order) {
    if (!amunet_ab_activo()) { return; }
    $producto = $item->get_product();
    if (!$producto || !amunet_ab_aplica($producto)) { return; }
    $disp = (float) $producto->get_stock_quantity();
    $falta = max(0.0, (float) $item->get_quantity() - max(0.0, $disp));
    if ($falta > 0) {
        $item->add_meta_data('Pendiente de produccion', wc_format_decimal($falta, 0) . ' pz', true);
        $item->add_meta_data('_amunet_pendiente', $falta, true);
        $order->update_meta_data('_amunet_pedido_agente_pendiente', 'yes');
    }
}

add_action('woocommerce_checkout_order_created', 'amunet_ab_nota', 20, 1);
function amunet_ab_nota($order) {
    if (!$order || $order->get_meta('_amunet_pedido_agente_pendiente') !== 'yes') { return; }
    $lineas = array();
    foreach ($order->get_items() as $item) {
        $f = (float) $item->get_meta('_amunet_pendiente');
        if ($f > 0) { $lineas[] = sprintf('%s: %s pz pendientes', $item->get_name(), wc_format_decimal($f, 0)); }
    }
    if ($lineas) {
        $order->add_order_note('Pedido de AGENTE con material pendiente de produccion. ' . implode(' | ', $lineas)
            . '. Se envia lo disponible; el resto se surte al liberar lote nuevo.');
    }
}
