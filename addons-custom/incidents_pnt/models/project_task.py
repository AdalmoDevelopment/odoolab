from odoo import fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    pnt_single_document_line_id = fields.Many2one(
        string="Lines DU",
        comodel_name="pnt.single.document.line",
    )
    pnt_incidence_ids = fields.One2many(
        comodel_name="pnt.incidence",
        string="Incidences",
        inverse_name="pnt_task_id",
        copy=False,
    )
