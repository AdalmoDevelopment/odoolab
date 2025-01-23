from odoo import models, fields


class PntLogisticRoute(models.Model):
    _name = "pnt.logistic.route"
    _description = "Pnt logistic route"

    name = fields.Char(
        string="Name",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_category_id = fields.Many2one(
        "pnt.fleet.vehicle.category",
        string="Category",
    )
    pnt_driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
    )
