from odoo import fields, models


class PntProjectTaskReason(models.Model):
    _name = "pnt.project.task.reason"
    _description = "Project Task Reason"
    _rec_name = "pnt_name"
    _sql_constraints = [
        (
            "name_uniq",
            "unique (pnt_name, company_id)",
            "Reason already exists.",
        )
    ]
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    pnt_name = fields.Char(
        string="Reason",
        required=True,
        translate=True,
    )
    pnt_type = fields.Selection(
        string="Type",
        required=True,
        selection=[
            ("discount", "Discount"),
            ("invoice", "Invoice"),
            ("close", "Close"),
        ],
    )
