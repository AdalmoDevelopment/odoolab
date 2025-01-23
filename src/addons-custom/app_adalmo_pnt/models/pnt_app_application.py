from odoo import models, fields, api, _

class PntAppApplication(models.Model):
    _name = "pnt.app.application"
    _description = "Pnt App Application"
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
    id_application = fields.Integer(
        string="Id application"
    )
