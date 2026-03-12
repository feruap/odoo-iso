
def find_all_duplicates(env):
    product_codes = ['MPMNC01', 'MPMNC02', 'MPMNC03', 'MPTS01', 'MPTS02']
    for code in product_codes:
        product = env['product.product'].search([('default_code', '=', code)], limit=1)
        if not product:
            print(f"Product {code} not found")
            continue
        
        template = product.product_tmpl_id
        print(f"Product {code} (Template ID: {template.id})")
        
        rels = env['amunet.quality.parameter.product.rel'].search([('product_tmpl_id', '=', template.id)])
        for rel in rels:
            param = rel.parameter_id
            print(f"  Rel {rel.id}: Parameter: {param.code} - {param.name} (ID: {param.id})")
            
            configs = env['amunet.quality.parameter.specification.config'].search([('product_parameter_rel_id', '=', rel.id)])
            for c in configs:
                print(f"    Config {c.id}: Spec Name='{c.specification_name}', Type={c.evaluation_type}, SpecID={c.specification_id.id}")

if 'env' in locals():
    find_all_duplicates(env)
elif 'env' in globals():
    find_all_duplicates(globals()['env'])
