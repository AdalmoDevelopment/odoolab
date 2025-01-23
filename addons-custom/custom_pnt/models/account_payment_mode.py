from odoo import fields, models


class AccountPaymentMove(models.Model):
    _inherit = "account.payment.mode"

    pnt_limit_cash_confirm_invoice_supplier = fields.Boolean(
        string="Check the amount (1000 €) on the supplier invoices",
    )

    pnt_is_giro = fields.Boolean(string="Bank Draft")
