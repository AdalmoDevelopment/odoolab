from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from datetime import date


class AccountMove(models.Model):
    _inherit = "account.move"

    pnt_is_isp = fields.Boolean(
        string="Is ISP",
        compute="compute_is_isp",
        store=True,
    )
    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.agreement",
    )
    pnt_ship_scale_num = fields.Char(
        string="Ship Scale No",
    )
    pnt_control_sheet_ids = fields.One2many(
        string="Control sheets",
        comodel_name="pnt.control.sheet",
        inverse_name="pnt_move_id",
        copy=False,
    )
    pnt_show_m3 = fields.Boolean(
        compute="_compute_pnt_show_m3",
        store=True,
    )
    invoice_user_id = fields.Many2one(
        compute="_compute_invoice_user_id",
        store=True,
        readonly=False,
    )
    pnt_proforma_date = fields.Date(
        string="Pro-forma date",
        default=lambda self: date.today(),
    )
    pnt_face_order_number = fields.Char(
        string="Order Number",
    )
    pnt_face_additional_info = fields.Char(
        string="Additional Info",
    )
    pnt_sale_state = fields.Selection(
        selection=[
            ("score", _("PENDING BILLING SCORE")),
            ("commercial", _("PENDING COMMERCIAL REVIEW")),
            ("review", _("PENDING REVIEW JOSEP")),
            ("incidence", _("INCIDENCE")),
            ("ok", _("OK")),
            ("order", _("PENDING ORDER")),
        ],
        string="Pnt sale state",
        copy=False,
        tracking=3,
    )
    pnt_purchase_state = fields.Selection(
        selection=[
            ("score", _("PENDING SCORE PURCHASES")),
            ("commercial", _("PENDING COMMERCIAL REVIEW")),
            ("incidence", _("INCIDENCE")),
            ("ok", _("OK")),
            ("order", _("PENDING NUM FRA SUPPLIER")),
        ],
        string="Pnt purchase state",
        copy=False,
        tracking=3,
    )
    sale_invoicing_grouping_criteria_id = fields.Many2one(
        related="partner_id.sale_invoicing_grouping_criteria_id",
        store=True,
        string="Sales Invoicing Grouping Criteria",
    )
    @api.depends("partner_id")
    def _compute_invoice_user_id(self):
        if hasattr(super(), "_compute_invoice_user_id"):
            super()._compute_invoice_user_id()
        for record in self:
            record.invoice_user_id = record.partner_id.user_id or self.env.user

    @api.depends("invoice_line_ids.product_id")
    def _compute_pnt_show_m3(self):
        for record in self:
            result = False
            if record.financial_type in (
                "receivable",
                "receivable_refund",
                "payable",
                "payable_refund",
            ):
                if record.financial_type in ("payable", "payable_refund"):
                    # Compres
                    purchase_ids = self.env["purchase.order"].search(
                        [("order_line.invoice_lines.move_id", "=", record.id)]
                    )
                    if purchase_ids:
                        purchase_marpol_ids = purchase_ids.filtered(
                            lambda r: r.pnt_single_document_id.pnt_single_document_type
                            == "marpol"
                        )
                        if purchase_marpol_ids:
                            result = True
                else:
                    # Vendes
                    sale_ids = self.env["sale.order"].search(
                        [("order_line.invoice_lines.move_id", "=", record.id)]
                    )
                    if sale_ids:
                        sale_marpol_ids = sale_ids.filtered(
                            lambda r: r.pnt_single_document_id.pnt_single_document_type
                            == "marpol"
                        )
                        if sale_marpol_ids:
                            result = True
            else:
                result = False
            record.pnt_show_m3 = result

    @api.depends("invoice_line_ids.tax_ids")
    def compute_is_isp(self):
        self.pnt_is_isp = False
        for mv in self:
            mv.pnt_is_isp = any(x.pnt_is_isp for x in mv.invoice_line_ids.tax_ids)

    def validate_limit_cash(self):
        for move in self:
            if (
                move.move_type != "in_invoice"
                or not move.payment_mode_id.pnt_limit_cash_confirm_invoice_supplier
            ):
                continue
            if move.amount_total >= 1000:
                raise ValidationError(
                    _(
                        "You cannot confirm supplier invoices with amounts of 1000 € "
                        "or more with - %s - payment mode."
                    )
                    % move.payment_mode_id.name
                )

    def post_validate_limit_cash(self):
        for move in self:
            if (
                move.move_type != "in_invoice"
                or not move.payment_mode_id.pnt_limit_cash_confirm_invoice_supplier
            ):
                continue
            if not move.partner_id.vat:
                raise ValidationError(
                    _("%s does not have a VAT number.") % move.partner_id.display_name
                )
            if not move.invoice_date:
                raise ValidationError(
                    _("The Bill/Refund date is required to validate this document.")
                )
            invoices = self.search(
                [
                    ("move_type", "=", "in_invoice"),
                    ("state", "=", "posted"),
                    ("partner_id.vat", "=", move.partner_id.vat),
                    ("invoice_date", "=", move.invoice_date),
                    (
                        "payment_mode_id.pnt_limit_cash_confirm_invoice_supplier",
                        "=",
                        True,
                    ),
                ]
            )
            check = move.amount_total + sum(invoices.mapped("amount_total"))
            if check >= 1000:
                raise ValidationError(
                    _("Invoices to the same NIF/CIF per day cannot exceed 1000 €.")
                )

    def action_post(self):
        self.validate_limit_cash()
        self.post_validate_limit_cash()
        return super().action_post()

    @api.onchange("ref")
    def onchange_ref(self):
        if self.ref:
            self.payment_reference = self.ref

    def write(self, values):
        res = super().write(values)
        if values.get("payment_reference"):
            payref = values.get("payment_reference")
            if payref and self.journal_id and self.journal_id.pnt_copy_ref_to_lines:
                for line in self.invoice_line_ids:
                    line.name = payref
        return res

    @api.model
    def create(self, vals):
        # result = super(AccountMove, self).create(vals)
        if ("move_type" in vals and vals["move_type"]
                in ("out_invoice","out_refund")):
            vals["pnt_sale_state"] = "score"
        if ("move_type" in vals and vals["move_type"]
                in ("in_invoice","in_refund")):
            vals["pnt_purchase_state"] = "score"
        return super(AccountMove, self).create(vals)
    def _update_order_force_invoiced(self):
        for record in self:
            if record.reversed_entry_id:
                for lin in record.reversed_entry_id.invoice_line_ids:
                    if record.move_type in ("out_refund"):
                        sale_obj_ids = (self.env["sale.order"]
                                    .search([
                                        ("order_line.invoice_lines","=",lin.id),
                                        ("force_invoiced","=",False),
                        ]))
                        if sale_obj_ids:
                            sale_obj_ids.write({'force_invoiced': True})
                    elif record.move_type in ("in_refund"):
                        purchase_obj_ids = (self.env["purchase.order"]
                                    .search([
                                        ("order_line.invoice_lines","=",lin.id),
                                        ("force_invoiced", "=", False),
                        ]))
                        if purchase_obj_ids:
                            purchase_obj_ids.write({'force_invoiced': True})
    @api.model_create_multi
    def create(self, vals):
        res = super().create(vals)
        for record in res:
            record._update_order_force_invoiced()
        return res

class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    pnt_agreement_line_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.line",
    )
    pnt_is_downpayment = fields.Boolean(string="Is Downpayment")
    pnt_m3 = fields.Float(
        string="M3",
    )
    pnt_du_line_container_qty = fields.Float(
        string="Container Qty",
        digits="Product Unit of Measure",
        store=False,
        help="Technical field to store the container quantity of the DU line",
    )
    pnt_du_line_weight_qty = fields.Float(
        string="Weight",
        digits="Product Unit of Measure",
        store=False,
        help="Technical field to store the weight quantity of the DU line",
    )
    pnt_company_group_id = fields.Many2one(
        string="Company Group",
        related="partner_id.company_group_id",
        store=True,
    )
    pnt_payment_management_ids = fields.One2many(
        comodel_name="pnt.payment.management",
        inverse_name="pnt_account_move_line_id",
        string="Payment Management Lines",
        copy=False,
        auto_join=True,
    )
    pnt_payment_management_date = fields.Date(
        string="Management date",
        index=True,
        copy=False,
        compute="_compute_pnt_payment_management",
        store=True,
    )
    pnt_management_status = fields.Selection(
        string="Management status",
        selection=[
            ("notmanaged", _("Not managed")),
            ("comercial", _("Commercial pending")),
            ("billing", _("Billing pending")),
            ("reclaimed", _("Reclaimed")),
        ],
        compute="_compute_pnt_payment_management",
        copy=False,
        store=True,
    )
    pnt_invoice_warn = fields.Selection(
        related="partner_id.invoice_warn",
        store=True,
    )

    @api.onchange("product_id")
    def onchange_pnt_product_id(self):
        if (self.move_id.journal_id
                and self.move_id.journal_id.pnt_copy_ref_to_lines):
            self.name = self.move_id.payment_reference

    @api.depends("pnt_payment_management_ids")
    def _compute_pnt_payment_management(self):
        for record in self:
            management_ordered = record.pnt_payment_management_ids.sorted(
                lambda t: t.pnt_payment_management_date, reverse=True
            )
            if management_ordered:
                record.pnt_payment_management_date = (
                    management_ordered[0].pnt_payment_management_date)
                record.pnt_management_status = (
                    management_ordered[0].pnt_management_status)
            else:
                record.pnt_payment_management_date = None
                record.pnt_management_status = None

    def default_get(self, default_fields):
        values = super().default_get(default_fields)

        for record in self:
            if record.move_id.journal_id.pnt_supplier_selection == 'supplier' and record.account_id.code == '41000000':
                record.account_id = record.journal_id.pnt_supplier_account
            elif record.move_id.journal_id.pnt_supplier_selection == 'vendor' and record.account_id.code == '40000000':
                record.account_id = record.journal_id.pnt_supplier_account

        return values



class PntPaymentManagement(models.Model):
    _name = "pnt.payment.management"

    pnt_account_move_line_id = fields.Many2one(
        comodel_name="account.move.line",
        string="Agreement Reference",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    invoice_date = fields.Date(
        related="pnt_account_move_line_id.invoice_date",
        store=True,
    )
    move_id = fields.Many2one(
        related="pnt_account_move_line_id.move_id",
        store=True,
    )
    invoice_origin = fields.Char(
        related="pnt_account_move_line_id.invoice_origin",
        store=True,
    )
    name = fields.Char(
        related="pnt_account_move_line_id.name",
        string="Label",
        store=True,
    )
    partner_id = fields.Many2one(
        related="pnt_account_move_line_id.partner_id",
        store=True,
    )
    pnt_payment_management_date = fields.Date(
        string="Management date",
        default=lambda self: date.today(),
        index=True,
        copy=False,
        required=True,
    )
    pnt_management_status = fields.Selection(
        string="Management status",
        selection=[
            ("notmanaged", _("Not managed")),
            ("comercial", _("Commercial pending")),
            ("billing", _("Billing pending")),
            ("reclaimed", _("Reclaimed")),
        ],
        default="notmanaged",
        required=True,
    )
    pnt_observations = fields.Char(
        string="Observations",
        copy=False,
    )



