import datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError


class PntPaymentDu(models.TransientModel):
    _name = "pnt.return.du"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single document",
    )

    pnt_note = fields.Char(
        string="Note",
        default="Existen pedidos facturados por lo que no se van a cancelar los pedidos. "
        "Debe realizar una factura rectificativa. Si presiona continuar solo se va a proceder a realizar la devolución del albaran",
    )
    pnt_has_invoice = fields.Boolean(
        related="pnt_single_document_id.pnt_has_invoice", store=False
    )

    def cancel_orders(self):
        self.cancel_purchase_orders()
        self.cancel_sale_orders()

    def cancel_purchase_orders(self):
        for po in self.pnt_single_document_id.pnt_purchase_order_ids:
            if po.invoice_count == 0:
                po.button_cancel()

    def cancel_sale_orders(self):
        for so in self.pnt_single_document_id.pnt_sale_order_ids:
            if so.invoice_count == 0:
                so.action_cancel()

    def create_returns_without_new(self):
        self.cancel_orders()
        # Tratar albaranes
        for pick in self.pnt_single_document_id.pnt_stock_picking_ids:
            srw = self.env["stock.return.picking"].create({"picking_id": pick.id})
            if srw:
                srw._onchange_picking_id()
                new_picking_id, pick_type_id = srw._create_returns()
                if new_picking_id:
                    # Validar los albaranes
                    npi = self.env["stock.picking"].search(
                        [("id", "=", new_picking_id)], limit=1
                    )
                    if npi:
                        # actualizar cantidad hecha
                        for npiline in npi.move_ids_without_package:
                            npiline.quantity_done = npiline.product_uom_qty
                        # Validar albarán
                        npi.button_validate()
                    # Asociar nuevo albaran a DU
                    self.pnt_single_document_id.write(
                        {
                            "pnt_stock_picking_ids": [(4, new_picking_id)],
                        }
                    )
        # Cambiar estado DU -> Cancelado
        self.pnt_single_document_id.action_cancel()
    def create_returns(self):
        self.cancel_orders()
        # Tratar albaranes
        for pick in self.pnt_single_document_id.pnt_stock_picking_ids:
            srw = self.env["stock.return.picking"].create({"picking_id": pick.id})
            if srw:
                srw._onchange_picking_id()
                new_picking_id, pick_type_id = srw._create_returns()
                if new_picking_id:
                    # Validar los albaranes
                    npi = self.env["stock.picking"].search(
                        [("id", "=", new_picking_id)], limit=1
                    )
                    if npi:
                        # actualizar cantidad hecha
                        for npiline in npi.move_ids_without_package:
                            npiline.quantity_done = npiline.product_uom_qty
                        # Validar albarán
                        npi.button_validate()
                    # Asociar nuevo albaran a DU
                    self.pnt_single_document_id.write(
                        {
                            "pnt_stock_picking_ids": [(4, new_picking_id)],
                        }
                    )
        # Cambiar estado DU -> Cancelado
        self.pnt_single_document_id.action_cancel()
        # Duplicar DU
        new_du = self.pnt_single_document_id.with_context(
            type_copy="standard_copy"
        ).copy()
        self.pnt_single_document_id.pnt_du_dest_id = new_du.id
        new_du.action_done_portal()
        return {
            "type": "ir.actions.act_window",
            "res_model": "pnt.single.document",
            "res_id": new_du.id,
            "view_type": "form",
            "view_mode": "form",
            "view_id": self.env.ref("custom_pnt.pnt_single_document_form_view").id,
            "target": "current",
        }
