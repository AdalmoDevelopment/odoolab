{
    "name": "Create automatic bank statement",
    "version": "14.0.1.0.0",
    "category": "Customizations",
    "website": "https://www.puntsistemes.es",
    "author": "Punt Sistemes",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base",
        "account",
    ],
    "data": [
        # "data/ir_module_category.xml",
        # "security/ir.model.access.csv",
        # "security/res_partner_security.xml",
        "views/account_journal_view.xml",
    ],
}
