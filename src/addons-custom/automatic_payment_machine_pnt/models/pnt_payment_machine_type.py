from odoo import models, fields, api, _

class PntPaymentMachineType(models.Model):
    _name = "pnt.payment.machine.type"
    _description = "Pnt Payment Machine Type"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    name = fields.Char(
        string="Name",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_machine_manufacturer = fields.Selection(
        [
            ("cashguard", _("CashGuard")),
            ("other", _("Others")),
        ],
        string="Automatic payment machine manufacturer",
        readonly=True,
        copy=True,
        index=True,
        tracking=3,
        required=True,
    )
    pnt_webapi = fields.Char(
        string="Machine WebAPI",
    )