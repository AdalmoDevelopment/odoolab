from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError

class ProductTemplate(models.Model):
    _inherit = "product.template"

    pnt_app_container_imege_txt = fields.Char(
        string="App container image",
        store=True,
        copy=False,
    )
    pnt_app_capacity = fields.Float(
        string="Capacity (Liters)",
        default=0.0,
        copy=False,
    )
    pnt_use_ibsalut = fields.Boolean(
        string="Use in ibsalut",
        default=False,
        copy=False,
    )
    pnt_use_tag_ibsalut = fields.Boolean(
        string="Use tag in son ibsalut",
        default=False,
        copy=False,
    )
    pnt_use_sonespases = fields.Boolean(
        string="Use in son espases",
        default=False,
        copy=False,
    )
    pnt_use_tag_sonespases = fields.Boolean(
        string="Use tag in son espases",
        default=False,
        copy=False,
    )
    pnt_use_quiron = fields.Boolean(
        string="Use in clinica quiron",
        default=False,
        copy=False,
    )
    pnt_use_tag_quiron = fields.Boolean(
        string="Use tag in clinica quiron",
        default=False,
        copy=False,
    )
    pnt_keep_in_du_quiron = fields.Boolean(
        string="Keep product in DU (Quiron)",
        default=False,
        copy=False,
    )
    pnt_apply_gross_weight_ib = fields.Boolean(
        string="Apply gross weight (ibSalut)",
        default=False,
        copy=False,
    )
    pnt_apply_gross_weight = fields.Boolean(
        string="Apply gross weight (Quiron)",
        default=False,
        copy=False,
    )
    pnt_apply_gross_weight_se = fields.Boolean(
        string="Apply gross weight (Son Espases)",
        default=False,
        copy=False,
    )
    pnt_waste_app_code = fields.Char(
        string="Waste app code",
        copy=False,
    )
    pnt_waste_app_code_number = fields.Integer(
        string="Waste app code number",
        copy=False,
    )
    pnt_qr_app_code = fields.Char(
        string="QR app code",
        copy=False,
    )
    pnt_qr_app_code_number = fields.Integer(
        string="QR app code number",
        copy=False,
    )
    pnt_print_tag = fields.Boolean(
        string="Print Tag (Not dangerous)",
        default=False,
    )
    def _assign_pnt_qr_app_code(self):
        for pt in self:
            # máximo numero de contador
            query = """select max(pnt_qr_app_code)::integer as num 
                        from product_template
                    """
            self.env.cr.execute(query)
            num = 0
            for val in self.env.cr.dictfetchall():
                num = val['num']
            if num:
                pt.pnt_qr_app_code = str(num + 1)

    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for record in res:
            record._assign_pnt_qr_app_code()
        return res
