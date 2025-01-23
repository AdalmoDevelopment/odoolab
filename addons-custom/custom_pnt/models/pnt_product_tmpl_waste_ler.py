from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PntProductTmplWasteLer(models.Model):
    _name = "pnt.product.tmpl.waste.ler"
    _description = "Pnt Product Tmpl Waste LER"

    name = fields.Char(
        string="LER Code",
        required=True,
        help="LER Format xxxxxx[*]" "RAEE Format xxxxxx-xx[*]",
    )
    pnt_description = fields.Char(
        string="Description",
        translate=True,
    )
    pnt_is_dangerous = fields.Boolean(
        string="Dangerous",
        copy=False,
        readonly=False,
        compute="_compute_pnt_ler_type",
        store=True,
    )
    pnt_is_raee = fields.Boolean(
        string="RAEE",
        copy=False,
        readonly=False,
        compute="_compute_pnt_ler_type",
        store=True,
    )
    pnt_product_tmpl_ids = fields.One2many(
        comodel_name="product.template",
        inverse_name="pnt_waste_ler_id",
        string="Product",
        copy=False,
    )
    pnt_product_tmpl_count = fields.Integer(
        string="Product",
        compute="_compute_pnt_product_tmpl_count",
    )

    @api.depends("name")
    def _compute_pnt_ler_type(self):
        for record in self:
            record.pnt_is_dangerous = False
            record.pnt_is_raee = False
            if record.name:
                if len(record.name) == 7 and record.name[-1] == "*":
                    record.pnt_is_dangerous = True
                elif len(record.name) == 10 and record.name[-1] == "*":
                    record.pnt_is_raee = True
                    record.pnt_is_dangerous = True
                elif len(record.name) == 9:
                    record.pnt_is_raee = True

    def _compute_pnt_product_tmpl_count(self):
        product_tmpl_data = self.env["product.template"].read_group(
            [("pnt_waste_ler_id", "in", self.ids)],
            ["pnt_waste_ler_id"],
            ["pnt_waste_ler_id"],
        )
        mapped_data = dict(
            [
                (m["pnt_waste_ler_id"][0], m["pnt_waste_ler_id_count"])
                for m in product_tmpl_data
            ]
        )
        for ler in self:
            ler.pnt_product_tmpl_count = mapped_data.get(ler.id, 0)

    def unlink(self):
        for ler in self:
            if ler.pnt_product_tmpl_ids:
                raise UserError(
                    _("You cannot delete a waste LER containing product requests.")
                )
        return super(PntProductTmplWasteLer, self).unlink()

    _sql_constraints = [
        (
            "name_unique",
            "unique(name)",
            _("A LER with this name already exists."),
        )
    ]
