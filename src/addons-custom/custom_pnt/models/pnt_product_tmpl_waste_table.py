from random import randint
from odoo import fields, models, api, _


class PntProductTmplWasteTable(models.Model):
    _name = "pnt.product.tmpl.waste.table"
    _description = "Waste Reasons For Mgm"
    _order = "name"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(
        string="Name",
        required=True,
    )
    pnt_description = fields.Char(
        string="Description",
        translate=True,
    )
    color = fields.Integer(string="Color Index", default=_get_default_color)
    active = fields.Boolean(
        default=True,
        help="The active field allows you to hide the category without removing it.",
    )
    pnt_table_type = fields.Selection(
        string="Table",
        selection=[
            ("table1", _("[Table 1] Waste Reasons For Mgm")),
            ("table2", _("[Table 2] Waste Mgm Mode")),
            ("table3", _("[Table 3] Waste Typology")),
            ("table4", _("[Table 4] Waste Constituents That Make It Dangerous")),
            ("table5", _("[Table 5] Waste Characteristics Of Hazardous Waste")),
            ("table6", _("[Table 6] Waste Generating Activity")),
            ("table7", _("[Table 7] Waste Generating Process")),
        ],
        required=True,
    )
    pnt_table_image_1 = fields.Binary()
    pnt_table_image_2 = fields.Binary()
