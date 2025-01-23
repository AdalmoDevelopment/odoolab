from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class ProductProduct(models.Model):
    _inherit = "product.product"

    def get_product_name_ticket(self):
        for record in self:
            result = record.name
            if record.product_template_attribute_value_ids:
                result = (result + " ("
                          + record.product_template_attribute_value_ids[0].name + ")")
            return result
