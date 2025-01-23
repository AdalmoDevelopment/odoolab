from odoo import _, api, fields, models


class PntWasteTransferDocument(models.Model):
    _name = "pnt.waste.transfer.document"
    _description = "Pnt Waste Transfer Document"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Code",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_legal_code = fields.Char(
        string="Legal code",
        compute="_compute_pnt_legal_code",
        store=True,
    )
    pnt_document_type = fields.Selection(
        [
            ("nt", _("NT")),
            ("di", _("DI")),
        ],
        string="Waste transfer document type",
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_type = fields.Selection(
        [
            ("esir", _("e-SIR")),
            ("singer", _("SINGER")),
            ("other", _("Other")),
        ],
        string="Type",
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_single_document_line_ids = fields.One2many(
        string="Single document lines",
        comodel_name="pnt.single.document.line",
        inverse_name="pnt_waste_transfer_document_id",
        copy=False,
    )
    pnt_single_document_id = fields.Many2one(
        "pnt.single.document",
        "Single Document",
        store=True,
    )
    pnt_product_id = fields.Many2one(
        # related="pnt_single_document_line_id.pnt_product_id",
        "product.product",
        "Product",
        compute="_compute_fields_pnt_single_document",
        readonly=False,
    )
    pnt_partner_id = fields.Many2one(
        # related="pnt_single_document_line_id.pnt_single_document_id.pnt_holder_id",
        "res.partner",
        "Partner",
        compute="_compute_fields_pnt_single_document",
        readonly=False,
    )
    pnt_sent = fields.Boolean(
        string="Sent",
        default=False,
    )
    pnt_date = fields.Date(
        string="Date",
        default=fields.Date.today,
    )
    pnt_end_date = fields.Date(
        string="End date",
    )
    pnt_agreement_registration_id = fields.Many2one(
        "pnt.agreement.registration",
        "Agreement registration",
    )
    pnt_document = fields.Binary(
        string="Document",
    )
    pnt_filename = fields.Char(
        string="File Name",
        readonly=True,
    )
    pnt_qty = fields.Float(
        string="Qty",
        # compute="_compute_pnt_qty",
        # store=True,
    )
    pnt_uom_id = fields.Many2one(
        "uom.uom",
        "Uom",
        compute="_compute_pnt_uom_id",
        readonly=False,
    )
    pnt_pn_id = fields.Many2one(
        "pnt.waste.transfer.document",
        "TN",
        domain=[
            ("pnt_document_type", "=", "tn"),
        ],
    )
    pnt_legal_code_hist = fields.Char(
        string="Legal code",
    )
    pnt_product_id_hist = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        readonly=False,
    )
    pnt_pdf_generated = fields.Binary(
        string="PDF generated",
    )
    pnt_xml_generated = fields.Binary(
        string="XML (E3L) generated",
    )

    # @api.depends("pnt_single_document_line_ids")
    # def _compute_pnt_qty(self):
    #     for record in self:
    #         if record.pnt_document_type == 'di' and record.pnt_single_document_line_ids:
    #             record.pnt_qty = sum(line.pnt_product_uom_qty
    #                          for line in record.pnt_single_document_line_ids)

    @api.depends(
        "pnt_single_document_line_ids",
        "pnt_agreement_registration_id",
    )
    def _compute_fields_pnt_single_document(self):
        for record in self:
            # record.pnt_single_document_id = record.pnt_single_document_line_ids[
            #     :1
            # ].pnt_single_document_id
            if record.pnt_single_document_line_ids:
                record.pnt_product_id = record.pnt_single_document_line_ids[
                    :1
                ].pnt_product_id
                record.pnt_partner_id = record.pnt_single_document_line_ids[
                    :1
                ].pnt_single_document_id.pnt_holder_id
            if record.pnt_agreement_registration_id:
                record.pnt_product_id = (
                    record.pnt_agreement_registration_id.pnt_product_id
                )
                record.pnt_partner_id = (
                    record.pnt_agreement_registration_id.pnt_pickup_id
                )

    def get_active_nt_of_current_di(self):
        for record in self:
            result = False
            if (record.pnt_document_type == 'di'
                and record.pnt_single_document_id
                and record.pnt_single_document_id.pnt_single_document_type == 'output'):
                current_partner_id = None
                current_product_id = None
                if record.pnt_single_document_line_ids:
                    current_partner_id = record.pnt_single_document_line_ids[
                        :1
                    ].pnt_single_document_id.pnt_partner_pickup_id
                    current_product_id = record.pnt_single_document_line_ids[
                        :1
                    ].pnt_product_id
                if current_partner_id and current_product_id:
                    active_nt_id = self.env['pnt.waste.transfer.document'].search([
                        ('pnt_agreement_registration_id.pnt_product_id',
                         '=',
                         current_product_id.id),
                        ('pnt_agreement_registration_id.pnt_pickup_id',
                         '=',
                         current_partner_id.id),
                        ('pnt_date','<=', record.pnt_date),
                        ('pnt_end_date','>=', record.pnt_date),
                    ],limit=1)
                    if active_nt_id:
                        result = active_nt_id
            return result

    def get_di_qty(self):
        for record in self:
            result = 0.0
            if record.pnt_document_type == 'di' and record.pnt_single_document_line_ids:
                result = sum(line.pnt_product_uom_qty
                             for line in record.pnt_single_document_line_ids)
            elif (record.pnt_document_type == 'di'
                        and not record.pnt_single_document_line_ids):
                result = record.pnt_qty
            return result
    @api.depends(
        "pnt_type",
        "pnt_document_type",
        "pnt_date",
        "pnt_single_document_line_ids",
    )
    def _compute_pnt_legal_code(self):
        legal_code = ""
        for record in self:
            if record.pnt_document_type == "di" and record.pnt_single_document_line_ids:
                # Si procede de DU -> Salida gestor debe coger NIMA de lugar de recogida
                du_type = record.pnt_single_document_id.pnt_single_document_type
                if du_type and du_type == "output":
                    nima_producer = record.pnt_single_document_id.get_partner_waste_codes(
                        "nima",
                        "end_mgm",
                        record.pnt_single_document_id.pnt_partner_delivery_id.id,
                    )
                else:
                    nima_producer = record.pnt_single_document_id.get_partner_waste_codes(
                        "nima", "producer"
                    )
                if nima_producer == "":
                    nima_producer = record.get_partner_waste_codes_di(
                        "nima",
                        "end_mgm",
                        self.company_id.du_di_partner_default_nima_id.id,
                    )
                if nima_producer == "":
                    nima_producer = "9999999999"
                sd_name = record.pnt_single_document_id.name[-5:]
                sd_id = str(record.pnt_single_document_line_ids[0].id)[-2:]
                legal_code = (
                    "DCS30"
                    + nima_producer
                    + str(record.pnt_date.year)
                    + sd_name
                    + sd_id
                )
            record.pnt_legal_code = legal_code

    def get_partner_waste_codes_di(self, typeinfo, typepartner, end_mgm_id=0):
        # typeinfo -> nima | rpgr | srap
        # typepartner -> agent | producer | transport | end_mgm
        # end_mgm_id -> solo se utiliza cuando typepartner es end_mgm
        result = ""
        partner = ""
        if typepartner == "end_mgm":
            partner = self.env["res.partner"].search([("id", "=", end_mgm_id)], limit=1)
        if partner:
            if partner.pnt_waste_nima_code_ids:
                agent = partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == typepartner
                )
                if agent:
                    if typeinfo == "nima":
                        result = agent[0].pnt_nima_code_id.name
                    elif typeinfo == "rpgr":
                        result = agent[0].display_name
                    elif typeinfo == "srap":
                        result = agent[0].pnt_operator_type_id.pnt_type_operator
            else:
                # Comprobar so el partner selecctonado tiene datso de gestor de residuos
                # en caso contrario, comprobar si tiene un padre y si es así asignarle el padre
                if partner.parent_id:
                    agent = partner.parent_id.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                        lambda x: x.pnt_authorization_code_type == typepartner
                    )
                    if agent:
                        if typeinfo == "nima":
                            result = agent[0].pnt_nima_code_id.name
                        elif typeinfo == "rpgr":
                            result = agent[0].display_name
                        elif typeinfo == "srap":
                            result = agent[0].pnt_operator_type
        return result

    def name_get(self):
        res = []
        for record in self:
            if record.pnt_legal_code:
                name = record.pnt_legal_code
            else:
                name = record.name
            res.append((record.id, name))
        return res

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.waste.transfer.document", sequence_date=seq_date
            ) or _("New")
        result = super(PntWasteTransferDocument, self).create(vals)
        return result

    @api.depends("pnt_product_id")
    def _compute_pnt_uom_id(self):
        for record in self:
            record.pnt_uom_id = False
            if record.pnt_product_id:
                record.pnt_uom_id = record.pnt_product_id.uom_id.id
