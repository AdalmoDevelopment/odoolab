from odoo import models, fields, api, _

class PntPaymentMachineRecord(models.Model):
    _name = "pnt.payment.machine.record"
    _description = "Pnt Payment Machine Record"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    name = fields.Char(
        string="Name",
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_payment_machine_id = fields.Many2one(
        comodel_name="pnt.payment.machine",
        string="Payment machine",
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
    )
    pnt_partner_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
    )
    pnt_account_payment_id = fields.Many2one(
        comodel_name="account.payment",
        string="Payment",
    )
    currency_id = fields.Many2one(
        related="pnt_account_payment_id.currency_id",
    )
    pnt_amount = fields.Monetary(
        related="pnt_account_payment_id.amount",
    )
    pnt_payment_type = fields.Selection(
        related="pnt_account_payment_id.payment_type",
    )
    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.payment.machine.record", sequence_date=seq_date
            ) or _("New")
        result = super(PntPaymentMachineRecord, self).create(vals)
        return result
