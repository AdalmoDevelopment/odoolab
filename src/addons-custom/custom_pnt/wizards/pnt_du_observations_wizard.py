from odoo import fields, models
from .. import TASK_STAGES

class PntDuObservationsWiz(models.TransientModel):
    _name = "pnt.du.observations.wiz"
    _description = "DU Observations Wizard"

    pnt_observations = fields.Html(
        string="Observations",
        readonly=True,
    )
