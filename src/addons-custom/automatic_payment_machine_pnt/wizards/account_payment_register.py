from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
    )
    pnt_payment_machine_id = fields.Many2one(
        comodel_name="pnt.payment.machine",
    )

    @api.onchange("pnt_payment_machine_id")
    def _onchange_pnt_payment_machine_id(self):
        for record in self:
            if (record.pnt_payment_machine_id
                    and record.pnt_payment_machine_id.pnt_journal_id):
                record.journal_id = record.pnt_payment_machine_id.pnt_journal_id

    def action_create_payments(self):
        if self.pnt_payment_machine_id:
            send_pay = self.action_pay_with_machine_payment()
            if send_pay:
                payments = self._create_payments()
                self._create_payment_machine_record(payments)
                return True
            else:
                raise UserError(
                    _(
                        "No se ha podido realizar el pago con la Máquina de cobro automático: "
                        + self.pnt_payment_machine_id.display_name
                    )
                )
        else:
            return super().action_create_payments()
    def action_pay_with_machine_payment(self):
        for record in self:
            if not record.pnt_payment_machine_id:
                return False
            pay_machine = record.pnt_payment_machine_id
            if pay_machine.send_pay_to_machine(record.amount,'outbound'):
                return True
            else:
                return False

    def _create_payment_machine_record(self,payments):
        for record in self:
            payment_id = None
            if len(payments) > 0:
                payment_id = payments[0].id
            newpmr = self.env["pnt.payment.machine.record"].create(
                {
                    "pnt_payment_machine_id": record.pnt_payment_machine_id.id,
                    "pnt_single_document_id": record.pnt_single_document_id.id,
                    "pnt_account_payment_id": payment_id,
                }
            )
            return newpmr
