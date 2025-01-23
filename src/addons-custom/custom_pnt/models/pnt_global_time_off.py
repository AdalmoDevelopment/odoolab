from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PntGlobalTimeOff(models.Model):
    _name = "pnt.global.time.off"
    _description = "Global Time Off"
    _order = "pnt_name"
    _rec_name = "pnt_name"
    _sql_constraints = [
        (
            "name_uniq",
            "unique (pnt_name, company_id)",
            "Name already exists.",
        )
    ]
    active = fields.Boolean(
        "Active",
        default=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    pnt_name = fields.Char(
        string="Name",
        required=True,
    )
    pnt_line_ids = fields.One2many(
        string="Leave Lines",
        comodel_name="pnt.global.time.off.line",
        inverse_name="leave_id",
    )


class PntGlobalTimeOffLine(models.Model):
    _name = "pnt.global.time.off.line"
    _description = "Global Time Off Lines"
    _order = "pnt_name"
    _rec_name = "pnt_name"
    _sql_constraints = [
        (
            "name_uniq",
            "unique (pnt_name, company_id)",
            "Name already exists.",
        )
    ]
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    leave_id = fields.Many2one(
        string="Global Time Off",
        comodel_name="pnt.global.time.off",
        required=True,
        ondelete="cascade",
    )
    pnt_name = fields.Char(
        string="Name",
        required=True,
    )
    pnt_date_from = fields.Date(
        string="Start Date",
        required=True,
    )
    pnt_date_to = fields.Date(
        string="End Date",
        required=True,
    )

    @api.constrains("pnt_date_from", "pnt_date_to")
    def _check_dates(self):
        for leave in self:
            if leave.pnt_date_from > leave.pnt_date_to:
                raise ValidationError(
                    _("The start date cannot be greater than the end date.")
                )
