<?php
/**
 * Plugin Name: Amunet Odoo Bridge
 * Description: Puente firmado para cambios manuales de nombre y fotografía desde Odoo.
 * Version: 1.0.0
 */

defined('ABSPATH') || exit;

function amunet_odoo_bridge_secret() {
    if (defined('AMUNET_ODOO_BRIDGE_SECRET')) return AMUNET_ODOO_BRIDGE_SECRET;
    return (string) get_option('amunet_odoo_bridge_secret', '');
}

/* Staging protege todo REST con login. Este namespace se protege con HMAC,
 * por lo que se exime únicamente después de que el guardia global falle. */
function amunet_odoo_bridge_allow_namespace($result) {
    if (!is_wp_error($result)) return $result;
    $uri = isset($_SERVER['REQUEST_URI']) ? (string) $_SERVER['REQUEST_URI'] : '';
    $route = isset($_GET['rest_route']) ? (string) $_GET['rest_route'] : '';
    if (strpos($uri, '/wp-json/amunet-odoo/v1/') !== false || strpos($route, '/amunet-odoo/v1/') !== false) {
        return true;
    }
    return $result;
}
add_filter('rest_authentication_errors', 'amunet_odoo_bridge_allow_namespace', 100);

function amunet_odoo_bridge_authorize(WP_REST_Request $request) {
    $secret = amunet_odoo_bridge_secret();
    $timestamp = $request->get_header('x-amunet-timestamp');
    $signature = $request->get_header('x-amunet-signature');
    if (!$secret || !$timestamp || !$signature || abs(time() - intval($timestamp)) > 300) {
        return new WP_Error('amunet_odoo_forbidden', 'Solicitud no autorizada.', array('status' => 403));
    }
    $expected = hash_hmac('sha256', $timestamp . '.' . $request->get_body(), $secret);
    if (!hash_equals($expected, $signature)) {
        return new WP_Error('amunet_odoo_forbidden', 'Firma no válida.', array('status' => 403));
    }
    return true;
}

function amunet_odoo_bridge_product($id) {
    $product = wc_get_product($id);
    if (!$product || !in_array($product->get_type(), array('simple', 'variable'), true)) {
        return new WP_Error('amunet_odoo_product', 'Solo se admiten productos simples o padres variables.', array('status' => 422));
    }
    return $product;
}

function amunet_odoo_bridge_update_name(WP_REST_Request $request) {
    $product = amunet_odoo_bridge_product(intval($request['id']));
    if (is_wp_error($product)) return $product;
    $data = $request->get_json_params();
    $name = sanitize_text_field($data['name'] ?? '');
    if ($name === '') return new WP_Error('amunet_odoo_name', 'El nombre es obligatorio.', array('status' => 422));
    $product->set_name($name);
    $product->save();
    return rest_ensure_response(array('id' => $product->get_id(), 'name' => $product->get_name()));
}

function amunet_odoo_bridge_update_image(WP_REST_Request $request) {
    $product = amunet_odoo_bridge_product(intval($request['id']));
    if (is_wp_error($product)) return $product;
    $data = $request->get_json_params();
    $binary = base64_decode($data['image_base64'] ?? '', true);
    if ($binary === false || strlen($binary) === 0 || strlen($binary) > 10 * 1024 * 1024) {
        return new WP_Error('amunet_odoo_image', 'Imagen inválida o mayor a 10 MB.', array('status' => 422));
    }
    $filename = sanitize_file_name($data['filename'] ?? ('odoo-' . $product->get_id() . '.png'));
    $upload = wp_upload_bits($filename, null, $binary);
    if (!empty($upload['error'])) return new WP_Error('amunet_odoo_upload', $upload['error'], array('status' => 500));
    $type = wp_check_filetype($upload['file']);
    $attachment_id = wp_insert_attachment(array(
        'post_mime_type' => $type['type'] ?: 'image/png',
        'post_title' => sanitize_text_field(pathinfo($filename, PATHINFO_FILENAME)),
        'post_status' => 'inherit',
    ), $upload['file'], $product->get_id());
    require_once ABSPATH . 'wp-admin/includes/image.php';
    wp_update_attachment_metadata($attachment_id, wp_generate_attachment_metadata($attachment_id, $upload['file']));
    $previous_id = $product->get_image_id();
    $product->set_image_id($attachment_id);
    $product->save();
    if ($previous_id) wp_delete_attachment($previous_id, true);
    return rest_ensure_response(array('id' => $product->get_id(), 'image_url' => wp_get_attachment_url($attachment_id)));
}

function amunet_odoo_bridge_delete_image(WP_REST_Request $request) {
    $product = amunet_odoo_bridge_product(intval($request['id']));
    if (is_wp_error($product)) return $product;
    $image_id = $product->get_image_id();
    $product->set_image_id(0);
    $product->save();
    if ($image_id) wp_delete_attachment($image_id, true);
    return rest_ensure_response(array('id' => $product->get_id(), 'deleted' => true));
}

add_action('rest_api_init', function () {
    $base = array('permission_callback' => 'amunet_odoo_bridge_authorize');
    register_rest_route('amunet-odoo/v1', '/product/(?P<id>\\d+)/name', $base + array('methods' => 'POST', 'callback' => 'amunet_odoo_bridge_update_name'));
    register_rest_route('amunet-odoo/v1', '/product/(?P<id>\\d+)/image', $base + array('methods' => 'POST', 'callback' => 'amunet_odoo_bridge_update_image'));
    register_rest_route('amunet-odoo/v1', '/product/(?P<id>\\d+)/image', $base + array('methods' => 'DELETE', 'callback' => 'amunet_odoo_bridge_delete_image'));
});
