from odoo import api, models
from odoo.osv import expression


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        if not self._context.get("only_products"):
            return super().name_search(
                name=name, args=args, operator=operator, limit=limit
            )
        args = args or []
        args = expression.AND([[("categ_id.pnt_service", "=", False)], args])
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    def is_product_rental(self):
        return bool(
            self.pnt_rental
            and self.pnt_recurrence
            and self.default_code == "TA"
            and self.type == "service"
            and not self.pnt_container_movement_type
        )

    def is_product_removal(self):
        return bool(
            self.pnt_rental
            and self.default_code == "TR"
            and self.type == "service"
            and self.pnt_container_movement_type == "removal"
        )
