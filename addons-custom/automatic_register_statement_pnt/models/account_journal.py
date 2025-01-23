from odoo import models, fields


class AccountJournal(models.Model):
    _inherit = "account.journal"

    pnt_auto_register_statement = fields.Boolean(
        string="Create register statement",
    )
