from odoo import models, fields, _


class PntPartnerWasteTable(models.Model):
    _name = "pnt.partner.waste.table"
    _description = "Pnt Partner Waste Table"

    name = fields.Char(
        string="Name",
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
    )
    pnt_product_tmpl_id = fields.Many2one(
        string="Product Tmpl",
        comodel_name="product.template",
        domain=[
            ("pnt_is_waste", "=", True),
        ],
    )
    pnt_waste_ler_id = fields.Many2one(
        string="LER Code",
        related="pnt_product_tmpl_id.pnt_waste_ler_id",
    )
    pnt_waste_table1_ids = fields.Many2many(
        string="Table 1",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table1")],
    )
    pnt_waste_table2_ids = fields.Many2many(
        string="Table 2",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table2")],
    )
    pnt_waste_table3_ids = fields.Many2many(
        string="Table 3",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table3")],
    )
    pnt_waste_table4_ids = fields.Many2many(
        string="Table 4",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table4")],
    )
    pnt_waste_table5_ids = fields.Many2many(
        string="Table 5",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table5")],
    )
    pnt_waste_table6_ids = fields.Many2many(
        string="Table 6",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table6")],
    )
    pnt_waste_table7_ids = fields.Many2many(
        string="Table 7",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_partner_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table7")],
    )
    pnt_label_name = fields.Char(
        string="Label Name",
    )

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.pnt_partner_id and record.pnt_product_tmpl_id:
                name = "[%s] %s" % (
                    record.pnt_partner_id.name,
                    record.pnt_product_tmpl_id.display_name,
                )
            res.append((record.id, name))
        return res

    _sql_constraints = [
        (
            "partner_waste_unique",
            "unique(pnt_partner_id, pnt_product_tmpl_id)",
            _("A product width this partner already exists."),
        )
    ]
