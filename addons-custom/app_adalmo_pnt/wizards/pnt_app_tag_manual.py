import datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
from datetime import date

class PntAppTagManual(models.TransientModel):
    _name = "pnt.app.tag.manual"

    name = fields.Char(
        string="QR code",
        store=True,
    )
    pnt_type = fields.Selection(
        [
            ("agreement", _("Agreement")),
            ("manual", _("Manual")),
        ],
        string="Type",
        copy=False,
        default='agreement',
        index=True,
        tracking=3,
    )
    pnt_related_holder_id = fields.Many2one(
        comodel_name="res.partner",
        string="Related Holder",
        default=lambda self: self.env.user.pnt_holder_id,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_holder_id = fields.Many2one(
        string="Holder",
        comodel_name="res.partner",
        store=True,
    )
    pnt_holder_domain_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="pnt_holder_domail_tags",
        compute='_compute_holder_domain_ids',
        store=True,
    )
    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.agreement",
    )
    pnt_agreement_domain_ids = fields.Many2many(
        comodel_name="pnt.agreement.agreement",
        store=True,
    )
    pnt_agreement_count = fields.Integer(
        string="Number of agreements",
        default=0,
        readonly=True,
    )
    pnt_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )
    pnt_partner_pickup_domain_ids = fields.Many2many(
        comodel_name="res.partner",
        store=True,
    )
    pnt_functional_unit_id = fields.Many2one(
        comodel_name="pnt.functional.unit",
        string="Functional unit",
    )
    pnt_date = fields.Date(
        string="Tag date",
        default=lambda self: date.today(),
    )
    pnt_print_date = fields.Boolean(
        string="Print date",
        default=True,
    )
    pnt_tag_type = fields.Selection(
        [
            ("sanitary", _("Sanitary")),
            ("dangerous", _("Dangerous")),
            ("notdangerous", _("Not Dangerous")),
        ],
        string="Tag type",
        copy=False,
        default='sanitary',
        index=True,
        tracking=3,
    )
    pnt_tag_waste_ids = fields.One2many(
        comodel_name="pnt.app.tag.manual.line",
        inverse_name="pnt_app_tag_manual_id",
    )
    # Methods
    @api.depends("pnt_related_holder_id")
    def _compute_holder_domain_ids(self):
        for tag in self:
            if tag.pnt_related_holder_id:
                holder_ids = self.env["res.partner"].search(
                    [
                        ("id", "=", tag.pnt_related_holder_id.id),
                    ],
                )
                tag.pnt_holder_domain_ids = holder_ids
            else:
                holder_ids = self.env["res.partner"].search(
                    [
                        ("is_company", "=", True),
                        ("pnt_is_lead", "=", False),
                        ("company_id", "in", (False,tag.company_id.id))
                    ],
                )
                tag.pnt_holder_domain_ids = holder_ids

        return False

    @api.onchange("pnt_type")
    def _onchange_pnt_type(self):
        for record in self:
            record.pnt_holder_id= None
            record.pnt_partner_id = None
            record.pnt_agreement_id = None
            record.pnt_partner_pickup_domain_ids = None
            record.pnt_agreement_count = 0
            record._onchange_pnt_agreement_id()
            record._onchange_pnt_partner_id()

    @api.onchange("pnt_agreement_id")
    def _onchange_pnt_agreement_id(self):
        for record in self:
            record.pnt_partner_id = None
            if record.pnt_type == "agreement":
                if (record.pnt_agreement_id
                        and record.pnt_agreement_id.pnt_partner_pickup_ids):
                    record.pnt_partner_pickup_domain_ids = (
                        record.pnt_agreement_id.pnt_partner_pickup_ids
                    )
            else:
                pnt_comp_ids = self.env["res.partner"].search(
                    [
                        ("type", "=", "delivery"),
                        ("company_id", "in", [self.env.company.id, False]),
                    ]
                )
                if pnt_comp_ids:
                    record.pnt_partner_pickup_domain_ids = pnt_comp_ids
    @api.onchange("pnt_holder_id")
    def _onchange_pnt_holder_id(self):
        for record in self:
            record.pnt_agreement_id = None
            record.pnt_agreement_domain_ids = None
            record.pnt_agreement_count = 0
            record.pnt_partner_id = None
            record.pnt_partner_pickup_domain_ids = None
            if record.pnt_holder_id:
                agreement_ids = self.env["pnt.agreement.agreement"].search(
                    [
                        ("pnt_holder_id", "=", record.pnt_holder_id.id),
                        ("state", "=", "done"),
                    ],
                )
                if agreement_ids:
                    record.pnt_agreement_domain_ids = agreement_ids
                    record.pnt_agreement_count = len(agreement_ids)
                agreement_id = self.env["pnt.agreement.agreement"].search(
                    [
                        ("pnt_holder_id", "=", record.pnt_holder_id.id),
                        ("state", "=", "done"),
                    ],
                    limit=1,
                )
                if agreement_id:
                    # if record.pnt_single_document_type != 'portal':
                    record.pnt_agreement_id = agreement_id
                    # Actualizar la lista de direcciones de recogida en función
                    # de las recogidas asignadas al contrato del titular
                    if record.pnt_agreement_id.pnt_partner_pickup_ids:
                        record.pnt_partner_pickup_domain_ids = (
                            record.pnt_agreement_id.pnt_partner_pickup_ids
                        )
                else:
                    raise UserError(
                        _(
                            "No se ha encontrado contrato activo para "
                            + record.pnt_holder_id.display_name
                        )
                    )
    @api.onchange('pnt_partner_id')
    def _onchange_pnt_partner_id(self):
        self.pnt_tag_waste_ids.unlink()
        self.pnt_functional_unit_id = None
        if self.pnt_partner_id.pnt_print_date_on_labels:
            self.pnt_print_date = True
        else:
            self.pnt_print_date = False
    @api.onchange('pnt_tag_type')
    def _onchange_pnt_tag_type(self):
        self.pnt_tag_waste_ids.unlink()

    def action_generate_tags(self):
        for tag in self:
            if tag.pnt_tag_waste_ids:
                docids = []
                for tag_qr in tag.pnt_tag_waste_ids:
                    for qty in range(tag_qr.pnt_quantity):
                        newtag = self.env["pnt.app.tag"].create(
                            {
                                "pnt_partner_id": tag.pnt_partner_id.id,
                                "pnt_holder_id": tag.pnt_holder_id.id,
                                "pnt_product_id": tag_qr.pnt_product_id.id,
                                "pnt_functional_unit_id": tag.pnt_functional_unit_id.id,
                                "pnt_tag_log_type": "manual",
                                "pnt_move_type": "outgoing",
                                "pnt_print_tag_date": tag.pnt_print_date,
                                "pnt_date": tag.pnt_date,
                            }
                        )
                        if newtag:
                            newtag.save_tag_log(False)
                            docids.append(newtag.id)
                if tag.pnt_tag_type in ('dangerous','notdangerous'):
                    xmlid = "app_adalmo_pnt.pnt_app_tag_report"
                else:
                    xmlid = "app_adalmo_pnt.pnt_app_tag_sanitary_report"
                action = self.env.ref(xmlid).report_action(docids)
                return action
            else:
                raise UserError(
                    _(
                        "Debe introducir residuos para poder generar las etiquetas"
                    )
                )
class PntAppTagManualLine(models.TransientModel):
    _name = "pnt.app.tag.manual.line"

    @api.depends("pnt_tag_type","pnt_agreement_id")
    def _get_pnt_products_domain_ids(self):
        for record in self:
            du_pickup = record.pnt_app_tag_manual_id.pnt_partner_id
            agree = record.pnt_agreement_id
            agree_lines = agree.pnt_agreement_line_ids
            agree_lines = agree_lines.filtered(
                lambda x, agreement=agree, pickup=du_pickup: x.pnt_partner_pickup_id.id
                in (False, pickup.id)
            )
            products = agree_lines.pnt_product_id.ids
            if record.pnt_tag_type == "sanitary":
                if record.pnt_app_tag_manual_id.pnt_type == "agreement":
                    products_filtered = self.env['product.product'].search(
                            [('pnt_is_sanitary', '=', True),
                             ('product_tmpl_id.company_id', '=', self.company_id.id),
                             ('id','in',products),
                             ],).ids
                else:
                    products_filtered = self.env['product.product'].search(
                            [('pnt_is_sanitary', '=', True),
                             ('product_tmpl_id.company_id', '=', self.company_id.id),
                             ], ).ids
            elif record.pnt_tag_type == "notdangerous":
                if record.pnt_app_tag_manual_id.pnt_type == "agreement":
                    products_filtered = self.env['product.product'].search(
                            [('pnt_is_sanitary', '=', False),
                             ('pnt_is_waste', '=', True),
                             ('pnt_is_dangerous', '=', False),
                             ('product_tmpl_id.company_id', '=', self.company_id.id),
                             ('id', 'in', products),
                             ],).ids
                else:
                    products_filtered = self.env['product.product'].search(
                            [('pnt_is_sanitary', '=', False),
                             ('pnt_is_waste', '=', True),
                             ('pnt_is_dangerous', '=', False),
                             ('product_tmpl_id.company_id', '=', self.company_id.id),
                             ],).ids
            else:
                if record.pnt_app_tag_manual_id.pnt_type == "agreement":
                    products_filtered = self.env['product.product'].search(
                            [('pnt_is_sanitary', '=', False),
                             ('pnt_is_dangerous', '=', True),
                             ('product_tmpl_id.company_id', '=', self.company_id.id),
                             ('id', 'in', products),
                             ],).ids
                else:
                    products_filtered = self.env['product.product'].search(
                            [('pnt_is_sanitary', '=', False),
                             ('pnt_is_dangerous', '=', True),
                             ('product_tmpl_id.company_id', '=', self.company_id.id),
                             ], ).ids
            record.pnt_products_domain_ids = [(6, False, products_filtered)]
            
    pnt_products_domain_ids = fields.Many2many(
        comodel_name="product.product",
        store=True,
        compute="_get_pnt_products_domain_ids",
        relation="pnt_products_tag_domain_rel",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_app_tag_manual_id = fields.Many2one(
        comodel_name="pnt.app.tag.manual",
        required=True,
    )
    pnt_agreement_id = fields.Many2one(
        related="pnt_app_tag_manual_id.pnt_agreement_id",
    )
    pnt_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        change_default=True,
        check_company=True,  # Unrequired company
        # domain=[
        #     ("pnt_is_waste", "=", True),
        # ],
    )
    pnt_tag_type = fields.Selection(
        related="pnt_app_tag_manual_id.pnt_tag_type",
    )
    pnt_quantity = fields.Integer(
        string="Quantity",
        default=1,
    )
