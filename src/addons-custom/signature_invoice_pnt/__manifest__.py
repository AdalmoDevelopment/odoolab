# -*- coding: utf-8 -*-

{
    'name': 'Firma digital Facturas (EpadLink)',
    'version': '14.0.1.0.0',
    'summary': 'Funcionalidad para integrar dispositivo externo de firma epadLink en facturas Odoo',
    'sequence': 5,
    'category': 'Hidden',
    'website': 'https://puntsistemes.com',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/account_move_views.xml',
        'views/templates.xml',
    ],
    'qweb': ['static/src/xml/template.xml'],

    'installable': True,
    'application': False,
    'auto_install': False,
}
