from odoo import models, fields


class PntGeneralConditions(models.Model):
    _name = "pnt.general.conditions"
    _description = "Pnt General Conditions"

    name = fields.Char(
        string="Name",
        required=True,
    )
    pnt_general_conditions = fields.Html(
        string="General conditions",
    )
    pnt_category_ids = fields.Many2many(
        comodel_name="product.category",
        string="Categories",
        domain=[
            ("type", "=", "normal"),
        ],
        relation="general_conditions_product_category_rel",
    )
