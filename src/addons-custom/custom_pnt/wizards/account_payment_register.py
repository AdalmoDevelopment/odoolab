from odoo import _, models
from odoo.exceptions import ValidationError


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def validate_payments(self):
        # Se podría mejorar la legibilidad haciendo groupby
        for move in self.env["account.move"].browse(self._context["active_ids"]):
            if not move.partner_id.vat:
                raise ValidationError(
                    _("%s does not have a VAT number.", move.partner_id.display_name)
                )
            check = sum(
                self.env["account.bank.statement.line"]
                .search(
                    [
                        ("date", "=", self.payment_date),
                        ("partner_id.vat", "=", move.partner_id.vat),
                    ]
                )
                .mapped("amount")
            )
            if (check - self.amount) <= -1000 and self.journal_id.type == "cash":
                raise ValidationError(
                    _("Cash payments to the same NIF/CIF per day cannot exceed 1000 €.")
                )

    def action_create_payments(self):
        self.validate_payments()
        return super().action_create_payments()
