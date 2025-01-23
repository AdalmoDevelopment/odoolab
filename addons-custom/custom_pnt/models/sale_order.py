from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form


class SaleOrder(models.Model):
    _inherit = "sale.order"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_single_document_id.pnt_single_document_type",
        store=True,
    )
    pnt_agreement_reference = fields.Char(
        related="pnt_single_document_id.pnt_agreement_reference",
        store=True,
    )
    pnt_order_reference = fields.Char(
        related="pnt_single_document_id.pnt_order_reference",
        store=True,
    )
    pnt_incidence_task_id = fields.Many2one(
        string="Incidence task",
        comodel_name="project.task",
    )
    pnt_ship_scale_num = fields.Char(
        string="Ship Scale No",
    )
    pnt_control_sheet_ids = fields.One2many(
        string="Control sheets",
        comodel_name="pnt.control.sheet",
        inverse_name="pnt_sale_id",
        copy=False,
    )
    pnt_check_number_certificate_sale = fields.Boolean(
        related="partner_id.pnt_check_number_certificate",
        string="N Cert",
        readonly=True,
    )
    pnt_is_created_rental_manual = fields.Boolean(
        string="Is created rental manual",
        copy=False,
    )
    pnt_is_rental_manual_active = fields.Boolean(
        string="Is rental manual active",
        copy=False,
    )
    pnt_rental_manual_agreement_line_id = fields.Many2one(
        string="Line rental manual",
        comodel_name="pnt.agreement.line",
        copy=False,
    )
    pnt_rental_manual_description = fields.Char(
        string="Rental description",
        copy=False,
    )
    pnt_rental_manual_processed = fields.Boolean(
        string="Rental processed",
        copy=False,
    )
    pnt_rental_manual_date_origin = fields.Date(
        string="Date origin",
        copy=False,
    )
    pnt_sd_effective_date = fields.Date(
        related="pnt_single_document_id.pnt_effective_date",
        store=True,
    )
    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.agreement",
    )

    def _action_confirm(self):
        # Si el tipo de pedido es de DU no genera stock picking
        if not self.type_id.pnt_is_DU:
            self.order_line._action_launch_stock_rule()
        return super()._action_confirm()

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        if not self.partner_id.user_id:
            self.update({"user_id": None})
    def pnt_has_rentals(self):
        for record in self:
            result = False
            rental_lines = record.order_line.filtered(lambda x: x.product_id.pnt_rental)
            if rental_lines:
                result = True
            return result

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_single_document_line_ids = fields.Many2many(
        string="Single document lines",
        comodel_name="pnt.single.document.line",
        relation="pnt_single_document_line_sale_order_line_rel",
        column1="sale_order_line_id",
        column2="pnt_single_document_line_id",
    )
    pnt_single_document_id = fields.Many2one(
        string="DU",
        comodel_name="pnt.single.document",
    )
    pnt_single_document_sale_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id",
        store=True,
    )
    pnt_du_effective_date = fields.Date(
        related="pnt_single_document_sale_id.pnt_effective_date",
    )
    pnt_categ_id = fields.Many2one(
        related="product_id.categ_id",
        store=True,
    )
    pnt_partner_invoice_id = fields.Many2one(
        related="order_id.partner_invoice_id",
        store=True,
    )
    pnt_partner_shipping_id = fields.Many2one(
        related="order_id.partner_shipping_id",
        store=True,
    )
    pnt_client_order_ref = fields.Char(
        related="order_id.client_order_ref",
        store=True,
    )
    pnt_m3 = fields.Float(
        string="M3",
        digits="Product Unit of Measure",
    )
    pnt_certificate_number_sale = fields.Char(
        related="pnt_single_document_line_id.pnt_certificate_number",
        string="N Cert",
        store=True,
    )
    pnt_check_number_certificate_sale_line = fields.Boolean(
        related="order_id.pnt_check_number_certificate_sale",
        string="N Cert",
        readonly=True,
    )
    pnt_rental_manual_container_id = fields.Many2one(
        string="Manual Rental Container",
        comodel_name="product.product",
        readonly=True,
    )
    pnt_rental_manual_waste_id = fields.Many2one(
        string="Manual Rental Waste",
        comodel_name="product.product",
        readonly=True,
    )
    pnt_sd_effective_date = fields.Date(
        related="order_id.pnt_single_document_id.pnt_effective_date",
        store=True,
    )

    @api.depends(
        "move_ids.state",
        "move_ids.scrapped",
        "move_ids.product_uom_qty",
        "move_ids.product_uom",
    )
    def _compute_qty_delivered(self):
        super(SaleOrderLine, self)._compute_qty_delivered()
        for line in self:
            if line.pnt_single_document_line_id:
                line.qty_delivered = line.product_uom_qty

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        if not self.order_id.type_id.pnt_is_DU:
            return super(SaleOrderLine, self)._action_launch_stock_rule(
                previous_product_uom_qty=False
            )
        else:
            return True

    def action_create_invoice_from_lines(self):
        if len(self.order_partner_id) != 1:
            raise UserError(_("El cliente debe ser el mismo para todas las líneas"))
        for line in self:
            if line.invoice_lines:
                raise UserError(
                    _(
                        "Hay una línea del pedido %s que ya está vinculada a una factura."
                    )
                    % line.order_id.name
                )
        obj_move = self.env["account.move"].with_context(
            default_move_type="out_invoice"
        )
        invoice_form = Form(recordp=obj_move, view="account.view_move_form")
        invoice_form.partner_id = self.order_partner_id
        invoice = invoice_form.save()
        new_lines = []
        for line in self:
            data = line._prepare_invoice_line()
            new_lines.append((0, 0, data))
        invoice.invoice_line_ids = new_lines
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        form_view = [(self.env.ref("account.view_move_form").id, "form")]
        if "views" in action:
            action["views"] = form_view + [
                (state, view) for state, view in action["views"] if view != "form"
            ]
        else:
            action["views"] = form_view
        action["res_id"] = invoice.id
        return action

    def _prepare_invoice_line(self, **optional_values):
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        line_du = self.pnt_single_document_line_id
        if (
            line_du
            and line_du.pnt_product_economic_uom.category_id
            != line_du.pnt_product_id.uom_id.category_id
        ):
            accounts = line_du.pnt_product_id.product_tmpl_id.get_product_accounts(
                fiscal_pos=self.order_id.fiscal_position_id
            )
            if accounts["income"]:
                res["account_id"] = accounts["income"]
        res["pnt_m3"] = self.pnt_m3
        return res
class SaleOrderTypology(models.Model):
    _inherit = "sale.order.type"

    pnt_is_DU = fields.Boolean(
        string="for use with DU",
        default=False,
    )
