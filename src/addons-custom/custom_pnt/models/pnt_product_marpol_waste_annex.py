from odoo import fields, models


class PntProductMarpolWasteAnnex(models.Model):
    _name = "pnt.product.marpol.waste.annex"
    _description = "Product Marpol Waste Annex"
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
    pnt_marpol_waste_category_ids = fields.Many2many(
        string="MARPOL Waste Categories",
        comodel_name="pnt.product.marpol.waste.category",
        relation="pnt_marpol_cat_annex_rel",
    )
