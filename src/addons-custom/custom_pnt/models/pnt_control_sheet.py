from odoo import fields, models


class PntControlSheet(models.Model):
    _name = "pnt.control.sheet"
    _description = "Control Sheets"
    _rec_name = "pnt_name"

    pnt_name = fields.Char(
        string="Name",
        required=True,
    )
    pnt_single_document_id = fields.Many2one(
        string="DU",
        comodel_name="pnt.single.document",
    )
    pnt_sale_id = fields.Many2one(
        string="Sale Order",
        comodel_name="sale.order",
    )
    pnt_purchase_id = fields.Many2one(
        string="Purchase Order",
        comodel_name="purchase.order",
    )
    pnt_move_id = fields.Many2one(
        string="Account Move",
        comodel_name="account.move",
    )
