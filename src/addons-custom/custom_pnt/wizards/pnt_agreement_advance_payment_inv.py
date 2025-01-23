import time

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PntAgreementAdvancePaymentInv(models.TransientModel):
    _name = "pnt.agreement.advance.payment.inv"
    _description = "Agreement Advance Payment Invoice"

    @api.model
    def default_get(self, fields):
        agreements = self.env["pnt.agreement.agreement"].browse(
            self._context.get("active_ids", [])
        )
        if any(not x.pnt_deposit for x in agreements):
            raise UserError(
                _(
                    "There is at least one contract that does not have an advance "
                    "payment."
                )
            )
        return super().default_get(fields)

    @api.model
    def _count(self):
        return len(self._context.get("active_ids", []))

    @api.model
    def _default_product_id(self):
        product_id = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("sale.default_deposit_product_id")
        )
        return self.env["product.product"].browse(int(product_id)).exists()

    @api.model
    def _default_deposit_account_id(self):
        return self._default_product_id()._get_product_accounts()["income"]

    @api.model
    def _default_deposit_taxes_id(self):
        return self._default_product_id().taxes_id

    @api.model
    def _default_has_down_payment(self):
        if self._context.get(
            "active_model"
        ) == "pnt.agreement.agreement" and self._context.get("active_id", False):
            agreement = self.env["pnt.agreement.agreement"].browse(
                self._context.get("active_id")
            )
            return agreement.pnt_agreement_line_ids.filtered("pnt_is_downpayment")
        return False

    @api.model
    def _default_currency_id(self):
        if self._context.get(
            "active_model"
        ) == "pnt.agreement.agreement" and self._context.get("active_id", False):
            agreement = self.env["pnt.agreement.agreement"].browse(
                self._context.get("active_id")
            )
            return agreement.company_id.currency_id

    advance_payment_method = fields.Selection(
        [
            ("percentage", "Down payment (percentage)"),
            ("fixed", "Down payment (fixed amount)"),
        ],
        string="Create Invoice",
        default="percentage",
        required=True,
        help="A standard invoice is issued with all the order lines ready for "
        "invoicing, according to their invoicing policy (based on ordered or "
        "delivered quantity).",
    )
    deduct_down_payments = fields.Boolean(
        "Deduct down payments",
        default=True,
    )
    has_down_payments = fields.Boolean(
        "Has down payments",
        default=_default_has_down_payment,
        readonly=True,
    )
    product_id = fields.Many2one(
        "product.product",
        string="Down Payment Product",
        domain=[("type", "=", "service")],
        default=_default_product_id,
    )
    count = fields.Integer(
        default=_count,
        string="Order Count",
    )
    amount = fields.Float(
        "Down Payment Amount",
        digits="Account",
        help="The percentage of amount to be invoiced in advance, taxes excluded.",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=_default_currency_id,
    )
    fixed_amount = fields.Monetary(
        "Down Payment Amount (Fixed)",
        help="The fixed amount to be invoiced in advance, taxes excluded.",
    )
    deposit_account_id = fields.Many2one(
        "account.account",
        string="Income Account",
        domain=[("deprecated", "=", False)],
        help="Account used for deposits",
        default=_default_deposit_account_id,
    )
    deposit_taxes_id = fields.Many2many(
        "account.tax",
        string="Customer Taxes",
        help="Taxes used for deposits",
        default=_default_deposit_taxes_id,
    )

    @api.onchange("advance_payment_method")
    def onchange_advance_payment_method(self):
        if self.advance_payment_method == "percentage":
            amount = self.default_get(["amount"]).get("amount")
            return {"value": {"amount": amount}}
        return {}

    def _prepare_invoice_values(self, order, name, amount, so_line):
        invoice_vals = {
            "pnt_agreement_id": so_line.pnt_agreement_id.id,
            "move_type": "out_invoice",
            "invoice_origin": order.name,
            "invoice_user_id": order.user_id.id,
            "partner_id": order.pnt_holder_id.id,
            "fiscal_position_id": (
                order.pnt_holder_id.property_account_position_id.get_fiscal_position(
                    order.pnt_holder_id.id
                ).id
            ),
            "partner_shipping_id": order.pnt_holder_id.id,
            "currency_id": order.company_id.currency_id.id,
            "invoice_payment_term_id": order.pnt_holder_id.property_payment_term_id.id,
            "partner_bank_id": order.company_id.partner_id.bank_ids[:1].id,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": name,
                        "price_unit": amount,
                        "quantity": 1.0,
                        "product_id": self.product_id.id,
                        "product_uom_id": so_line.pnt_product_uom.id,
                        "pnt_agreement_line_id": so_line.id,
                        "pnt_is_downpayment": so_line.pnt_is_downpayment
                    },
                )
            ],
        }
        return invoice_vals

    def _get_advance_details(self, order):
        if self.advance_payment_method == "percentage":
            total = sum(
                x.pnt_product_uom_qty * x.pnt_price_unit
                for x in order.pnt_agreement_line_ids
            )
            amount = total * self.amount / 100
            name = _("Down payment of %s%%") % self.amount
        else:
            amount = self.fixed_amount
            name = _("Down Payment")
        return amount, name

    def _create_invoice(self, order, so_line):
        if (self.advance_payment_method == "percentage" and self.amount <= 0.00) or (
            self.advance_payment_method == "fixed" and self.fixed_amount <= 0.00
        ):
            raise UserError(_("The value of the down payment amount must be positive."))
        amount, name = self._get_advance_details(order)
        invoice_vals = self._prepare_invoice_values(order, name, amount, so_line)
        invoice = (
            self.env["account.move"]
            .with_company(order.company_id)
            .sudo()
            .create(invoice_vals)
            .with_user(self.env.uid)
        )
        invoice.message_post_with_view(
            "mail.message_origin_link",
            values={"self": invoice, "origin": order},
            subtype_id=self.env.ref("mail.mt_note").id,
        )
        return invoice

    def _prepare_agreement_line(self, order, amount):
        so_values = {
            "name": _("Down Payment: %s") % (time.strftime("%m %Y"),),
            "pnt_price_unit": amount,
            "pnt_product_uom_qty": 0,
            "pnt_agreement_id": order.id,
            "pnt_product_uom": self.product_id.uom_id.id,
            "pnt_product_id": self.product_id.id,
            "pnt_is_downpayment": True,
        }
        return so_values

    def create_invoices(self):
        agreements = self.env["pnt.agreement.agreement"].browse(
            self._context.get("active_ids", [])
        )
        # Create deposit product if necessary
        if not self.product_id:
            vals = self._prepare_deposit_product()
            self.product_id = self.env["product.product"].create(vals)
            self.env["ir.config_parameter"].sudo().set_param(
                "sale.default_deposit_product_id", self.product_id.id
            )
        agreement_line_obj = self.env["pnt.agreement.line"]
        for order in agreements:
            amount, name = self._get_advance_details(order)
            if self.product_id.invoice_policy != "order":
                raise UserError(
                    _(
                        "The product used to invoice a down payment should have an "
                        'invoice policy set to "Ordered quantities". Please update '
                        "your deposit product to be able to create a deposit invoice."
                    )
                )
            if self.product_id.type != "service":
                raise UserError(
                    _(
                        "The product used to invoice a down payment should be of "
                        "type 'Service'. Please use another product or update "
                        "this product."
                    )
                )
            line_values = self._prepare_agreement_line(order, amount)
            line = agreement_line_obj.create(line_values)
            self._create_invoice(order, line)
        if self._context.get("open_invoices", False):
            return agreements.action_view_invoice()
        return {"type": "ir.actions.act_window_close"}

    def _prepare_deposit_product(self):
        return {
            "name": "Down payment",
            "type": "service",
            "invoice_policy": "order",
            "property_account_income_id": self.deposit_account_id.id,
            "taxes_id": [(6, 0, self.deposit_taxes_id.ids)],
            "company_id": False,
        }
