import socket
import os, re, telnetlib
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PntContainerMovement(models.Model):
    _name = "pnt.container.movement"
    _description = "Pnt Container Movement"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Code",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
        string="Single document line",
        required=True,
        copy=False,
        ondelete="cascade",
        readonly=True,
    )
    pnt_single_document_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id",
        store=True,
    )
    pnt_pickup_date = fields.Datetime(
        string="Movement Date",
        compute="_pnt_pickup_date",
        store=True,
    )
    pnt_product_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_product_id",
        store=True,
    )
    pnt_single_document_state = fields.Selection(
        related="pnt_single_document_line_id.pnt_single_document_id.state",
        store=True,
    )
    pnt_container_movement_type = fields.Selection(
        [
            ("delivery", _("Delivery")),
            ("removal", _("Removal")),
            ("change", _("Change")),
        ],
        string="Container movement type",
        readonly=True,
        # states={
        #     'newdu': [('readonly', False)]
        # },
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_container_delivery_id = fields.Many2one(
        comodel_name="product.product",
        string="Container delivered",
        domain=[("pnt_is_container", "=", True)],
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
        compute="_compute_container",
        store=True,
    )
    pnt_container_delivery_code = fields.Char(
        string="Code container delivered",
    )
    pnt_container_removal_id = fields.Many2one(
        comodel_name="product.product",
        string="Container removed",
        domain=[("pnt_is_container", "=", True)],
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
        compute="_compute_container",
        store=True,
    )
    pnt_container_removal_code = fields.Char(
        string="Code container removed",
    )
    @api.depends("pnt_single_document_line_id","pnt_product_id")
    def _compute_container(self):
        for record in self:
            if record.pnt_product_id and record.pnt_single_document_line_id:
                if (record.pnt_product_id.pnt_container_movement_type
                    in ("delivery")):
                    record.pnt_container_delivery_id = (
                        record.pnt_single_document_line_id.pnt_container_id)
                elif (record.pnt_product_id.pnt_container_movement_type
                    in ("removal")):
                    record.pnt_container_removal_id = (
                        record.pnt_single_document_line_id.pnt_container_id)
                elif (record.pnt_product_id.pnt_container_movement_type
                      in ("change")):
                    record.pnt_container_removal_id = (
                        record.pnt_single_document_line_id.pnt_container_id)
                    record.pnt_container_delivery_id = (
                        record.pnt_single_document_line_id.pnt_container_id)
    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.container.movement", sequence_date=seq_date
            ) or _("New")
        result = super(PntContainerMovement, self).create(vals)
        return result

    @api.depends("pnt_single_document_id")
    def _pnt_pickup_date(self):
        for rec in self:
            if rec.pnt_single_document_id:
                rec.pnt_pickup_date = rec.pnt_single_document_id.pnt_pickup_date
