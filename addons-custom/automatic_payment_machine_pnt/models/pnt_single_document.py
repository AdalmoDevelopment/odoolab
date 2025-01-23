from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class PntSingleDocument(models.Model):
    _inherit = "pnt.single.document"

    pnt_payment_machine_id = fields.Many2one(
        comodel_name="pnt.payment.machine",
        string="Payment machine",
        compute="_compute_pnt_payment_machine",
        store=True,
    )
    @api.depends("pnt_scales_id","pnt_single_document_type")
    def _compute_pnt_payment_machine(self):
        for record in self:
            record.pnt_payment_machine_id = None
            if (record.pnt_scales_id and record.pnt_scales_id.pnt_warehouse_id and
                    record.pnt_single_document_type):
                if record.pnt_single_document_type in ('portal'):
                    pm = self.env['pnt.payment.machine'].search([('pnt_warehouse_id','='
                                            ,record.pnt_scales_id.pnt_warehouse_id.id)]
                                            ,limit=1)
                    if pm:
                        record.pnt_payment_machine_id=pm
    def action_generate_payment_machine_record(self):
        for du in self:
            for purchase in du.pnt_purchase_order_ids:
                purchase.sudo()._read(["invoice_ids"])
                invoices = purchase.invoice_ids
            total = 0
            invoices_to_pay = []
            for invoice in invoices:
                invoices_to_pay.append(invoice.id)
                total += invoice.amount_total
            view_id = self.env.ref(
                'account.view_account_payment_register_form').id
            return {
                'type': 'ir.actions.act_window',
                'name': "Register Payment",
                'view_type': 'form',
                'view_mode': 'form',
                'view_id': view_id,
                'res_model': 'account.payment.register',
                'context': {
                    'active_ids': invoices_to_pay,
                    'default_journal_id': du.pnt_payment_machine_id.pnt_journal_id.id,
                    'active_model': 'account.move',
                    'dont_redirect_to_payments': True,
                    'default_amount': total,
                    'default_pnt_single_document_id': du.id,
                    'default_pnt_payment_machine_id': du.pnt_payment_machine_id.id,
                },
                'target': 'new',
            }
