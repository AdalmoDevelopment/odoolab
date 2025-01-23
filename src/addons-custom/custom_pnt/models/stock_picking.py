# Copyright 2021 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_single_document_id.pnt_single_document_type",
        store=True,
    )
    pnt_single_document_state = fields.Selection(
        related="pnt_single_document_id.state", store=True
    )


class StockMove(models.Model):
    _inherit = "stock.move"

    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_single_document_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id",
        store=True,
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_single_document_line_id.pnt_single_document_id.pnt_single_document_type",
        store=True,
    )
    pnt_sd_effective_date = fields.Date(
        related="pnt_single_document_line_id.pnt_single_document_id.pnt_effective_date",
        store=True,
    )
    pnt_sd_holder_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id.pnt_holder_id",
        store=True,
    )
    pnt_sd_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id.pnt_partner_pickup_id",
        store=True,
    )
