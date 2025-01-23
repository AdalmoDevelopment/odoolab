from odoo import SUPERUSER_ID, _, api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pnt_is_waste = fields.Boolean(
        string="Waste",
        help="This product belongs to a waste",
    )
    pnt_is_marpol_waste = fields.Boolean(
        string="MARPOL",
        help="This product belongs to a waste MARPOL",
    )
    pnt_waste_table1_ids = fields.Many2many(
        string="Table 1",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table1")],
    )
    pnt_waste_table2_ids = fields.Many2many(
        string="Table 2",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table2")],
    )
    pnt_waste_table3_ids = fields.Many2many(
        string="Table 3",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table3")],
    )
    pnt_waste_table4_ids = fields.Many2many(
        string="Table 4",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table4")],
    )
    pnt_waste_table5_ids = fields.Many2many(
        string="Table 5",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table5")],
    )
    pnt_waste_table6_ids = fields.Many2many(
        string="Table 6",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table6")],
    )
    pnt_waste_table7_ids = fields.Many2many(
        string="Table 7",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_product_tmpl_waste_table_rel",
        column1="product_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table7")],
    )
    pnt_waste_ler_id = fields.Many2one(
        string="LER Code",
        comodel_name="pnt.product.tmpl.waste.ler",
    )
    pnt_waste_ler_dangerous = fields.Boolean(
        string="LER Dangerous",
        related="pnt_waste_ler_id.pnt_is_dangerous",
    )
    pnt_label_name = fields.Char(
        string="Label Name",
    )
    pnt_marpol_waste_annex_id = fields.Many2one(
        string="MARPOL Attached",
        comodel_name="pnt.product.marpol.waste.annex",
        tracking=True,
    )
    pnt_marpol_waste_category_domain_ids = fields.Many2many(
        related="pnt_marpol_waste_annex_id.pnt_marpol_waste_category_ids",
    )
    pnt_marpol_waste_category_id = fields.Many2one(
        string="MARPOL Waste Category",
        comodel_name="pnt.product.marpol.waste.category",
        compute="_compute_pnt_marpol_waste_category_id",
        store=True,
        readonly=False,
        tracking=True,
        group_expand="_read_group_category_ids",
    )
    pnt_is_sanitary = fields.Boolean(
        string="Is Sanitary",
        related="categ_id.pnt_is_sanitary",
        store=True,
    )
    pnt_monetary_waste = fields.Selection(
        string="Monetary Waste",
        copy=False,
        selection=[
            ("inbound", "Inbound"),
            ("outbound", "Outbound"),
        ],
    )
    pnt_is_container = fields.Boolean(
        string="Is Container",
        related="categ_id.pnt_is_container",
        store=True,
    )
    pnt_product_tmpl_container_ids = fields.Many2many(
        string="Containers",
        comodel_name="product.template",
        domain=[("pnt_is_container", "=", True)],
        relation="pnt_product_tmpl_container_rel",
        column1="pnt_product_tmpl_id",
        column2="pnt_product_tmpl_container_id",
    )
    pnt_invisible_monetary_waste = fields.Boolean(
        string="Invisible Monetary Waste",
        compute="compute_pnt_invisible_monetary_waste",
        store=True,
    )
    pnt_container_movement_type = fields.Selection(
        [
            ("delivery", _("Delivery")),
            ("removal", _("Removal")),
            ("change", _("Change")),
        ],
        string="Container movement type",
        readonly=True,
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_container_color = fields.Integer(
        string="Color Index",
        default=0,
    )
    pnt_acceptance_waste_condition = fields.Text(string="Acceptance waste condition")
    pnt_more_relevant_info = fields.Text(string="More relevant information")
    pnt_rental = fields.Boolean(string="Rental")
    pnt_recurrence = fields.Boolean(string="Recurrence")
    pnt_is_waste_manipulation = fields.Boolean(string="Manipulation Waste")
    pnt_is_product_incidence = fields.Boolean(string="Product Incidence")

    @api.depends("pnt_marpol_waste_annex_id")
    def _compute_pnt_marpol_waste_category_id(self):
        self.pnt_marpol_waste_category_id = False

    @api.depends("pnt_is_container")
    def _compute_pnt_container_type(self):
        for record in self:
            if not record.pnt_is_container:
                record.pnt_container_type = False

    @api.depends("pnt_is_container", "pnt_is_sanitary", "pnt_is_waste")
    def compute_pnt_invisible_monetary_waste(self):
        for record in self:
            record.pnt_invisible_monetary_waste = True
            if record.pnt_is_container or record.pnt_is_sanitary or record.pnt_is_waste:
                record.pnt_invisible_monetary_waste = False

    @api.onchange("pnt_waste_ler_id")
    def _onchange_pnt_is_dangerous(self):
        for record in self:
            if record.pnt_waste_ler_id:
                record.is_dangerous = record.pnt_waste_ler_id.pnt_is_dangerous

    @api.model
    def _read_group_category_ids(self, categories, domain, order):
        category_ids = categories._search(
            [], order=order, access_rights_uid=SUPERUSER_ID
        )
        return categories.browse(category_ids)
