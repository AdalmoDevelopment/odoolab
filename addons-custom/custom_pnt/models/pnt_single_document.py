import datetime
import socket
import telnetlib
import time as imp_time
from datetime import date, datetime, time, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from .. import TASK_STAGES


class PntSingleDocument(models.Model):
    _name = "pnt.single.document"
    _description = "Pnt Single Document"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    task_id = fields.Many2one(
        comodel_name="project.task",
        string="Task associated to this single document",
        copy=False,
    )
    tasks_count = fields.Integer(
        string="Tasks",
        compute="_compute_task_id",
        groups="project.group_project_user",
    )
    project_id = fields.Many2one(
        string="Project",
        comodel_name="project.project",
        default=lambda self: self.env.company.pnt_single_document_project_id.id,
    )
    name = fields.Char(
        string="Single document",
        required=True,
        copy=False,
        readonly=True,
        states={"newdu": [("readonly", False)]},
        index=True,
        default=lambda self: _("New"),
    )
    pnt_single_document_type = fields.Selection(
        [
            ("portal", _("Portal")),
            ("pickup", _("DU service")),
            ("output", _("Output manager")),
            ("toplant", _("Brought to plant")),
            ("marpol", "Marpol"),
            ("others", _("External service")),
            ("internal", _("Internal")),
        ],
        string="Single Document type",
        readonly=True,
        states={"newdu": [("readonly", False)]},
        copy=True,
        index=True,
    )
    pnt_single_document_type_logistic = fields.Selection(
        [
            ("pickup", _("DU service")),
            ("output", _("Output manager")),
            ("toplant", _("Brought to plant")),
            ("marpol", "Marpol"),
            ("others", _("External service")),
            ("internal", _("Internal")),
        ],
        string="Single Document type",
        readonly=True,
        states={"newdu": [("readonly", False)]},
        copy=True,
        index=True,
        default="pickup",
    )

    @api.onchange("pnt_single_document_type_logistic")
    def _onchange_pnt_single_document_type_logistic(self):
        self.pnt_single_document_type = self.pnt_single_document_type_logistic

    pnt_create_service = fields.Selection(
        [
            ("yes", _("Si")),
            ("no", _("No")),
        ],
        string="Create service",
        compute="compute_pnt_create_service",
        store=True,
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_logistic_route_id = fields.Many2one(
        "pnt.logistic.route",
        string="Logistic route",
    )
    pnt_metal_scales_description = fields.Char(
        string="Description",
    )
    state = fields.Selection(
        [
            ("newdu", _("DU Petition ")),
            ("dispached", _("DU in progress")),
            ("active", _("Active")),
            ("done", _("Locked")),
            ("cancel", _("Cancelled")),
            ("plant", _("In plant")),
            ("received", _("Received")),
            ("finished", _("Finished")),
        ],
        string="State",
        readonly=True,
        copy=False,
        index=True,
        tracking=4,
        default="newdu",
    )
    pnt_pickup_date_type = fields.Selection(
        [
            ("date", _("Date")),
            ("soon", _("As soon as possible")),
        ],
        string="When",
        readonly=True,
        index=True,
        tracking=3,
        default="soon",
    )
    pnt_pickup_date = fields.Datetime(
        string="Pickup Date",
        index=True,
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
            "done": [("readonly", False)],
        },
        readonly=True,
        default=lambda self: fields.Datetime.now(),
    )
    pnt_customer_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Customer Payment mode",
        check_company=True,
        compute="compute_pnt_holder_id",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        store=True,
        readonly=True,
    )
    pnt_customer_payment_term_id = fields.Many2one(
        comodel_name="account.payment.term",
        string="Customer Payment Terms",
        check_company=True,  # Unrequired company
        compute="compute_pnt_holder_id",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        store=True,
        readonly=True,
    )
    pnt_supplier_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Supplier Payment mode",
        check_company=True,
        compute="compute_pnt_holder_id",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        store=True,
        readonly=True,
    )
    pnt_supplier_payment_term_id = fields.Many2one(
        comodel_name="account.payment.term",
        string="Supplier Payment Terms",
        check_company=True,  # Unrequired company
        compute="compute_pnt_holder_id",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Salesperson",
        index=True,
        tracking=2,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ),
        readonly=False,
        compute="_compute_pnt_user_id",
        store=True,
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    pnt_du_partner_id = fields.Many2one(
        string="DU partner",
        comodel_name="res.partner",
        compute="_compute_pnt_du_partner_id",
        store=True,
    )

    pnt_holder_id = fields.Many2one(
        string="Holder",
        comodel_name="res.partner",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        readonly=True,
        store=True,
        domain=[
            ("is_company", "=", True),
            ("pnt_is_lead", "=", False),
        ],
        copy=True,
    )
    pnt_partner_pickup_id = fields.Many2one(
        string="Partner pickup",
        comodel_name="res.partner",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        domain=[
            ("type", "=", "delivery"),
        ],
        readonly=True,
    )
    pnt_partner_pickup_id_name = fields.Char(
        string="Partner pickup",
        related="pnt_partner_pickup_id.display_name",
    )
    pnt_partner_pickup_domain_ids = fields.Many2many(
        comodel_name="res.partner",
        compute="_compute_pnt_partner_pickup_domain_ids",
    )
    pnt_partner_delivery_domain_ids = fields.Many2many(
        comodel_name="res.partner",
        compute="_compute_pnt_partner_pickup_domain_ids",
    )

    pnt_variable_direction = fields.Boolean(
        string="Variable direction",
        related="pnt_partner_pickup_id.pnt_variable_direction",
    )
    pnt_producer_id = fields.Many2one(
        string="Producer",
        comodel_name="res.partner",
        compute="compute_pnt_producer_id",
    )
    pnt_carrier_id = fields.Many2one(
        string="Carrier",
        comodel_name="res.partner",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        domain=[
            ("is_company", "=", True),
            ("category_id", "=", 9),
        ],
        readonly=True,
        copy=False,
        check_company=True,
        compute="_compute_pnt_carrier_id",
        store=True,
    )
    pnt_domain_vehicle_ids = fields.Many2many(
        string="Domain vehicles",
        comodel_name="fleet.vehicle",
        compute="_compute_pnt_domain_vehicle_ids",
    )
    pnt_domain_transport_ids = fields.Many2many(
        string="Domain transports",
        comodel_name="res.partner",
        compute="_compute_pnt_domain_transport_ids",
    )
    pnt_transport_id = fields.Many2one(
        string="Driver",
        comodel_name="res.partner",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        readonly=True,
        copy=False,
        check_company=True,
    )
    pnt_vehicle_category_id = fields.Many2one(
        string="Vehicle Category",
        comodel_name="pnt.fleet.vehicle.category",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_vehicle_id = fields.Many2one(
        string="Vehicle",
        comodel_name="fleet.vehicle",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_vehicle_aux_id = fields.Many2one(
        string="Vehicle",
        comodel_name="fleet.vehicle",
    )
    pnt_vehicle_second_registration = fields.Char(
        string="Second registration",
    )
    pnt_partner_delivery_id = fields.Many2one(
        string="Partner delivery",
        comodel_name="res.partner",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        domain=[
            ("type", "=", "delivery"),
        ],
        readonly=True,
    )
    pnt_operator_id = fields.Many2one(
        string="Operator",
        comodel_name="res.partner",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        readonly=True,
        default=lambda self: self.env.company.partner_id.id,
    )
    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.agreement",
        states={
            "newdu": [("readonly", False)],
            "dispached": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_agreement_domain_ids = fields.Many2many(
        comodel_name="pnt.agreement.agreement",
        store=False,
    )
    pnt_scales_domain_ids = fields.Many2many(
        comodel_name="pnt.scales",
        relation="pnt_single_document_scales_domain_rel",
        column1="scale_id",
        column2="du_id",
        compute="_compute_pnt_scales_domain_ids",
    )
    pnt_agreement_count = fields.Integer(
        string="Number of agreements",
        default=0,
        readonly=True,
    )
    pnt_admitted = fields.Boolean(
        string="Admitted",
        compute="_compute_pnt_admitted",
        store=True,
        readonly=False,
        tracking=True,
        copy=False,
    )
    # dirección
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one(
        "res.country.state",
        string="State",
        ondelete="restrict",
        domain="[('country_id', '=?', country_id)]",
    )
    country_id = fields.Many2one("res.country", string="Country", ondelete="restrict")
    partner_latitude = fields.Float(string="Geo Latitude", digits=(16, 6))
    partner_longitude = fields.Float(string="Geo Longitude", digits=(16, 6))
    email = fields.Char()
    email_formatted = fields.Char(
        "Formatted Email",
        compute="_compute_email_formatted",
        help='Format email address "Name <email@domain>"',
    )
    phone = fields.Char()
    mobile = fields.Char()

    # Lineas
    pnt_single_document_line_ids = fields.One2many(
        comodel_name="pnt.single.document.line",
        inverse_name="pnt_single_document_id",
        string="Single Document Lines",
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "active": [("readonly", False)],
        },
        copy=True,
        auto_join=True,
    )
    pnt_single_document_holder_portal_ids = fields.One2many(
        comodel_name="pnt.single.document.holder.portal",
        inverse_name="pnt_single_document_id",
        string="Single Document Holder portal",
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "active": [("readonly", False)],
        },
        copy=True,
        auto_join=True,
    )
    pnt_stock_picking_ids = fields.Many2many(
        comodel_name="stock.picking",
        string="Stock pickings",
        relation="pnt_du_stock_picking_rel",
        column1="pnt_single_document_id",
        column2="stock_picking_id",
        copy=False,
    )
    pnt_stock_picking_id = fields.Many2one(
        comodel_name="stock.picking",
        string="Alabarà generat",
        copy=False,
    )
    picking_count = fields.Integer(
        string="# Pickings",
        compute="_compute_picking_count",
        copy=False,
    )
    pnt_di_count = fields.Integer(
        string="# DI",
        compute="_compute_pnt_di_count",
        copy=False,
    )
    pnt_purchase_order_ids = fields.Many2many(
        comodel_name="purchase.order",
        string="Purchase orders",
        relation="pnt_du_purchase_order_rel",
        column1="pnt_single_document_id",
        column2="purchase_order_id",
        copy=False,
    )
    pnt_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Compra generada",
        copy=False,
    )
    purchase_count = fields.Integer(
        string="# Purchases",
        compute="_compute_purchase_count",
        copy=False,
    )
    purchase_invoice_count = fields.Integer(
        string="# Purchase invoives",
        compute="_compute_purchase_invoice_count",
        copy=False,
    )
    pnt_sale_order_ids = fields.Many2many(
        comodel_name="sale.order",
        string="Sale orders",
        relation="pnt_du_sale_order_rel",
        column1="pnt_single_document_id",
        column2="sale_order_id",
        copy=False,
    )
    sale_count = fields.Integer(
        string="# Sales",
        compute="_compute_sale_count",
        copy=False,
    )
    sale_invoice_count = fields.Integer(
        string="# Sale invoives",
        compute="_compute_sale_invoice_count",
        copy=False,
    )
    pnt_partner_pickup_id_vat = fields.Char(
        related="pnt_partner_pickup_id.vat",
        string="Holder pickup vat",
        store=True,
    )
    pnt_scales_id = fields.Many2one(
        comodel_name="pnt.scales",
        string="Default scales",
        compute="_compute_pnt_scale_id",
        store=True,
    )
    pnt_product_product_metal_scale_ids = fields.Many2many(
        store=True,
        comodel_name="pnt.single.document.metal.line",
        compute="_get_pnt_product_product_metal_scale_ids",
    )

    pnt_partner_pickup_id_locked = fields.Boolean(
        compute="compute_pnt_partner_pickup_id_locked",
    )
    pnt_du_dest_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="DU destination",
        copy=False,
    )
    pnt_observations = fields.Html(
        string="Observaciones",
        readonly=True,
    )
    pnt_there_is_waste = fields.Boolean(
        compute="compute_pnt_there_is_waste",
    )
    pnt_show_create_service = fields.Boolean(
        compute="_compute_pnt_show_create_service",
    )
    pnt_show_du_lines = fields.Boolean(
        compute="_compute_pnt_show_du_lines",
    )
    pnt_last_weighing_qty = fields.Float(
        string="Last weighing",
        default=0.0,
        digits="Product Unit of Measure",
        copy=False,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    pnt_amount_total_sale = fields.Monetary(
        string="Amount total sale",
        required=True,
        digits="Product Price",
        default=0.0,
        compute="compute_pnt_amount_total_sale_purchase",
        store=True,
        readonly=False,
    )
    pnt_amount_total_purchase = fields.Monetary(
        string="Amount total purchase",
        required=True,
        digits="Product Price",
        default=0.0,
        compute="compute_pnt_amount_total_sale_purchase",
        store=True,
        readonly=False,
    )
    pnt_single_document_issue_project_ids = fields.One2many(
        "project.task",
        "pnt_single_document_id",
        string="SD Issues",
        # domain=[
        #     ("project_id", "=", "company_id.pnt_single_document_issue_project_id")
        # ]
    )
    pnt_single_document_issue_project_count = fields.Integer(
        string="Count SD Issue",
        compute="_pnt_compute_issue_project_count",
    )
    pnt_has_invoice = fields.Boolean(store=False)
    pnt_agreement_reference = fields.Char(
        string="Agreement reference",
    )
    pnt_order_reference = fields.Char(
        string="DU Order reference",
        copy=False,
    )
    pnt_group_lines = fields.Boolean(
        string="Group same product lines in order",
        default=False,
    )
    pnt_load_du_visible = fields.Boolean(
        compute="_compute_load_du_visible",
        store=True,
    )
    pnt_force_admitted = fields.Boolean(
        string="Force Admittted",
        copy=False,
    )
    pnt_force_in_final_manager = fields.Boolean(
        string="In Final Manager",
        copy=False,
    )
    pnt_ship_scale_num = fields.Char(
        string="Ship Scale No",
    )
    pnt_control_sheet_ids = fields.One2many(
        string="Control sheets",
        comodel_name="pnt.control.sheet",
        inverse_name="pnt_single_document_id",
        copy=False,
    )
    pnt_show_vehicle = fields.Boolean(
        compute="_compute_pnt_show_vehicle",
        store=True,
        default=False,
    )
    pnt_show_vehicle_aux = fields.Boolean(
        compute="_compute_pnt_show_vehicle",
        store=True,
        default=False,
    )
    pnt_check_number_certificate_single = fields.Boolean(
        related="pnt_holder_id.pnt_check_number_certificate",
        string="N Cert",
        readonly=True,
    )
    pnt_di_ids = fields.Many2many(
        string="DI",
        comodel_name="pnt.waste.transfer.document",
        compute="_compute_pnt_di_ids",
    )
    pnt_effective_date = fields.Date(
        string="Efective date",
        compute="_compute_pnt_effective_date",
        store=True,
    )
    pnt_du_end_date = fields.Date(
        string="DU end date",
        compute="_compute_pnt_du_end_date",
        store=True,
    )
    pnt_du_signed_file = fields.Binary(
        string="DU Signed",
        copy=False,
    )
    pnt_date_email_sent = fields.Datetime(
        string="Date email sent",
    )
    pnt_filename_du_signed = fields.Char(
        string="DU Signed filename",
        copy=False,
    )
    pnt_hours = fields.Float(
        string="Hours",
        default=0.0,
    )
    pnt_date_to_plant = fields.Datetime(
        string="Date to plant",
        compute="_compute_pnt_date_to_plant",
        store=True,
    )
    @api.depends("state")
    def _compute_pnt_date_to_plant(self):
        for du in self:
            if du.state in ("plant"):
                du.pnt_date_to_plant = fields.Datetime.now()
    @api.depends("pnt_agreement_id")
    def _compute_pnt_user_id(self):
        for du in self:
            du.pnt_user_id = du.pnt_agreement_id.pnt_user_id or self.env.user

    def _compute_pnt_di_ids(self):
        for record in self:
            record.pnt_di_ids = (
                record.pnt_single_document_line_ids.pnt_waste_transfer_document_id
            )

    @api.depends("task_id.date_deadline", "pnt_pickup_date")
    def _compute_pnt_effective_date(self):
        for record in self:
            ddate = fields.Datetime.context_timestamp(self, record.pnt_pickup_date)
            if record.task_id.date_deadline:
                ddate = record.task_id.date_deadline
            record.pnt_effective_date = ddate

    @api.depends("state")
    def _compute_pnt_du_end_date(self):
        for record in self:
            if record.state == "finished":
                record.pnt_du_end_date = fields.Date.today()

    @api.depends("pnt_single_document_type", "pnt_agreement_id", "pnt_holder_id")
    def _compute_pnt_partner_pickup_domain_ids(self):
        for record in self:
            record.pnt_partner_pickup_domain_ids = False
            record.pnt_partner_delivery_domain_ids = False
            record._set_pnt_partner_pickup_delivery_domain_ids()

    def name_get(self):
        # res = super().name_get()
        if self._context.get('pnt_change_name'):
            res = []
            for record in self:
                name = record.name
                if record.pnt_vehicle_id and record.pnt_vehicle_id.license_plate:
                    name = name + " | " + record.pnt_vehicle_id.license_plate
                if record.pnt_transport_id:
                    name = name + " | " + record.pnt_transport_id.display_name
                if record.pnt_partner_pickup_id:
                    name = name + " | " + record.pnt_partner_pickup_id.display_name
                res.append((record.id, name))
            return res
        return super().name_get()
    @api.depends("state")
    def _compute_pnt_scales_domain_ids(self):
        for record in self:
            record.pnt_scales_domain_ids = self.env.user.pnt_scales_ids

    @api.depends(
        "pnt_single_document_type",
        "pnt_vehicle_id",
        "pnt_vehicle_category_id",
    )
    def _compute_pnt_show_vehicle(self):
        for record in self:
            record.pnt_show_vehicle = False
            record.pnt_show_vehicle_aux = False
            if record.pnt_single_document_type == "output":
                if record.pnt_vehicle_category_id.id == 12:
                    record.pnt_show_vehicle_aux = True
                else:
                    record.pnt_show_vehicle = True
            else:
                if record.pnt_vehicle_id:
                    record.pnt_show_vehicle = True

    @api.depends(
        "pnt_single_document_issue_project_ids",
        "pnt_single_document_issue_project_ids.stage_id",
    )
    def _compute_pnt_admitted(self):
        # Omitimos la dependencia is_closed, no queremos que se revisen si en un futuro
        # se cambia la condición de cerrada (is_closed).
        for du in self:
            if du.pnt_force_admitted or all(
                x.stage_id.is_closed for x in du.pnt_single_document_issue_project_ids
            ):
                du.pnt_admitted = True
                continue
            du.pnt_admitted = False

    @api.depends("pnt_single_document_line_ids.pnt_price_subtotal")
    def compute_pnt_amount_total_sale_purchase(self):
        for record in self:
            sales = 0.0
            purchases = 0.0
            for line in record.pnt_single_document_line_ids:
                if line.pnt_monetary_waste == "inbound":
                    sales += line.pnt_price_subtotal
                elif line.pnt_monetary_waste == "outbound":
                    purchases += line.pnt_price_subtotal
            record.pnt_amount_total_sale = sales
            record.pnt_amount_total_purchase = purchases

    @api.depends("pnt_single_document_type")
    def compute_pnt_create_service(self):
        for record in self:
            if record.state == "newdu":
                result = None
                if (
                    record.pnt_single_document_type
                    and record.pnt_single_document_type
                    in (
                        "portal",
                        "toplant",
                    )
                ):
                    result = "no"
                elif (
                    record.pnt_single_document_type
                    and record.pnt_single_document_type
                    in ("pickup", "output", "internal", "marpol")
                ):
                    result = "yes"
                record.pnt_create_service = result

    @api.depends("pnt_single_document_line_ids.pnt_product_id")
    def compute_pnt_there_is_waste(self):
        for record in self:
            is_waste = False
            for rec in record.pnt_single_document_line_ids:
                if rec.pnt_is_waste:
                    is_waste = True
            record.pnt_there_is_waste = is_waste

    @api.depends("pnt_single_document_type", "state")
    def compute_pnt_partner_pickup_id_locked(self):
        for record in self:
            if record.state in ("newdu", "dispached"):
                record.pnt_partner_pickup_id_locked = False
            elif record.state == "plant":
                if record.pnt_single_document_type == "metal":
                    record.pnt_partner_pickup_id_locked = False
                else:
                    record.pnt_partner_pickup_id_locked = True
            else:
                record.pnt_partner_pickup_id_locked = True

    @api.depends(
        "pnt_single_document_type", "state", "pnt_scales_id.pnt_company_default"
    )
    def _compute_load_du_visible(self):
        load_du_visible = self.pnt_search_load_du_visible()
        for record in self:
            record.pnt_load_du_visible = record.id in load_du_visible.ids

    @api.model
    def pnt_search_load_du_visible(self):
        res = self.browse().exists()
        domain = [
            ("pnt_single_document_type", "=", "portal"),
            ("state", "in", ["dispached"]),
        ]
        res |= self.search(domain)
        domain = [
            ("pnt_single_document_type", "=", "toplant"),
            ("pnt_scales_id.pnt_company_default", "=", True),
            ("state", "in", ["dispached"]),
        ]
        res |= self.search(domain)
        return res

    def confirm_du_metal(self):
        # Pasar estado DU a 'en planta'
        if self.state == "dispached":
            self.state = "plant"
            # Pasar a estado RECEPCIONADO/ADMISION
            self.action_received()
        else:
            raise UserError(
                _("Este DU ya se ha procesado. Presione el boton CARGAR OTRO DU")
            )

    def new_du_metal(self):
        # Forzar nuevo registro de DU
        view_id = self.env.ref("custom_pnt.view_form_pnt_load_du").id
        return {
            "type": "ir.actions.act_window",
            "name": "Load DU",
            "view_type": "form",
            "view_mode": "form",
            "view_id": view_id,
            "res_model": "pnt.load.du",
            "target": "new",
        }

    def get_partner_waste_codes(self, typeinfo, typepartner, end_mgm_id=0, ler=False):
        # typeinfo -> nima | rpgr | srap
        # typepartner -> agent | producer | transport | end_mgm
        # end_mgm_id -> solo se utiliza cuando typepartner es end_mgm
        # Si tiene valor, debe filtrar typeinfo por LER

        result = ""
        partner = None
        if typepartner == "agent":
            if self.pnt_operator_id:
                partner = self.pnt_operator_id
            else:
                partner = self.company_id.partner_id
        elif typepartner == "producer":
            partner = self.pnt_partner_pickup_id
        elif typepartner == "transport":
            if self.pnt_carrier_id:
                partner = self.pnt_carrier_id
            else:
                partner = self.pnt_transport_id
        elif typepartner == "end_mgm":
            partner = self.env["res.partner"].search([("id", "=", end_mgm_id)], limit=1)
        if partner:
            agent = []
            cod_aut = None
            if not partner.pnt_waste_nima_code_ids and partner.parent_id:
                partner = partner.parent_id
            if ler:
                for lineler in ler:
                    cod_aut = partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                            lambda
                                x: x.pnt_authorization_code_type == typepartner and
                                   lineler.pnt_waste_ler_id.id in x.pnt_product_tmpl_waste_ler_ids.ids)
                    if cod_aut:
                        agent.append(cod_aut)
                if not agent and typeinfo == "nima":
                    agent = partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                        lambda x: x.pnt_authorization_code_type == typepartner
                    )
            else:
                agent = partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == typepartner
                )
            if agent:
                current_nima = False
                current_rpgr = False
                current_srap = False
                for ag in agent:
                    for ag2 in ag:
                        if not result:
                            if typeinfo == "nima":
                                current_nima = ag2.pnt_nima_code_id.name
                                result = ag2.pnt_nima_code_id.name
                            elif typeinfo == "rpgr":
                                current_rpgr = ag2.display_name
                                result = ag2.display_name
                            elif typeinfo == "srap":
                                current_srap = ag2.pnt_operator_type_id.pnt_type_operator
                                result = ag2.pnt_operator_type_id.pnt_type_operator
                        else:
                            if typeinfo == "nima":
                                if ag2.pnt_nima_code_id.name != current_nima:
                                    result += ", " + str(ag2.pnt_nima_code_id.name)
                                current_nima = ag2.pnt_nima_code_id.name
                            elif typeinfo == "rpgr":
                                if ag2.display_name != current_rpgr:
                                    result += ", " + str(ag2.display_name)
                                current_rpgr = ag2.display_name
                            elif typeinfo == "srap":
                                if ag2.pnt_operator_type_id.pnt_type_operator != current_srap:
                                    result += (", " +
                                            str(ag2.pnt_operator_type_id.pnt_type_operator))
                                current_srap = ag2.pnt_operator_type_id.pnt_type_operator
        return result

    def hi_ha_compres(self):
        for du in self:
            if du.pnt_purchase_order_ids:
                return True
            else:
                return False

    def hi_ha_vendes(self):
        for du in self:
            if du.pnt_sale_order_ids:
                return True
            else:
                return False

    def create_invoice(self):
        for du in self:
            # Compres
            active_invoices = []
            total = 0
            for purchase in du.pnt_purchase_order_ids:
                purchase.action_create_invoice()
                for order in purchase:
                    active_invoice_ids = order.invoice_ids.id
                    invoices = order.invoice_ids
                    for invoice in invoices:
                        active_invoices.append(invoice.id)
                        invoice.action_post()
                        total += invoice.amount_total

            # Vendes
            active_invoices_sale = []
            total = 0
            for sale in du.pnt_sale_order_ids:
                sale._create_invoices()
                for order in sale:
                    active_invoice_ids = order.invoice_ids.id
                    invoices = order.invoice_ids
                    for invoice in invoices:
                        active_invoices_sale.append(invoice.id)
                        invoice.action_post()
                        total += invoice.amount_total

    def create_returns(self):
        for du in self:
            # Comprobar si los documentos generados estan facturados
            total_invoices = 0
            for purchase in du.pnt_purchase_order_ids:
                total_invoices += purchase.invoice_count
            for sale in du.pnt_sale_order_ids:
                total_invoices += sale.invoice_count

            if total_invoices > 0:
                du.pnt_has_invoice = True
                view_id = self.env.ref("custom_pnt.view_form_pnt_return_du").id
                return {
                    "type": "ir.actions.act_window",
                    "name": "Aviso proceso devolución",
                    "view_type": "form",
                    "view_mode": "form",
                    "view_id": view_id,
                    "res_model": "pnt.return.du",
                    "context": {
                        "default_pnt_single_document_id": du.id,
                        "default_pnt_has_invoice": True,
                    },
                    "target": "new",
                }
            else:
                du.pnt_has_invoice = False
                view_id = self.env.ref("custom_pnt.view_form_pnt_return_du").id
                return {
                    "type": "ir.actions.act_window",
                    "name": "Aviso proceso devolución",
                    "view_type": "form",
                    "view_mode": "form",
                    "view_id": view_id,
                    "res_model": "pnt.return.du",
                    "context": {
                        "default_pnt_single_document_id": du.id,
                        "default_pnt_has_invoice": False,
                    },
                    "target": "new",
                }

    @api.depends("pnt_single_document_type", "pnt_agreement_id")
    def _get_pnt_product_product_metal_scale_ids(self):
        for record in self:
            if (
                record.pnt_single_document_type in ("metal", "portal", "toplant")
                and record.pnt_agreement_id
            ):
                record.write(
                    {
                        "pnt_agreement_id": record.pnt_agreement_id.id,
                        "pnt_single_document_type": record.pnt_single_document_type,
                    }
                )
                prod_list = []
                product_ids = []
                for prod in record.pnt_agreement_id.pnt_agreement_line_ids:
                    if (
                        prod.pnt_product_id.pnt_is_waste
                        and prod.pnt_product_id.id not in product_ids
                    ):
                        dict_line = {
                            "pnt_single_document_id": record.id,
                            "pnt_product_id": prod.pnt_product_id.id,
                        }
                        product_ids.append(prod.pnt_product_id.id)
                        prod_list.append((0, 0, dict_line))
                record.pnt_product_product_metal_scale_ids = prod_list

    @api.depends("pnt_there_is_waste")
    def compute_pnt_producer_id(self):
        for record in self:
            if record.pnt_there_is_waste and record.pnt_partner_pickup_id:
                record.pnt_producer_id = (
                    record.pnt_partner_pickup_id.commercial_partner_id
                )
            else:
                record.pnt_producer_id = None

    @api.depends("pnt_single_document_type", "state")
    def _compute_pnt_scale_id(self):
        for record in self:
            if record.state in ("plant", "newdu"):
                record.pnt_scales_id = False
                if self.env.user.pnt_scales_id:
                    record.pnt_scales_id = self.env.user.pnt_scales_id

    @api.onchange("pnt_vehicle_aux_id")
    def onchange_pnt_vehicle_aux_id(self):
        self.pnt_vehicle_id = self.pnt_vehicle_aux_id

    @api.onchange("pnt_vehicle_category_id")
    def onchange_pnt_vehicle_category_id(self):
        self.pnt_vehicle_id = None
        self.pnt_vehicle_aux_id = None
        self.pnt_transport_id = None
        self.pnt_carrier_id = None

    @api.onchange("pnt_carrier_id")
    def onchange_pnt_carrier_id(self):
        self.pnt_vehicle_id = None
        self.pnt_vehicle_aux_id = None
        if (
            not self.pnt_carrier_id
            or self.pnt_carrier_id
            and self.pnt_transport_id
            and self.pnt_transport_id.parent_id
        ):
            if self.pnt_carrier_id != self.pnt_transport_id.parent_id:
                self.pnt_transport_id = None

    @api.onchange("pnt_transport_id")
    def onchange_pnt_transport_id(self):
        self.pnt_vehicle_id = False
        if not self.pnt_vehicle_category_id or not self.pnt_transport_id:
            return
        domain = [("pnt_category_ids", "in", self.pnt_vehicle_category_id.ids)]
        if self.pnt_transport_id:
            domain.append(("driver_id", "=", self.pnt_transport_id.id))
        if self.pnt_carrier_id:
            domain.append(("pnt_carrier_id", "=", self.pnt_carrier_id.id))
        vehicle = self.env["fleet.vehicle"].search(domain, limit=1)
        if vehicle:
            self.pnt_vehicle_id = vehicle
        elif self.pnt_domain_vehicle_ids:
            self.pnt_vehicle_id = self.pnt_domain_vehicle_ids[:1]

    @api.depends("pnt_vehicle_category_id")
    def _compute_pnt_domain_vehicle_ids(self):
        self.pnt_domain_vehicle_ids = False
        for record in self:
            if not record.pnt_vehicle_category_id:
                continue
            domain = [("pnt_category_ids", "in", record.pnt_vehicle_category_id.ids)]
            record.pnt_domain_vehicle_ids = self.env["fleet.vehicle"].search(domain).ids

    @api.depends("pnt_transport_id")
    def _compute_pnt_carrier_id(self):
        for record in self:
            if (
                not record.pnt_carrier_id
                and record.pnt_transport_id
                and record.pnt_transport_id.parent_id
            ):
                record.pnt_carrier_id = record.pnt_transport_id.parent_id

    @api.depends("pnt_vehicle_category_id", "pnt_carrier_id")
    def _compute_pnt_domain_transport_ids(self):
        self.pnt_domain_transport_ids = False
        for record in self:
            if not record.pnt_vehicle_category_id:
                continue
            if not record.pnt_carrier_id:
                record.pnt_domain_transport_ids = (
                    self.env["res.partner"]
                    .search(
                        [
                            ("pnt_is_driver", "=", True),
                            ("company_id", "in", [False, record.company_id.id]),
                        ]
                    )
                    .ids
                )
                continue
            domain = [
                ("pnt_carrier_id", "=", record.pnt_carrier_id.id),
            ]
            record.pnt_domain_transport_ids = (
                self.env["fleet.vehicle"].search(domain).driver_id.ids
            )

    @api.onchange("pnt_partner_pickup_id", "pnt_holder_id")
    def onchange_pnt_partner_pickup_id_warning(self):
        partner_eval = ""
        if self.pnt_single_document_type in ("portal", "metal"):
            partner_eval = self.pnt_partner_pickup_id
        else:
            partner_eval = self.pnt_holder_id
        if not partner_eval:
            return
        warning = {}
        title = False
        message = False
        partner = partner_eval
        # If partner has no warning, check its company
        if partner.du_warn == "no-message" and partner.parent_id:
            partner = partner.parent_id

        if partner.du_warn and partner.du_warn != "no-message":
            # Block if partner only has warning but parent company is blocked
            if (
                partner.du_warn != "block"
                and partner.parent_id
                and partner.parent_id.du_warn == "block"
            ):
                partner = partner.parent_id
            title = _("Warning for %s") % partner.name
            message = partner.du_warn_msg
            warning = {
                "title": title,
                "message": message,
            }
            if partner.du_warn == "block":
                if self.pnt_single_document_type == "portal":
                    self.update(
                        {
                            "pnt_partner_pickup_id": False,
                        }
                    )
                else:
                    self.update(
                        {
                            "pnt_holder_id": False,
                        }
                    )
                return {"warning": warning}

        if warning:
            return {"warning": warning}

    @api.depends("pnt_single_document_type", "pnt_create_service", "state")
    def _compute_pnt_show_create_service(self):
        for rec in self:
            result = False
            if rec.state not in ["dispached"]:
                result = False
            else:
                if rec.pnt_single_document_type in ["portal", "toplant"]:
                    result = False
                elif rec.pnt_single_document_type in ["pickup", "marpol"]:
                    result = True
                elif rec.pnt_single_document_type in ["output", "others", "internal"]:
                    if rec.pnt_create_service == "yes":
                        result = True
            rec.pnt_show_create_service = result

    @api.depends("pnt_agreement_id", "pnt_holder_id", "pnt_partner_pickup_id")
    def _compute_pnt_show_du_lines(self):
        for rec in self:
            result = False
            if rec.pnt_single_document_type == "internal":
                if rec.pnt_holder_id and rec.pnt_partner_pickup_id:
                    result = True
            else:
                if (
                    rec.pnt_holder_id
                    and rec.pnt_partner_pickup_id
                    and rec.pnt_agreement_id
                ):
                    result = True
            rec.pnt_show_du_lines = result

    def _prepare_done_values(self):
        return {
            "state": "done",
        }

    def action_done(self):
        if self._action_confirm():
            self.write(self._prepare_done_values())

    def action_done_portal(self):
        self.write(self._prepare_done_values())
        self.action_inplant()

    def test_scale(self):
        if not self.env.company.pnt_scale_host:
            raise UserError(
                _("Debe indicar una dirección IP para la báscula en configuración")
            )
        if not self.env.company.pnt_scale_port:
            raise UserError(
                _("Debe indicar un puerto para la báscula en configuración")
            )
        host = self.env.company.pnt_scale_host
        port = self.env.company.pnt_scale_port
        try:
            telnet_client = telnetlib.Telnet(host, port)
            pes = None
            telnet_client.write(b"$")
            pes = telnet_client.read_some()
            pesnumeric = int("".join(filter(str.isdigit, str(pes).split("x01", 1)[-1])))
            if pes:
                raise UserError(_("El peso es: " + str(pesnumeric) + "kg"))
            else:
                raise UserError(
                    _("No puede leerse el peso. Revise si está conectada la báscula")
                )
            telnet_client.write(b"exit")
        except socket.error as msg:
            raise UserError(
                _(
                    "No puede leerse el peso. Revise si la báscula está conectada - "
                    + str(msg)
                )
            )

    def _action_confirm(self):
        """On SO confirmation, some lines should generate a task or a project."""
        # result = super()._action_confirm()
        if len(self.company_id) == 1:
            # All orders are in the same company
            return (
                self.sudo()
                .with_company(self.company_id)
                ._timesheet_service_generation()
            )
        else:
            # Orders from different companies are confirmed together
            for du in self:
                return (
                    du.sudo()
                    .with_company(du.company_id)
                    ._timesheet_service_generation()
                )
        # return result

    def _timesheet_service_generation(self):
        # task_global_project: create task in global project
        for du in self:
            if not du.task_id and du.project_id:
                new_task = du._timesheet_create_task(project=du.project_id.id)
                return new_task
            else:
                self.write(self._prepare_done_values())

    def _timesheet_create_task(self, project):
        values = self._timesheet_create_task_prepare_values(project)
        task = self.env["project.task"].sudo().create(values)
        list_lines = []
        for line in self.pnt_single_document_line_ids:
            if (
                line.pnt_product_id.pnt_is_waste
                or line.pnt_product_id.pnt_is_container
                or line.pnt_product_id.pnt_container_movement_type
            ):
                container = None
                if line.pnt_container_movement_id:
                    if line.pnt_container_movement_id.pnt_container_delivery_id:
                        container = (
                            line.pnt_container_movement_id.pnt_container_delivery_id.id
                        )
                    elif line.pnt_container_movement_id.pnt_container_removal_id:
                        container = (
                            line.pnt_container_movement_id.pnt_container_removal_id.id
                        )
                else:
                    if line.pnt_container_id:
                        container = line.pnt_container_id.id
                dict_line = {
                    "pnt_task_id": task.id,
                    "pnt_product_id": line.pnt_product_id.id,
                    "pnt_container_id": container,
                }
                list_lines.append((0, 0, dict_line))
        task.write({"pnt_product_container_ids": list_lines})
        self.write({"task_id": task.id})
        # post message on task
        task_msg = _(
            "This task has been created from: <a href=# data-oe-model=pnt.single.document data-oe-id=%d>%s</a> (%s)"
        ) % (
            self.id,
            self.pnt_holder_id.display_name,
            self.pnt_partner_pickup_id.display_name,
        )
        task.message_post(body=task_msg)
        return task

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        currentproject = self.env["project.project"].search([("id", "=", project)])
        title = self.name + " | " + self.pnt_partner_pickup_id.display_name
        product_res_ids = [
            p.id for p in self.pnt_single_document_line_ids.pnt_product_id
        ]
        if self.pnt_pickup_date_type == "date":
            date_task = self.pnt_pickup_date
        else:
            sometime = time(7, 00)
            date_task = datetime.combine(date.today() + timedelta(days=1), sometime)
        return {
            "name": title,
            "partner_id": self.pnt_partner_pickup_id.id,
            "email_from": self.pnt_partner_pickup_id.email,
            "project_id": currentproject.id,
            "pnt_single_document_id": self.id,
            "company_id": currentproject.company_id.id,
            "pnt_carrier_id": self.pnt_carrier_id.id,
            "pnt_transport_id": self.pnt_transport_id.id,
            "pnt_vehicle_category_id": self.pnt_vehicle_category_id.id,
            "pnt_vehicle_id": self.pnt_vehicle_id.id,
            "date_deadline": date_task,
            "pnt_expected_pickup_date": date_task,
            "pnt_product_ids": product_res_ids,
            "user_id": False,  # force non assigned task, as created as sudo()
            "pnt_logistic_route_id": self.pnt_logistic_route_id.id,
        }

    def _stock_picking_create_prepare_values(
        self, picking_type, location_id, location_dest, typemove, partner_type
    ):
        self.ensure_one()
        list_lines = []
        for line in self.pnt_single_document_line_ids.filtered(
            lambda r: not r.pnt_product_id.type == "service"
        ):
            if (
                not line.pnt_product_id.pnt_is_container
                and picking_type.id
                == self.pnt_scales_id.pnt_stock_picking_type_purchase_du_id.id
                and typemove == "inbound"
            ):
                if line.pnt_product_id.uom_id.category_id.name == "Peso":
                    qtyline = line.pnt_product_uom_qty
                    price_unit = line.pnt_price_unit
                    # price_unit = line.pnt_product_uom._compute_price(line.pnt_price_unit,line.pnt_product_economic_uom)
                    if line.pnt_product_economic_uom == line.pnt_product_uom:
                        price_unit = line.pnt_price_unit
                    else:
                        if (
                            line.pnt_product_uom.uom_type == "reference"
                            and line.pnt_product_economic_uom.uom_type == "bigger"
                        ):
                            price_unit = (
                                line.pnt_price_unit
                                / line.pnt_product_economic_uom.factor_inv
                            )
                        elif (
                            line.pnt_product_uom.uom_type == "reference"
                            and line.pnt_product_economic_uom.uom_type == "smaller"
                        ):
                            price_unit = (
                                line.pnt_price_unit
                                * line.pnt_product_economic_uom.factor
                            )
                else:
                    qtyline = line.pnt_container_qty
                    price_unit = line.pnt_price_unit
                dict_line = {
                    "name": line.pnt_product_id.name,
                    "product_id": line.pnt_product_id.id,
                    "product_uom_qty": qtyline,
                    "quantity_done": qtyline,
                    "price_unit": price_unit,
                    "product_uom": line.pnt_product_uom.id,
                    "pnt_single_document_line_id": line.id,
                }
                list_lines.append((0, 0, dict_line))
            elif (
                not line.pnt_product_id.pnt_is_container
                and picking_type.id
                == self.pnt_scales_id.pnt_stock_picking_type_sale_du_id.id
                and typemove == "outbound"
            ):
                if line.pnt_product_id.uom_id.category_id.name == "Peso":
                    qtyline = line.pnt_product_uom_qty
                    price_unit = line.pnt_price_unit
                    # price_unit = line.pnt_product_uom._compute_price(line.pnt_price_unit,line.pnt_product_economic_uom)
                    if line.pnt_product_economic_uom == line.pnt_product_uom:
                        price_unit = line.pnt_price_unit
                    else:
                        if (
                            line.pnt_product_uom.uom_type == "reference"
                            and line.pnt_product_economic_uom.uom_type == "bigger"
                        ):
                            price_unit = (
                                line.pnt_price_unit
                                / line.pnt_product_economic_uom.factor_inv
                            )
                        elif (
                            line.pnt_product_uom.uom_type == "reference"
                            and line.pnt_product_economic_uom.uom_type == "smaller"
                        ):
                            price_unit = (
                                line.pnt_price_unit
                                * line.pnt_product_economic_uom.factor
                            )
                else:
                    qtyline = line.pnt_container_qty
                    price_unit = line.pnt_price_unit
                dict_line = {
                    "name": line.pnt_product_id.name,
                    "product_id": line.pnt_product_id.id,
                    "product_uom_qty": qtyline,
                    "quantity_done": qtyline,
                    "price_unit": price_unit * (-1),
                    "product_uom": line.pnt_product_uom.id,
                    "pnt_single_document_line_id": line.id,
                }

                list_lines.append((0, 0, dict_line))
            elif not line.pnt_product_id.pnt_is_container and typemove == "internal":
                if line.pnt_product_id.uom_id.category_id.name == "Peso":
                    qtyline = line.pnt_product_uom_qty
                    price_unit = line.pnt_price_unit
                    # price_unit = line.pnt_product_uom._compute_price(line.pnt_price_unit,line.pnt_product_economic_uom)
                    if line.pnt_product_economic_uom == line.pnt_product_uom:
                        price_unit = line.pnt_price_unit
                    else:
                        if (
                            line.pnt_product_uom.uom_type == "reference"
                            and line.pnt_product_economic_uom.uom_type == "bigger"
                        ):
                            price_unit = (
                                line.pnt_price_unit
                                / line.pnt_product_economic_uom.factor_inv
                            )
                        elif (
                            line.pnt_product_uom.uom_type == "reference"
                            and line.pnt_product_economic_uom.uom_type == "smaller"
                        ):
                            price_unit = (
                                line.pnt_price_unit
                                * line.pnt_product_economic_uom.factor
                            )
                else:
                    qtyline = line.pnt_container_qty
                    price_unit = line.pnt_price_unit
                dict_line = {
                    "name": line.pnt_product_id.name,
                    "product_id": line.pnt_product_id.id,
                    "product_uom_qty": qtyline,
                    "quantity_done": qtyline,
                    "price_unit": price_unit * (-1),
                    "product_uom": line.pnt_product_uom.id,
                    "pnt_single_document_line_id": line.id,
                }
                list_lines.append((0, 0, dict_line))
            elif line.pnt_product_id.pnt_is_container and typemove in (
                "container",
                "internal",
            ):
                qtyline = line.pnt_container_qty
                dict_line = {
                    "name": line.pnt_product_id.name,
                    "product_id": line.pnt_product_id.id,
                    "product_uom_qty": qtyline,
                    "quantity_done": qtyline,
                    "price_unit": line.pnt_price_unit * (-1),
                    "product_uom": line.pnt_product_uom.id,
                    "pnt_single_document_line_id": line.id,
                }
                list_lines.append((0, 0, dict_line))
        # Añadir las envases vinculados a las líneas
        for lineenv in self.pnt_single_document_line_ids:
            if (
                lineenv.pnt_container_id
                and lineenv.pnt_container_qty
                and lineenv.pnt_container_id.type == "product"
                and picking_type.id
                == self.pnt_scales_id.pnt_stock_picking_type_purchase_du_id.id
                and typemove == "inbound"
            ):
                dict_line = {
                    "name": lineenv.pnt_container_id.name,
                    "product_id": lineenv.pnt_container_id.id,
                    "product_uom_qty": lineenv.pnt_container_qty,
                    "quantity_done": lineenv.pnt_container_qty,
                    "price_unit": lineenv.pnt_price_unit,
                    "product_uom": lineenv.pnt_container_id.uom_id,
                    "pnt_single_document_line_id": lineenv.id,
                }
                list_lines.append((0, 0, dict_line))
            elif (
                lineenv.pnt_container_id
                and lineenv.pnt_container_qty
                and lineenv.pnt_container_id.type == "product"
                and picking_type.id
                == self.pnt_scales_id.pnt_stock_picking_type_sale_du_id.id
                and typemove == "outbound"
            ):
                dict_line = {
                    "name": lineenv.pnt_container_id.name,
                    "product_id": lineenv.pnt_container_id.id,
                    "product_uom_qty": lineenv.pnt_container_qty,
                    "quantity_done": lineenv.pnt_container_qty,
                    "price_unit": lineenv.pnt_price_unit * (-1),
                    "product_uom": lineenv.pnt_container_id.uom_id,
                    "pnt_single_document_line_id": lineenv.id,
                }
                list_lines.append((0, 0, dict_line))
        if list_lines:
            if partner_type == "delivery":
                partner = self.pnt_partner_delivery_id.id
            else:
                if self.pnt_single_document_type in ("output", "internal"):
                    partner = self.pnt_holder_id.id
                else:
                    partner = self.pnt_partner_pickup_id.id
            return {
                "partner_id": partner,
                "company_id": self.company_id.id,
                "scheduled_date": self.pnt_pickup_date,
                "picking_type_id": picking_type.id,
                "location_id": location_id.id,
                "location_dest_id": location_dest.id,
                "pnt_single_document_id": self.id,
                "move_ids_without_package": list_lines,
            }
        else:
            return {}

    def _stock_picking_create(
        self, picking_type, location_id, location_dest, typemov, partner_type
    ):
        values = self._stock_picking_create_prepare_values(
            picking_type, location_id, location_dest, typemov, partner_type
        )
        if values:
            sp = self.env["stock.picking"].sudo().create(values)
            self.write(
                {
                    "pnt_stock_picking_ids": [(4, sp.id)],
                }
            )
            return sp
        else:
            return False

    def _get_single_document_reference(self):
        self.ensure_one()
        reference = ""
        contract = self.pnt_agreement_reference or ""
        ref = self.pnt_order_reference or ""
        if contract and ref:
            reference = "Contr: %s // Ref: %s" % (contract, ref)
        elif contract:
            reference = "Contr: %s" % contract
        elif ref:
            reference = "Ref: %s" % ref
        return reference

    def _sale_order_create_prepare_values(self, orderType, partner, factor):
        self.ensure_one()
        list_lines = []
        pos_fiscal = None
        if partner.property_account_position_id:
            pos_fiscal = partner.property_account_position_id.id
        # Comprobar si debe agrupar o no las lineas
        if self.pnt_group_lines:
            product_groups = self.env["pnt.single.document.line"].read_group(
                domain=[
                    ("pnt_single_document_id", "=", self.id),
                    ("pnt_monetary_waste", "=", "inbound"),
                ],
                fields=[
                    "pnt_product_id",
                    "pnt_container_id",
                ],
                groupby=[
                    "pnt_product_id",
                    "pnt_container_id",
                ],
                lazy=False,
            )
            for group in product_groups:
                peso_agrupado = 0
                lines_du = []
                envas = group["pnt_container_id"]
                if envas:
                    lines_filtered = self.pnt_single_document_line_ids.filtered(
                        lambda ml: ml.pnt_product_id.id == group["pnt_product_id"][0]
                        and ml.pnt_container_id.id == group["pnt_container_id"][0]
                        and ml.pnt_monetary_waste == "inbound"
                    )
                else:
                    lines_filtered = self.pnt_single_document_line_ids.filtered(
                        lambda ml: ml.pnt_product_id.id == group["pnt_product_id"][0]
                        and not ml.pnt_container_id.id
                        and ml.pnt_monetary_waste == "inbound"
                    )
                if len(lines_filtered) > 1:
                    for line in lines_filtered:
                        peso_agrupado += line.pnt_product_economic_uom_qty * factor
                        lines_du.append((4, line.id))
                else:
                    if len(lines_filtered) == 1:
                        peso_agrupado = (
                            lines_filtered[0].pnt_product_economic_uom_qty * factor
                        )
                        lines_du.append((4, lines_filtered[0].id))
                productline = lines_filtered[0].pnt_product_id.id
                descripline = lines_filtered[0].pnt_product_id.name
                if (
                    lines_filtered[0].pnt_product_economic_uom.category_id
                    != lines_filtered[0].pnt_product_id.uom_id.category_id
                ):
                    if lines_filtered[0].pnt_container_qty == 0.0:
                        raise UserError(
                            _(
                                "Si la unidad economica son UNIDADES debe indicar las UNIDADES - "
                                + lines_filtered[0].pnt_product_id.display_name
                            )
                        )
                    if not lines_filtered[0].pnt_container_id:
                        raise UserError(
                            _(
                                "Si la unidad economica son UNIDADES debe indicar un contenedor - "
                                + lines_filtered[0].pnt_product_id.display_name
                            )
                        )
                    productline = lines_filtered[0].pnt_container_id.id
                    descripline = (
                        lines_filtered[0].pnt_container_id.name
                        + " - "
                        + lines_filtered[0].pnt_product_id.name
                    )
                # if lines_filtered[0].pnt_customer_name:
                #     product_name = lines_filtered[0].pnt_customer_name
                # else:
                #     product_name = lines_filtered[0].pnt_product_id.display_name
                if lines_filtered[0].pnt_description_line:
                    product_name = lines_filtered[0].pnt_description_line
                else:
                    product_name = lines_filtered[0].pnt_product_id.display_name
                dict_line = {
                    "name":  product_name,
                    "product_id": productline,
                    "product_uom_qty": peso_agrupado,
                    "qty_to_invoice": peso_agrupado,
                    "pnt_m3": lines_filtered[0].pnt_m3,
                    "product_uom": lines_filtered[0].pnt_product_economic_uom.id,
                    "price_unit": lines_filtered[0].pnt_price_unit,
                    "pnt_single_document_line_id": lines_filtered[0].id,
                    "pnt_single_document_line_ids": lines_du,
                }
                list_lines.append((0, 0, dict_line))
        else:
            for line in self.pnt_single_document_line_ids:
                if line.pnt_monetary_waste == "inbound":
                    # Preprar els grups
                    productline = line.pnt_product_id.id
                    descripline = line.pnt_product_id.name
                    if (
                        line.pnt_product_economic_uom.category_id
                        != line.pnt_product_id.uom_id.category_id
                    ):
                        if line.pnt_container_qty == 0.0:
                            raise UserError(
                                _(
                                    "Si la unidad economica son UNIDADES debe indicar las UNIDADES - "
                                    + line.pnt_product_id.display_name
                                )
                            )
                        if not line.pnt_container_id:
                            raise UserError(
                                _(
                                    "Si la unidad economica son UNIDADES debe indicar un contenedor - "
                                    + line.pnt_product_id.display_name
                                )
                            )
                        productline = line.pnt_container_id.id
                        descripline = (
                            line.pnt_container_id.name
                            + " - "
                            + line.pnt_product_id.name
                        )
                    lines_du = []
                    lines_du.append((4, line.id))
                    # if line.pnt_customer_name:
                    #     product_name = line.pnt_customer_name
                    # else:
                    #     product_name = line.pnt_product_id.display_name
                    if line.pnt_description_line:
                        product_name = line.pnt_description_line
                    else:
                        product_name = line.pnt_product_id.display_name
                    dict_line = {
                        "name": product_name,
                        "product_id": productline,
                        "product_uom_qty": line.pnt_product_economic_uom_qty * factor,
                        "qty_to_invoice": line.pnt_product_economic_uom_qty * factor,
                        "pnt_m3": line.pnt_m3,
                        "product_uom": line.pnt_product_economic_uom.id,
                        "price_unit": line.pnt_price_unit,
                        "pnt_single_document_line_id": line.id,
                        "pnt_single_document_line_ids": lines_du,
                    }
                    if line.pnt_product_id != productline and pos_fiscal:
                        taxes = line.pnt_product_id.taxes_id.filtered(
                            lambda t: t.company_id == self.company_id
                        )
                        tax_id = partner.property_account_position_id.map_tax(
                            taxes, line.pnt_product_id, self.pnt_partner_pickup_id
                        )
                        dict_line["tax_id"] = [(6, 0, tax_id.ids)]
                    list_lines.append((0, 0, dict_line))
        return {
            "pnt_agreement_id": self.pnt_agreement_id.id,
            "partner_id": partner.id,
            "fiscal_position_id": pos_fiscal,
            "company_id": self.company_id.id,
            "date_order": self.pnt_pickup_date,
            "type_id": orderType.id,
            "pnt_single_document_id": self.id,
            "order_line": list_lines,
            "partner_shipping_id": self.pnt_partner_pickup_id.id,
            "partner_invoice_id": self._get_partner_invoice_id(),
            "client_order_ref": self._get_single_document_reference(),
            "pnt_ship_scale_num": self.pnt_ship_scale_num,
            "pnt_control_sheet_ids": self.pnt_control_sheet_ids,
            "user_id": self.pnt_user_id.id,
            "payment_mode_id": self.pnt_customer_payment_mode_id.id,
            "payment_term_id": self.pnt_customer_payment_term_id.id,
        }

    def _get_partner_invoice_id(self):
        def _is_partner_shipping_contact_of_holder(holder, partner_shipping):
            if partner_shipping == holder or partner_shipping in holder.child_ids:
                return partner_shipping
            if partner_shipping.parent_id:
                return _is_partner_shipping_contact_of_holder(
                    holder, partner_shipping.parent_id
                )
            else:
                return holder

        partner = self.pnt_partner_pickup_id
        if self.pnt_holder_id:
            partner = _is_partner_shipping_contact_of_holder(
                self.pnt_holder_id, self.pnt_partner_pickup_id
            )
        if partner.type == "invoice":
            return partner.id
        parent = partner.parent_id
        if parent.type == "invoice":
            return parent.id
        invoice = parent.child_ids.filtered(lambda x: x.type == "invoice")[:1].id
        if invoice:
            return invoice
        while parent:
            if parent.type == "invoice":
                return parent.id
            invoice = parent.child_ids.filtered(lambda x: x.type == "invoice")[:1].id
            if invoice:
                return invoice
            parent = parent.parent_id
        return (
            partner.commercial_partner_id.child_ids.filtered(
                lambda x: x.type == "invoice"
            )[:1].id
            or partner.commercial_partner_id.id
        )

    def _sale_order_create(self, orderType, partner, factor):
        values = self._sale_order_create_prepare_values(orderType, partner, factor)
        so = self.env["sale.order"].sudo().create(values)
        # self.write({'pnt_purchase_order_id': pu.id})
        self.write(
            {
                "pnt_sale_order_ids": [(4, so.id)],
            }
        )
        return so

    # Inici creacio compres
    def _purchase_order_create_prepare_values(self, orderType, partner, factor):
        self.ensure_one()
        list_lines = []
        pos_fiscal = None
        if partner.property_account_position_id:
            pos_fiscal = partner.property_account_position_id.id
        for line in self.pnt_single_document_line_ids:
            if line.pnt_monetary_waste == "outbound":
                productline = line.pnt_product_id.id
                descripline = line.pnt_product_id.name
                if (
                    line.pnt_product_economic_uom.category_id
                    != line.pnt_product_id.uom_id.category_id
                ):
                    if line.pnt_container_qty == 0.0:
                        raise UserError(
                            _(
                                "Si la unidad economica son UNIDADES debe indicar las UNIDADES - "
                                + line.pnt_product_id.display_name
                            )
                        )
                    if not line.pnt_container_id:
                        raise UserError(
                            _(
                                "Si la unidad economica son UNIDADES debe indicar un contenedor - "
                                + line.pnt_product_id.display_name
                            )
                        )
                    productline = line.pnt_container_id.id
                    descripline = (
                        line.pnt_container_id.name + " - " + line.pnt_product_id.name
                    )
                # if line.pnt_supplier_name:
                #     product_name = line.pnt_supplier_name
                # else:
                #     product_name = line.pnt_product_id.display_name
                if line.pnt_description_line:
                    product_name = line.pnt_description_line
                else:
                    product_name = line.pnt_product_id.display_name
                dict_line = {
                    "name": product_name,
                    "product_id": productline,
                    "product_qty": line.pnt_product_economic_uom_qty * factor,
                    "qty_received": line.pnt_product_economic_uom_qty * factor,
                    "qty_to_invoice": line.pnt_product_economic_uom_qty * factor,
                    "pnt_m3": line.pnt_m3,
                    "product_uom": line.pnt_product_economic_uom.id,
                    "price_unit": line.pnt_price_unit,
                    "pnt_single_document_line_id": line.id,
                }
                list_lines.append((0, 0, dict_line))

        return {
            "partner_id": partner.id,
            "fiscal_position_id": pos_fiscal,
            "company_id": self.company_id.id,
            "date_order": self.pnt_pickup_date,
            "order_type": orderType.id,
            "pnt_single_document_id": self.id,
            "pnt_ship_scale_num": self.pnt_ship_scale_num,
            "pnt_control_sheet_ids": self.pnt_control_sheet_ids.ids,
            "order_line": list_lines,
            "user_id": self.pnt_user_id.id,
            "payment_mode_id": self.pnt_supplier_payment_mode_id.id,
            "payment_term_id": self.pnt_supplier_payment_term_id.id,
        }

    def _purchase_order_create(self, orderType, partner, factor):
        values = self._purchase_order_create_prepare_values(orderType, partner, factor)
        pu = self.env["purchase.order"].sudo().create(values)
        # self.write({'pnt_purchase_order_id': pu.id})
        self.write(
            {
                "pnt_purchase_order_ids": [(4, pu.id)],
            }
        )
        return pu

    # Fi creacio Compres

    @api.depends("task_id")
    def _compute_task_id(self):
        for du in self:
            if du.task_id:
                du.tasks_count = 1
                du.task_id = self.env["project.task"].search(
                    [("pnt_single_document_id", "=", du.id)], limit=1
                )
            else:
                du.tasks_count = 0
                du.task_id = None

    @api.depends("pnt_single_document_type", "pnt_holder_id", "pnt_partner_pickup_id")
    def _compute_pnt_du_partner_id(self):
        for du in self:
            if du.pnt_single_document_type in ("portal", "metal"):
                du.pnt_du_partner_id = du.pnt_partner_pickup_id
            else:
                du.pnt_du_partner_id = du.pnt_holder_id

    def action_view_task(self):
        self.ensure_one()
        form_view_id = self.env.ref("project.view_task_form2").id
        action = {"type": "ir.actions.act_window_close"}
        if self.task_id:  # redirect to task of the project (with kanban stage, ...)
            action = self.env["ir.actions.actions"]._for_xml_id(
                "project.action_view_task"
            )
            action["context"] = {}  # erase default context to avoid default filter
            action["views"] = [(form_view_id, "form")]
            action["res_id"] = self.task_id.id
        # filter on the task of the current SO
        action.setdefault("context", {})
        action["context"].update({"search_default_pnt_signle_document_id": self.id})
        return action

    def _compute_purchase_count(self):
        for rec in self:
            rec.purchase_count = len(rec.pnt_purchase_order_ids)

    def _compute_purchase_invoice_count(self):
        for rec in self:
            total_invoices = 0
            for purchase in rec.pnt_purchase_order_ids:
                total_invoices += purchase.invoice_count
            rec.purchase_invoice_count = total_invoices

    def _compute_sale_invoice_count(self):
        for rec in self:
            total_invoices = 0
            for sale in rec.pnt_sale_order_ids:
                total_invoices += sale.invoice_count
            rec.sale_invoice_count = total_invoices

    def _compute_sale_count(self):
        for rec in self:
            rec.sale_count = len(rec.pnt_sale_order_ids)

    def _compute_picking_count(self):
        for rec in self:
            # if rec.pnt_stock_picking_id:
            #     rec.picking_count = 1
            # else:
            #     rec.picking_count = 0
            rec.picking_count = len(rec.pnt_stock_picking_ids)

    def _compute_pnt_di_count(self):
        for rec in self:
            rec.pnt_di_count = len(rec.lines_with_di())

    def action_view_stock_picking(self):
        """This function returns an action that display existing pickings of
        given batch picking.
        """
        self.ensure_one()
        # pickings = self.mapped("picking_ids")
        # pickings = self.mapped(self.pnt_stock_picking_id.id)
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.action_picking_tree_all"
        )
        # action["domain"] = [("id", "=", self.pnt_stock_picking_id.id)]
        action["domain"] = [("pnt_single_document_id", "=", self.id)]
        return action

    def action_view_purchase_order(self):
        self.ensure_one()
        # pickings = self.mapped("picking_ids")
        # pickings = self.mapped(self.pnt_stock_picking_id.id)
        action = self.env.ref("custom_pnt.pnt_action_purchase_tree_all").read([])[0]
        # action["domain"] = [("id", "=", self.pnt_purchase_order_id.id)]
        action["domain"] = [("pnt_single_document_id", "=", self.id)]
        return action

    def action_view_sale_order(self):
        self.ensure_one()
        # pickings = self.mapped("picking_ids")
        # pickings = self.mapped(self.pnt_stock_picking_id.id)
        action = self.env.ref("custom_pnt.pnt_action_sale_tree_all").read([])[0]
        # action["domain"] = [("id", "=", self.pnt_purchase_order_id.id)]
        action["domain"] = [("pnt_single_document_id", "=", self.id)]
        return action

    def action_view_purchase_invoice(self):
        self.ensure_one()
        invoice_list = []
        for purchase in self.pnt_purchase_order_ids:
            purchase.sudo()._read(["invoice_ids"])
            invoices = purchase.invoice_ids
            for inv in invoices:
                invoice_list.append(inv.id)
        action = self.env.ref("custom_pnt.pnt_action_purchase_invoice_tree_all").read(
            []
        )[0]
        action["domain"] = [("id", "in", invoice_list)]
        return action

    def action_view_sale_invoice(self):
        self.ensure_one()
        invoice_list = []
        for sale in self.pnt_sale_order_ids:
            sale.sudo()._read(["invoice_ids"])
            invoices = sale.invoice_ids
            for inv in invoices:
                invoice_list.append(inv.id)
        action = self.env.ref("custom_pnt.pnt_action_purchase_invoice_tree_all").read(
            []
        )[0]
        action["domain"] = [("id", "in", invoice_list)]
        return action

    def action_view_di(self):
        self.ensure_one()
        di_list = (
            self.env["pnt.waste.transfer.document"]
            .search(
                [
                    (
                        "pnt_single_document_line_ids",
                        "in",
                        self.pnt_single_document_line_ids.ids,
                    )
                ]
            )
            .ids
        )
        if di_list:
            action = self.env.ref(
                "custom_pnt.action_waste_transfer_document_tree_pnt"
            ).read([])[0]
            action["domain"] = [("id", "in", di_list)]
            return action

    @api.depends("pnt_agreement_id")
    def compute_pnt_holder_id(self):
        for record in self:
            if record.pnt_agreement_id:
                record.pnt_customer_payment_mode_id = (
                    record.pnt_agreement_id.pnt_customer_payment_mode_id.id or False
                )
                record.pnt_customer_payment_term_id = (
                    record.pnt_agreement_id.pnt_customer_payment_term_id.id or False
                )
                record.pnt_supplier_payment_mode_id = (
                    record.pnt_agreement_id.pnt_supplier_payment_mode_id.id or False
                )
                record.pnt_supplier_payment_term_id = (
                    record.pnt_agreement_id.pnt_supplier_payment_term_id.id or False
                )

    def set_pnt_agreement_id(self):
        for record in self:
            if record.pnt_single_document_type == "portal":
                continue
            record.pnt_agreement_domain_ids = None
            record.pnt_agreement_count = 0
            record.pnt_agreement_id = None
            if record.pnt_single_document_type == "portal":
                if record.pnt_partner_pickup_id:
                    if record.pnt_partner_pickup_id.pnt_portal_agreement_type_id:
                        record.pnt_agreement_domain_ids = [
                            record.pnt_partner_pickup_id.pnt_portal_agreement_type_id.id
                        ]
                        record.pnt_agreement_id = (
                            record.pnt_partner_pickup_id.pnt_portal_agreement_type_id
                        )
                        record.pnt_agreement_count = 1
                    else:
                        record.pnt_agreement_domain_ids = [
                            self.env.company.pnt_single_document_default_portal_id.id
                        ]
                        record.pnt_agreement_id = (
                            self.env.company.pnt_single_document_default_portal_id
                        )
                        record.pnt_agreement_count = 1
                else:
                    record.pnt_agreement_domain_ids = [
                        self.env.company.pnt_single_document_default_portal_id.id
                    ]
                    record.pnt_agreement_id = (
                        self.env.company.pnt_single_document_default_portal_id
                    )
                    record.pnt_agreement_count = 1
            else:
                if record.pnt_holder_id and record.pnt_partner_pickup_id:
                    if record.pnt_single_document_type == "output":
                        agreement_ids = self.env["pnt.agreement.agreement"].search(
                            [
                                (
                                    "pnt_partner_pickup_id",
                                    "=",
                                    record.pnt_partner_pickup_id.id,
                                ),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "=", "manager"),
                                ("company_id", "=", self.env.company.id),
                            ],
                            order="name",
                        )
                    elif record.pnt_single_document_type == "marpol":
                        agreement_ids = self.env["pnt.agreement.agreement"].search(
                            [
                                (
                                    "pnt_partner_pickup_id",
                                    "=",
                                    record.pnt_partner_pickup_id.id,
                                ),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "=", "marpol"),
                                ("company_id", "=", self.env.company.id),
                            ],
                            order="name",
                        )
                    else:
                        agreement_ids = self.env["pnt.agreement.agreement"].search(
                            [
                                (
                                    "pnt_partner_pickup_id",
                                    "=",
                                    record.pnt_partner_pickup_id.id,
                                ),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "=", "others"),
                                ("company_id", "=", self.env.company.id),
                            ],
                            order="name",
                        )
                    if agreement_ids:
                        record.pnt_agreement_domain_ids = agreement_ids
                        record.pnt_agreement_count = len(agreement_ids)
                    if record.pnt_single_document_type == "output":
                        agreement_id = self.env["pnt.agreement.agreement"].search(
                            [
                                (
                                    "pnt_partner_pickup_id",
                                    "=",
                                    record.pnt_partner_pickup_id.id,
                                ),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "=", "manager"),
                                ("company_id", "=", self.env.company.id),
                            ],
                            order="name",
                            limit=1,
                        )
                    elif record.pnt_single_document_type == "marpol":
                        agreement_id = self.env["pnt.agreement.agreement"].search(
                            [
                                (
                                    "pnt_partner_pickup_id",
                                    "=",
                                    record.pnt_partner_pickup_id.id,
                                ),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "=", "marpol"),
                                ("company_id", "=", self.env.company.id),
                            ],
                            order="name",
                            limit=1,
                        )
                    else:
                        agreement_id = self.env["pnt.agreement.agreement"].search(
                            [
                                (
                                    "pnt_partner_pickup_id",
                                    "=",
                                    record.pnt_partner_pickup_id.id,
                                ),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "=", "others"),
                                ("company_id", "=", self.env.company.id),
                            ],
                            order="name",
                            limit=1,
                        )
                    if agreement_id:
                        record.pnt_agreement_id = agreement_id
                    else:
                        if record.pnt_single_document_type == "output":
                            agreement_ids = self.env["pnt.agreement.agreement"].search(
                                [
                                    ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                    ("state", "=", "done"),
                                    ("pnt_agreement_type", "=", "manager"),
                                    ("company_id", "=", self.env.company.id),
                                ],
                                order="name",
                            )
                        elif record.pnt_single_document_type == "marpol":
                            agreement_ids = self.env["pnt.agreement.agreement"].search(
                                [
                                    ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                    ("state", "=", "done"),
                                    ("pnt_agreement_type", "=", "marpol"),
                                    ("company_id", "=", self.env.company.id),
                                ],
                                order="name",
                            )
                        else:
                            agreement_ids = self.env["pnt.agreement.agreement"].search(
                                [
                                    ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                    ("state", "=", "done"),
                                    ("pnt_agreement_type", "=", "others"),
                                    ("company_id", "=", self.env.company.id),
                                ],
                                order="name",
                            )
                        if agreement_ids:
                            record.pnt_agreement_domain_ids = agreement_ids
                            record.pnt_agreement_count = len(agreement_ids)
                        if record.pnt_single_document_type == "output":
                            agreement_parent_id = self.env[
                                "pnt.agreement.agreement"
                            ].search(
                                [
                                    ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                    ("state", "=", "done"),
                                    ("pnt_agreement_type", "=", "manager"),
                                    ("company_id", "=", self.env.company.id),
                                ],
                                order="name",
                                limit=1,
                            )
                        elif record.pnt_single_document_type == "marpol":
                            agreement_parent_id = self.env[
                                "pnt.agreement.agreement"
                            ].search(
                                [
                                    ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                    ("state", "=", "done"),
                                    ("pnt_agreement_type", "=", "marpol"),
                                    ("company_id", "=", self.env.company.id),
                                ],
                                order="name",
                                limit=1,
                            )
                        else:
                            agreement_parent_id = self.env[
                                "pnt.agreement.agreement"
                            ].search(
                                [
                                    ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                    ("state", "=", "done"),
                                    ("pnt_agreement_type", "=", "others"),
                                    ("company_id", "=", self.env.company.id),
                                ],
                                order="name",
                                limit=1,
                            )
                        if agreement_parent_id:
                            record.pnt_agreement_id = agreement_parent_id

    @api.onchange("pnt_agreement_id")
    def _onchange_delete_lines(self):
        for record in self:
            if (
                record.pnt_single_document_type != "portal"
                or record._origin != record.pnt_agreement_id
            ):
                record.pnt_single_document_line_ids = [(6, False, [])]

    @api.onchange("pnt_holder_id")
    def _onchange_pnt_holder_id(self):
        for record in self:
            # Vaciar lineas
            if record.pnt_single_document_type != "portal":
                record.pnt_single_document_line_ids = [(6, False, [])]
            # Buscar y asignar, si lo encuentra, un contrato activo del titular (pnt_holder_id)
            record.pnt_agreement_id = None
            record.pnt_agreement_domain_ids = None
            record.pnt_agreement_count = 0
            # if record.pnt_single_document_type == 'portal':
            #     record.pnt_partner_pickup_id = self.env.company.pnt_single_document_portal_partner_pickup_id
            # else:
            if not record.pnt_single_document_type:
                record.pnt_partner_pickup_id = None
                # record.pnt_agreement_id = None
            elif record.pnt_single_document_type not in ("metal",):
                if (
                    record.pnt_single_document_type in ("toplant", "others")
                    and record.pnt_holder_id
                ):
                    record.pnt_partner_pickup_id = record.pnt_holder_id
                else:
                    record.pnt_partner_pickup_id = None
            # record.pnt_partner_delivery_domain_ids = None
            if record.pnt_holder_id:
                if record.pnt_single_document_type == "output":
                    agreement_ids = self.env["pnt.agreement.agreement"].search(
                        [
                            ("pnt_holder_id", "=", record.pnt_holder_id.id),
                            ("state", "=", "done"),
                            ("pnt_agreement_type", "in", ["manager"]),
                            ("company_id", "=", record.env.company.id),
                        ],
                    )
                elif record.pnt_single_document_type == "marpol":
                    agreement_ids = self.env["pnt.agreement.agreement"].search(
                        [
                            ("pnt_holder_id", "=", record.pnt_holder_id.id),
                            ("state", "=", "done"),
                            ("pnt_agreement_type", "in", ["marpol"]),
                            ("company_id", "=", record.env.company.id),
                        ],
                    )
                else:
                    if record.pnt_single_document_type in (
                        "pickup",
                        "toplant",
                        "others",
                    ):
                        agreement_ids = self.env["pnt.agreement.agreement"].search(
                            [
                                ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "in", ["others"]),
                                ("company_id", "=", record.env.company.id),
                            ],
                        )
                    else:
                        agreement_ids = self.env["pnt.agreement.agreement"].search(
                            [
                                ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "in", ["portal"]),
                                ("company_id", "=", record.env.company.id),
                            ],
                        )
                if agreement_ids:
                    record.pnt_agreement_domain_ids = agreement_ids
                    record.pnt_agreement_count = len(agreement_ids)
                if record.pnt_single_document_type == "output":
                    agreement_id = self.env["pnt.agreement.agreement"].search(
                        [
                            ("pnt_holder_id", "=", record.pnt_holder_id.id),
                            ("state", "=", "done"),
                            ("pnt_agreement_type", "in", ["manager"]),
                            ("company_id", "=", record.env.company.id),
                        ],
                        limit=1,
                    )
                elif record.pnt_single_document_type == "marpol":
                    agreement_id = self.env["pnt.agreement.agreement"].search(
                        [
                            ("pnt_holder_id", "=", record.pnt_holder_id.id),
                            ("state", "=", "done"),
                            ("pnt_agreement_type", "in", ["marpol"]),
                            ("company_id", "=", record.env.company.id),
                        ],
                        limit=1,
                    )
                elif record.pnt_single_document_type == "portal":
                    agreement_id = (
                        self.env.company.pnt_single_document_default_portal_id
                    )
                else:
                    if record.pnt_single_document_type in (
                        "pickup",
                        "toplant",
                        "others",
                    ):
                        agreement_id = self.env["pnt.agreement.agreement"].search(
                            [
                                ("pnt_holder_id", "=", record.pnt_holder_id.id),
                                ("state", "=", "done"),
                                ("pnt_agreement_type", "in", ["others"]),
                            ],
                            limit=1,
                        )
                    else:
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
                    # self._set_pnt_partner_pickup_delivery_domain_ids()
                else:
                    raise UserError(
                        _(
                            "No se ha encontrado contrato activo para "
                            + record.pnt_holder_id.display_name
                        )
                    )

    def _set_pnt_partner_pickup_delivery_domain_ids(self):
        for record in self:
            if record.pnt_single_document_type not in ("portal", "metal", "internal"):
                # Actualizar la lista de direcciones de recogida en función
                # de las recogidas asignadas al contrato del titular
                if record.pnt_agreement_id.pnt_partner_pickup_ids:
                    record.pnt_partner_pickup_domain_ids = (
                        record.pnt_agreement_id.pnt_partner_pickup_ids
                    )
                pnt_comp_del_ids = self.env["res.partner"].search(
                    [
                        ("type", "=", "delivery"),
                        ("company_id", "in", [self.env.company.id, False]),
                    ]
                )
                record.pnt_partner_delivery_domain_ids = pnt_comp_del_ids
            else:
                if record.pnt_single_document_type in ("internal"):
                    pnt_comp_ids = self.env["res.partner"].search(
                        [
                            ("type", "=", "delivery"),
                            ("parent_id", "=", record.pnt_holder_id.id),
                        ]
                    )
                    pnt_comp_del_ids = pnt_comp_ids
                else:
                    pnt_comp_ids = self.env["res.partner"].search(
                        [("is_company", "=", True)]
                    )
                    pnt_comp_del_ids = self.env["res.partner"].search(
                        [
                            ("type", "=", "delivery"),
                            ("company_id", "in", [self.env.company.id, False]),
                        ]
                    )
                if pnt_comp_ids:
                    record.pnt_partner_pickup_domain_ids = pnt_comp_ids
                if pnt_comp_del_ids:
                    record.pnt_partner_delivery_domain_ids = pnt_comp_del_ids

    @api.onchange("pnt_single_document_type")
    def _onchange_pnt_single_document_type(self):
        for record in self:
            # Asignar valor de crear servei
            # self.compute_pnt_create_service()
            record.pnt_holder_id = None
            record.pnt_partner_delivery_id = None
            record.pnt_agreement_id = None
            record.pnt_partner_pickup_id = None
            record.pnt_vehicle_category_id = None
            if record.pnt_single_document_type == "metal":
                if self.env.company.pnt_metal_scale_agreement_id:
                    record.pnt_agreement_id = (
                        self.env.company.pnt_metal_scale_agreement_id
                    )
                else:
                    raise UserError(
                        _(
                            "No se ha establecido contrato para la Báscula metales en ajustes"
                        )
                    )
                record.pnt_pickup_date_type = "date"
                record.pnt_holder_id = self.env.company.partner_id
                record.pnt_partner_delivery_id = (
                    self.env.company.pnt_single_document_portal_partner_delivery_id
                )
                record.pnt_partner_pickup_id = (
                    self.env.company.pnt_single_document_metal_partner_pickup_id
                )
            elif record.pnt_single_document_type == "portal":
                record.pnt_pickup_date_type = "date"
                record.pnt_holder_id = self.env.company.partner_id
                record.pnt_partner_delivery_id = (
                    self.env.company.pnt_single_document_portal_partner_delivery_id
                )
            elif record.pnt_single_document_type == "internal":
                record.pnt_pickup_date_type = "date"
                record.pnt_holder_id = self.env.company.partner_id
            elif record.pnt_single_document_type == "pickup":
                record.pnt_pickup_date_type = "soon"
                record.pnt_partner_delivery_id = (
                    self.env.company.pnt_single_document_portal_partner_delivery_id
                )
            elif record.pnt_single_document_type == "output":
                record.pnt_pickup_date_type = "date"
            elif record.pnt_single_document_type == "toplant":
                record.pnt_pickup_date_type = "date"
                record.pnt_partner_delivery_id = (
                    self.env.company.pnt_single_document_portal_partner_delivery_id
                )
            elif record.pnt_single_document_type == "others":
                record.pnt_partner_delivery_id = (
                    self.env.company.pnt_single_document_portal_partner_delivery_id
                )
            else:
                record.pnt_pickup_date_type = "soon"

    @api.onchange("pnt_partner_pickup_id")
    def _onchange_pnt_partner_pickup_id(self):
        for record in self:
            # Vaciar terceros
            # record.pnt_single_document_holder_portal_ids.unlink()
            if record.pnt_partner_pickup_id:
                # Si es portal -> comprobar si tiene DNI escaneado y que la fecha de validez sea correcta
                # Verificar si ha de comprobar es DNI - Només fer-ho si es dni
                verificar_dni = False
                if record.pnt_partner_pickup_id.pnt_id_type in ("nif", "nie"):
                    verificar_dni = True
                if record.pnt_single_document_type in ("portal",) and verificar_dni:
                    # Actualizar contrato de portal del partner
                    if record.pnt_partner_pickup_id.pnt_portal_agreement_type_id:
                        if (
                            record.pnt_agreement_id
                            != self.env.company.pnt_metal_scale_agreement_id
                        ):
                            record.pnt_agreement_id = (
                                self.env.company.pnt_metal_scale_agreement_id
                            )
                    # Comprobar fecha validez DNI
                    if record.pnt_partner_pickup_id.pnt_dni_date_validity:
                        date_val = record.pnt_partner_pickup_id.pnt_dni_date_validity
                    else:
                        date_val = datetime(1900, 1, 1, 00, 00, 00, 00000).date()
                    if date_val < fields.Date.today():
                        record.pnt_partner_pickup_id = None
                        raise UserError(
                            _(
                                "El DNI que se tiene en la base de datos tiene la fecha de Validez vencida o la fecha de validez está en blanco"
                            )
                        )
                    # Comprobar que esté subida la imagen del DNI
                    if not record.pnt_partner_pickup_id.pnt_dni_image:
                        record.pnt_partner_pickup_id = None
                        raise UserError(
                            _("El partner no tienen subida la imagen del DNI")
                        )

                record.street = record.pnt_partner_pickup_id.street
                record.street2 = record.pnt_partner_pickup_id.street2
                record.city = record.pnt_partner_pickup_id.city
                record.state_id = record.pnt_partner_pickup_id.state_id
                record.zip = record.pnt_partner_pickup_id.zip
                record.country_id = record.pnt_partner_pickup_id.country_id
                record.partner_latitude = record.pnt_partner_pickup_id.partner_latitude
                record.partner_longitude = (
                    record.pnt_partner_pickup_id.partner_longitude
                )
                record.email = record.pnt_partner_pickup_id.email
                record.email_formatted = record.pnt_partner_pickup_id.email_formatted
                record.phone = record.pnt_partner_pickup_id.phone
                record.mobile = record.pnt_partner_pickup_id.mobile
                # Reasignar trato una vez asignada la recogida
                if record.pnt_single_document_type == "others":
                    self.set_pnt_agreement_id()
                # Revisar los datos especificos de contrato (referencia, etc) para
                # nuevo pnt_partner_pickup_id
                self.update_du_contract_reference()
                # Asignar recogida a tercero
                self.add_tercero()
            else:
                record.street = None
                record.street2 = None
                record.city = None
                record.state_id = None
                record.zip = None
                record.country_id = None
                record.partner_latitude = None
                record.partner_longitude = None
                record.email = None
                record.email_formatted = None
                record.phone = None
                record.mobile = None
                record.pnt_agreement_reference = None
            # Vaciar lineas
            if record.pnt_single_document_type != "portal":
                record.pnt_single_document_line_ids = [(6, False, [])]

    def add_tercero(self):
        # Asignar recogida a tercero
        self.pnt_single_document_holder_portal_ids = False
        for record in self:
            record.pnt_single_document_holder_portal_ids = [
                (
                    0,
                    0,
                    {
                        "pnt_partner_id": record.pnt_partner_pickup_id.id,
                    },
                )
            ]

    @api.onchange("pnt_agreement_id")
    def _onchange_pnt_agreement_id(self):
        for record in self:
            record.pnt_operator_id = record.pnt_agreement_id.pnt_operator_id
            if record.pnt_single_document_type not in ("others", "portal"):
                record.pnt_partner_pickup_id = None
            if record.pnt_single_document_line_ids:
                raise UserError(
                    _("No se puede cambiar el contrado del DU si existen lineas")
                )
            else:
                # Copiar referencias del contrato en el DU
                self.update_du_contract_reference()
    def update_du_contract_reference(self):
        for record in self:
            if record.pnt_agreement_id.pnt_agreement_reference_ids:
                references_partner = (
                    record.pnt_agreement_id.pnt_agreement_reference_ids.filtered(
                        lambda x: x.pnt_partner_pickup_id
                                  == record.pnt_partner_pickup_id
                    )
                )
                if references_partner:
                    record.pnt_agreement_reference = references_partner[0].name
                else:
                    references_not_partner = record.pnt_agreement_id.pnt_agreement_reference_ids.filtered(
                        lambda x: not x.pnt_partner_pickup_id
                    )
                    if references_not_partner:
                        record.pnt_agreement_reference = references_not_partner[
                            0
                        ].name
                    else:
                        record.pnt_agreement_reference = False
            else:
                record.pnt_agreement_reference = False

    @api.onchange("pnt_partner_delivery_id")
    def onchange_pnt_partner_delivery_id(self):
        for rec in self:
            if rec.pnt_single_document_line_ids and rec.pnt_partner_delivery_id:
                for lin in rec.pnt_single_document_line_ids:
                    # if not lin.pnt_partner_delivery_id:
                    lin.pnt_partner_delivery_id = rec.pnt_partner_delivery_id

    def _prepare_unlocked_values(self):
        return {
            "state": "dispached",
        }

    def _prepare_received_values(self):
        return {
            "state": "received",
        }

    def _prepare_finished_values(self):
        return {
            "state": "finished",
        }

    def _prepare_inplant_values(self):
        return {
            "state": "plant",
        }

    def _prepare_cancel_values(self):
        return {
            "state": "cancel",
        }

    def action_unlocked(self):
        self.with_context(generate_service_skip=True).write(
            self._prepare_unlocked_values()
        )

    def action_inplant(self):
        for rec in self:
            rec.write(rec._prepare_inplant_values())

    def action_received(self):
        for rec in self:
            if not rec.pnt_scales_id and rec.pnt_single_document_type not in (
                "others",
            ):
                raise UserError(
                    _(
                        "Debe indicar una Báscula para poder realizar los movimientos de stock"
                    )
                )
            rec.write(rec._prepare_received_values())
            # Crear els albarans
            rec.generate_delivery_notes(False)
            if rec.pnt_single_document_type == "marpol":
                rec.button_set_admitted()
            if not rec.task_id:
                return
            # Cerrar la tarea de logística
            if rec.pnt_single_document_type not in ("output",):
                if rec.task_id:
                    rec.task_id.stage_id = 7
                    rec.task_id.pnt_pickup_date = fields.datetime.now()
        if rec.pnt_single_document_type in ("output",):
            return
        else:
            return self.env["ir.actions.actions"]._for_xml_id(
                "custom_pnt.pnt_du_confirm_timesheet_action"
            )

    def generate_delivery_notes(self, confirm):
        for rec in self:
            if rec.pnt_single_document_type not in (
                "portal",
                "metal",
                "others",
                "internal",
            ):
                # Entrada de residuos en almacén
                # Si lugar de entrega es Adalmo/Ferrimet
                if not rec.pnt_partner_delivery_id.parent_id:
                    partner_delivery = rec.pnt_partner_delivery_id
                else:
                    partner_delivery = rec.pnt_partner_delivery_id.parent_id
                if partner_delivery == self.env.company.partner_id:
                    existnocontainer = self.pnt_single_document_line_ids.filtered(
                        lambda x: not x.pnt_product_id.pnt_is_container
                    )
                    if existnocontainer:
                        if rec.pnt_single_document_type == "output":
                            typemov = "outbound"
                            pick_type = (
                                rec.pnt_scales_id.pnt_stock_picking_type_sale_du_id
                            )
                            location = rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                            location_dest = (
                                self.env.company.pnt_stock_location_vendors_du_id
                            )
                        else:
                            typemov = "inbound"
                            pick_type = (
                                rec.pnt_scales_id.pnt_stock_picking_type_purchase_du_id
                            )
                            location = self.env.company.pnt_stock_location_vendors_du_id
                            location_dest = (
                                rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                            )
                        sp = rec._stock_picking_create(
                            pick_type, location, location_dest, typemov, "pickup"
                        )
                        if sp and confirm:
                            # Confirmar recepción mercancia
                            sp.action_confirm()
                # Salida de residuos en almacén
                # Si lugar de recogida es Adalmo/Ferrimet
                if not rec.pnt_partner_pickup_id.parent_id:
                    partner_pickup = rec.pnt_partner_pickup_id
                else:
                    partner_pickup = rec.pnt_partner_pickup_id.parent_id
                if partner_pickup == self.env.company.partner_id:
                    existnocontainer = self.pnt_single_document_line_ids.filtered(
                        lambda x: not x.pnt_product_id.pnt_is_container
                    )
                    if existnocontainer:
                        if rec.pnt_single_document_type == "output":
                            typemov = "inbound"
                            pick_type = (
                                rec.pnt_scales_id.pnt_stock_picking_type_purchase_du_id
                            )
                            location = (
                                self.env["stock.warehouse"]
                                .search([("partner_id", "=", partner_pickup.id)])
                                .lot_stock_id
                            )
                            if not location:
                                location = (
                                    rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                                )
                            location_dest = (
                                self.env.company.pnt_stock_location_vendors_du_id
                            )
                        else:
                            typemov = "outbound"
                            pick_type = (
                                rec.pnt_scales_id.pnt_stock_picking_type_sale_du_id
                            )
                            location = self.env.company.pnt_stock_location_vendors_du_id
                            location_dest = (
                                self.env["stock.warehouse"]
                                .search([("partner_id", "=", partner_pickup.id)])
                                .lot_stock_id
                            )
                            if not location_dest:
                                location_dest = (
                                    rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                                )
                        sp = rec._stock_picking_create(
                            pick_type, location_dest, location, typemov, "pickup"
                        )
                        if sp and confirm:
                            # Confirmar recepción mercancia
                            sp.action_confirm()

                # Comprobar si hay contenedores para entregar
                existcontainer = self.pnt_single_document_line_ids.filtered(
                    lambda x: x.pnt_product_id.pnt_is_container
                )
                if existcontainer:
                    if not rec.pnt_partner_delivery_id.parent_id:
                        partner_delivery = rec.pnt_partner_delivery_id
                    else:
                        partner_delivery = rec.pnt_partner_delivery_id.parent_id
                    if partner_delivery == self.env.company.partner_id:
                        typemov = "container"
                        pick_type_container = (
                            rec.pnt_scales_id.pnt_stock_picking_type_sale_du_id
                        )
                        location_container = (
                            self.env.company.pnt_stock_location_vendors_du_id
                        )
                        location_dest_container = (
                            rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                        )
                        sp_container = rec._stock_picking_create(
                            pick_type_container,
                            location_dest_container,
                            location_container,
                            typemov,
                            "pickup",
                        )
                        if sp_container and confirm:
                            # Confirmar recepción mercancia
                            sp_container.action_confirm()

                    if not rec.pnt_partner_pickup_id.parent_id:
                        partner_pickup = rec.pnt_partner_pickup_id
                    else:
                        partner_pickup = rec.pnt_partner_pickup_id.parent_id
                    if partner_pickup == self.env.company.partner_id:
                        typemov = "container"
                        pick_type_container = (
                            rec.pnt_scales_id.pnt_stock_picking_type_sale_du_id
                        )
                        location_container = (
                            self.env.company.pnt_stock_location_vendors_du_id
                        )
                        location_dest_container = (
                            self.env["stock.warehouse"]
                            .search([("partner_id", "=", partner_pickup.id)])
                            .lot_stock_id
                        )
                        if not location_dest_container:
                            location_dest_container = (
                                rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                            )
                        sp_container = rec._stock_picking_create(
                            pick_type_container,
                            location_dest_container,
                            location_container,
                            typemov,
                            "delivery",
                        )
                        # Confirmar recepción mercancia
                        if sp_container and confirm:
                            sp_container.action_confirm()
            else:
                if rec.pnt_single_document_type == "portal":
                    # Entrada de residuos en almacén
                    typemov = "inbound"
                    pick_type = rec.pnt_scales_id.pnt_stock_picking_type_purchase_du_id
                    location = self.env.company.pnt_stock_location_vendors_du_id
                    if not rec.pnt_partner_delivery_id.parent_id:
                        partner_delivery = rec.pnt_partner_delivery_id
                    else:
                        partner_delivery = rec.pnt_partner_delivery_id.parent_id
                    location_dest = rec.pnt_scales_id.pnt_warehouse_id.lot_stock_id
                    sp = rec._stock_picking_create(
                        pick_type, location, location_dest, typemov, "pickup"
                    )
                    # Confirmar recepción mercancia
                    if sp and confirm:
                        # Confirmar recepción mercancia
                        sp.action_confirm()
                elif rec.pnt_single_document_type == "internal":
                    typemov = "internal"
                    warehouse_ori = self.env["stock.warehouse"].search(
                        [
                            ("partner_id", "=", rec.pnt_partner_pickup_id.id),
                        ]
                    )
                    if warehouse_ori:
                        pick_type = self.env["stock.picking.type"].search(
                            [
                                ("code", "=", "internal"),
                                ("company_id", "=", self.env.company.id),
                                ("warehouse_id", "=", warehouse_ori.id),
                            ]
                        )
                        location = warehouse_ori.lot_stock_id
                    else:
                        break
                    warehouse_dest = self.env["stock.warehouse"].search(
                        [
                            ("partner_id", "=", rec.pnt_partner_delivery_id.id),
                        ]
                    )
                    if warehouse_dest:
                        location_dest = warehouse_dest.lot_stock_id
                    else:
                        break
                    sp = rec._stock_picking_create(
                        pick_type, location, location_dest, typemov, "internal"
                    )
                    # Confirmar recepción mercancia
                    if sp and confirm:
                        # Confirmar recepción mercancia
                        sp.action_confirm()

    def set_admitted(self):
        ddate = fields.Datetime.now()
        company_id = self.env.company.id
        dus = self.search(
            [
                ("company_id", "=", company_id),
                ("pnt_admitted", "=", False),
                ("pnt_scales_id.pnt_time_cron", "!=", False),
                ("task_id.pnt_pickup_date", "!=", False),
                ("pnt_single_document_type", "!=", "portal"),
            ]
        )
        for du in dus:
            if all(
                x.stage_id.is_closed for x in du.pnt_single_document_issue_project_ids
            ):
                pickup = (ddate - du.task_id.pnt_pickup_date).seconds
                hours = pickup / 3600
                ttime = float(du.pnt_scales_id.pnt_time_cron)
                if ttime == 24 or hours > 24:
                    du.button_set_admitted()

    def cron_set_admitted(self):
        for company in self.env["res.company"].sudo().search([]):
            self.sudo().with_company(company.id).set_admitted()

    def check_admitted(self):
        if self.env.context.get("skip_check_admitted"):
            return
        if any(
            not x.pnt_admitted and x.pnt_single_document_type != "portal" for x in self
        ):
            raise UserError(_("The document is not admitted."))

    def button_set_admitted(self):
        if not self.pnt_force_in_final_manager and self.pnt_single_document_type in (
            "output",
        ):
            raise UserError(_("Para poder estar ADMITIDO debe estar EN GESTOR FINAL"))
        self.pnt_force_admitted = True
        self.pnt_admitted = True
        if self.pnt_single_document_type == "internal":
            for sp in self.pnt_stock_picking_ids:
                sp.button_validate()
            self.state = "finished"

    def button_set_in_final_manager(self):
        self.pnt_force_in_final_manager = True
        if self.task_id:
            self.task_id.stage_id = 7
            self.task_id.pnt_pickup_date = fields.datetime.now()

    def action_finished(self):
        self.check_admitted()
        order = False
        for rec in self:
            rec.write(rec._prepare_finished_values())
            # Tornar a generar el albarans per si hi ha hagut canvis a les linies de DU
            for alb in rec.pnt_stock_picking_ids:
                if alb.state == "draft":
                    alb.move_lines.unlink()
                    alb.unlink()
                elif alb.state in ("assigned", "confirmed"):
                    alb.action_cancel()
            rec.generate_delivery_notes(True)
            # Validar los albaranes
            for sp in rec.pnt_stock_picking_ids:
                # sp.action_assign()
                if sp.state in ("assigned", "confirmed"):
                    sp.button_validate()
            # Generar documentos de Compra y venta
            if rec.pnt_single_document_type in (
                "portal",
                "pickup",
                "output",
                "toplant",
                "others",
                "marpol",
            ):
                outbounds = self.pnt_single_document_line_ids.filtered(
                    lambda x: x.pnt_monetary_waste in ("outbound",)
                )
                if rec.pnt_single_document_type in ("portal", "metal"):
                    outbounds_partners = (
                        self.pnt_single_document_holder_portal_ids.filtered(
                            lambda x: x.pnt_monetary_waste in ("outbound", "inout")
                        )
                    )
                else:
                    # outbounds_partners = self.pnt_partner_pickup_id
                    outbounds_partners = self.pnt_holder_id
                inbounds = self.pnt_single_document_line_ids.filtered(
                    lambda x: x.pnt_monetary_waste in ("inbound",)
                )
                if rec.pnt_single_document_type in ("portal", "metal"):
                    inbounds_partners = (
                        self.pnt_single_document_holder_portal_ids.filtered(
                            lambda x: x.pnt_monetary_waste in ("inbound", "inout")
                        )
                    )
                else:
                    # inbounds_partners = self.pnt_partner_pickup_id
                    inbounds_partners = self.pnt_holder_id
                if self.env.company.pnt_waste_order_purchase_id:
                    if outbounds and outbounds_partners:
                        if rec.pnt_single_document_type in ("portal", "metal"):
                            factor_percent = 1 / len(outbounds_partners)
                            for tercero in outbounds_partners:
                                order = rec._purchase_order_create(
                                    self.env.company.pnt_waste_order_purchase_id,
                                    tercero.pnt_partner_id,
                                    factor_percent,
                                )
                                order.button_confirm()
                        else:
                            order = rec._purchase_order_create(
                                self.env.company.pnt_waste_order_purchase_id,
                                outbounds_partners,
                                1,
                            )
                            order.button_confirm()
                else:
                    raise UserError(
                        _(
                            "No se ha definido un tipo de pedido de residuos de compra en configuración"
                        )
                    )
                if self.env.company.pnt_waste_order_sale_id:
                    if inbounds and inbounds_partners:
                        if rec.pnt_single_document_type in ("portal", "metal"):
                            factor_percent = 1 / len(inbounds_partners)
                            for tercero in inbounds_partners:
                                order = rec._sale_order_create(
                                    self.env.company.pnt_waste_order_purchase_id,
                                    tercero.pnt_partner_id,
                                    factor_percent,
                                )
                                order.action_confirm()
                                order.action_unlock()
                        else:
                            order = rec._sale_order_create(
                                self.env.company.pnt_waste_order_purchase_id,
                                inbounds_partners,
                                1,
                            )
                            order.action_confirm()
                            order.action_unlock()
                else:
                    raise UserError(
                        _(
                            "No se ha definido un tipo de pedido de residuos de venta en configuración"
                        )
                    )
        if order and order._name == "sale.order":
            self.generate_sale_line_downpayment(order)
        return order

    def generate_sale_line_downpayment(self, sale):
        downpayment = self.pnt_agreement_id.pnt_amount_downpayment
        if downpayment <= 0:
            return
        deposit = self.env["sale.advance.payment.inv"]._default_product_id()
        if not deposit:
            return
        diff = min(sale.amount_untaxed, downpayment)
        if diff <= 0:
            return
        sale.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": _("Down Payment: %s")
                            % (imp_time.strftime("%m %Y"),),
                            "price_unit": diff,
                            "order_id": sale.id,
                            "discount": 0.0,
                            "product_uom": deposit.uom_id.id,
                            "product_uom_qty": -1,
                            "product_id": deposit.id,
                            "is_downpayment": True,
                            "sequence": sale.order_line
                            and sale.order_line[-1].sequence + 1
                            or 10,
                        },
                    )
                ]
            }
        )

    def action_cancel(self):
        self.write(self._prepare_cancel_values())
        # Si hi ha un servei, també l'ha de cancel·lar
        if self.task_id:
            self.task_id.stage_id = TASK_STAGES["cancelled"]
        # Si hi ha albarans, també s'han de cancel·lar
        for alb in self.pnt_stock_picking_ids:
            if alb.state not in ("done", "cancel"):
                alb.action_cancel()

    def _pnt_compute_issue_project_count(self):
        obj_task = self.env["project.task"]
        project_id = self[:1].company_id.pnt_single_document_issue_project_id.id
        for record in self:
            record.pnt_single_document_issue_project_count = obj_task.search_count(
                [
                    ("project_id", "=", project_id),
                    ("pnt_sd_line_id", "in", record.pnt_single_document_line_ids.ids),
                ]
            )

    def action_view_issue_project(self):
        self.ensure_one()
        project_id = self.company_id.pnt_single_document_issue_project_id
        issues = self.pnt_single_document_issue_project_ids.filtered(
            lambda x: x.pnt_single_document_id.id == self.id
            and x.project_id.id == project_id.id
        )
        action = self.env["ir.actions.actions"]._for_xml_id(
            "project.action_view_all_task"
        )
        if len(issues) > 1:
            action["domain"] = [("id", "in", issues.ids)]
        elif issues:
            form_view = [(self.env.ref("project.view_task_form2").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = issues.id
        return action

    def generate_service(self):
        if self._context.get("generate_service_skip"):
            return
        for record in self.with_context(generate_service_skip=True):
            if not record.pnt_show_create_service or record.state != "dispached":
                continue
            record.action_done()

    def generate_di(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Create DI",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "pnt.create.di",
            "nodestroy": True,
            "target": "new",
        }

    def lines_without_di(self):
        for record in self:
            return record.pnt_single_document_line_ids.filtered(
                lambda ml: ml.pnt_product_id.pnt_is_waste
                and not ml.pnt_waste_transfer_document_id
            )

    def lines_with_di(self):
        for record in self:
            return (record.pnt_single_document_line_ids
                    .pnt_waste_transfer_document_id.filtered(
                    lambda x: x.active
                ))

    def copy_transporter_to_task(self):
        for record in self:
            if record.task_id and record.pnt_transport_id:
                record.task_id.pnt_transport_id = record.pnt_transport_id

    def auto_create_di(self):
        wizard = (
            self.env["pnt.create.di"]
            .with_context(
                default_pnt_single_document_id=self.id,
                default_pnt_document_type="di",
                default_pnt_type="other",
            )
            .create({})
        )
        wizard.create_dis()

    def _stop_rental_agreement(self):
        if self._context.get("skip_stop_rental_agreement"):
            return
        for record in self.with_context(skip_stop_rental_agreement=True):
            if record.pnt_single_document_type != "pickup" or not record.task_id:
                continue
            sales_agreement_manual = (
                record.pnt_agreement_id.pnt_sale_rental_ids.filtered(
                    "pnt_is_rental_manual_active"
                )
            )
            if not sales_agreement_manual:
                continue
            single_products = (
                record.pnt_single_document_line_ids.pnt_product_id.filtered(
                    lambda x: x.is_product_removal()
                )
            )
            lines = record.pnt_single_document_line_ids.filtered(
                lambda x, products=single_products: x.pnt_product_id in products
            )
            if not lines:
                continue
            keys_single_lines = []
            for single_line in lines:
                keys_single_lines.append(
                    (
                        single_line.pnt_single_document_id.pnt_partner_pickup_id.id,
                        single_line.pnt_container_id.id,
                        single_line.pnt_product_waste_id.id,
                    )
                )
            sales_created = {}
            for line in sales_agreement_manual.order_line:
                key = (
                    line.order_id.partner_shipping_id.id,
                    line.pnt_rental_manual_container_id.id,
                    line.pnt_rental_manual_waste_id.id,
                )
                sales_created.setdefault(key, []).append(line.order_id)
            for key in keys_single_lines:
                if key in sales_created:
                    for sale in sales_created[key]:
                        sale.pnt_is_rental_manual_active = False

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.single.document", sequence_date=seq_date
            ) or _("New")
        vals["state"] = "dispached"
        result = super().create(vals)
        result.generate_service()
        # Desactivar
        # result._stop_rental_agreement()
        if result.pnt_single_document_type in ["pickup", "marpol"]:
            result.auto_create_di()
        return result

    def write(self, values):
        res = super().write(values)
        self.generate_service()
        for record in self.filtered(lambda x: x.pnt_single_document_type in ["pickup", "marpol"]):
            record.auto_create_di()
        self.copy_transporter_to_task()
        if values.get("pnt_vehicle_category_id"):
            vcat = values.get("pnt_vehicle_category_id")
            if vcat and self.task_id.pnt_vehicle_category_id.id != vcat:
                self.task_id.pnt_vehicle_category_id = vcat
        if values.get("pnt_vehicle_id"):
            veh = values.get("pnt_vehicle_id")
            if veh and self.task_id.pnt_vehicle_id.id != veh:
                self.task_id.pnt_vehicle_id = veh
        if values.get("pnt_vehicle_aux_id"):
            veh = values.get("pnt_vehicle_aux_id")
            if veh and self.task_id.pnt_vehicle_id.id != veh:
                self.task_id.pnt_vehicle_id = veh
        if values.get("pnt_transport_id"):
            tras = values.get("pnt_transport_id")
            if tras and self.task_id.pnt_transport_id.id != tras:
                self.task_id.pnt_transport_id = tras
        if values.get("pnt_carrier_id"):
            carr = values.get("pnt_carrier_id")
            if carr and self.task_id.pnt_carrier_id.id != carr:
                self.task_id.pnt_carrier_id = carr
        if values.get("pnt_single_document_line_ids"):
            lines = values.get("pnt_single_document_line_ids")
            if lines and self.task_id:
                list_lines = []
                for line in self.pnt_single_document_line_ids:
                    if (
                            line.pnt_product_id.pnt_is_waste
                            or line.pnt_product_id.pnt_is_container
                            or line.pnt_product_id.pnt_container_movement_type
                    ):
                        container = None
                        if line.pnt_container_movement_id:
                            if line.pnt_container_movement_id.pnt_container_delivery_id:
                                container = (
                            line.pnt_container_movement_id.pnt_container_delivery_id.id
                                )
                            elif line.pnt_container_movement_id.pnt_container_removal_id:
                                container = (
                              line.pnt_container_movement_id.pnt_container_removal_id.id
                                )
                        else:
                            if line.pnt_container_id:
                                container = line.pnt_container_id.id
                        dict_line = {
                            "pnt_task_id": self.task_id.id,
                            "pnt_product_id": line.pnt_product_id.id,
                            "pnt_container_id": container,
                        }
                        list_lines.append((0, 0, dict_line))
                self.task_id.pnt_product_container_ids.unlink()
                self.task_id.write({"pnt_product_container_ids": list_lines})
        # Actualizar partner en albarenes generados cuando se cambia el partner en portal
        if values.get("pnt_partner_pickup_id"):
            part = values.get("pnt_partner_pickup_id")
            if (
                part
                and self.pnt_stock_picking_ids
                and self.pnt_single_document_type == "portal"
            ):
                for sto in self.pnt_stock_picking_ids:
                    if sto.partner_id != part:
                        sto.partner_id = part
        return res

    @api.onchange("pnt_scales_id")
    def onchange_pnt_pnt_scale_id(self):
        if (
            self.pnt_single_document_type
            and self.pnt_single_document_type
            in (
                "portal",
                "toplant",
            )
            and self.pnt_scales_id
            and self.pnt_scales_id.pnt_default_delivery_id
        ):
            self.pnt_partner_delivery_id = self.pnt_scales_id.pnt_default_delivery_id.id

    def pnt_get_sale_invoices(self):
        invoice_ids = self.env["account.move"]
        for sale in self.pnt_sale_order_ids:
            sale.sudo()._read(["invoice_ids"])
            invoice_ids += sale.invoice_ids
        return invoice_ids

    def pnt_get_sale_invoices_for_portal(self):
        invoice_ids = self.pnt_get_sale_invoices()
        return invoice_ids.filtered(lambda x: x.state in ["posted"])

    def pnt_get_purchase_invoices(self):
        invoice_ids = self.env["account.move"]
        for purchase in self.pnt_purchase_order_ids:
            purchase.sudo()._read(["invoice_ids"])
            invoice_ids += purchase.invoice_ids
        return invoice_ids

    def pnt_get_purchase_invoices_for_portal(self):
        invoice_ids = self.pnt_get_purchase_invoices()
        return invoice_ids.filtered(lambda x: x.pnt_purchase_state in ["order"] or x.state in ["post"])


class PntSingleDocumentMetalLine(models.Model):
    _name = "pnt.single.document.metal.line"
    _description = "Pnt Single Document Metal Line"
    _order = "pnt_single_document_id, id"
    _check_company_auto = True
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        related="pnt_single_document_id.pnt_agreement_id",
    )
    state = fields.Selection(
        related="pnt_single_document_id.state",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_single_document_id.pnt_single_document_type",
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single Document Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    pnt_product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    pnt_weight_qty = fields.Float(
        string="Economic Quantity",
        digits="Product Unit of Measure",
        required=True,
        default=0.0,
    )
    pnt_product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Economic Unit of Measure",
        default=lambda self: self.env["uom.uom"].search([("name", "=", "kg")], limit=1),
    )

    def _get_container_metal_scale_du(self, product):
        if self.pnt_agreement_id:
            container_ids = self.pnt_agreement_id.pnt_agreement_line_ids.filtered(
                lambda r: r.pnt_product_id.id == product
            )
            if len(container_ids) == 1 and container_ids[0].pnt_container_id:
                return container_ids[0].pnt_container_id.id
            else:
                return False
        else:
            return False

    @api.constrains("pnt_single_document_id.pnt_single_document_line_ids")
    def button_add_line(self):
        if self.pnt_single_document_id:
            if self.pnt_single_document_id.state in ("dispached",):
                newduline = self.env["pnt.single.document.line"].create(
                    {
                        "pnt_single_document_id": self.pnt_single_document_id.id,
                        "pnt_product_id": self.pnt_product_id.id,
                        "pnt_container_id": self._get_container_metal_scale_du(
                            self.pnt_product_id.id
                        ),
                        "pnt_monetary_waste": self.pnt_product_id.pnt_monetary_waste,
                        "name": self.pnt_product_id.display_name,
                        "pnt_product_uom_qty": self.pnt_weight_qty,
                        "pnt_product_uom": self.pnt_product_uom.id,
                        "pnt_partner_delivery_id": self.pnt_single_document_id.pnt_partner_delivery_id.id,
                    }
                )
                if newduline:
                    newduline.compute_pnt_price_unit()
                    newduline.onchange_pnt_product_uom_qty()
                self.pnt_weight_qty = 0
                view_id = self.env.ref(
                    "custom_pnt.pnt_single_document_form_metal_scale_view"
                ).id
                return {
                    "type": "ir.actions.act_window",
                    "name": "Single document",
                    "view_type": "form",
                    "view_mode": "form",
                    "view_id": view_id,
                    "res_model": "pnt.single.document",
                    "res_id": self.pnt_single_document_id.id,
                    "target": "main",
                }
            else:
                raise UserError(_("No pueden agregarse pesadas a un DU ya procesado"))

    def _weight_update(self, pes):
        temp = str(int(self.pnt_weight_qty))
        if temp == "0":
            temp = ""
        result = temp + pes
        self.pnt_weight_qty = float(result)

    def button_delete(self):
        self.pnt_weight_qty = 0
        return 0

    def button_0(self):
        self._weight_update("0")

    def button_1(self):
        self._weight_update("1")

    def button_2(self):
        self._weight_update("2")

    def button_3(self):
        self._weight_update("3")

    def button_4(self):
        self._weight_update("4")

    def button_5(self):
        self._weight_update("5")

    def button_6(self):
        self._weight_update("6")

    def button_7(self):
        self._weight_update("7")

    def button_8(self):
        self._weight_update("8")

    def button_9(self):
        self._weight_update("9")


class PntSingleDocumentLine(models.Model):
    _name = "pnt.single.document.line"
    _description = "Pnt Single Document Line"
    _order = "pnt_single_document_id, sequence, id"
    _check_company_auto = True
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    def _has_second_weight(self):
        """
        Functión calculada para saber si tiene segundo pesaje y mostrar en el view el peso neto o no
        :return:
        """
        for record in self:
            second_weight = (
                record.env["pnt.scales.record"]
                .search([("pnt_single_document_line_id", "=", record.id)])
                .pnt_second_weighing_qty
            )
            if second_weight > 0:
                record.pnt_second_weighing = True
            else:
                record.pnt_second_weighing = False

    @api.depends("pnt_agreement_id")
    def _get_authorized_products_domain_ids(self):
        for record in self:
            if record.pnt_single_document_type not in ("internal",):
                du_pickup = record.pnt_single_document_id.pnt_partner_pickup_id
                agree = record.pnt_agreement_id
                agree_lines = agree.pnt_agreement_line_ids
                agree_lines = agree_lines.filtered(
                    lambda x, agreement=agree, pickup=du_pickup: x.pnt_partner_pickup_id.id
                    in (False, pickup.id)
                )
                products = agree_lines.pnt_product_id.ids
            else:
                products = (
                    self.env["product.product"]
                    .search(
                        [
                            ("product_tmpl_id.type", "in", ["product", "service"]),
                            ("product_tmpl_id.company_id", "=", self.env.company.id),
                        ]
                    )
                    .ids
                )
            record.authorized_products_domain_ids = [(6, False, products)]

    # Campo calculado para saber si tiene o no segundo pesaje
    pnt_second_weighing = fields.Boolean(
        string="Second weighing", compute="_has_second_weight", store=False
    )

    authorized_products_domain_ids = fields.Many2many(
        comodel_name="product.product",
        store=False,
        compute="_get_authorized_products_domain_ids",
        relation="pnt_authorized_products_domain_rel",
    )

    authorized_containers_domain_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_get_authorized_containers_domain_ids",
    )
    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        related="pnt_single_document_id.pnt_agreement_id",
        store=True,
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_single_document_id.pnt_single_document_type",
        store=True,
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single Document Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    state = fields.Selection(
        related="pnt_single_document_id.state",
        store=True,
    )
    pnt_holder_id = fields.Many2one(
        related="pnt_single_document_id.pnt_holder_id",
        store=True,
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
        store=True,
    )
    pnt_effective_date = fields.Date(
        related="pnt_single_document_id.pnt_effective_date",
        store=True,
    )
    pnt_du_end_date = fields.Date(
        related="pnt_single_document_id.pnt_du_end_date",
        store=True,
    )
    pnt_date_to_plant = fields.Datetime(
        related="pnt_single_document_id.pnt_date_to_plant",
        store=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    display_type = fields.Selection(
        selection=[("line_section", "Section"), ("line_note", "Note")],
        default=False,
        help="Technical field for UX purpose.",
    )
    pnt_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
    )
    pnt_lot_id = fields.Many2one(
        comodel_name="stock.production.lot",
        string="Container number",
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
    )

    pnt_is_waste = fields.Boolean(
        string="Waste",
        related="pnt_product_id.pnt_is_waste",
    )
    pnt_product_type = fields.Selection(
        related="pnt_product_id.type",
    )
    pnt_is_container = fields.Boolean(
        string="Waste",
        related="pnt_product_id.pnt_is_container",
    )
    pnt_waste_ler_id = fields.Many2one(
        string="Waste LER",
        related="pnt_product_id.pnt_waste_ler_id",
        store=True,
    )
    pnt_product_economic_uom = fields.Many2one(
        # related="pnt_agreement_line_id.pnt_product_economic_uom",
        comodel_name="uom.uom",
        compute="_compute_pnt_product_economic_uom",
        store=True,
    )
    pnt_product_economic_uom_qty = fields.Float(
        string="Economic Quantity",
        digits="Product Unit of Measure",
        required=True,
        default=0.0,
        tracking=True,
    )
    pnt_price_unit = fields.Float(
        string="Unit Price",
        required=True,
        digits="Product Price",
        default=0.0,
        compute="compute_pnt_price_unit",
        store=True,
        readonly=False,
        track_visibility="onchange",
    )
    pnt_price_subtotal = fields.Float(
        string="Subtotal Price",
        required=True,
        digits="Product Price",
        default=0.0,
        compute="compute_pnt_price_subtotal",
        store=True,
        readonly=False,
    )
    pnt_container_id = fields.Many2one(
        comodel_name="product.product",
        string="Container",
        ondelete="restrict",
        check_company=True,
    )
    pnt_container_qty = fields.Float(
        string="Quantity",
        digits="Product Unit of Measure",
        required=True,
        default=0.0,
    )
    pnt_monetary_waste = fields.Selection(
        string="Monetary Waste",
        selection=[
            ("inbound", "Inbound"),
            ("outbound", "Outbound"),
        ],
        compute="compute_pnt_product_id",
        store=True,
        readonly=False,
    )
    pnt_product_uom_qty = fields.Float(
        string="Forecast Quantity",
        digits="Product Unit of Measure",
        # digits=(16, 3),
        required=True,
        default=0.0,
    )
    pnt_output_weight_qty = fields.Float(
        string="output weight",
        digits="Product Unit of Measure",
        default=0.0,
        tracking=True,
        compute="_compute_pnt_output_weight_qty",
        store=True,
    )
    pnt_product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
    )
    pnt_certificate_number = fields.Char(
        string="N Cert",
    )
    name = fields.Text(
        string="Description",
        required=True,
        compute="compute_pnt_product_id",
        store=True,
        readonly=False,
    )
    pnt_customer_name = fields.Char(
        name="Customer description",
        compute="_compute_description_line",
        store=True,
        readonly=False,
    )
    pnt_supplier_name = fields.Char(
        name="Supplier description",
        compute="_compute_description_line",
        store=True,
        readonly=False,
    )
    pnt_description_line = fields.Char(
        string="Description for documents",
        compute="_compute_description_line",
        store=True,
        readonly=False,
    )
    company_id = fields.Many2one(
        related="pnt_single_document_id.company_id",
        string="Company",
        store=True,
        readonly=True,
        index=True,
    )
    pnt_product_waste_id = fields.Many2one(
        string="Wastes",
        comodel_name="product.product",
    )
    pnt_domain_product_waste_ids = fields.Many2many(
        string="Wastes",
        comodel_name="product.product",
        compute="_compute_pnt_domain_product_waste_ids",
    )
    pnt_fleet_vehicle_category_ids = fields.Many2many(
        string="Vehicle category",
        comodel_name="pnt.fleet.vehicle.category",
        relation="pnt_single_document_line_vehicle_category_rel",
        column1="pnt_single_document_line_id",
        column2="pnt_fleet_vehicle_category_id",
    )
    pnt_product_container_ids = fields.Many2many(
        string="Containers",
        comodel_name="product.product",
        relation="pnt_single_document_line_product_container_rel",
        column1="pnt_single_document_line_id",
        column2="product_id",
        domain=[("pnt_is_container", "=", True)],
    )
    pnt_partner_delivery_id = fields.Many2one(
        string="Partner delivery",
        comodel_name="res.partner",
        readonly=False,
        domain=[
            ("type", "=", "delivery"),
        ],
    )
    pnt_scales_record_id = fields.Many2one(
        comodel_name="pnt.scales.record",
        string="Scales record",
        readonly=False,
        copy=False,
    )
    pnt_container_movement_id = fields.Many2one(
        comodel_name="pnt.container.movement",
        string="Container movement",
        readonly=False,
        copy=False,
    )
    pnt_agreement_line_id = fields.Many2one(
        string="Agreement Line",
        comodel_name="pnt.agreement.line",
    )
    pnt_rental = fields.Boolean(
        related="pnt_product_id.pnt_rental",
    )
    pnt_line_rental_done = fields.Selection(
        string="Line Rental Sale",
        selection=[
            ("0", "Unset"),
            ("1", "Started"),
            ("2", "Finished"),
        ],
        required=True,
        default="0",
    )
    pnt_task_flag = fields.Boolean(string="Task flag", compute="_compute_pnt_task_flag")
    pnt_task_ids = fields.One2many(
        "project.task",
        "pnt_sd_line_id",
        "Tasks",
    )
    pnt_waste_transfer_document_id = fields.Many2one(
        comodel_name="pnt.waste.transfer.document",
        string="DI",
        copy=False,
    )
    pnt_m3 = fields.Float(
        string="M3",
        compute="_compute_pnt_m3",
        store=True,
        readonly=False,
        digits="Product Unit of Measure",
    )
    pnt_carrier_id = fields.Many2one(
        string="Carrier",
        related="pnt_single_document_id.pnt_carrier_id",
        store=True,
    )
    pnt_vehicle_id = fields.Many2one(
        related="pnt_single_document_id.pnt_vehicle_id",
        store=True,
    )
    pnt_license_plate = fields.Char(
        string="Plate",
        compute="_compute_pnt_license_plate",
        store=True,
    )

    @api.depends("pnt_agreement_line_id", "pnt_vehicle_id")
    def _compute_pnt_license_plate(self):
        for record in self:
            record.pnt_license_plate = record.pnt_vehicle_id.license_plate

    @api.depends("pnt_agreement_line_id")
    def _compute_pnt_m3(self):
        for record in self:
            record.pnt_m3 = record.pnt_agreement_line_id.pnt_m3

    @api.depends(
        "pnt_single_document_id.state",
        "pnt_product_uom_qty",
        "pnt_single_document_id.pnt_force_in_final_manager",
    )
    def _compute_pnt_output_weight_qty(self):
        for record in self:
            if record.pnt_single_document_id.state in (
                "received",
                "finished",
            ) and record.pnt_single_document_type in ("output",):
                if (
                    record.pnt_single_document_id.state in ("received",)
                    and not record.pnt_single_document_id.pnt_force_in_final_manager
                ):
                    record.pnt_output_weight_qty = record.pnt_product_uom_qty
            else:
                record.pnt_output_weight_qty = 0.0

    @api.depends("pnt_product_id", "pnt_agreement_line_id")
    def _compute_description_line(self):
        for line in self:
            if line.pnt_agreement_line_id:
                line.pnt_customer_name = line.pnt_agreement_line_id.pnt_customer_name
                line.pnt_supplier_name = line.pnt_agreement_line_id.pnt_supplier_name
                line.pnt_description_line = (
                    line.pnt_agreement_line_id.pnt_description_line)
            else:
                line.pnt_customer_name = line.pnt_product_id.display_name
                line.pnt_supplier_name = line.pnt_product_id.display_name
                line.pnt_description_line = line.pnt_product_id.display_name

    @api.depends("pnt_product_id", "pnt_agreement_line_id", "pnt_container_id")
    def _compute_pnt_domain_product_waste_ids(self):
        obj_agree_line = self.env["pnt.agreement.line"]
        self.pnt_domain_product_waste_ids = [(6, False, [])]
        for record in self:
            if not record.pnt_container_id:
                continue
            agreement_lines = obj_agree_line.search(
                [
                    ("pnt_agreement_id", "=", record.pnt_agreement_id.id),
                    "|",
                    (
                        "pnt_partner_pickup_id",
                        "=",
                        record.pnt_single_document_id.pnt_partner_pickup_id.id,
                    ),
                    ("pnt_partner_pickup_id", "=", False),
                ]
            )
            waste_ids = (
                agreement_lines.filtered(
                    lambda x, container=record.pnt_container_id.id: x.pnt_container_id.id
                    == container
                )
                .pnt_product_id.filtered("pnt_is_waste")
                .ids
            )
            record.pnt_domain_product_waste_ids = [(6, False, waste_ids)]

    @api.depends("pnt_product_id")
    def compute_pnt_product_id(self):
        for record in self:
            if record.pnt_product_id:
                trobat = False
                agreement_lines = (
                    self.env["pnt.agreement.agreement"]
                    .search([("id", "=", record.pnt_agreement_id.id)], limit=1)
                    .pnt_agreement_line_ids
                )
                if record.pnt_single_document_id.pnt_single_document_type not in (
                    "portal",
                    "metal",
                ):
                    if agreement_lines:
                        for line in agreement_lines:
                            if (
                                line.pnt_product_id == record.pnt_product_id
                                and line.pnt_monetary_waste
                            ):
                                if not trobat:
                                    record.pnt_monetary_waste = line.pnt_monetary_waste
                                    trobat = True

                        if not trobat:
                            record.pnt_monetary_waste = (
                                record.pnt_product_id.pnt_monetary_waste or False
                            )
                else:
                    if (
                        record.pnt_single_document_id.pnt_partner_pickup_id.pnt_portal_agreement_specific_id
                    ):
                        for (
                            linespecific
                        ) in (
                            record.pnt_single_document_id.pnt_partner_pickup_id.pnt_portal_agreement_specific_id.pnt_agreement_line_ids
                        ):
                            if (
                                linespecific.pnt_product_id == record.pnt_product_id
                                and linespecific.pnt_monetary_waste
                            ):
                                if not trobat:
                                    record.pnt_monetary_waste = (
                                        linespecific.pnt_monetary_waste
                                    )
                                    trobat = True
                    if not trobat:
                        for line in agreement_lines:
                            if (
                                line.pnt_product_id == record.pnt_product_id
                                and line.pnt_monetary_waste
                                and not trobat
                            ):
                                record.pnt_monetary_waste = line.pnt_monetary_waste
                                trobat = True
                    if not trobat:
                        record.pnt_monetary_waste = (
                            record.pnt_product_id.pnt_monetary_waste or False
                        )
                record.name = record.pnt_product_id.display_name
                record.pnt_product_uom = record.pnt_product_id.uom_id.id

    def get_lines_agreement(self, du_pickup):
        obj_agreement_line = self.env["pnt.agreement.line"]
        domain = [
            ("pnt_product_id", "=", self.pnt_product_id.id),
            ("pnt_agreement_id", "=", self.pnt_agreement_id.id),
        ]
        new_domain = domain + [("pnt_partner_pickup_id", "=", du_pickup.id)]
        lines_agreement = obj_agreement_line.search(new_domain)
        if not lines_agreement:
            new_domain = domain + [("pnt_partner_pickup_id", "=", False)]
            lines_agreement = obj_agreement_line.search(new_domain)
        return lines_agreement

    def get_lines_agreement_with_pricelist(self, lines_agreement):
        return lines_agreement.filtered("pnt_according_market_price")

    def get_lines_pricelist_agreement_market(self, lines_pricelist):
        container = self.pnt_container_id.id or lines_pricelist.pnt_container_id.id
        partner = self.pnt_single_document_id.pnt_holder_id
        domain = [
            None,
            ("pnt_product_id", "=", self.pnt_product_id.id),
            ("pnt_container_id", "=", container),
            ("pnt_container_id", "!=", False),
            ("pnt_agreement_id", "!=", False),
        ]
        obj_agreement_line = self.env["pnt.agreement.line"]
        agreement = partner.pnt_portal_agreement_specific_id
        if agreement:
            domain[0] = ("pnt_agreement_id", "=", agreement.id)
            lines = obj_agreement_line.search(domain)
            if lines:
                return lines
        agreement = partner.pnt_portal_agreement_type_id
        if agreement:
            domain[0] = ("pnt_agreement_id", "=", agreement.id)
            lines = obj_agreement_line.search(domain)
            if lines:
                return lines
        agreement = self.env["pnt.agreement.agreement"].search(
            [
                ("pnt_is_market_price", "=", True),
                ("company_id", "=", self.env.company.id),
            ],
            limit=1,
        )
        domain[0] = ("pnt_agreement_id", "=", agreement.id)
        return obj_agreement_line.search(domain)

    def get_desc_lines(self, lines_agreement):
        return "".join(
            [
                _("\nProduct: %s; container: %s; pickup: %s")
                % (
                    x.pnt_product_id.display_name or "",
                    x.pnt_container_id.display_name or "",
                    x.pnt_partner_pickup_id.display_name or "",
                )
                for x in lines_agreement
            ]
        )

    def get_price_lines_pricelist(self, lines_pricelist):
        lines_market = self.get_lines_pricelist_agreement_market(lines_pricelist)
        if not lines_market:
            return ["ERROR_NOT_LINES", False]
        if len(lines_market) > 1:
            return ["ERROR_MULTI_LINES", False]
        return [lines_market.pnt_price_unit, lines_market]

    def get_price_lines(self, ttype, agreement=False):
        for du in self:
            du_pickup = du.pnt_single_document_id.pnt_partner_pickup_id.id
            if ttype == "product":
                ffield = "pnt_container_id"
                value = du.pnt_container_id.id
            else:
                ffield = "pnt_product_waste_id"
                value = du.pnt_product_waste_id.id
            lines = self.env["pnt.agreement.line"].search(
                [
                    ("pnt_agreement_id", "=", du.pnt_agreement_id.id),
                    "|",
                    ("pnt_partner_pickup_id", "=", du_pickup),
                    ("pnt_partner_pickup_id", "=", False),
                    "|",
                    (ffield, "=", value),
                    "&",
                    ("pnt_product_id", "=", du.pnt_product_id.id),
                    ("pnt_product_id.type", "=", ttype),
                ]
            )
            if agreement:
                lines = lines.filtered(
                    lambda x: x.pnt_product_id.id == du.pnt_product_id.id
                )
                return lines.sorted("pnt_price_unit", True)[:1]
            if not lines:
                return ["ERROR_NOT_LINES"]
            lines = lines.filtered(
                lambda x: x.pnt_product_id.id == du.pnt_product_id.id
            )
            return [lines.sorted("pnt_price_unit", True)[0].pnt_price_unit]

    def get_price_lines_portal_metal(self):
        # Programación para otros tipos de contrato (original de Tolo)
        price = 0
        line_agree = False
        pickup = self.pnt_single_document_id.pnt_partner_pickup_id
        for line in pickup.pnt_portal_agreement_specific_id.pnt_agreement_line_ids:
            if line.pnt_product_id == self.pnt_product_id:
                price = line.pnt_price_unit
                line_agree = line
                break
        for line in self.pnt_agreement_id.pnt_agreement_line_ids:
            if line.pnt_product_id == self.pnt_product_id:
                price = line.pnt_price_unit
                line_agree = line
                # # Comprobar si te contracte especific
                # if self.pnt_single_document_id.pnt_single_document_type == 'portal':
                #     if self.pnt_single_document_id.pnt_partner_pickup_id:
                #         portal_specific = (self.pnt_single_document_id
                #                            .pnt_partner_pickup_id
                #                            .pnt_portal_agreement_specific_id)
                #         if (portal_specific and portal_specific.state == 'done'):
                #             agree_line_specific = (
                #                       portal_specific.pnt_agreement_line_ids.filtered(
                #                             lambda x: x.pnt_product_id
                #                             == self.pnt_product_id
                #                 )
                #             )
                #             if agree_line_specific:
                #                 price = agree_line_specific[0].pnt_price_unit
                #                 line_agree = agree_line_specific[0]
                break
        return price, line_agree

    @api.depends(
        "pnt_product_id",
        "pnt_container_id",
        "pnt_product_waste_id",
    )
    def compute_pnt_price_unit(self):
        self.pnt_m3 = 0
        self.pnt_agreement_line_id = False
        self.pnt_price_unit = 0
        for line in self.filtered("pnt_product_id"):
            if line.pnt_single_document_id.pnt_single_document_type not in (
                "internal",
            ):
                if line.pnt_single_document_id.pnt_single_document_type in (
                    "portal",
                    "metal",
                ):
                    (
                        line.pnt_price_unit,
                        line.pnt_agreement_line_id,
                    ) = line.get_price_lines_portal_metal()
                    continue
                du_product = line.pnt_product_id
                du_container = line.pnt_container_id
                du_waste = line.pnt_product_waste_id
                du_pickup = line.pnt_single_document_id.pnt_partner_pickup_id
                lines_agreement = line.get_lines_agreement(du_pickup)
                if not lines_agreement:
                    raise UserError(
                        _(
                            "No contract lines have been found for product %(product)s.",
                            product=du_product.display_name or "",
                        )
                    )
                lines_pricelist = line.get_lines_agreement_with_pricelist(
                    lines_agreement
                )
                # Precio tarifa
                if lines_pricelist:
                    lines_agreement_f = lines_agreement.filtered(
                        lambda x, container=du_container: x.pnt_container_id
                        == container
                    )
                    if lines_agreement_f and (
                        len(lines_agreement_f) > 1 or len(lines_pricelist) > 1
                    ):
                        raise UserError(
                            _(
                                "There are identical products with a market fee and others "
                                "without a market fee."
                            )
                        )
                    price, line.pnt_agreement_line_id = self.get_price_lines_pricelist(
                        lines_pricelist
                    )
                    if price == "ERROR_NOT_LINES":
                        raise UserError(
                            _(
                                "No contract lines have been found for product "
                                "%(product)s.",
                                product=self.pnt_product_id.display_name or "",
                            )
                        )
                    if price == "ERROR_MULTI_LINES":
                        msg = self.get_desc_lines(price[1])
                        raise UserError(_("More than one line has been found:%s") % msg)
                    line.pnt_price_unit = price
                    continue
                # Precio envase y alquileres
                if (du_container or du_waste) and du_product.type in (
                    "product",
                    "service",
                ):
                    lines_agreement_filter = lines_agreement.filtered(
                        lambda x, ttype=du_product.type: x.pnt_product_id.type == ttype
                    )
                    if du_product.type == "product":
                        lines_agreement_f = lines_agreement_filter.filtered(
                            lambda x, container=du_container.id: x.pnt_container_id
                            and x.pnt_container_id.id == container
                        )
                        if not lines_agreement_f:
                            lines_agreement_f = lines_agreement_filter.filtered(
                                lambda x: not x.pnt_container_id
                            )
                        if du_waste and len(lines_agreement_f) > 1:
                            lines_agreement_f = lines_agreement_f.filtered(
                                lambda x, waste=du_waste.id: x.pnt_product_waste_id.id
                                in (waste, False)
                            )
                    else:
                        lines_agreement_f = lines_agreement_filter.filtered(
                            lambda x, waste=du_waste.id: x.pnt_product_waste_id
                            and x.pnt_product_waste_id.id == waste
                        )
                        if not lines_agreement_f:
                            lines_agreement_f = lines_agreement_filter.filtered(
                                lambda x: not x.pnt_product_waste_id
                            )
                        if du_container and len(lines_agreement_f) > 1:
                            lines_agreement_f = lines_agreement_f.filtered(
                                lambda x, container=du_container.id: x.pnt_container_id.id
                                in (container, False)
                            )
                    if len(lines_agreement_f) > 1:
                        msg = self.get_desc_lines(lines_agreement_f)
                        raise UserError(_("More than one line has been found:%s") % msg)
                    if len(lines_agreement_f) == 1:
                        line.pnt_price_unit = lines_agreement_f.pnt_price_unit
                        line.pnt_agreement_line_id = lines_agreement_f
                        continue
                    price = self.get_price_lines(du_product.type)
                    if price[0] == "ERROR_NOT_LINES":
                        raise UserError(
                            _(
                                "No contract lines have been found for product "
                                "%(product)s.",
                                product=self.pnt_product_id.display_name or "",
                            )
                        )
                    lines = line.get_price_lines(du_product.type, agreement=True)
                    line.pnt_price_unit = price[0]
                    line.pnt_agreement_line_id = lines
                    continue
                # Otros casos no contemplados
                if len(lines_agreement) == 1:
                    line.pnt_price_unit = lines_agreement.pnt_price_unit
                    line.pnt_agreement_line_id = lines_agreement
                # Control lineas duplicadas en contratos para envases
                elif len(lines_agreement) > 1 and line.pnt_product_id.pnt_is_container:
                    msg = self.get_desc_lines(lines_agreement)
                    raise UserError(_("More than one line has been found:%s") % msg)

    @api.depends("pnt_price_unit", "pnt_product_economic_uom_qty")
    def compute_pnt_price_subtotal(self):
        for record in self:
            record.pnt_price_subtotal = (
                record.pnt_product_economic_uom_qty * record.pnt_price_unit
            )

    @api.depends("pnt_product_id", "pnt_agreement_line_id")
    def _get_authorized_containers_domain_ids(self):
        self.authorized_containers_domain_ids = [(6, False, [])]
        for record in self:
            if record.pnt_product_id.type != "service" and not record.pnt_is_waste:
                self.authorized_containers_domain_ids = [(6, False, [])]
                continue
            du_pickup = record.pnt_single_document_id.pnt_partner_pickup_id
            agree_lines = record.pnt_agreement_id.pnt_agreement_line_ids
            agree_lines = agree_lines.filtered(
                lambda x, pickup=du_pickup: x.pnt_partner_pickup_id.id
                in (pickup.id, False)
            )
            agree_container_ids = agree_lines.pnt_product_id.filtered(
                "pnt_is_container"
            ).ids
            product_container_ids = (
                record.pnt_product_id.pnt_product_tmpl_container_ids.ids
            )
            product_container_ids = (
                self.env["product.product"]
                .search([("product_tmpl_id", "in", product_container_ids)])
                .ids
            )
            if (
                record.pnt_product_id.type == "service"
                and record.pnt_product_id.pnt_rental
            ):
                final_containers = agree_lines.filtered(
                    lambda x, product=record.pnt_product_id.id: x.pnt_product_id.id
                    == product
                ).pnt_container_id.ids
            else:
                container_rental_ids = agree_lines.filtered(
                    lambda x: x.pnt_product_id.type == "service"
                    and x.pnt_product_id.pnt_rental
                ).pnt_container_id.ids
                final_containers = list(
                    set(agree_container_ids + container_rental_ids)
                    & set(product_container_ids)
                )
                if (
                    record.pnt_agreement_line_id.pnt_container_id
                    and record.pnt_agreement_line_id.pnt_container_id
                    == record.company_id.pnt_agreement_bulk_product_id
                ):
                    final_containers += (
                        record.company_id.pnt_agreement_bulk_product_id.ids
                    )
            # Tolo - 10/06/2024 - Si no hi ha GRANEL a la llista aquí s'afageix
            # perque sempre estigui disponible el GRANEL encara que aquest no estigui
            # al contracte
            if (record.company_id.pnt_agreement_bulk_product_id.id
                not in final_containers
                    and self.pnt_exist_bulk_container_in_agreement()):
                final_containers += (
                    record.company_id.pnt_agreement_bulk_product_id.ids
                )
            record.authorized_containers_domain_ids = [(6, False, final_containers)]

    def pnt_exist_bulk_container_in_agreement(self):
        # Tolo - 10/06/2024 - comproba si existeix la combinació producte/granel al
        # contracte
        for record in self:
            result = False
            lines = (record.pnt_single_document_id.pnt_agreement_id
                     .pnt_agreement_line_ids.filtered(
                lambda x: x.pnt_product_id == record.pnt_product_id and
                   x.pnt_container_id == record.company_id.pnt_agreement_bulk_product_id
                ))
            if lines:
                result = True
            return result

    @api.onchange("pnt_product_id", "pnt_agreement_line_id")
    def onchange_pnt_product_id(self):
        if self.pnt_single_document_type == "internal":
            if self.pnt_product_id.pnt_is_waste:
                self.pnt_container_id = self.env.company.pnt_agreement_bulk_product_id
        else:
            if (
                self.pnt_single_document_id.pnt_partner_delivery_id
                and not self.pnt_partner_delivery_id
            ):
                self.pnt_partner_delivery_id = (
                    self.pnt_single_document_id.pnt_partner_delivery_id
                )
            if not self.pnt_is_waste and self.pnt_product_id:
                self.pnt_product_uom_qty = 1
            if self.pnt_product_type == "service" and self.pnt_rental:
                return
            if (
                self.pnt_product_id.type == "service"
                and self.pnt_product_id.pnt_rental
                or (
                    self.pnt_agreement_line_id.pnt_container_id.id
                    in (
                        self.authorized_containers_domain_ids.ids
                        + self.company_id.pnt_agreement_bulk_product_id.ids
                    )
                )
            ):
                self.pnt_container_id = self.pnt_agreement_line_id.pnt_container_id

    @api.onchange("pnt_product_uom_qty")
    def onchange_pnt_product_uom_qty(self):
        if self.pnt_product_uom_qty > 0:
            if self.pnt_agreement_line_id:
                uom_category = self.pnt_agreement_line_id.pnt_product_economic_uom
            else:
                uom_category = self.pnt_product_economic_uom
            if uom_category.category_id.name == "Peso":
                if uom_category.pnt_use_marpol_m3:
                    # if self.pnt_m3 > 0.0 and uom_category.pnt_use_marpol_m3:
                    self.pnt_product_economic_uom_qty = self.pnt_m3
                else:
                    if uom_category == self.pnt_product_uom:
                        self.pnt_product_economic_uom_qty = self.pnt_product_uom_qty
                    else:
                        self.pnt_product_economic_uom_qty = (
                            self.pnt_product_uom._compute_quantity(
                                self.pnt_product_uom_qty, uom_category
                            )
                        )
            else:
                if self.pnt_product_uom.category_id.name != "Peso":
                    self.pnt_container_qty = self.pnt_product_uom_qty
                    self.pnt_product_economic_uom_qty = self.pnt_product_uom_qty
                    self.pnt_product_uom_qty = 0
                else:
                    self.pnt_product_economic_uom_qty = self.pnt_container_qty

    @api.onchange("pnt_m3")
    def onchange_pnt_m3(self):
        # if self.pnt_m3 > 0.0:
        if self.pnt_agreement_line_id:
            uom_category = self.pnt_agreement_line_id.pnt_product_economic_uom
        else:
            uom_category = self.pnt_product_economic_uom
        if uom_category.category_id.name == "Peso" and uom_category.pnt_use_marpol_m3:
            self.pnt_product_economic_uom_qty = self.pnt_m3

    @api.onchange("pnt_container_qty","pnt_agreement_line_id")
    def onchange_pnt_container_qty(self):
        if self.pnt_agreement_line_id:
            uom_category = self.pnt_agreement_line_id.pnt_product_economic_uom
        else:
            uom_category = self.pnt_product_economic_uom
        if uom_category and uom_category.category_id.name not in ("Peso"):
            self.pnt_product_economic_uom_qty = self.pnt_container_qty
        elif uom_category and uom_category.category_id.name in ("Peso"):
            self.pnt_product_economic_uom_qty = self.pnt_product_uom_qty

    def scale_read(self):
        if not self.env.company.pnt_scale_host:
            raise UserError(
                _("Debe indicar una dirección IP para la báscula en configuración")
            )
        if not self.env.company.pnt_scale_port:
            raise UserError(
                _("Debe indicar un puerto para la báscula en configuración")
            )
        host = self.env.company.pnt_scale_host
        port = self.env.company.pnt_scale_port
        try:
            telnet_client = telnetlib.Telnet(host, port)
            pes = None
            telnet_client.write(b"$")
            pes = telnet_client.read_some()
            pesnumeric = int("".join(filter(str.isdigit, str(pes).split("x01", 1)[-1])))
            if pes:
                # raise UserError(_('El peso es: ' + str(pesnumeric) + 'kg'))
                self.pnt_product_uom_qty = pesnumeric
                self.onchange_pnt_product_uom_qty()
            else:
                raise UserError(
                    _("No puede leerse el peso. Revise si está conectada la báscula")
                )
            telnet_client.write(b"exit")
        except socket.error as msg:
            raise UserError(
                _(
                    "No puede leerse el peso. Revise si la báscula está conectada - "
                    + str(msg)
                )
            )

    def scale_record(self):
        # pnt_scales_record_id
        # Si no existe: Crear registro báscula y asignarlo a linea DU
        if not self.pnt_scales_record_id:
            sr = self._pnt_scales_record_create()
        else:
            if (
                self.pnt_single_document_id.pnt_last_weighing_qty > 0
                and self.pnt_scales_record_id.pnt_first_weighing_qty == 0.0
            ):
                self.pnt_scales_record_id.pnt_first_weighing_qty = (
                    self.pnt_single_document_id.pnt_last_weighing_qty
                )
        return {
            "res_model": "pnt.scales.record",
            "type": "ir.actions.act_window",
            "context": {},
            "view_mode": "form",
            "view_type": "form",
            "view_id": self.env.ref("custom_pnt.pnt_scales_record_form_view").id,
            "res_id": self.pnt_scales_record_id.id,
            "target": "new",
        }

    def scale_record_metal(self):
        # pnt_scales_record_id
        # Si no existe: Crear registro báscula y asignarlo a linea DU
        if self.pnt_single_document_id.state in ("dispached",):
            if not self.pnt_scales_record_id:
                sr = self._pnt_scales_record_create()
            else:
                if (
                    self.pnt_single_document_id.pnt_last_weighing_qty > 0
                    and self.pnt_scales_record_id.pnt_first_weighing_qty == 0.0
                ):
                    self.pnt_scales_record_id.pnt_first_weighing_qty = (
                        self.pnt_single_document_id.pnt_last_weighing_qty
                    )
            return {
                "res_model": "pnt.scales.record",
                "type": "ir.actions.act_window",
                "context": {},
                "view_mode": "form",
                "view_type": "form",
                "view_id": self.env.ref("custom_pnt.pnt_scales_record_form_view").id,
                "res_id": self.pnt_scales_record_id.id,
                "target": "new",
            }
        else:
            raise UserError(_("No pueden agregarse pesadas a un DU ya procesado"))

    def container_movement(self):
        if self.pnt_product_id.categ_id.id == 24:
            if not self.pnt_container_movement_id:
                sr = self._pnt_container_movement_create()
            return {
                "res_model": "pnt.container.movement",
                "type": "ir.actions.act_window",
                "context": {},
                "view_mode": "form",
                "view_type": "form",
                "view_id": self.env.ref(
                    "custom_pnt.pnt_container_movement_form_view"
                ).id,
                "res_id": self.pnt_container_movement_id.id,
                "target": "new",
            }
        else:
            return False

    def delete_line(self):
        if self.pnt_single_document_id.state in ("dispached",):
            self.unlink()
        else:
            raise UserError(_("No pueden eliminarse pesadas a un DU ya procesado"))

    def _pnt_scales_record_create_prepare_values(self):
        self.ensure_one()
        return {
            "pnt_single_document_line_id": self.id,
            "pnt_first_weighing_qty": self.pnt_single_document_id.pnt_last_weighing_qty,
        }

    def _pnt_container_movement_create_prepare_values(self):
        self.ensure_one()
        return {
            "pnt_single_document_line_id": self.id,
            "pnt_container_movement_type": self.pnt_product_id.pnt_container_movement_type,
        }

    def _pnt_scales_record_create(self):
        values = self._pnt_scales_record_create_prepare_values()
        sr = self.env["pnt.scales.record"].sudo().create(values)
        self.pnt_scales_record_id = sr
        return sr

    def update_quantities_picking(self, vals):
        if "pnt_product_uom_qty" not in vals:
            return
        for record in self.filtered(
            lambda x: x.pnt_single_document_id.state == "received"
        ):
            pickings = record.pnt_single_document_id.pnt_stock_picking_ids.filtered(
                lambda x: x.state in ["assigned", "confirmed"]
            )
            lines = [
                x.id
                for x in pickings.move_ids_without_package
                if x.pnt_single_document_line_id == record
            ]
            for line in self.env["stock.move"].browse(lines):
                if len(line.move_line_ids) > 1:
                    raise UserError(
                        _(
                            "Delivery note with more than one line in detailed "
                            "operations."
                        )
                    )
                unlocked = False
                if line.picking_id.is_locked:
                    line.picking_id.action_toggle_is_locked()
                    unlocked = True
                line.product_uom_qty = (
                    line.pnt_single_document_line_id.pnt_product_uom_qty
                )
                if line.move_line_ids:
                    line.move_line_ids.qty_done = (
                        line.pnt_single_document_line_id.pnt_product_uom_qty
                    )
                if unlocked:
                    line.picking_id.action_toggle_is_locked()
    def update_weight_scale_record(self,vals):
        if "pnt_product_uom_qty" not in vals:
            return
        for record in self.filtered(
            lambda x: x.pnt_scales_record_id):
            if vals.get("pnt_product_uom_qty") != 0.0:
                if not record.pnt_single_document_id.pnt_partner_delivery_id.parent_id:
                    partner_delivery = record.pnt_single_document_id.pnt_partner_delivery_id
                else:
                    partner_delivery = (
                        record.pnt_single_document_id.pnt_partner_delivery_id.parent_id
                    )
                if (
                    partner_delivery == self.env.company.partner_id
                ):
                    record.pnt_scales_record_id.pnt_second_weighing_qty = (
                            record.pnt_scales_record_id.pnt_first_weighing_qty
                            -
                            vals.get("pnt_product_uom_qty"))
                else:
                    record.pnt_scales_record_id.pnt_first_weighing_qty = (
                            record.pnt_scales_record_id.pnt_second_weighing_qty
                            -
                            vals.get("pnt_product_uom_qty"))

    def write(self, vals):
        res = super().write(vals)
        self.update_quantities_picking(vals)
        # self.update_weight_scale_record(vals)
        return res
    def pnt_check_du_lines_in_di(self,du):
        if du:
            di_ids = self.env["pnt.waste.transfer.document"].search([
                ("pnt_single_document_id","=",du),
                ("pnt_legal_code_hist","!=",False)
            ])
        for di in di_ids:
            if (di.pnt_single_document_id and not di.pnt_single_document_line_ids
                and di.pnt_legal_code_hist):
                # di.pnt_legal_code_hist = lc
                # di.pnt_product_id_hist = prod
                di.active = False

    def unlink(self):
        for record in self:
            current_di = record.pnt_waste_transfer_document_id
            current_du = self.pnt_single_document_id.id
            if current_di:
                current_di.pnt_legal_code_hist = current_di.pnt_legal_code
                current_di.pnt_product_id_hist = current_di.pnt_product_id
        res = super().unlink()
        if current_di:
            self.pnt_check_du_lines_in_di(current_du)
        return res
    def _pnt_container_movement_create(self):
        values = self._pnt_container_movement_create_prepare_values()
        sr = self.env["pnt.container.movement"].sudo().create(values)
        self.pnt_container_movement_id = sr
        return sr

    def _pnt_prepare_task_values(self, project_id):
        du = self.pnt_single_document_id
        waste = [(6, False, [])]
        product_waste_manipulation = self.env["product.product"].search(
            [("pnt_is_waste_manipulation", "=", True)], limit=1
        )
        if product_waste_manipulation:
            waste = [
                (
                    0,
                    0,
                    {
                        "pnt_waste_id": product_waste_manipulation.id,
                        "pnt_weight": 1,
                    },
                )
            ]
        if du.pnt_single_document_type in ("output",):
            default_user = du.pnt_scales_id.pnt_manager_responsible_id
        else:
            default_user = du.pnt_scales_id.pnt_responsible_id
        return {
            "default_name": (
                "%s | %s"
                % (self.pnt_agreement_id.name, self.pnt_agreement_id.pnt_holder_id.name)
            ),
            "default_project_id": project_id.id,
            "default_partner_id": du.pnt_holder_id.id,
            "default_date_deadline": du.pnt_pickup_date,
            "default_pnt_single_document_id": du.id,
            "default_pnt_sd_line_id": self.id,
            "default_pnt_input_weight": self.pnt_product_uom_qty,
            "default_user_id": default_user.id or self.env.user.id,
            "default_pnt_du_visible": True,
            "default_pnt_waste_reclassified_ids": waste,
        }

    def pnt_action_create_new_issue(self):
        project_id = self.company_id.pnt_single_document_issue_project_id
        if not project_id:
            raise UserError(
                _(
                    """Not project assigned in configuration.
                    Contact the administration."""
                )
            )
        ctx = dict(self._context)
        ctx.update(self._pnt_prepare_task_values(project_id))
        view_id = self.env.ref("project.view_task_form2").id
        return {
            "type": "ir.actions.act_window",
            "name": "Issue",
            "view_type": "form",
            "view_mode": "form",
            "view_id": view_id,
            "res_model": "project.task",
            "flags": {"mode": "edit"},
            "context": ctx,
        }

    @api.depends("pnt_single_document_id.state", "pnt_task_ids")
    def _compute_pnt_task_flag(self):
        for record in self:
            if record.pnt_single_document_type in ("marpol",):
                record.pnt_task_flag = False
            else:
                record.pnt_task_flag = (
                    True
                    if record.pnt_single_document_id.state in ("plant", "received")
                    and not record.pnt_task_ids
                    and record.pnt_product_id.pnt_is_waste
                    else False
                )

    @api.depends("pnt_product_id", "pnt_agreement_line_id")
    def _compute_pnt_product_economic_uom(self):
        for record in self:
            if record.pnt_agreement_line_id:
                record.pnt_product_economic_uom = (
                    record.pnt_agreement_line_id.pnt_product_economic_uom
                )
            else:
                record.pnt_product_economic_uom = record.pnt_product_id.uom_id

    ### ISSUE ###


class PntSingleDocumentHolderLine(models.Model):
    _name = "pnt.single.document.holder.portal"
    _description = "Pnt Single Document Holder Portal"
    _order = "pnt_single_document_id, sequence, id"
    _check_company_auto = True

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single Document Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    state = fields.Selection(
        related="pnt_single_document_id.state",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    pnt_monetary_waste = fields.Selection(
        string="Monetary Waste",
        selection=[
            ("inbound", "Inbound"),
            ("outbound", "Outbound"),
            ("inout", "Inbound/Outbound"),
        ],
        store=True,
        readonly=False,
        default="inout",
    )
    pnt_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
        domain=[
            ("is_company", "=", True),
        ],
    )
    pnt_percent = fields.Float(
        string="Percent",
        default=100,
    )
    company_id = fields.Many2one(
        related="pnt_single_document_id.company_id",
        string="Company",
        store=True,
        readonly=True,
        index=True,
    )
