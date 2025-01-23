from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    pnt_is_dangerous = fields.Boolean(
        string="Is dangerous",
        compute="_compute_pnt_is_dangerous",
        store=True,
    )
    @api.depends("pnt_waste_table5_ids")
    def _compute_pnt_is_dangerous(self):
        for record in self:
            if record.pnt_waste_table5_ids:
                record.pnt_is_dangerous = True
            else:
                record.pnt_is_dangerous = False
    def get_pnt_tag_identification_code(self):
        for record in self:
            if record.pnt_waste_table5_ids:
                return record.pnt_waste_table5_ids[0].name
            else:
                return None