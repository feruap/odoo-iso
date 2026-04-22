"""
setup_amunet_bom_data.py
Crea los BoMs de productos Solucion en la base de datos destino si no existen.
Idempotente: verifica antes de crear.
"""

BOM_DATA = [
    {'tmpl_code': 'SPNPS01', 'tmpl_name': 'Solución de Nanoparticulas', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC01', 'product_name': 'Citrato de sodio', 'qty': 0.1, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Ácido cloroáurico', 'qty': 0.1, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Agua tridestilada filtrada', 'qty': 10.0, 'uom': 'ml'},
    ]},
    {'tmpl_code': 'SPSAS01', 'tmpl_name': 'Azida de sodio 20 %', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC07', 'product_name': 'Azida de sodio (NaN3)', 'qty': 200.0, 'uom': 'g'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSHS02', 'tmpl_name': 'Hidróxido de sodio 20%', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC09', 'product_name': 'Hidróxido de sodio (NaOH)', 'qty': 200.0, 'uom': 'g'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSAC01', 'tmpl_name': 'Solución HCl 6 M', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': '', 'product_name': 'Ácido Clorhídrico 37% HCl', 'qty': 501.6, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSHS01', 'tmpl_name': 'Solución Hidroxido de Sodio 1 M', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC09', 'product_name': 'Hidróxido de sodio (NaOH)', 'qty': 40.0, 'uom': 'g'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPC03', 'tmpl_name': 'Solución Amortiguadora de Borato 0.1 M', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': '', 'product_name': 'Borato de sodio', 'qty': 6.18, 'uom': 'g'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPC04', 'tmpl_name': 'Solución Amortiguadora de Borato 20 mM pH 7.5', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'SPSPC03', 'product_name': 'Solución Amortiguadora de Borato 0.1 M', 'qty': 200.0, 'uom': 'ml'},
        {'product_code': 'SPSHS02', 'product_name': 'Hidróxido de sodio 20%', 'qty': 0.25, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPC05', 'tmpl_name': 'Solución Amortiguadora de Borato 20 mM pH 8.5', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'SPSPC03', 'product_name': 'Solución Amortiguadora de Borato 0.1 M', 'qty': 200.0, 'uom': 'ml'},
        {'product_code': 'SPSHS02', 'product_name': 'Hidróxido de sodio 20%', 'qty': 1.1, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPB01', 'tmpl_name': 'Solución de bloqueo de BSA 7.5', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC16', 'product_name': 'Albumina de Suero Bovino BSA', 'qty': 10.0, 'uom': 'g'},
        {'product_code': 'SPSPC04', 'product_name': 'Solución Amortiguadora de Borato 20 mM pH 7.5', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPB02', 'tmpl_name': 'Solución de bloqueo de BSA 8.5', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC16', 'product_name': 'Albumina de Suero Bovino BSA', 'qty': 10.0, 'uom': 'g'},
        {'product_code': 'SPSPC05', 'product_name': 'Solución Amortiguadora de Borato 20 mM pH 8.5', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPB03', 'tmpl_name': 'Solución de Bloqueo Caseina', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 10.0, 'uom': 'g'},
        {'product_code': 'MPREC08', 'product_name': 'Ácido bórico', 'qty': 6.18, 'uom': 'g'},
        {'product_code': 'SPSHS02', 'product_name': 'Hidróxido de sodio 20%', 'qty': 10.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSRB01', 'tmpl_name': 'Reactivo de Bradford', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC17', 'product_name': 'Azul Brillante de Coomassie G-250', 'qty': 100.0, 'uom': 'g'},
        {'product_code': 'MPREC18', 'product_name': 'Etanol 96%', 'qty': 1.0, 'uom': 'L'},
        {'product_code': 'MPREC19', 'product_name': 'Ácido fosfórico 85%', 'qty': 1.0, 'uom': 'L'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPPBS01', 'tmpl_name': 'PBS 1X', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 8.0, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Cloruro de Potasio', 'qty': 0.2, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Fosfato de Sodio Dibásico', 'qty': 1.44, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Fosfato de Potasio Monobásico', 'qty': 0.24, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Ácido Clorhídrico 37% HCl', 'qty': 0.06, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPPBS02', 'tmpl_name': 'PBS 10X', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 80.0, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Cloruro de Potasio', 'qty': 2.0, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Fosfato de Sodio Dibásico', 'qty': 14.4, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Fosfato de Potasio Monobásico', 'qty': 2.4, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Ácido Clorhídrico 37% HCl', 'qty': 0.6, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPLPT01', 'tmpl_name': 'Solución de Lavado (PBS/Tween)', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'SPPBS02', 'product_name': 'PBS 10X', 'qty': 10.0, 'uom': 'ml'},
        {'product_code': '', 'product_name': 'Tween 20X', 'qty': 0.5, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSDM01', 'tmpl_name': 'Solución Diluyente β Trehalosa', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': '', 'product_name': 'Fosfato de Sodio Dibásico', 'qty': 1.5, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Fosfato de Sodio Monobásico', 'qty': 0.23, 'uom': 'g'},
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 9.2, 'uom': 'g'},
        {'product_code': 'MPREC13', 'product_name': 'D-Trehalosa', 'qty': 15.0, 'uom': 'g'},
        {'product_code': 'MPREC07', 'product_name': 'Azida de sodio (NaN3)', 'qty': 0.2, 'uom': 'g'},
        {'product_code': 'SPSHS02', 'product_name': 'Hidróxido de sodio 20%', 'qty': 360.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSDC01', 'tmpl_name': 'Solución diluyente para conjugado (AD 0)', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC10', 'product_name': 'Tris-base', 'qty': 2.43, 'uom': 'g'},
        {'product_code': 'MPREC16', 'product_name': 'Albumina de Suero Bovino BSA', 'qty': 1.0, 'uom': 'g'},
        {'product_code': 'MPREC13', 'product_name': 'D-Trehalosa', 'qty': 50.0, 'uom': 'g'},
        {'product_code': 'MPREC14', 'product_name': 'Sacarosa', 'qty': 100.0, 'uom': 'g'},
        {'product_code': 'MPREC07', 'product_name': 'Azida de sodio (NaN3)', 'qty': 0.2, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Ácido Clorhídrico 37% HCl', 'qty': 1.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSDC02', 'tmpl_name': 'Solución diluyente para conjugado (AD1)', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC10', 'product_name': 'Tris-base', 'qty': 2.43, 'uom': 'g'},
        {'product_code': 'MPREC13', 'product_name': 'D-Trehalosa', 'qty': 50.0, 'uom': 'g'},
        {'product_code': 'MPREC14', 'product_name': 'Sacarosa', 'qty': 100.0, 'uom': 'g'},
        {'product_code': 'MPREC07', 'product_name': 'Azida de sodio (NaN3)', 'qty': 0.2, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Ácido Clorhídrico 37% HCl', 'qty': 13.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPA01', 'tmpl_name': 'Solución de pretratamiento para almohadilla de conjugado', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC10', 'product_name': 'Tris-base', 'qty': 6.0, 'uom': 'g'},
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 5.0, 'uom': 'g'},
        {'product_code': 'MPREC11', 'product_name': 'Polivinilpirrolidona (PVP)', 'qty': 5.0, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Tween 20X', 'qty': 0.46, 'uom': 'ml'},
        {'product_code': 'SPSAC01', 'product_name': 'Solución HCl 6 M', 'qty': 3.4, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPA02', 'tmpl_name': 'Solución de pretratamiento para almohadilla de muestra', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC10', 'product_name': 'Tris-base', 'qty': 6.0, 'uom': 'g'},
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 10.0, 'uom': 'g'},
        {'product_code': 'MPREC15', 'product_name': 'S9', 'qty': 10.0, 'uom': 'g'},
        {'product_code': 'SPSAC01', 'product_name': 'Solución HCl 6 M', 'qty': 3.2, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSPA03', 'tmpl_name': 'Solución de pretratamiento para almohadilla de muestra (V2)', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 10.0, 'uom': 'g'},
        {'product_code': 'MPREC10', 'product_name': 'Tris-base', 'qty': 6.0, 'uom': 'g'},
        {'product_code': 'MPREC06', 'product_name': 'Tritón X-100', 'qty': 4.67, 'uom': 'g'},
        {'product_code': 'SPSAC01', 'product_name': 'Solución HCl 6 M', 'qty': 6.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPHBB01', 'tmpl_name': 'Solución de Corrimiento de Hemoglobina Cualitativa', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 0.84, 'uom': 'g'},
        {'product_code': 'MPREC04', 'product_name': 'Tris-HCl', 'qty': 0.66, 'uom': 'g'},
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 1.47, 'uom': 'g'},
        {'product_code': 'MPREC06', 'product_name': 'Tritón X-100', 'qty': 0.79, 'uom': 'g'},
        {'product_code': 'SPSAS01', 'product_name': 'Azida de sodio 20 %', 'qty': 4.2, 'uom': 'ml'},
        {'product_code': 'SPSHS02', 'product_name': 'Hidróxido de sodio 20%', 'qty': 2.0, 'uom': 'ml'},
        {'product_code': 'SPPBS01', 'product_name': 'PBS 1X', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPSAG01', 'tmpl_name': 'Solución de corrimiento Tracto Respiratorio', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 5.0, 'uom': 'g'},
        {'product_code': 'MPREC04', 'product_name': 'Tris-HCl', 'qty': 3.94, 'uom': 'g'},
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 8.77, 'uom': 'g'},
        {'product_code': 'MPREC06', 'product_name': 'Tritón X-100', 'qty': 4.72, 'uom': 'g'},
        {'product_code': 'SPSAS01', 'product_name': 'Azida de sodio 20 %', 'qty': 25.0, 'uom': 'ml'},
        {'product_code': 'SPSHS02', 'product_name': 'Hidróxido de sodio 20%', 'qty': 7.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPBAB01', 'tmpl_name': 'Solución de corrimeinto Ac', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': '', 'product_name': 'Fosfato de Sodio Dibásico', 'qty': 7.1, 'uom': 'g'},
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 5.0, 'uom': 'g'},
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 8.7, 'uom': 'g'},
        {'product_code': 'SPSAS01', 'product_name': 'Azida de sodio 20 %', 'qty': 8.0, 'uom': 'g'},
        {'product_code': 'SPSAC01', 'product_name': 'Solución HCl 6 M', 'qty': 0.05, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPBAB02', 'tmpl_name': 'Solución de corrimeinto Ac CHEM', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': '', 'product_name': 'Fosfato de Sodio Dibásico', 'qty': 7.1, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Caseína CHEMS', 'qty': 5.0, 'uom': 'g'},
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 8.7, 'uom': 'g'},
        {'product_code': 'SPSAS01', 'product_name': 'Azida de sodio 20 %', 'qty': 8.0, 'uom': 'g'},
        {'product_code': 'SPSAC01', 'product_name': 'Solución HCl 6 M', 'qty': 0.05, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
    {'tmpl_code': 'SPAPB01', 'tmpl_name': 'Solución de Corrimiento AC + PBS', 'product_qty': 1.0, 'product_uom_name': 'L', 'bom_type': 'normal', 'lines': [
        {'product_code': '', 'product_name': 'Fosfato de Sodio Dibásico', 'qty': 4.7, 'uom': 'g'},
        {'product_code': 'MPREC03', 'product_name': 'Caseína láctica', 'qty': 3.3, 'uom': 'g'},
        {'product_code': 'MPREC05', 'product_name': 'Cloruro de sodio', 'qty': 5.8, 'uom': 'g'},
        {'product_code': 'MPREC07', 'product_name': 'Azida de sodio (NaN3)', 'qty': 5.3, 'uom': 'g'},
        {'product_code': '', 'product_name': 'Ácido Clorhídrico 37% HCl', 'qty': 0.04, 'uom': 'ml'},
        {'product_code': 'SPPBS01', 'product_name': 'PBS 1X', 'qty': 333.0, 'uom': 'ml'},
        {'product_code': 'MPATR01', 'product_name': 'Agua tridestilada', 'qty': 1.0, 'uom': 'L'},
    ]},
]

Product = env['product.template']
ProductProduct = env['product.product']
Bom = env['mrp.bom']
Uom = env['uom.uom']

def find_product_tmpl(code, name):
    if code:
        p = Product.search([('default_code', '=', code)], limit=1)
        if p:
            return p
    p = Product.search([('name', '=', name)], limit=1)
    if not p:
        p = Product.search([('name', 'ilike', name[:30])], limit=1)
    return p

def find_product(code, name):
    if code:
        p = ProductProduct.search([('default_code', '=', code)], limit=1)
        if p:
            return p
    p = ProductProduct.search([('name', '=', name)], limit=1)
    if not p:
        p = ProductProduct.search([('name', 'ilike', name[:30])], limit=1)
    return p

def find_uom(name):
    u = Uom.search([('name', '=', name)], limit=1)
    if not u:
        u = Uom.search([('name', 'ilike', name)], limit=1)
    return u

created = 0
skipped = 0
errors = []

for bom_def in BOM_DATA:
    tmpl = find_product_tmpl(bom_def['tmpl_code'], bom_def['tmpl_name'])
    if not tmpl:
        errors.append(f"[ERROR] Producto no encontrado: {bom_def['tmpl_code']} / {bom_def['tmpl_name']}")
        continue

    existing = Bom.search([('product_tmpl_id', '=', tmpl.id), ('type', '=', bom_def['bom_type'])], limit=1)
    if existing:
        print(f"[SKIP] BoM ya existe: {bom_def['tmpl_code']} | {tmpl.name[:40]}")
        skipped += 1
        continue

    uom = find_uom(bom_def['product_uom_name'])
    if not uom:
        errors.append(f"[ERROR] UoM no encontrada: {bom_def['product_uom_name']} para {bom_def['tmpl_code']}")
        continue

    lines = []
    line_errors = False
    for line_def in bom_def['lines']:
        comp = find_product(line_def['product_code'], line_def['product_name'])
        if not comp:
            errors.append(f"  [ERROR] Componente no encontrado: {line_def['product_code']} / {line_def['product_name']}")
            line_errors = True
            continue
        line_uom = find_uom(line_def['uom'])
        if not line_uom:
            line_uom = comp.uom_id
        lines.append((0, 0, {
            'product_id': comp.id,
            'product_qty': line_def['qty'],
            'product_uom_id': line_uom.id,
        }))

    if line_errors:
        errors.append(f"[SKIP] BoM {bom_def['tmpl_code']} omitida por errores en componentes")
        continue

    Bom.create({
        'product_tmpl_id': tmpl.id,
        'product_qty': bom_def['product_qty'],
        'product_uom_id': uom.id,
        'type': bom_def['bom_type'],
        'bom_line_ids': lines,
    })
    env.cr.commit()
    print(f"[OK] BoM creada: {bom_def['tmpl_code']} | {tmpl.name[:40]} | {len(lines)} lineas")
    created += 1

print(f"\nResumen: {created} creados, {skipped} ya existian")
if errors:
    print("\nErrores:")
    for e in errors:
        print(e)
