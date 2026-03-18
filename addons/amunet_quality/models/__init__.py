# -*- coding: utf-8 -*-

# Epic-029: Sistema de Control de Calidad (base)
from . import amunet_quality_parameter
from . import amunet_quality_check
from . import amunet_quality_point
from . import amunet_quality_test_line
from . import product_template
from . import product_product
from . import stock_picking
from . import stock_lot
from . import res_users
from . import amunet_quality_signature_pin

# Epic-031: Sistema de Parámetros de Calidad Jerárquicos
from . import amunet_quality_check_parameter_specification
from . import amunet_quality_parameter_conditional_option
from . import amunet_quality_parameter_product_rel
from . import amunet_quality_parameter_specification_config
from . import amunet_quality_test_line_detail
from . import amunet_quality_parameter_decision_matrix

# Epic-032: Información Adicional en Control de Calidad
from . import amunet_quality_additional_info_field
from . import amunet_quality_additional_info_config

# Epic-034: Control de Permisos Granular por Numeral en QC (MOVIDO)
# Los modelos de permisos granulares fueron refactorizados al módulo amunet_quality_permissions

# Document Control (ISO 13485)
from . import amunet_quality_procedure

# CAPA (ISO 13485)
from . import amunet_quality_capa

# Audit Log (ISO 13485)
from . import amunet_quality_audit_log

# Supplier Quality (ISO 13485)
from . import res_partner
from . import amunet_quality_supplier_audit

# Anexo General (Numeral 7)
from . import amunet_quality_anexo_line

# Tecnovigilancia (NOM-240)
from . import amunet_tecno_mixin
from . import amunet_quality_tecno_standalone
# from . import amunet_quality_helpdesk
