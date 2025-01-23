from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    project_task_id = fields.Many2one(
        comodel_name="project.task",
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
        store=True,
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
    pnt_ship_scale_num = fields.Char(
        string="Ship Scale No",
    )
    pnt_control_sheet_ids = fields.One2many(
        string="Control sheets",
        comodel_name="pnt.control.sheet",
        inverse_name="pnt_purchase_id",
        copy=False,
    )
    pnt_sd_effective_date = fields.Date(
        related="pnt_single_document_id.pnt_effective_date",
        store=True,
    )

    def _create_picking(self):
        # Si el tipo de pedido es de DU no genera stock picking
        if not self.order_type.pnt_is_DU:
            return super(PurchaseOrder, self)._create_picking()
        else:
            return True

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.pnt_single_document_id:
            res["check_total"] = self.amount_total
            res["invoice_date"] = fields.Datetime.now().date()
            res["pnt_ship_scale_num"] = self.pnt_ship_scale_num
            res["pnt_control_sheet_ids"] = self.pnt_control_sheet_ids.ids
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_m3 = fields.Float(
        string="M3",
        digits="Product Unit of Measure",
    )
    pnt_sd_effective_date = fields.Date(
        related="order_id.pnt_single_document_id.pnt_effective_date",
        store=True,
    )
    pnt_single_document_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id",
        store=True,
    )

    def _prepare_account_move_line(self, move=False):
        res = super()._prepare_account_move_line(move=move)
        res.update(
            {
                "pnt_m3": self.pnt_m3,
            }
        )
        return res

    def action_create_invoice_from_lines(self):
        if len(self.partner_id) != 1:
            raise UserError(_("El proveedor debe ser el mismo para todas las líneas"))
        for line in self:
            if line.invoice_lines:
                raise UserError(
                    _(
                        "Hay una línea del pedido %s que ya está vinculada a una factura."
                    )
                    % line.order_id.name
                )
        obj_move = self.env["account.move"].with_context(
            default_move_type="in_invoice"
        )
        invoice_form = Form(recordp=obj_move, view="account.view_move_form")
        invoice_form.partner_id = self.partner_id
        invoice = invoice_form.save()
        new_lines = []
        for line in self:
            data = line._prepare_account_move_line()
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


class PurchaseOrderType(models.Model):
    _inherit = "purchase.order.type"

    pnt_is_DU = fields.Boolean(
        string="for use with DU",
        default=False,
    )
