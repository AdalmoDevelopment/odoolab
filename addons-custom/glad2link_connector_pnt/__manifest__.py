{
    "name": "Glad2link Connetor",
    "version": "14.0.1.0.0",
    "category": "Customizations",
    "website": "https://www.puntsistemes.es",
    "author": "Punt Sistemes",
    "summary": "Customizations for the client",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "auth_api_key",
        "custom_pnt",
    ],
    "data": [
        "data/template_mail.xml",
        "views/pnt_single_document.xml",
        "views/account_move.xml",
    ],
}
