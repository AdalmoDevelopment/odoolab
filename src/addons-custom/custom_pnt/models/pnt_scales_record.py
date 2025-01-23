import socket
import os, re, telnetlib
import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PntScalesRecord(models.Model):
    _name = "pnt.scales.record"
    _description = "Pnt Scales Record"
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
    pnt_scales_domain_ids = fields.Many2many(
        related="pnt_single_document_id.pnt_scales_domain_ids",
    )
    pnt_holder_id = fields.Many2one(
        related='pnt_single_document_id.pnt_holder_id',
        string='Holders',
        required=True,
    )
    pnt_product_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_product_id",
        store=True,
    )
    pnt_single_document_state = fields.Selection(
        related="pnt_single_document_line_id.pnt_single_document_id.state",
        store=True,
    )
    pnt_first_weighing_scales_id = fields.Many2one(
        comodel_name="pnt.scales",
        string="First weighing scales",
        copy=False,
        readonly=True,
        compute="_compute_pnt_scale_id",
        store=True,
    )
    pnt_first_weighing_user_id = fields.Many2one(
        comodel_name="res.users",
        string="First weighing user",
        copy=False,
        readonly=True,
    )
    pnt_first_weighing_date = fields.Datetime(
        string="First weighing date",
    )
    pnt_first_weighing_qty = fields.Float(
        string="First weighing",
        default=0.0,
        digits="Product Unit of Measure",
    )
    pnt_first_weighing_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="First Weighing Unit of Measure",
        store=True,
        compute="_compute_uom",
    )
    pnt_second_weighing_scales_id = fields.Many2one(
        comodel_name="pnt.scales",
        string="Second weighing scales",
        copy=False,
        readonly=True,
        compute="_compute_pnt_scale_id",
        store=True,
    )
    pnt_second_weighing_user_id = fields.Many2one(
        comodel_name="res.users",
        string="Second weighing user",
        copy=False,
        readonly=True,
    )
    pnt_second_weighing_date = fields.Datetime(
        string="Second weighing date",
    )
    pnt_second_weighing_qty = fields.Float(
        string="Second weighing",
        default=0.0,
        digits="Product Unit of Measure",
    )
    pnt_second_weighing_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Second Weighing Unit of Measure",
        store=True,
        compute="_compute_uom",
    )
    pnt_weighing_qty = fields.Float(
        string="Weighing",
        default=0.0,
        digits="Product Unit of Measure",
        store=True,
        copy=False,
        compute="_compute_pnt_weighing_qty",
    )
    pnt_weighing_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Weighing Unit of Measure",
        store=True,
        compute="_compute_uom",
    )
    pnt_weight_warning = fields.Char(
        string="Warning",
        default="La primera pesada es menor que la segunda pesada",
    )
    pnt_show_warning = fields.Boolean(
        compute="compute_show_warning",
    )

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.scales.record", sequence_date=seq_date
            ) or _("New")
        result = super(PntScalesRecord, self).create(vals)
        return result

    @api.depends("pnt_first_weighing_qty", "pnt_second_weighing_qty")
    def compute_show_warning(self):
        for record in self:
            result = False
            if not record.pnt_single_document_id.pnt_partner_delivery_id.parent_id:
                partner_delivery = record.pnt_single_document_id.pnt_partner_delivery_id
            else:
                partner_delivery = (
                    record.pnt_single_document_id.pnt_partner_delivery_id.parent_id
                )
            if (
                partner_delivery == self.env.company.partner_id
                and record.pnt_second_weighing_qty > 0
            ):
                if record.pnt_first_weighing_qty < record.pnt_second_weighing_qty:
                    result = True
            record.pnt_show_warning = result

    @api.depends("pnt_single_document_line_id")
    def _compute_pnt_scale_id(self):
        for record in self:
            if record.pnt_single_document_line_id.pnt_single_document_id.pnt_scales_id:
                record.pnt_first_weighing_scales_id = (
                    record.pnt_single_document_line_id.pnt_single_document_id.pnt_scales_id
                )
                record.pnt_second_weighing_scales_id = (
                    record.pnt_single_document_line_id.pnt_single_document_id.pnt_scales_id
                )

    @api.depends("pnt_first_weighing_qty", "pnt_second_weighing_qty")
    def _compute_pnt_weighing_qty(self):
        for record in self:
            # Primero se comprueba si tiene segundo peso
            if record.pnt_second_weighing_qty:
                if record.pnt_first_weighing_qty > record.pnt_second_weighing_qty:
                    record.pnt_weighing_qty = (
                        record.pnt_first_weighing_qty - record.pnt_second_weighing_qty
                    )
                else:
                    record.pnt_weighing_qty = (
                        record.pnt_second_weighing_qty - record.pnt_first_weighing_qty
                    )

    @api.depends(
        "pnt_single_document_line_id",
        "pnt_first_weighing_scales_id",
        "pnt_second_weighing_scales_id",
    )
    def _compute_uom(self):
        for record in self:
            record.pnt_weighing_uom = record.pnt_single_document_line_id.pnt_product_uom
            if (
                record.pnt_first_weighing_scales_id
                and record.pnt_first_weighing_scales_id.pnt_scale_uom
            ):
                record.pnt_first_weighing_uom = (
                    record.pnt_first_weighing_scales_id.pnt_scale_uom
                )
            else:
                record.pnt_first_weighing_uom = (
                    record.pnt_single_document_line_id.pnt_product_uom
                )
            if (
                record.pnt_second_weighing_scales_id
                and record.pnt_second_weighing_scales_id.pnt_scale_uom
            ):
                record.pnt_second_weighing_uom = (
                    record.pnt_second_weighing_scales_id.pnt_scale_uom
                )
            else:
                record.pnt_second_weighing_uom = (
                    record.pnt_single_document_line_id.pnt_product_uom
                )

    @api.onchange("pnt_first_weighing_qty")
    def _onchange_pnt_first_weighing_qty(self):
        for record in self:
            record.pnt_first_weighing_date = fields.Datetime.now()
            record.pnt_first_weighing_user_id = self.env.user

    @api.onchange("pnt_second_weighing_qty")
    def _onchange_pnt_second_weighing_qty(self):
        for record in self:
            record.pnt_second_weighing_date = fields.Datetime.now()
            record.pnt_second_weighing_user_id = self.env.user
            record.pnt_single_document_id.pnt_last_weighing_qty = (
                record.pnt_second_weighing_qty
            )

    @api.onchange("pnt_single_document_line_id")
    def _onchange_pnt_single_document_line_id(self):
        for record in self:
            record.pnt_second_weighing_scales_id = (
                record.pnt_single_document_line_id.pnt_single_document_id.pnt_scales_id
            )
            record.pnt_first_weighing_scales_id = (
                record.pnt_single_document_line_id.pnt_single_document_id.pnt_scales_id
            )

    @api.onchange("pnt_weighing_qty")
    def _onchange_pnt_weighing_qty(self):
        for record in self:
            record.pnt_single_document_line_id.pnt_product_uom_qty = (
                record.pnt_weighing_qty
            )
            record.pnt_single_document_line_id.onchange_pnt_product_uom_qty()

    def scale_read_first(self):
        scales = None
        scales = self.pnt_first_weighing_scales_id
        if scales:
            rw = scales.scale_read()
            if rw >= 0:
                self.pnt_first_weighing_qty = rw
                self._onchange_pnt_first_weighing_qty()
                self.pnt_single_document_line_id.pnt_product_uom_qty = (
                    self.pnt_weighing_qty
                )
                self.pnt_single_document_line_id.onchange_pnt_product_uom_qty()
            else:
                raise UserError(
                    _("No puede leerse el peso. Revise si está conectada la báscula")
                )
        else:
            raise UserError(
                _(
                    "Debe asignar una báscula a la primera pesada para poder leer el peso"
                )
            )

    def scale_read_second(self):
        scales = None
        scales = self.pnt_second_weighing_scales_id
        if scales:
            rw = scales.scale_read()
            if rw >= 0:
                self.pnt_second_weighing_qty = rw
                self._onchange_pnt_second_weighing_qty()
                self.pnt_single_document_line_id.pnt_product_uom_qty = (
                    self.pnt_weighing_qty
                )
                self.pnt_single_document_line_id.onchange_pnt_product_uom_qty()
            else:
                raise UserError(
                    _("No puede leerse el peso. Revise si está conectada la báscula")
                )
        else:
            raise UserError(
                _(
                    "Debe asignar una báscula a la segunda pesada para poder leer el peso"
                )
            )
