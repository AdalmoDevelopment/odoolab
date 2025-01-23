from odoo import _, api, fields, models


class AccountAsset(models.Model):
    _inherit = "account.asset"

    pnt_is_deferred_payment = fields.Boolean(
        string="Is deferred payment",
        deafult=False,
    )