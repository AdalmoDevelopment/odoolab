from odoo import fields, models


class PntBoatType(models.Model):
    _name = "pnt.boat.type"
    _description = "Boat Type"
    _rec_name = "pnt_name"
    _order = "pnt_name"
    _check_company_auto = True
    _sql_constraints = [
        (
            "name_uniq",
            "unique (pnt_name, company_id)",
            "Name already exists.",
        )
    ]

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    pnt_name = fields.Char(
        string="Name",
        required=True,
        translate=False,
        index=True,
    )
