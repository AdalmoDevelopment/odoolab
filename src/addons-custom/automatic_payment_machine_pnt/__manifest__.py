{
    "name": "Automatic Payment Machine pnt",
    "summary": "Automatic Payment Machine pnt",
    "version": "14.0.1.0.0",
    "category": "Hidden",
    "website": "https://www.puntsistemes.es",
    "author": "Punt Sistemes",
    "maintainers": [
        "Tolo Torres",
    ],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "custom_pnt",
        "base",
        "account"
    ],
    "data": [
        "data/ir_sequence_data.xml",
        "security/res_groups.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizards/account_payment_register_views.xml",
        "views/pnt_payment_machine_views.xml",
        "views/pnt_payment_machine_type_views.xml",
        "views/pnt_payment_machine_record_views.xml",
        "views/pnt_single_document_views.xml",
    ],
}
