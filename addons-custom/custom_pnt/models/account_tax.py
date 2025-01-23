from odoo import fields, models


class AccountTax(models.Model):
    _inherit = "account.tax"

    pnt_is_isp = fields.Boolean(
        string="Is ISP",
        default=False,
    )
