from datetime import datetime, timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tests import Form
from odoo.tools.misc import format_date


class PntAgreementAgreement(models.Model):
    _name = "pnt.agreement.agreement"
    _description = "Pnt Agreement Agreement"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]
    _order = "pnt_end_date desc, pnt_complete_name"
    _check_company_auto = True
    _parent_name = "pnt_parent_agreement_id"
    _parent_store = True
    _rec_name = "pnt_complete_name"

    name = fields.Char(
        string="Agreement",
        required=True,
        copy=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        index=True,
        default=lambda self: _("New"),
    )
    pnt_agreement_type = fields.Selection(
        [
            ("portal", _("Portal general")),
            ("portali", _("Portal individual")),
            ("manager", _("Gestor")),
            ("marpol", _("Marpol")),
            ("others", _("Others")),
        ],
        string="Agreement type",
        readonly=True,
        copy=True,
        index=True,
        tracking=3,
        default="others",
    )
    pnt_description = fields.Char(
        string="Description",
    )
    pnt_is_market_price = fields.Boolean(
        string="Es precio mercado?",
        default=False,
        copy=False,
        readonly=True,
    )
    pnt_complete_name = fields.Char(
        "Complete Name",
        compute="_compute_complete_name",
        store=True,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_holder_id = fields.Many2one(
        string="Holder",
        comodel_name="res.partner",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        readonly=True,
        store=True,
        domain=[
            ("company_type", "=", "company"),
        ],
        copy=True,
        compute="compute_pnt_parent_agreement_id",
    )
    pnt_parent_partner_pickup_ids = fields.Many2many(
        string="Related Pickup",
        related="pnt_parent_agreement_id.pnt_partner_pickup_ids",
    )
    pnt_opportunity_id = fields.Many2one(
        comodel_name="crm.lead",
        string="Opportunity",
        check_company=True,
        domain="[('type', '=', 'opportunity'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    pnt_partner_pickup_id = fields.Many2one(
        string="Partner pickup",
        comodel_name="res.partner",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_parent_agreement_id = fields.Many2one(
        string="Parent agreement",
        comodel_name="pnt.agreement.agreement",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        index=True,
        readonly=True,
        store=True,
    )
    pnt_child_ids = fields.One2many(
        string="Childs agreement",
        comodel_name="pnt.agreement.agreement",
        inverse_name="pnt_parent_agreement_id",
    )
    pnt_child_all_count = fields.Integer(
        string="Indirect Agreement Count",
        compute="_compute_pnt_inheritance",
        store=False,
        compute_sudo=True,
    )
    pnt_inheritance_ids = fields.One2many(
        comodel_name="pnt.agreement.agreement",
        string="Inheritance",
        compute="_compute_pnt_inheritance",
        help="Direct and indirect agreements",
        compute_sudo=True,
    )
    parent_path = fields.Char(
        index=True,
    )
    pnt_partner_pickup_domain_ids = fields.Many2many(
        comodel_name="res.partner",
        compute="_compute_pnt_domain_product_ids",
    )
    pnt_partner_pickup_ids = fields.Many2many(
        string="Partner pickups",
        comodel_name="res.partner",
        relation="pnt_agreement_partner_pickup_rel",
        column1="pnt_agreement_id",
        column2="partner_id",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_operator_id = fields.Many2one(
        string="Operator",
        comodel_name="res.partner",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        readonly=True,
        default=lambda self: self.env.company.partner_id.id,
    )
    pnt_date_budget = fields.Date(
        string="Budget Date",
    )
    state = fields.Selection(
        [
            ("draft", _("Quotation")),
            ("sent", _("Quotation Sent")),
            ("active", _("Active")),
            ("done", _("Locked")),
            ("finish", _("Finished")),
            ("to_renew", _("To Renew")),
            ("cancel", _("Cancelled")),
        ],
        string="State",
        readonly=True,
        copy=False,
        index=True,
        tracking=3,
        default="draft",
    )
    pnt_start_date = fields.Date(
        string="Start Date",
        index=True,
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_end_date = fields.Date(
        string="End Date",
        index=True,
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        copy=False,
    )
    pnt_activate_date = fields.Date(
        string="Activate Date",
        index=True,
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        copy=False,
    )
    pnt_transport_id = fields.Many2one(
        string="Driver",
        comodel_name="res.partner",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
        readonly=True,
    )
    pnt_user_id = fields.Many2one(
        "res.users",
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
    user_id = fields.Many2one(
        "res.users",
        related="pnt_user_id",
        store=True,
        readonly=True,
    )
    pnt_note = fields.Html(
        string="Terms and conditions",
        readonly=True,
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
        },
    )
    pnt_customer_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Customer Payment mode",
        check_company=True,
        compute="compute_pnt_holder_id",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
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
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
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
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
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
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
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
    pnt_auto_renewal = fields.Boolean(
        string="Auto renewal",
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
            "to_renew": [("readonly", False)],
        },
        copy=False,
        readonly=True,
        tracking=2,
    )
    pnt_agreement_line_ids = fields.One2many(
        comodel_name="pnt.agreement.line",
        inverse_name="pnt_agreement_id",
        string="Agreement Lines",
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "finish": [("readonly", True)],
            "active": [("readonly", False)],
        },
        copy=True,
        auto_join=True,
        domain=[("pnt_is_downpayment", "=", False)],
    )
    pnt_agreement_reference_ids = fields.One2many(
        comodel_name="pnt.agreement.reference",
        inverse_name="pnt_agreement_id",
        string="Reference/order",
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "finish": [("readonly", True)],
            "active": [("readonly", False)],
        },
        copy=True,
        auto_join=True,
    )
    pnt_general_conditions = fields.Html(
        string="General conditions",
        states={
            "cancel": [("readonly", True)],
            "done": [("readonly", True)],
            "finish": [("readonly", True)],
            "active": [("readonly", False)],
        },
    )
    pnt_treatment_date = fields.Date(
        string="Treatment date",
        required=False,
    )
    pnt_agreement_lot_ids = fields.One2many(
        "pnt.agreement.lot",
        "pnt_agreement_id",
        string="Lots",
        ondelete="cascade",
    )
    pnt_use_company_email = fields.Boolean(string="Use company email")
    pnt_deposit = fields.Boolean(string="Deposit")
    pnt_invoice_ids = fields.One2many(
        string="Invoices",
        comodel_name="account.move",
        inverse_name="pnt_agreement_id",
    )
    pnt_invoice_count = fields.Integer(
        string="Invoices",
        compute="_compute_pnt_invoice_count",
    )
    pnt_agreement_downpayment_line_ids = fields.One2many(
        comodel_name="pnt.agreement.line",
        inverse_name="pnt_agreement_id",
        string="Agreement Lines",
        domain=[("pnt_is_downpayment", "=", True)],
        readonly=True,
    )
    pnt_single_document_ids = fields.One2many(
        string="DU", comodel_name="pnt.single.document", inverse_name="pnt_agreement_id"
    )
    pnt_amount_downpayment = fields.Float(
        string="Down payment",
        compute="_compute_pnt_amount_downpayment",
        digits="Product Price",
        store=True,
    )
    pnt_sale_rental_ids = fields.Many2many(
        string="Sale Rentals",
        comodel_name="sale.order",
        relation="pnt_sale_rental_agreement_rel",
        copy=False,
    )
    pnt_domain_product_ids = fields.Many2many(
        string="Domain Product",
        comodel_name="product.product",
        compute="_compute_pnt_domain_product_ids",
    )
    pnt_partner_pickup_count = fields.Integer(
        string="Partner Pickup Count",
        compute="_compute_pnt_partner_pickup_count",
    )

    @api.depends("pnt_partner_pickup_ids")
    def _compute_pnt_partner_pickup_count(self):
        for record in self:
            record.pnt_partner_pickup_count = len(record.pnt_partner_pickup_ids)

    @api.depends("pnt_holder_id")
    def _compute_pnt_user_id(self):
        for du in self:
            du.pnt_user_id = du.pnt_holder_id.user_id or self.env.user

    def _pnt_upgrade_stage_method(self):
        for record in self:
            opportunity = record.pnt_opportunity_id
            if opportunity:
                stage = self.env["crm.stage"].search(
                    [("pnt_is_pending_confirm", "=", True)]
                )
                opportunity.stage_id = stage.id

    @api.depends("pnt_agreement_type")
    def _compute_pnt_domain_product_ids(self):
        self.pnt_domain_product_ids = False
        self.pnt_partner_pickup_domain_ids = False
        product_marpol = False
        product_all = False
        obj_product = self.env["product.product"]
        for record in self:
            if record.pnt_agreement_type == "marpol":
                product_marpol = product_marpol or obj_product.search(
                    [
                        "|",
                        "|",
                        ("type", "=", "service"),
                        ("pnt_is_container", "=", True),
                        ("pnt_is_marpol_waste", "=", True),
                        ("company_id", "in", (False, record.company_id.id)),
                    ]
                )
                record.pnt_domain_product_ids = product_marpol
                pnt_comp_ids = self.env["res.partner"].search(
                    [
                        ("type", "=", "delivery"),
                        ("pnt_is_boat", "=", True),
                        ("company_id", "in", [self.env.company.id, False]),
                    ]
                )
                record.pnt_partner_pickup_domain_ids = pnt_comp_ids
            else:
                product_all = product_all or obj_product.search(
                    [("company_id", "in", (False, record.company_id.id))]
                )
                record.pnt_domain_product_ids = product_all
                pnt_comp_ids = self.env["res.partner"].search(
                    [
                        ("type", "=", "delivery"),
                        ("company_id", "in", [self.env.company.id, False]),
                    ]
                )
                record.pnt_partner_pickup_domain_ids = pnt_comp_ids

    @api.depends(
        "pnt_agreement_downpayment_line_ids",
        "pnt_agreement_downpayment_line_ids.pnt_price_unit",
        "pnt_single_document_ids.pnt_sale_order_ids",
        "pnt_single_document_ids.pnt_sale_order_ids.state",
        "pnt_single_document_ids.pnt_sale_order_ids.order_line",
        "pnt_single_document_ids.pnt_sale_order_ids.order_line.price_subtotal",
        "pnt_single_document_ids.pnt_sale_order_ids.order_line.is_downpayment",
    )
    def _compute_pnt_amount_downpayment(self):
        for agreement in self:
            total_downpayment = sum(
                x.pnt_price_unit for x in agreement.pnt_agreement_downpayment_line_ids
            )
            total_downpayment_sales = sum(
                x.price_subtotal * -1
                for x in agreement.pnt_single_document_ids.pnt_sale_order_ids.filtered(
                    lambda x: x.state != "cancel"
                ).order_line.filtered("is_downpayment")
            )
            agreement.pnt_amount_downpayment = (
                total_downpayment - total_downpayment_sales
            )

    @api.onchange("pnt_agreement_type")
    def onchange_pnt_agreement_type(self):
        self.pnt_partner_pickup_ids = None

    def _compute_pnt_invoice_count(self):
        for agreement in self:
            agreement.pnt_invoice_count = len(agreement.pnt_invoice_ids)

    def pnt_action_copy(self):
        self.ensure_one()
        # copy agreement updating pnt_end_date = (today - 1) & update contract pnt_start_date to today
        start_date = self.pnt_start_date
        today = fields.Date.context_today(self, fields.datetime.today())
        end_date = today - timedelta(days=1)
        new_agreement = self.copy(
            default={
                "pnt_end_date": end_date,
                "state": "finish",
            }
        )
        self.write(
            {
                "pnt_start_date": today,
            }
        )
        self.message_post(
            body=_(
                """<h4>Create and finished agreement</h4>
                <b>%s</b>
                <br/>Start date: %s
                <br/>End date: %s"""
                % (
                    new_agreement.display_name,
                    format_date(self.env, start_date, self.env.lang),
                    format_date(self.env, end_date, self.env.lang),
                )
            ),
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )

    @api.onchange("pnt_holder_id")
    def onchange_pnt_holder_id_warning(self):
        if not self.pnt_holder_id:
            return
        warning = {}
        title = False
        message = False
        partner = self.pnt_holder_id

        # If partner has no warning, check its company
        if partner.agreement_warn == "no-message" and partner.parent_id:
            partner = partner.parent_id

        if partner.agreement_warn and partner.agreement_warn != "no-message":
            # Block if partner only has warning but parent company is blocked
            if (
                partner.agreement_warn != "block"
                and partner.parent_id
                and partner.parent_id.agreement_warn == "block"
            ):
                partner = partner.parent_id
            title = _("Warning for %s") % partner.name
            message = partner.agreement_warn_msg
            warning = {
                "title": title,
                "message": message,
            }
            if partner.agreement_warn == "block":
                self.update(
                    {
                        "pnt_holder_id": False,
                    }
                )
                return {"warning": warning}

        if warning:
            return {"warning": warning}

    @api.onchange("pnt_is_market_price")
    def onchange_pnt_is_market_price(self):
        if self.pnt_is_market_price:
            io = self.check_pnt_is_market_price()
            if io != "":
                self.pnt_is_market_price = False
                return {
                    "value": {},
                    "warning": {
                        "Aviso": "warning",
                        "message": "Ya existe un contrato marcado como precio de mercado: "
                        + io,
                    },
                }

    def button_start_rental(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "custom_pnt.pnt_rental_manual_action"
        )
        ctx = dict(self.env.context)
        ctx["default_pnt_domain_pickup_ids"] = self.pnt_partner_pickup_ids.ids
        ctx["default_pnt_domain_waste_ids"] = (
            self.pnt_agreement_line_ids.pnt_product_id.filtered("pnt_is_waste").ids
        )
        ctx["default_pnt_rental_line_ids"] = [
            (
                0,
                0,
                {
                    "pnt_line_agreement_id": x.id,
                    "pnt_exist_waste": bool(x.pnt_product_waste_id.id),
                    "pnt_exist_pickup": bool(x.pnt_partner_pickup_id.id),
                    "pnt_product_id": x.pnt_product_id.id,
                    "pnt_quantity": x.pnt_product_uom_qty,
                    "pnt_price_unit": x.pnt_price_unit,
                    "pnt_container_id": x.pnt_container_id.id,
                    "pnt_waste_id": x.pnt_product_waste_id.id,
                    "pnt_pickup_id": x.pnt_partner_pickup_id.id,
                },
            )
            for x in self.pnt_agreement_line_ids
            if x.pnt_monetary_waste == "inbound"
            and x.pnt_product_id.is_product_rental()
        ]
        action["context"] = ctx
        return action

    def button_stop_rental(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "custom_pnt.pnt_rental_manual_action"
        )
        view_id = self.env.ref("custom_pnt.pnt_rental_manual_delete_view_form").id
        action["name"] = _("Stop Rental")
        action["views"] = [(view_id, "form")]
        action["view_id"] = view_id
        sales = self.env["sale.order"].search(
            [
                (
                    "pnt_rental_manual_agreement_line_id",
                    "in",
                    self.pnt_agreement_line_ids.ids,
                ),
                ("pnt_is_created_rental_manual", "=", True),
                ("pnt_is_rental_manual_active", "=", True),
                ("pnt_rental_manual_processed", "=", False),
                ("state", "not in", ("draft", "sent", "cancel")),
            ]
        )
        ctx = dict(self.env.context)
        ctx["default_pnt_rental_sale_ids"] = sales.ids
        action["context"] = ctx
        return action

    def check_pnt_is_market_price(self):
        prl = self.env["pnt.agreement.agreement"].search(
            [
                ("id", "!=", self._origin.id),
                ("pnt_is_market_price", "=", 1),
                ("state", "=", "done"),
            ],
            limit=1,
        )
        if prl:
            return "[" + prl.name + "] " + prl.pnt_description
        else:
            return ""

    @api.depends("name", "pnt_parent_agreement_id.pnt_complete_name", "pnt_holder_id")
    def _compute_complete_name(self):
        for agreement in self:
            name = "[%s] %s" % (
                agreement.name,
                (
                    agreement.pnt_partner_pickup_id.display_name
                    if agreement.pnt_partner_pickup_id
                    else agreement.pnt_holder_id.display_name
                ),
            )
            if agreement.pnt_parent_agreement_id:
                agreement.pnt_complete_name = "%s / %s" % (
                    agreement.pnt_parent_agreement_id.pnt_complete_name,
                    name,
                )
            else:
                agreement.pnt_complete_name = name

    @api.depends("pnt_holder_id")
    def compute_pnt_holder_id(self):
        for record in self:
            if record.pnt_holder_id:
                record.pnt_customer_payment_mode_id = (
                    record.pnt_holder_id.customer_payment_mode_id.id or False
                )
                record.pnt_customer_payment_term_id = (
                    record.pnt_holder_id.property_payment_term_id.id or False
                )
                record.pnt_supplier_payment_mode_id = (
                    record.pnt_holder_id.supplier_payment_mode_id.id or False
                )
                record.pnt_supplier_payment_term_id = (
                    record.pnt_holder_id.property_supplier_payment_term_id.id or False
                )

    @api.depends("pnt_parent_agreement_id")
    def compute_pnt_parent_agreement_id(self):
        if not self.pnt_parent_agreement_id:
            return
        self.pnt_holder_id = self.pnt_parent_agreement_id.pnt_holder_id.id
        self.pnt_note = self.pnt_parent_agreement_id.pnt_note

    def action_view_pickups(self):
        action = self.env["ir.actions.actions"]._for_xml_id("contacts.action_contacts")
        action["domain"] = [("id", "in", self.pnt_partner_pickup_ids.ids)]
        action["views"] = [(False, "tree"), (False, "form"), (False, "kanban")]
        action["view_mode"] = "tree,form,kanban"
        action["view_id"] = self.env.ref("base.view_partner_tree").id
        return action

    def action_view_invoice(self):
        invoices = self.mapped("pnt_invoice_ids")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        if len(invoices) > 1:
            action["domain"] = [("id", "in", invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref("account.view_move_form").id, "form")]
            if "views" in action:
                action["views"] = form_view + [
                    (state, view) for state, view in action["views"] if view != "form"
                ]
            else:
                action["views"] = form_view
            action["res_id"] = invoices.id
        else:
            action = {"type": "ir.actions.act_window_close"}

        context = {
            "default_move_type": "out_invoice",
        }
        if len(self) == 1:
            context.update(
                {
                    "default_partner_id": self.pnt_holder_id.id,
                    "default_partner_shipping_id": self.pnt_holder_id.id,
                    "default_invoice_payment_term_id": (
                        self.pnt_holder_id.property_payment_term_id.id
                    ),
                    "default_invoice_origin": self.name,
                    "default_user_id": self.user_id.id,
                }
            )
        action["context"] = context
        return action

    def update_general_condition(self):
        for rec in self:
            result = ""
            list_categ = []
            list_gencon = []
            for line in rec.pnt_agreement_line_ids:
                if line.pnt_product_id.categ_id.id not in list_categ:
                    conditions = self.env["pnt.general.conditions"].search(
                        [("pnt_category_ids", "=", line.pnt_product_id.categ_id.id)]
                    )
                    for condition in conditions:
                        if condition.id not in list_gencon:
                            result += condition.pnt_general_conditions
                            list_gencon.append(condition.id)
                    list_categ.append(line.pnt_product_id.categ_id.id)
            rec.pnt_general_conditions = result

    def generate_product_list(self):
        for rec in self:
            list_lines = []
            for lin in rec.pnt_parent_agreement_id.pnt_agreement_line_ids:
                te = self.env["pnt.agreement.line"]
                inv_obj = te.create(
                    {
                        "pnt_agreement_id": rec.id,
                        "sequence": lin.sequence,
                        "display_type": lin.display_type,
                        "pnt_product_id": lin.pnt_product_id.id,
                        "pnt_is_waste": lin.pnt_is_waste,
                        "pnt_is_container": lin.pnt_is_container,
                        "pnt_product_economic_uom": lin.pnt_product_economic_uom.id,
                        "pnt_price_unit": lin.pnt_price_unit,
                        "pnt_container_id": lin.pnt_container_id.id,
                        "pnt_monetary_waste": lin.pnt_monetary_waste,
                        "pnt_product_uom_qty": lin.pnt_product_uom_qty,
                        "pnt_product_uom": lin.pnt_product_uom.id,
                        "name": lin.name,
                        "pnt_customer_name": lin.pnt_customer_name,
                        "pnt_supplier_name": lin.pnt_supplier_name,
                        "pnt_description_line": lin.pnt_description_line,
                        "company_id": lin.company_id.id,
                        "pnt_product_waste_id": lin.pnt_product_waste_id.id,
                        "pnt_fleet_vehicle_category_ids": lin.pnt_fleet_vehicle_category_ids,
                        "pnt_product_container_ids": lin.pnt_product_container_ids,
                        "pnt_default": lin.pnt_default,
                    }
                )
                list_lines.append(inv_obj.id)
            rec.pnt_agreement_line_ids = list_lines

    def _prepare_activation_values(self):
        return {"state": "done", "pnt_activate_date": fields.Date.context_today(self)}

    def _prepare_done_values(self):
        return {
            "state": "done",
        }

    def _prepare_unlocked_values(self):
        return {
            "state": "active",
        }

    def _prepare_cancel_values(self):
        return {
            "state": "cancel",
        }

    def _prepare_to_renewal_values(self):
        return {
            "state": "to_renew",
        }

    def _prepare_finished_values(self):
        if self.pnt_end_date:
            return {
                "state": "finish",
            }
        else:
            return {
                "state": "finish",
                "pnt_activate_date": fields.Date.context_today(self),
            }

    def waste_without_container(self):
        for record in self:
            result = False
            for line in record.pnt_agreement_line_ids:
                if (
                    line.pnt_is_waste
                    and not line.pnt_container_id
                    and not line.pnt_all_containers
                ):
                    result = True
            return result

    def _action_cancel(self):
        for record in self:
            record._prepare_cancel_values()

    def action_activate(self):
        if self.pnt_start_date == False:
            raise UserError(_("Es obligatorio indicar una Fecha de Inicio"))
        if (
            self.pnt_agreement_type in ("others", "manager")
            and self.waste_without_container()
        ):
            raise UserError(
                _(
                    "Es obligatorio indicar un Envase para los Residuos en este tipo de contrato"
                )
            )
        else:
            if self.pnt_holder_id.pnt_is_lead:
                raise UserError(
                    _(
                        "Los contactos con LEAD activado no puden tener contratos activos"
                    )
                )
            else:
                self.write(self._prepare_activation_values())

    def action_done(self):
        if (
            self.pnt_agreement_type in ("others", "manager")
            and self.waste_without_container()
        ):
            raise UserError(
                _(
                    "Es obligatorio indicar un Envase para los Residuos en este tipo de contrato"
                )
            )
        else:
            self.write(self._prepare_done_values())

    def action_unlocked(self):
        self.write(self._prepare_unlocked_values())

    def action_finished(self):
        for record in self:
            record.write(record._prepare_finished_values())

    def action_to_renewal(self):
        for record in self:
            record.write(record._prepare_to_renewal_values())

    def action_cancel(self):
        if self.pnt_child_ids:
            self.pnt_child_ids.filtered(lambda x: x.state != "cancel")._action_cancel()
        self.write(self._prepare_cancel_values())

    def action_agreement_send(self):
        """Opens a wizard to compose an email, with relevant mail template loaded by default"""
        self.ensure_one()
        # template_id = self._find_mail_template()
        ir_model_data = self.env["ir.model.data"]
        template_id = ir_model_data.get_object_reference(
            "custom_pnt", "email_template_agreement_agreement"
        )[1]
        lang = self.env.context.get("lang")
        template = self.env["mail.template"].browse(template_id)
        # template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            "default_model": "pnt.agreement.agreement",
            "default_res_id": self.ids[0],
            "default_use_template": bool(template_id),
            "default_template_id": template_id,
            "default_composition_mode": "comment",
            "mark_ag_as_sent": True,
            "custom_layout": "mail.mail_notification_paynow",
            # 'proforma': self.env.context.get('proforma', False),
            "force_email": True,
            # 'model_description': self.with_context(lang=lang).type_name,
        }
        return {
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(False, "form")],
            "view_id": False,
            "target": "new",
            "context": ctx,
        }

    def _get_lines_du(self, du):
        dus = self.env["pnt.single.document"].browse([x.id for x in du])
        return dus.pnt_single_document_line_ids.filtered(
            lambda x: x.pnt_product_id.pnt_rental
            and x.pnt_product_id.pnt_container_movement_type == "delivery"
        )

    def _get_lines_finish_du(self, du):
        done = self.env["ir.model.data"].xmlid_to_res_id(
            "project_task_default_stage.project_tt_deployment"
        )
        dus = self.env["pnt.single.document"].browse([x.id for x in du])
        return dus.pnt_single_document_line_ids.filtered(
            lambda x: x.pnt_product_id.pnt_rental
            and x.pnt_single_document_id.task_id.stage_id.id == done
            and x.pnt_single_document_id.state != "cancel"
            and x.pnt_product_id.pnt_container_movement_type == "removal"
        )

    def _create_sale_from_du(self, lines, line_agreement):
        for line in lines:
            sale = Form(recordp=self.env["sale.order"], view="sale.view_order_form")
            sale.partner_id = line_agreement.pnt_agreement_id.pnt_holder_id
            sale.partner_shipping_id = line.pnt_single_document_id.pnt_partner_pickup_id
            sale.date_order = fields.Datetime.now()
            with sale.order_line.new() as line_form:
                line_form.product_id = line_agreement.pnt_product_id
                line_form.price_unit = line_agreement.pnt_price_unit
            sale = sale.save()
            sale.order_line.name = f"{sale.order_line.name}\n{line_agreement.pnt_container_id.display_name or ''}"
            sale.action_confirm()
            return sale

    def is_finish(self, line_agreement, du):
        finish_rental = self._get_lines_finish_du(du)
        if line_agreement.pnt_partner_pickup_id:
            finish_rental = finish_rental.filtered(
                lambda x: x.pnt_single_document_id.pnt_partner_pickup_id
                == line_agreement.pnt_partner_pickup_id
            )
        if line_agreement.pnt_container_id:
            finish_rental = finish_rental.filtered(
                lambda x: x.pnt_container_id == line_agreement.pnt_container_id
            )
        if line_agreement.pnt_product_waste_id:
            finish_rental = finish_rental.filtered(
                lambda x: x.pnt_product_waste_id == line_agreement.pnt_product_waste_id
            )
        return finish_rental

    def _cron_create_manual_rental_sale(self):
        day = str(fields.Date.today().day)
        for company in self.env["res.company"].sudo().search([]):
            if company.pnt_rental_generation_day == day:
                self.with_company(company.id)._create_manual_rental_sale()

    def _create_manual_rental_sale(self):
        company_id = self.env.company.id
        sales = self.env["sale.order"].search(
            [
                (
                    "pnt_rental_manual_agreement_line_id",
                    "!=",
                    False,
                ),
                ("pnt_is_created_rental_manual", "=", True),
                ("pnt_is_rental_manual_active", "=", True),
                ("pnt_rental_manual_processed", "=", False),
                ("state", "not in", ("draft", "sent", "cancel")),
                ("company_id", "=", company_id),
            ]
        )
        for sale in sales:
            agreement_line = sale.pnt_rental_manual_agreement_line_id
            new_sale = sale.copy(
                {
                    "pnt_is_created_rental_manual": True,
                    "pnt_is_rental_manual_active": True,
                    "pnt_rental_manual_date_origin": (
                        sale.pnt_rental_manual_date_origin
                    ),
                    "pnt_rental_manual_description": sale.pnt_rental_manual_description,
                    "pnt_rental_manual_agreement_line_id": agreement_line.id,
                }
            )
            new_sale.action_confirm()
            sale.pnt_rental_manual_processed = True
            agreement_line.pnt_agreement_id.pnt_sale_rental_ids = [(4, new_sale.id)]

    def create_rentals(self):
        company_id = self.env.company.id
        done = self.env["ir.model.data"].xmlid_to_res_id(
            "project_task_default_stage.project_tt_deployment"
        )
        lines_agreements = self.env["pnt.agreement.line"].search(
            [
                ("pnt_agreement_id.state", "!=", "cancel"),
                ("pnt_line_rental_done", "in", ("0", "1")),
                ("pnt_product_id.pnt_rental", "=", True),
                ("pnt_product_id.pnt_recurrence", "=", True),
                ("pnt_product_id.type", "=", "service"),
                ("pnt_product_id.default_code", "=", "TA"),
                ("pnt_product_id.pnt_container_movement_type", "=", False),
                ("company_id", "=", company_id),
            ]
        )
        record_dus = self.env["pnt.single.document"].search(
            [
                ("pnt_agreement_id", "in", lines_agreements.pnt_agreement_id.ids),
                ("task_id.stage_id", "=", done),
                ("company_id", "=", company_id),
                ("state", "!=", "cancel"),
            ]
        )
        dus = {}
        for rec in record_dus:
            dus.setdefault(rec.pnt_agreement_id, []).append(rec)
        for line in lines_agreements:
            du = dus.get(line.pnt_agreement_id)
            if not du:
                continue
            lines = self._get_lines_du(du)
            if not lines:
                continue
            if line.pnt_partner_pickup_id:
                lines = lines.filtered(
                    lambda x: x.pnt_single_document_id.pnt_partner_pickup_id
                    == line.pnt_partner_pickup_id
                )
            if line.pnt_container_id:
                lines = lines.filtered(
                    lambda x: x.pnt_container_id == line.pnt_container_id
                )
            if line.pnt_product_waste_id:
                lines = lines.filtered(
                    lambda x: x.pnt_product_waste_id == line.pnt_product_waste_id
                )
            if not lines:
                continue
            sale = self._create_sale_from_du(lines[:1], line)
            line.pnt_agreement_id.pnt_sale_rental_ids = [(4, sale.id)]
            finish = self.is_finish(line, du)
            if finish:
                line.pnt_line_rental_done = "2"
                finish.pnt_line_rental_done = "2"
            else:
                line.pnt_line_rental_done = "1"
                lines.pnt_line_rental_done = "2"

    def generate_rental_sale(self):
        day = str(fields.Date.today().day)
        for company in self.env["res.company"].sudo().search([]):
            if company.pnt_rental_generation_day == day:
                self.with_company(company.id).create_rentals()

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get("mark_ag_as_sent"):
            self.filtered(lambda o: o.state == "draft").with_context(
                tracking_disable=True
            ).write({"state": "sent"})
        return super(
            PntAgreementAgreement, self.with_context(mail_post_autofollow=True)
        ).message_post(**kwargs)

    @api.model
    def _get_agreement_line_product_types(self):
        product_type = []
        lines = self.pnt_agreement_line_ids.sorted(
            lambda t: t.pnt_product_id.categ_id.pnt_order_budget_format
        )
        for line in lines:
            if line.pnt_product_id.categ_id.name not in product_type:
                product_type.append(line.pnt_product_id.categ_id.name)
        return product_type

    @api.model
    def _get_lines_with_product_type(self, product_type):
        return self.pnt_agreement_line_ids.filtered(
            lambda r: r.pnt_product_id.categ_id.name == product_type
        )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.agreement.agreement", sequence_date=seq_date
            ) or _("New")
        result = super(PntAgreementAgreement, self).create(vals)
        if "state" in vals and vals["state"] in ("active", "done"):
            self.register_agreement()
        return result

    @api.model
    def name_search(self, name, args=None, operator="ilike", limit=100):
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                ("pnt_holder_id", "=ilike", name + "%"),
                ("pnt_holder_id", operator, name),
            ]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ["&", "!"] + domain[1:]
        assets = self.search(domain + args, limit=limit)
        return assets.name_get()

    def name_get(self):
        res = []
        for record in self:
            code = record.name
            name = (
                record.pnt_partner_pickup_id.display_name
                if record.pnt_partner_pickup_id
                else record.pnt_holder_id.display_name
            )
            if record.pnt_parent_agreement_id:
                name = "[%s] %s" % (code, name)
                name = "%s / %s" % (record.pnt_parent_agreement_id.display_name, name)
                name = "%s" % name
            else:
                name = "[%s] %s" % (code, name)
            # if record.pnt_agreement_type == "portal":
            #     name = "[" + record.name + "] " + record.pnt_description
            if record.pnt_description:
                name = "[" + record.name + "] " + record.pnt_description
            res.append((record.id, name))
        return res

    def _get_inheritance(self, parents=None):
        if not parents:
            parents = self.env[self._name]

        indirect_inheritance = self.env[self._name]
        parents |= self
        direct_inheritance = self.pnt_child_ids - parents
        for child in direct_inheritance:
            child_inheritance = child._get_inheritance(parents=parents)
            indirect_inheritance |= child_inheritance
        return indirect_inheritance | direct_inheritance

    @api.depends("pnt_child_ids", "pnt_child_ids.pnt_child_all_count")
    def _compute_pnt_inheritance(self):
        for agreement in self:
            agreement.pnt_inheritance_ids = agreement._get_inheritance()
            agreement.pnt_child_all_count = len(agreement.pnt_inheritance_ids)

    def _finish_agreement(self):
        agreement_ids = self.env["pnt.agreement.agreement"].search(
            [
                ("state", "in", ("active", "done")),
                ("pnt_end_date", "<=", fields.Date.context_today(self)),
            ]
        )
        if agreement_ids:
            agreement_ids.action_finished()

    def _to_renewal_agreement(self):
        today = fields.Datetime.today()
        agreement_ids = self.env["pnt.agreement.agreement"].search(
            [
                ("state", "in", ("active", "done")),
            ]
        )
        if agreement_ids:
            for agreement_id in agreement_ids:
                if agreement_id.pnt_end_date:
                    date = agreement_id.pnt_end_date - timedelta(
                        days=self.env.company.pnt_delay_days_due_agreement_to_renew
                    )
                    if date <= today:
                        agreement_id.write(self._prepare_to_renewal_values())

    def _renewal_agreements(self):
        agreement_ids = self.env["pnt.agreement.agreement"].search(
            [
                ("state", "=", "to_renew"),
                ("pnt_auto_renewal", "=", True),
            ]
        )
        for agreement_id in agreement_ids:
            agreement = agreement_id.copy(
                {
                    "pnt_start_date": agreement_id.pnt_start_date,
                }
            )
            agreement_id.update({"pnt_auto_renewal": False})
            # old agreement
            agreement_id.message_post(
                body=_(
                    "This agreement has created other agreement: %s"
                    % agreement.display_name
                ),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )
            # new agreement
            agreement.message_post(
                body=_(
                    "This agreement has been created by: %s" % agreement_id.display_name
                ),
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

    def open_agreement_entity(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "pnt.agreement.agreement",
            "view_mode": "form",
            "res_id": self.pnt_parent_agreement_id.id,
            "target": "current",
            "flags": {"form": {"action_buttons": True}},
        }

    def lines_agreement_created(self, lines):
        lines_waste = lines
        registrations = self.env["pnt.agreement.registration"].search(
            [
                ("company_id", "=", self.env.company.id),
                ("pnt_product_id", "!=", False),
                ("pnt_product_id", "in", lines_waste.pnt_product_id.ids),
                ("pnt_pickup_id", "!=", False),
                "|",
                ("pnt_pickup_id", "in", lines_waste.pnt_partner_pickup_id.ids),
                (
                    "pnt_pickup_id",
                    "in",
                    lines_waste.pnt_agreement_id.pnt_partner_pickup_ids.ids,
                ),
            ]
        )
        return list(
            set(
                [
                    (
                        x.company_id.id,
                        x.pnt_product_id.id,
                        x.pnt_pickup_id.id,
                    )
                    for x in registrations
                ]
            )
        )

    def register_agreement(self, old=False, raise_exception=True):
        data = []
        today = fields.Date.today()
        lines = self.pnt_agreement_line_ids.filtered("pnt_is_waste")
        checks = self.lines_agreement_created(lines)
        pickups = lines.pnt_agreement_id.pnt_partner_pickup_ids
        agreement_registration = ""
        if self.pnt_agreement_type == "manager":
            agreement_registration = "mgm"
        if self.pnt_agreement_type not in ("manager", "portal"):
            agreement_registration = "producer"

        for line in lines.filtered(lambda x: not x.pnt_partner_pickup_id):
            for location in pickups:
                key = (
                    line.company_id.id,
                    line.pnt_product_id.id,
                    location.id,
                )
                if key in checks:
                    continue
                checks.append(key)
                values = line.get_values_agreement_registration(location)
                if old:
                    values["pnt_sign_date"] = today
                values["pnt_agreement_registration_type"] = agreement_registration
                data.append(values)
        for line in lines.filtered("pnt_partner_pickup_id"):
            key = (
                line.company_id.id,
                line.pnt_product_id.id,
                line.pnt_partner_pickup_id.id,
            )
            if key in checks:
                continue
            checks.append(key)
            values = line.get_values_agreement_registration(line.pnt_partner_pickup_id)
            if old:
                values["pnt_sign_date"] = today
            values["pnt_agreement_registration_type"] = agreement_registration
            data.append(values)
        # todo: delete
        # if not data and raise_exception:
        #     raise UserError(_("No new contracts have been added."))
        # todo: delete
        if data:
            self.env["pnt.agreement.registration"].create(data)

    def action_register_agreement(self):
        return self.register_agreement()

    def action_register_agreement_old(self):
        return self.register_agreement(old=True)

    def _fields_sync(self, values):
        self._children_sync(values)
        # self._commercial_sync_to_children()

    def _update_fields_values(self, fields):
        values = {}
        for fname in fields:
            field = self._fields[fname]
            if field.type == "many2one":
                values[fname] = self[fname].id
            elif field.type == "one2many":
                raise AssertionError(
                    _(
                        "One2Many fields cannot be synchronized as part of `commercial_fields` or `address fields`"
                    )
                )
            elif field.type == "many2many":
                values[fname] = [(6, 0, self[fname].ids)]
            else:
                values[fname] = self[fname]
        return values

    @api.model
    def _agreement_fields(self):
        return [
            "pnt_start_date",
            "pnt_end_date",
            "pnt_note",
            "pnt_customer_payment_mode_id",
            "pnt_customer_payment_term_id",
            "pnt_supplier_payment_mode_id",
            "pnt_supplier_payment_term_id",
        ]

    def _commercial_sync_to_children(self):
        agreement_partner = self
        sync_vals = agreement_partner._update_fields_values(self._agreement_fields())
        sync_children = self.pnt_child_ids
        for child in sync_children:
            child._commercial_sync_to_children()
        res = sync_children.write(sync_vals)
        return res

    def _children_sync(self, values):
        if not self.pnt_child_ids:
            return
        if self.pnt_parent_agreement_id == self:
            commercial_fields = self._agreement_fields()
            if any(field in values for field in commercial_fields):
                self._agreement_sync_to_children()
        for child in self.pnt_child_ids:
            if child.pnt_parent_agreement_id != self.pnt_parent_agreement_id:
                self._commercial_sync_to_children()
                break

    @api.constrains("state", "pnt_deposit")
    def _check_state(self):
        for agreement in self:
            if agreement.pnt_deposit and agreement.state == "done":
                raise ValidationError(
                    _(
                        "A contract cannot have the deposit option selected and be in "
                        "a done state."
                    )
                )

    def get_partner_waste_codes_agreement(self, typeinfo, typepartner, end_mgm_id=0):
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

    def deposit_change_state_done(self, values):
        if not values.get("pnt_deposit") or self._context.get(
            "deposit_to_state_done_skip"
        ):
            return
        self.with_context(deposit_change_state_done_skip=True).filtered(
            lambda x: x.state == "done"
        ).state = "active"

    def write(self, vals):
        result = super().write(vals)
        self.deposit_change_state_done(vals)
        for record in self.filtered(lambda x: x.state in ("active", "done")):
            record.register_agreement()
        for agreement in self:
            agreement._fields_sync(vals)
        vals.get("state") == "sent" and self._pnt_upgrade_stage_method()
        return result


class PntAgreementLine(models.Model):
    _name = "pnt.agreement.line"
    _description = "Pnt Agreement Line"
    _order = "pnt_agreement_id, sequence, id"
    _check_company_auto = True

    @api.depends("pnt_product_id")
    def _get_authorized_container_domain_ids(self):
        self.authorized_container_domain_ids = False
        for record in self:
            product = record.pnt_product_id
            if record.pnt_is_waste or (
                product.pnt_rental and product.type == "service"
            ):
                product_tmpl_container_ids = product.pnt_product_tmpl_container_ids
                if not product_tmpl_container_ids:
                    record.authorized_container_domain_ids = [
                        self.env.company.pnt_agreement_bulk_product_id.id
                    ]
                else:
                    record.authorized_container_domain_ids = self.env[
                        "product.product"
                    ].search(
                        [("product_tmpl_id", "in", product_tmpl_container_ids.ids)]
                    )

    pnt_agreement_id = fields.Many2one(
        comodel_name="pnt.agreement.agreement",
        string="Agreement Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    pnt_agreement_type = fields.Selection(
        related="pnt_agreement_id.pnt_agreement_type",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
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
    pnt_waste_ler_id = fields.Many2one(
        related="pnt_product_id.pnt_waste_ler_id",
    )
    pnt_is_waste = fields.Boolean(
        string="Waste",
        related="pnt_product_id.pnt_is_waste",
    )
    pnt_is_container = fields.Boolean(
        string="Waste",
        related="pnt_product_id.pnt_is_container",
    )
    pnt_product_economic_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Economic Unit of Measure",
    )
    pnt_price_unit = fields.Float(
        string="Unit Price",
        required=True,
        digits="Product Price",
        default=0.0,
        compute="compute_pnt_product_id",
        store=True,
        readonly=False,
    )
    authorized_container_domain_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_get_authorized_container_domain_ids",
    )
    pnt_all_containers = fields.Boolean(
        string="Apply to all containers",
        default=False,
    )
    pnt_container_id = fields.Many2one(
        comodel_name="product.product",
        string="Container",
        domain=[("pnt_is_container", "=", True)],
        ondelete="restrict",
        compute="compute_pnt_product_id",
        store=True,
        readonly=False,
        check_company=True,
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
        required=True,
        default=1.0,
    )
    pnt_product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
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
        compute="compute_pnt_product_id",
        store=True,
        readonly=False,
    )
    pnt_supplier_name = fields.Char(
        name="Supplier description",
        compute="compute_pnt_product_id",
        store=True,
        readonly=False,
    )
    pnt_description_line = fields.Char(
        string="Description for documents",
        compute="compute_pnt_description_line",
        store=True,
        readonly=False,
    )
    company_id = fields.Many2one(
        related="pnt_agreement_id.company_id",
        string="Company",
        store=True,
        readonly=True,
        index=True,
    )
    pnt_product_waste_id = fields.Many2one(
        string="Wastes",
        comodel_name="product.product",
        domain=[("pnt_is_waste", "=", True)],
    )
    pnt_fleet_vehicle_category_ids = fields.Many2many(
        string="Vehicle category",
        comodel_name="pnt.fleet.vehicle.category",
        relation="pnt_agreement_line_vehicle_category_rel",
        column1="pnt_agreement_line_id",
        column2="pnt_fleet_vehicle_category_id",
    )
    pnt_product_container_ids = fields.Many2many(
        string="Containers",
        comodel_name="product.product",
        relation="pnt_agreement_line_product_container_rel",
        column1="pnt_agreement_line_id",
        column2="product_id",
        domain=[("pnt_is_container", "=", True)],
    )
    pnt_default = fields.Boolean(
        string="Default",
        copy=False,
    )
    pnt_according_market_price = fields.Boolean(
        string="According to market price",
        default=False,
    )
    pnt_transfer_periodicity = fields.Selection(
        selection=[("periodic", "Periodic"), ("punctual", "Punctual")],
        default="periodic",
        required=False,
        string="Transfer periodicity",
    )
    pnt_processed_contract = fields.Boolean(
        string="Processed",
        copy=False,
        readonly=True,
    )
    pnt_processed_contract_text = fields.Char(
        string="State",
        compute="_compute_pnt_processed_contract_text",
        store=True,
    )
    pnt_processed_contract_filter = fields.Boolean(
        string="State",
        compute="_compute_pnt_processed_contract_text",
        store=True,
    )
    pnt_partner_pickup_id = fields.Many2one(
        string="Partner pickup",
        comodel_name="res.partner",
    )
    pnt_is_downpayment = fields.Boolean(
        string="Is Downpayment",
    )
    pnt_line_rental_done = fields.Selection(
        string="Line Rental Sale",
        selection=[
            ("0", "Unset"),
            ("1", "Started"),
            ("2", "Finished"),
        ],
        required=True,
        copy=False,
        default="0",
    )
    pnt_m3 = fields.Float(
        string="M3",
        digits="Product Unit of Measure",
    )
    pnt_observations_agreement = fields.Char(
        string="Observations",
    )

    # todo: delete
    # pnt_agreement_registration_id = fields.Many2one(
    #     string="Agreement Registration",
    #     comodel_name="pnt.agreement.registration",
    #     compute="_compute_pnt_agreement_registration_id",
    #     store=True,
    # )
    # pnt_agreement_registration_sequence = fields.Char(
    #     related="pnt_agreement_registration_id.pnt_agreement_sequence",
    # )
    # pnt_agreement_registration_sign_date = fields.Date(
    #     related="pnt_agreement_registration_id.pnt_sign_date",
    # )
    # pnt_agreement_registration_ler_id = fields.Many2one(
    #     related="pnt_agreement_registration_id.pnt_ler_id",
    # )
    # pnt_agreement_registration_nima = fields.Char(
    #     related="pnt_agreement_registration_id.pnt_nima",
    # )
    # pnt_agreement_registration_agreement_original = fields.Char(
    #     related="pnt_agreement_registration_id.pnt_agreement_original",
    # )

    # @api.depends("pnt_agreement_registration_id.pnt_document")
    # def _compute_pnt_processed_contract_text(self):
    #     for record in self:
    #         if record.pnt_agreement_registration_id.pnt_document:
    #             record.pnt_processed_contract_text = _("Processed")
    #             record.pnt_processed_contract_filter = True
    #         else:
    #             record.pnt_processed_contract_text = _("Unprocessed")
    #             record.pnt_processed_contract_filter = False
    #
    # @api.depends(
    #     "company_id",
    #     "pnt_agreement_id",
    #     "pnt_agreement_id.state",
    #     "pnt_agreement_id.pnt_agreement_registration_ids",
    #     "pnt_agreement_id.pnt_agreement_registration_ids.pnt_agreement_line_ids",
    # )
    # def _compute_pnt_agreement_registration_id(self):
    #     company_id = self.env.company.id
    #     obj_reg = self.env["pnt.agreement.registration"]
    #     for record in self:
    #         record.pnt_agreement_registration_id = obj_reg.search(
    #             [
    #                 ("pnt_agreement_id", "=", record.pnt_agreement_id.id),
    #                 ("pnt_agreement_id.company_id", "=", company_id),
    #                 ("company_id", "=", company_id),
    #             ],
    #             limit=1,
    #         )
    # todo: delete

    @api.depends("pnt_product_id", "pnt_container_id")
    def name_get(self):
        line_lot = self._context.get("line_lot")
        res = []
        for record in self:
            name = record.pnt_product_id.display_name
            if record.pnt_container_id:
                name = name + " | " + record.pnt_container_id.display_name
            elif line_lot and record.pnt_partner_pickup_id:
                name += " | " + record.pnt_partner_pickup_id.display_name
            res.append((record.id, name))
        return res

    @api.depends("pnt_product_id")
    def compute_pnt_description_line(self):
        for record in self:
            record.pnt_description_line = record.pnt_product_id.display_name

    @api.depends("pnt_product_id")
    def compute_pnt_product_id(self):
        #
        # ¡¡¡¡¡MUY IMPORTANTE!!!!!
        #
        # Si se realiza alguna modificación en este método se deben revisar las
        # lineas de contrato previamente existentes para estar seguros de que no se han
        # cambiado los precios, unidades, etc., que ya estaban en las lineas de contrato
        #
        # Sobretodo es IMPORTANTE no añadir campos nuevos a este cumpute y evaluar
        # alternativas
        #
        # Es IMPORTANTE revisarlo y haber realizado todas las comprobaciones antes de
        # subir los cambios a producción
        #
        for record in self:
            if (record.pnt_product_id
                    and record.pnt_agreement_id.state in ('draft','sent','active')):
                record.pnt_monetary_waste = (
                    record.pnt_product_id.pnt_monetary_waste or False
                )
                record.name = record.pnt_product_id.display_name
                record.pnt_customer_name = record.pnt_product_id.display_name
                record.pnt_supplier_name = record.pnt_product_id.display_name
                record.pnt_product_economic_uom = record.pnt_product_id.uom_id.id
                record.pnt_product_uom = record.pnt_product_id.uom_id.id
                record.pnt_price_unit = record.pnt_product_id.lst_price
                # Comprobar si el articulo tiene envases en su ficha
                product_tmpl_container_ids = (
                    self.pnt_product_id.product_tmpl_id.pnt_product_tmpl_container_ids
                )
                if not product_tmpl_container_ids:
                    if (
                        record.pnt_product_id.pnt_is_waste
                        and self.env.company.pnt_agreement_bulk_product_id
                        and record.pnt_agreement_type in ("others", "manager")
                    ):
                        record.pnt_container_id = (
                            self.env.company.pnt_agreement_bulk_product_id
                        )
                else:
                    if (
                        record.pnt_product_id.pnt_is_waste
                        and record.pnt_agreement_type in ("others", "manager")
                        and len(product_tmpl_container_ids) == 1
                    ):
                        record.pnt_container_id = self.env["product.product"].search(
                            [
                                (
                                    "product_tmpl_id",
                                    "=",
                                    product_tmpl_container_ids[0].id,
                                )
                            ],
                            limit=1,
                        )

    @api.onchange("pnt_container_id")
    def onchange_pnt_container_id(self):
        if self.pnt_container_id:
            self.pnt_all_containers = False
            if not self.pnt_is_waste and (
                self.pnt_product_id.type != "service"
                or not self.pnt_product_id.pnt_rental
            ):
                self.pnt_container_id = None

    @api.onchange("pnt_all_containers")
    def onchange_pnt_all_containers(self):
        if self.pnt_all_containers:
            self.pnt_container_id = None
    def pnt_contract_product_name(self):
        for record in self:
            result = record.pnt_product_id.name
            if record.pnt_description_line:
                if record.pnt_description_line.partition(']')[2]:
                    result = str(record.pnt_description_line.partition(']')[2]).lstrip()
                else:
                    result = record.pnt_description_line
            # if record.pnt_monetary_waste == 'inbound' and record.pnt_customer_name:
            #     if record.pnt_customer_name.partition(']')[2]:
            #         result = str(record.pnt_customer_name.partition(']')[2]).lstrip()
            #     else:
            #         result = record.pnt_customer_name
            # elif record.pnt_monetary_waste == 'outbound' and record.pnt_supplier_name:
            #     if record.pnt_supplier_name.partition(']')[2]:
            #         result = str(record.pnt_supplier_name.partition(']')[2]).lstrip()
            #     else:
            #         result = record.pnt_supplier_name
            return result

    def get_values_agreement_registration(self, location):
        return {
            # todo: delete
            # "pnt_agreement_id": self.pnt_agreement_id.id,
            # "pnt_agreement_line_ids": [(4, self.id)],
            # "pnt_agreement_sequence": "",
            # "pnt_agreement_original": "",
            # todo: delete
            "pnt_pickup_id": location.id,
            "pnt_product_id": self.pnt_product_id.id,
            "pnt_qty_to_transport": self.pnt_product_uom_qty,
            "pnt_agreement_date": self.pnt_agreement_id.pnt_start_date,
            "pnt_auto_generate": True,
        }

    def get_line_agreement_registration(self):
        for record in self:
            agree_reg = self.env["pnt.agreement.registration"].search(
                [("pnt_agreement_line_ids", "in", self.id)], limit=1
            )
            if agree_reg:
                return agree_reg
            else:
                return ""

    def _get_contract_price(self):
        self.ensure_one()
        price_unit = self.pnt_price_unit
        if self.pnt_according_market_price:
            contract_id = (
                self.pnt_agreement_id.pnt_holder_id.pnt_portal_agreement_specific_id
                or self.pnt_agreement_id.pnt_holder_id.pnt_portal_agreement_type_id
                # or self.pnt_agreement_id.compnay_id.pnt_single_document_default_portal_id
                or self.env["pnt.agreement.agreement"].search(
                    [
                        ("pnt_is_market_price", "=", True),
                        ("state", "in", ("active", "done")),
                    ]
                )[0]
            )
            if contract_id:
                line_id = contract_id.pnt_agreement_line_ids.filtered(
                    lambda x: x.pnt_product_id.id == self.pnt_product_id.id
                    and x.pnt_container_id.id == self.pnt_container_id.id
                )
                if line_id:
                    price_unit = line_id.pnt_product_economic_uom._compute_price(
                        line_id[0].pnt_price_unit,
                        self.pnt_product_economic_uom,
                    )
        return price_unit


class PntAgreementReference(models.Model):
    _name = "pnt.agreement.reference"
    _description = "Pnt Agreement Reference"
    _check_company_auto = True

    pnt_agreement_id = fields.Many2one(
        comodel_name="pnt.agreement.agreement",
        string="Agreement Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    name = fields.Char(
        string="Code",
        required=True,
    )
    pnt_partner_pickup_ids = fields.Many2many(
        related="pnt_agreement_id.pnt_partner_pickup_ids",
    )
    pnt_partner_pickup_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner pickup",
        domain="[('id', 'in', pnt_partner_pickup_ids)]",
    )
