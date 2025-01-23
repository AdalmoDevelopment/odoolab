from odoo import _, api, fields, models


class PntAgreementRegistration(models.Model):
    _name = "pnt.agreement.registration"
    _description = "Agreement Registration"
    _rec_name = "pnt_pickup_id"
    _check_company_auto = True

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    pnt_agreement_sequence = fields.Char(
        string="Nº A.T.",
        # todo: delete
        # compute="_compute_pnt_agreement",
        # todo: delete
        store=True,
    )
    pnt_pickup_id = fields.Many2one(
        string="Producer",
        comodel_name="res.partner",
        ondelete="restrict",
    )
    pnt_product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
        check_company=True,
        ondelete="restrict",
    )
    pnt_ler_id = fields.Many2one(
        related="pnt_product_id.pnt_waste_ler_id",
    )
    pnt_nima = fields.Char(
        string="Nima",
        compute="_compute_pnt_agreement",
        store=True,
    )
    pnt_agreement_date = fields.Date(
        string="T.A. Date",
    )
    pnt_document = fields.Binary(
        string="Document",
    )
    pnt_filename = fields.Char(
        string="File Name",
        readonly=True,
    )
    pnt_waste_table1_ids = fields.Many2many(
        string="Table 1",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_agreement_registration_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table1")],
    )
    pnt_waste_table2_ids = fields.Many2many(
        string="Table 2",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_agreement_registration_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table2")],
    )
    pnt_waste_table3_ids = fields.Many2many(
        string="Table 3",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_agreement_registration_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table3")],
    )
    pnt_waste_table4_ids = fields.Many2many(
        string="Table 4",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_pagreement_registration_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table4")],
    )
    pnt_waste_table5_ids = fields.Many2many(
        string="Table 5",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_agreement_registration_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table5")],
    )
    pnt_waste_table6_ids = fields.Many2many(
        string="Table 6",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_agreement_registration_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table6")],
    )
    pnt_waste_table7_ids = fields.Many2many(
        string="Table 7",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_agreement_registration_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_waste_table_id",
        domain=[("pnt_table_type", "=", "table7")],
    )
    pnt_agreement_registration_type = fields.Selection(
        [
            ("producer", _("Producer")),
            ("mgm", _("Manager")),
        ],
        "Agreement registration type",
    )
    pnt_end_mgm_waste_table2_ids = fields.Many2many(
        string="Table 2",
        comodel_name="pnt.product.tmpl.waste.table",
        relation="pnt_end_mgm_waste_table_rel",
        column1="pnt_agreement_registration_id",
        column2="pnt_partner_id",
        domain=[("pnt_table_type", "=", "table2")],
    )
    pnt_state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("create", _("Create")),
            ("active", _("Active")),
        ],
        default="draft",
        readonly=True,
    )
    pnt_state_tn = fields.Selection(
        [
            ("without_tn", _("Without TN")),
            ("with_tn", _("With TN")),
        ],
        default="without_tn",
    )
    pnt_waste_transfer_document_ids = fields.One2many(
        "pnt.waste.transfer.document",
        "pnt_agreement_registration_id",
        "Transfer documents",
    )
    pnt_qty_to_transport = fields.Float(
        string="Quantity to Transport",
        digits="Product Unit of Measure",
    )
    pnt_periodicity_transfer = fields.Char(
        string="Periodicity of transfer",
        default=_("Periodicity"),
    )
    pnt_comments = fields.Char(
        string="Conditions for waste acceptance",
    )
    pnt_real_producer_id = fields.Many2one(
        string="Real Producer",
        comodel_name="res.partner",
        compute='_compute_pnt_real_producer_id',
        store=True,
    )
    pnt_report_name = fields.Char(
        string="Name",
        compute="_compute_report_fields",
    )
    pnt_report_email = fields.Char(
        string="Report Email",
        compute="_compute_report_fields",
    )
    pnt_report_phone = fields.Char(
        string="Report Phone",
        compute="_compute_report_fields",
    )
    pnt_auto_generate = fields.Boolean(
        string="Auto generate",
        default=False,
        help="Technical field, it is used to know if the contract has been autogenerated from the economic contract",
    )

    @api.depends("pnt_agreement_registration_type")
    def _compute_pnt_real_producer_id(self):
        for record in self:
            record.pnt_real_producer_id = None
            if (record.pnt_agreement_registration_type == "producer"
                    and self.env.company.pnt_agree_reg_producer_default_manager_id):
                record.pnt_real_producer_id = (
                    self.env.company.pnt_agree_reg_producer_default_manager_id)
    @api.depends("pnt_pickup_id")
    def _compute_pnt_agreement(self):
        for record in self:
            nima = ", ".join(
                record.pnt_pickup_id.pnt_waste_nima_code_ids.mapped("name")
            )
            record.pnt_nima = nima

    def _compute_report_fields(self):
        for record in self:
            if record.pnt_agreement_registration_type == "end_mgm":
                pickup_id = record.pnt_pickup_id
            else:
                pickup_id = record.company_id.partner_id
            name = pickup_id
            email = pickup_id
            phone = pickup_id
            if record.pnt_agreement_registration_type == "mgm":
                contact = pickup_id.child_ids.filtered(
                    lambda x: x.type == "contact" and x.pnt_is_contact_person
                )[:1]
                contact = (
                    contact
                    or pickup_id.commercial_partner_id.child_ids.filtered(
                        lambda x: x.type == "contact" and x.pnt_is_contact_person
                    )[:1]
                )
                email = contact or email
                phone = contact or phone
                name = contact or ""
            record.pnt_report_email = email.email or ""
            record.pnt_report_phone = (
                f"{phone.phone or ''}{(phone.mobile and '/' + phone.mobile) or ''}"
            )
            record.pnt_report_name = name and name.name or ""

    def active_contract(self):
        for record in self:
            record.pnt_state = "active"

    def process_contract(self):
        year = str(fields.Date.context_today(self).year)
        for record in self:
            if not record.pnt_agreement_sequence:
                code = record.env["ir.sequence"].next_by_code("agreement_registration")
                nima = record.pnt_nima
                nima = nima and nima[:10] or "0799999999"
                record.pnt_agreement_sequence = f"DA20{nima}{year}{code}"

    def _update_num_at(self):
        for record in self.filtered(lambda x: not x.pnt_agreement_sequence):
            record.process_contract()

    @api.model_create_multi
    def create(self, list_values):
        res = super().create(list_values)
        if "pnt_document" in list_values:
            self.active_contract()
        return res

    def write(self, values):
        res = super().write(values)
        if "pnt_document" in values:
            self.active_contract()
        if "pnt_agreement_sequence" in values:
            for record in self:
                record.pnt_state = "create"
        return res

    def pnt_get_table2_to_portal(self):
        table2_values = False
        if self.pnt_agreement_registration_type == "producer":
            table2_values = self.pnt_product_id.pnt_waste_table2_ids
        elif self.pnt_agreement_registration_type == "mgm":
            table2_values = self.pnt_waste_table2_ids
        return ", ".join(table2_values.mapped("name")) if table2_values else ''

    def pnt_get_table5_to_portal(self):
        table5_values = False
        if self.pnt_agreement_registration_type == "producer":
            table5_values = self.pnt_product_id.pnt_waste_table5_ids
        elif self.pnt_agreement_registration_type == "mgm":
            table5_values = self.pnt_waste_table5_ids
        return ", ".join(table5_values.mapped("name")) if table5_values else ''
