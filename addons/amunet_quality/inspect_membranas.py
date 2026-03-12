
import logging
_logger = logging.getLogger(__name__)

def inspect_membranas(env):
    product_codes = ['MPMNC01', 'MPMNC02', 'MPMNC03', 'MPTS01', 'MPTS02']
    
    # Try product.product
    products = env['product.product'].search([('default_code', 'in', product_codes)])
    if not products:
        # Try product.template
        products = env['product.template'].search([('default_code', 'in', product_codes)])
    
    print(f"DEBUG: Found {len(products)} products: {[p.default_code for p in products]}")

    if not products:
        # List some products to see what's in there
        some_products = env['product.product'].search([], limit=10)
        print(f"DEBUG: Sample products in DB: {[p.default_code for p in some_products if p.default_code]}")
        return

    for product in products:
        # Get template if it's a product.product
        template = product if product._name == 'product.template' else product.product_tmpl_id
        
        print(f"\nProduct: {product.default_code} (Template ID: {template.id})")
        # Find parameters via amunet.quality.parameter.product.rel
        rel_obj = env['amunet.quality.parameter.product.rel']
        rels = rel_obj.search([('product_tmpl_id', '=', template.id)])
        for rel in rels:
            param = rel.parameter_id
            print(f"  Parameter: {param.code} - {param.name} (ID: {param.id})")
            
            # Check amunet.quality.parameter.specification.config
            configs = env['amunet.quality.parameter.specification.config'].search([('product_parameter_rel_id', '=', rel.id)])
            if configs:
                print(f"    Product-specific Specs (Configs):")
                for config in configs:
                    spec = config.specification_id
                    print(f"      Config ID: {config.id}, Spec: {config.specification_name} (Spec ID: {spec.id}, Eval Type in Config: {config.evaluation_type})")
                    print(f"        Acceptance Criteria: {config.acceptance_criteria}")
                    
                    if config.evaluation_type == 'binary_selection':
                        print(f"        Binary Config: Prefix={config.binary_prefix}, Suffix={config.binary_suffix}, Expected={config.binary_expected_option}")
                        print(f"        Resulting Options: Pass='{config.binary_option_pass}', Fail='{config.binary_option_fail}'")
                    elif config.evaluation_type == 'numeric_range':
                        print(f"        Numeric Config: Nominal={config.nominal_value}, Tolerance={config.tolerance}, Manual={config.use_manual_range}")
                        print(f"        Range: Min={config.min_value}, Max={config.max_value}, Display='{config.range_display}'")
            else:
                print(f"    No product-specific configs found.")

# If running in odoo shell
if 'env' in locals():
    inspect_membranas(env)
elif 'env' in globals():
    inspect_membranas(globals()['env'])
