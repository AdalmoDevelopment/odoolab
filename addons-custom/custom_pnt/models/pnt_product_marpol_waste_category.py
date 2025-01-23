from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PntProductMarpolWasteCategory(models.Model):
    _name = "pnt.product.marpol.waste.category"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Pnt Porduct MARPOL Waste Category"

    name = fields.Char(
        string="Category Name",
        required=True,
        translate=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    pnt_note = fields.Text(
        string="Comments",
        translate=True,
    )
    pnt_product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="pnt_marpol_waste_category_id",
        string="Product",
        copy=False,
    )
    pnt_product_tmpl_count = fields.Integer(
        string="Product",
        compute="_compute_pnt_product_tmpl_count",
    )

    def _compute_pnt_product_tmpl_count(self):
        product_tmpl_data = self.env["product.template"].read_group(
            [("pnt_marpol_waste_category_id", "in", self.ids)],
            ["pnt_marpol_waste_category_id"],
            ["pnt_marpol_waste_category_id"],
        )
        mapped_data = dict(
            [
                (
                    m["pnt_marpol_waste_category_id"][0],
                    m["pnt_marpol_waste_category_id_count"],
                )
                for m in product_tmpl_data
            ]
        )
        for category in self:
            category.pnt_product_tmpl_count = mapped_data.get(category.id, 0)

    def unlink(self):
        for category in self:
            if category.pnt_fleet_ids:
                raise UserError(
                    _(
                        "You cannot delete an MARPOL waste category containing product requests."
                    )
                )
        return super(PntProductMarpolWasteCategory, self).unlink()
