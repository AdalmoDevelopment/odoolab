from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _send_mail_du_signed(self):
        obj_single_document = self.env["pnt.single.document"]
        for move in self:
            obj_single_document._send_mail_du_signed(force_send=True, invoice=move)
