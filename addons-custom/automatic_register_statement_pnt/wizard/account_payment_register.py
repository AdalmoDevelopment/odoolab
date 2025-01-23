from odoo import models, fields, _


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _create_payments(self):
        payments = super()._create_payments()
        if self.journal_id.pnt_auto_register_statement:
            self._create_register()
        return payments

    def _prepare_statement_vals(self):
        return {
            "name": _("Automatic %s" % fields.datetime.now()),
            "journal_id": self.journal_id.id,
            "date": fields.Date.today(),
        }

    def _create_account_bank_statement(self):
        self.ensure_one()
        vals = self._prepare_statement_vals()
        account_back_statement_id = self.env["account.bank.statement"].create(vals)
        return account_back_statement_id

    def _prepare_register_vals(self):
        self.ensure_one()
        factor = -1 if self.payment_type == "outbound" else 1
        return {
            "date": fields.Date.today(),
            "payment_ref": self.communication,
            "partner_id": self.partner_id.commercial_partner_id.id,
            "amount": self.amount * factor,
        }

    def _create_register(self):
        self.ensure_one()
        account_back_statement_id = self.env["account.bank.statement"].search(
            [
                ("journal_id", "=", self.journal_id.id),
                ("state", "=", "open"),
                ("date", "=", fields.Date.today()),
            ]
        )
        if not account_back_statement_id:
            account_back_statement_id = self._create_account_bank_statement()
        vals = self._prepare_register_vals()
        vals["statement_id"] = account_back_statement_id.id
        account_back_statement_id.line_ids.create(vals)
