# -*- coding: utf-8 -*-
{
    'name': "Reports Pnt",
    'version': '1.0',
    'author': 'Tolo Torres (Punt Sistemes)',
    'website': 'http://www.puntsistemes.com/',
    'sequence': 1,
    'category': 'Specific Modules',
    'summary': 'Reports Pnt',
    'depends': [
        'web',
        'custom_pnt',
        'app_adalmo_pnt',
        'purchase',
        "account",
    ],
    'data': [
        "security/ir.model.access.csv",
        'reports/pnt_ticket_du.xml',
        'reports/pnt_report_invoice.xml',
        'reports/pnt_agreement_contract.xml',
        'reports/pnt_sale_order_contract.xml',
        'reports/template_pnt.xml',
        "reports/sale_report_templates.xml",
        "wizards/pnt_print_tag_format_wizard_views.xml",
        'reports/sale_report_templates.xml',
        'reports/pnt_general_conditions.xml',
        'reports/pnt_general_conditions_amianto.xml',
        'reports/report_document_identification.xml',
        'reports/account_statement.xml',
        'reports/project_task_templates.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'description': """
Descripción
===========
Customization reports for Punt
Configuración
=============
Limitaciones/Problemas
======================
No se conocen.
Registro de cambios
===================
14.0.1.0.0:
Desarrollo inicial.
"""
}
