from odoo import _, api, fields, models
from odoo.addons.base.models.res_partner import WARNING_HELP, WARNING_MESSAGE
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    pnt_is_driver = fields.Boolean(
        string="Is Driver",
        default=False,
    )
    pnt_is_lead = fields.Boolean(
        string="Is Lead",
        default=True,
    )
    pnt_favorite_driver_asign = fields.Boolean(
        string="Favorite driver (Asign)",
        default=False,
        copy=False,
    )
    pnt_is_end_mgm = fields.Boolean(
        string="Is End Management",
        copy=False,
        compute="_compute_pnt_check_pnt_is_end_mgm",
    )
    pnt_waste_nima_code_ids = fields.One2many(
        string="Waste NIMA Code",
        comodel_name="pnt.nima.code",
        inverse_name="pnt_partner_id",
    )
    pnt_flag_is_driver = fields.Boolean(
        string="Flag Driver",
        compute="_compute_pnt_flag",
    )
    pnt_flag_is_end_mgm = fields.Boolean(
        string="Flag End Mgm",
        compute="_compute_pnt_flag",
    )
    pnt_flag_nima = fields.Boolean(
        string="Flag NIMA",
        compute="_compute_pnt_flag",
    )
    pnt_partner_waste_table_ids = fields.One2many(
        string="Partner Waste Table",
        comodel_name="pnt.partner.waste.table",
        inverse_name="pnt_partner_id",
    )
    pnt_agreement_count = fields.Integer(
        string="Agreement count",
        compute="_compute_pnt_agreement_count",
    )
    pnt_du_count = fields.Integer(
        string="Single document count",
        compute="_compute_pnt_du_count",
    )
    pnt_property_ref_customer = fields.Char(
        string="Reference customer",
        company_dependent=True,
    )
    pnt_property_ref_supplier = fields.Char(
        string="Reference supplier",
        company_dependent=True,
    )
    pnt_property_ref_creditor = fields.Char(
        string="Reference creditor",
        company_dependent=True,
    )
    pnt_variable_direction = fields.Boolean(
        string="Variable direction",
        default=False,
    )
    pnt_functional_unit_ids = fields.One2many(
        comodel_name="pnt.functional.unit",
        inverse_name="pnt_partner_id",
        string="Functional Units",
        copy=True,
        auto_join=True,
    )
    pnt_resource_pick_id = fields.Many2one(
        string="Resource pick",
        comodel_name="resource.calendar",
        domain="[('pnt_external', '=', True)]",
    )
    pnt_resource_pick_ids = fields.One2many(
        "resource.calendar",
        "pnt_partner_id",
        string="Resource pick",
    )

    pnt_portal_agreement_type_id = fields.Many2one(
        string="Portal Agreement: Generic",
        comodel_name="pnt.agreement.agreement",
        domain="[('pnt_agreement_type', '=', 'portal'),"
        "('state', 'in', ('active','done'))]",
    )
    pnt_portal_agreement_specific_id = fields.Many2one(
        string="Portal Agreement: Specific",
        comodel_name="pnt.agreement.agreement",
    )

    pnt_dni_image = fields.Binary(
        string="DNI image",
    )
    pnt_dni_image_reverse = fields.Binary(
        string="DNI image reverse",
    )
    pnt_dni_date_validity = fields.Date(
        string="DNI date validity",
    )
    pnt_create_date = fields.Datetime(
        string="contact creation date",
        default=lambda self: fields.Datetime.now(),
    )
    property_account_position_id = fields.Many2one(
        default=lambda self: self.env["account.fiscal.position"].search(
            [("pnt_default_in_partner", "=", 1)], limit=1
        ),
    )
    pnt_is_contact_person = fields.Boolean(
        default=False,
        string="Is contact person",
    )
    pnt_check_number_certificate = fields.Boolean(
        default=False,
        string="N Cert",
        store=True,
        index=True,
    )
    du_warn = fields.Selection(
        WARNING_MESSAGE,
        "DU Warnings",
        default="no-message",
        help=WARNING_HELP,
        track_visibility="onchange",
    )
    du_warn_msg = fields.Text(
        "Message for DU",
        track_visibility="onchange",
    )
    agreement_warn = fields.Selection(
        WARNING_MESSAGE,
        "Agreement Warnings",
        default="no-message",
        help=WARNING_HELP,
        track_visibility="onchange",
    )
    agreement_warn_msg = fields.Text(
        "Message for Agreement",
        track_visibility="onchange",
    )
    pnt_id_type = fields.Selection(
        string="Identity document",
        selection=[
            ("nif", "NIF"),
            ("cif", "CIF"),
            ("nie", "NIE"),
        ],
        default="nif",
    )
    pnt_agreement_registration_count = fields.Integer(
        string="Agreement Registration Count",
        compute="_compute_pnt_agreement_registration_count",
    )
    pnt_agreement_pickup_registration_count = fields.Integer(
        string="Agreement Pickup Registration Count",
        compute="_compute_pnt_agreement_pickup_registration_count",
    )
    pnt_is_boat = fields.Boolean(
        string="Is Boat",
        compute="_compute_pnt_is_boat",
        store=True,
        readonly=False,
    )
    pnt_num_imo = fields.Char(
        string="Num IMO",
    )
    pnt_gross_tonnage = fields.Float(
        string="Gross Tonnage",
    )
    pnt_boat_type_id = fields.Many2one(
        string="Boat Type",
        comodel_name="pnt.boat.type",
    )
    pnt_ship_owner = fields.Char(
        string="Ship Owner",
    )
    pnt_distributive_number_or_letters = fields.Char(
        string="Distributive number or letters",
    )
    pnt_flag_state = fields.Char(
        string="Flag state",
    )
    pnt_boat_type = fields.Char(
        string="Boat Type",
    )
    pnt_sign_image = fields.Image(
        "Manager Sign",
        max_width=800,
        max_height=800,
        store=True,
        tracking=True,
    )
    pnt_cnae = fields.Char(
        string="CNAE",
    )
    pnt_agreement_registration_ids = fields.One2many(
        string="Agreement Registrations",
        comodel_name="pnt.agreement.registration",
        inverse_name="pnt_pickup_id",
    )
    pnt_send_du_signed = fields.Boolean(
        string="Send DU signed",
        default=False,
    )
    partner_latitude = fields.Float(
        digits=(16, 6),
    )
    partner_longitude = fields.Float(
        digits=(16, 6),
    )
    @api.depends("type")
    def _compute_pnt_is_boat(self):
        for record in self.filtered("pnt_is_boat"):
            if record.type != "delivery":
                record.pnt_is_boat = False

    def _search_agreement_only_lines_products_waste(self):
        company_id = self.env.company.id
        lines = self.env["pnt.agreement.registration"].search(
            [
                ("company_id", "=", company_id),
                ("pnt_pickup_id", "=", self.id),
            ]
        )
        return lines
    def pnt_is_scrap(self):
        for record in self:
            result = False
            # Tolo - 24/05/2024 - Modificado por historia HU52424
            # if record.category_id.filtered(
            #         lambda x: x.name == 'SRAP/SCRAP'
            #     ):
            #     result = True
            if record.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == 'scrap'
                ):
                result = True
            return result

    def _compute_pnt_agreement_registration_count(self):
        self.pnt_agreement_registration_count = 0
        for record in self:
            if record.type != "delivery":
                continue
            record.pnt_agreement_registration_count = len(
                record._search_agreement_only_lines_products_waste()
            )
    def _compute_pnt_agreement_pickup_registration_count(self):
        self.pnt_agreement_pickup_registration_count = 0
        for record in self:
            if record.type == "delivery":
                agreement_obj = self.env['pnt.agreement.agreement'].search(
                    [
                        ('pnt_partner_pickup_ids','=',record.id),
                        ('state', 'in', ('done', 'active', 'to_renew')),
                     ])
                if agreement_obj:
                    record.pnt_agreement_pickup_registration_count = len(agreement_obj)

    def action_view_agreement_registration(self):
        if self.type != "delivery":
            return {}
        lines = self._search_agreement_only_lines_products_waste()
        if not lines:
            return {}
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "custom_pnt.pnt_agreement_registration_action"
        )
        action["domain"] = [("id", "in", lines.ids)]
        return action

    @api.constrains("pnt_is_boat")
    def _check_pnt_is_boat(self):
        for record in self:
            if record.pnt_is_boat and record.type != "delivery":
                raise ValidationError(_("Only transporters can be boats!"))

    @api.model
    def _get_default_address_format(self):
        return f"{self._get_default_street()}, {self.zip if self.zip else ''}, {self.city if self.city else ''}"

    @api.model
    def _get_default_street(self):
        return f"{self.street if self.street else ''} {self.street2 if self.street2 else ''}"

    @api.model
    def _get_contact_person(self):
        contact_person = self.child_ids.filtered(
            lambda x: x.type == "contact" and x.pnt_is_contact_person
        )
        if not contact_person:
            contact_person = self.commercial_partner_id.child_ids.filtered(
                lambda x: x.type == "contact" and x.pnt_is_contact_person
            )
        if contact_person:
            return contact_person[0]

    def _get_contact_person_phones(self):
        contact_person = self.search(
            [
                ("pnt_is_contact_person", "=", True),
                ("parent_id", "=", self.id),
                ("type", "=", "contact"),
            ],
            limit=1,
        )
        if contact_person:
            phones = ""
            if contact_person.phone:
                phones += contact_person.phone
            if contact_person.mobile:
                if len(phones) > 0:
                    phones += "/"
                phones += contact_person.mobile
            return phones

    def _compute_pnt_flag(self):
        for record in self:
            record.pnt_flag_is_driver = False
            record.pnt_flag_nima = False
            record.pnt_flag_is_end_mgm = False
            if record.company_type == "person" and record.type == "contact":
                record.pnt_flag_is_driver = True
            if (
                record.company_type == "company" and record.type == "contact"
            ) or record.type == "delivery":
                record.pnt_flag_nima = True
                record.pnt_flag_is_end_mgm = True

    def _compute_pnt_agreement_count(self):
        all_partners = self.with_context(active_test=False).search(
            [("id", "child_of", self.ids)]
        )
        all_partners.read(["parent_id"])

        agreement_groups = self.env["pnt.agreement.agreement"].read_group(
            domain=[
                ("state", "in", ("done", "to_renew", "active")),
                ("pnt_holder_id", "in", all_partners.ids),
            ],
            fields=[
                "pnt_holder_id",
            ],
            groupby=[
                "pnt_holder_id",
            ],
        )
        partners = self.browse()
        for group in agreement_groups:
            partner = self.browse(group["pnt_holder_id"][0])
            while partner:
                if partner in self:
                    partner.pnt_agreement_count += group["pnt_holder_id_count"]
                    partners |= partner
                partner = partner.parent_id
        (self - partners).pnt_agreement_count = 0

    def _compute_pnt_du_count(self):
        all_partners = self.with_context(active_test=False).search(
            [("id", "child_of", self.ids)]
        )
        all_partners.read(["parent_id"])

        du_groups = self.env["pnt.single.document"].read_group(
            domain=[
                ("state", "in", ("done", "active", "plant", "received", "finished")),
                ("pnt_du_partner_id", "in", all_partners.ids),
            ],
            fields=[
                "pnt_du_partner_id",
            ],
            groupby=[
                "pnt_du_partner_id",
            ],
        )
        partners = self.browse()
        for group in du_groups:
            partner = self.browse(group["pnt_du_partner_id"][0])
            while partner:
                if partner in self:
                    partner.pnt_du_count += group["pnt_du_partner_id_count"]
                    partners |= partner
                partner = partner.parent_id
        (self - partners).pnt_du_count = 0

    def _compute_pnt_check_pnt_is_end_mgm(self):
        for record in self:
            record.pnt_is_end_mgm = False
            # record.pnt_is_end_mgm = False
            # nima_type = record.mapped("pnt_waste_nima_code_ids").mapped(
            #     "pnt_authorization_code_type_ids.name")
            # if nima_type and "end_mgm" in nima_type:
            #     record.pnt_is_end_mgm = True

    def action_resource_calendar_attendance(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "custom_pnt.resource_calendar_attendance_action"
        )
        action["context"] = {
            "search_default_calendar_id": self.pnt_resource_pick_id.id,
            "search_default_groupby_date_from": True,
            "search_default_groupby_pnt_custom_name": True,
            "default_calendar_id": self.pnt_resource_pick_id.id,
            "not_copy": True,
        }
        return action

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        fields_to_search = ["name", "vat"]
        for field in fields_to_search:
            recs = self.search([(field, operator, name)] + args, limit=limit)
            if recs.ids:
                break
        else:
            return super(ResPartner, self).name_search(
                name=name, args=args, operator=operator, limit=limit
            )
        return recs.name_get()

    @api.onchange("pnt_is_lead")
    def onchange_pnt_is_lead(self):
        if self.pnt_is_lead and self.ids:
            active_agreements = self.env["pnt.agreement.agreement"].search(
                [
                    ("pnt_holder_id", "=", self.ids[0]),
                    ("state", "in", ["active", "done"]),
                ]
            )
            if active_agreements:
                raise ValidationError(
                    _(
                        f"¡Este usuario tiene contratos activos (o bloqueados). Debe cancelar sus contratos antes de poder marcarlo como LEAD!"
                    )
                )

    @api.onchange("pnt_is_contact_person")
    def onchange_pnt_is_contact_person(self):
        if self.create_uid:
            exist = self.search(
                [
                    ("pnt_is_contact_person", "=", True),
                    ("id", "!=", self.id.origin),
                    ("parent_id", "=", self.parent_id.id.origin),
                ]
            )
            if exist and self.pnt_is_contact_person:
                raise ValidationError(
                    _(
                        "¡Este usuario ya tiene un contacto asignado! -- %s --. Si has desmarcado dicho contacto, guarde el usuario para poder marcar este."
                        % exist.name
                    )
                )

    @api.constrains("customer_payment_mode_id")
    def _check_giro_fields(self):
        for partner in self:
            if partner.customer_payment_mode_id.pnt_is_giro:
                if not partner.bank_ids:
                    raise models.ValidationError(
                        "El campo cuenta bancaria del cliente es obligatorio para giros."
                    )
                if self.mandate_count < 1:
                    raise models.ValidationError(
                        "El cliente debe tener un mandato bancario creado para giros."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("is_company") == True:
                vals["type"] = "contact"
            if "parent_id" in vals:
                parent = vals.get("parent_id")
                if parent:
                    parent_obj = self.env["res.partner"].search([("id","=",parent)],
                                                                limit=1)
                    if parent_obj and parent_obj.pnt_id_type:
                        vals["pnt_id_type"] = parent_obj.pnt_id_type
        return super().create(vals_list)

    @api.onchange("company_type")
    def _onchange_company_type(self):
        if self.company_type == "person":
            self.pnt_is_lead = False
        elif self.company_type == "company":
            self.pnt_is_lead = True


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    pnt_type = fields.Selection(
        [
            ("other", _("Other")),
            ("sector", _("Sector")),
        ],
        string="Partner tag type",
        readonly=True,
        copy=True,
        index=True,
    )


class PntFunctionalUnit(models.Model):
    _name = "pnt.functional.unit"
    _description = "Pnt Functional Unit"
    _check_company_auto = True

    pnt_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )

    name = fields.Char(
        string="Code",
        required=True,
    )
    description = fields.Char(
        string="Description",
    )

    def name_get(self):
        res = []
        for record in self:
            code = record.name
            name = code
            if record.description:
                name = "[" + record.name + "] " + record.description
            res.append((record.id, name))
        return res


class Partner(models.Model):
    _inherit = "res.partner"

    type = fields.Selection(
        [
            ("contact", "Contact"),
            ("invoice", "Invoice Address"),
            ("delivery", "Delivery Address"),
            ("other", "Other Address"),
            ("private", "Private Address"),
        ],
        string="Address Type",
        default="delivery",
        help="Invoice & Delivery addresses are used in sales orders. Private addresses are only visible by authorized users.",
    )
