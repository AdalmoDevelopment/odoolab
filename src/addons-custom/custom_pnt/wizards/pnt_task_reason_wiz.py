from odoo import fields, models
from .. import TASK_STAGES


class PntTaskReasonWiz(models.TransientModel):
    _name = "pnt.task.reason.wiz"
    _description = "Task Reason Wizard"
    _rec_name = "pnt_reason_id"

    pnt_reason_id = fields.Many2one(
        string="Reason",
        comodel_name="pnt.project.task.reason",
        required=True,
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

    def confirm(self):
        stages = {
            "discount": TASK_STAGES["discount"],
            "invoice": TASK_STAGES["invoiced"],
            "close": TASK_STAGES["closed"],
        }
        task = self._context.get("task_id")
        task_id = self.env["project.task"].browse(task)
        task_id.with_context(control_stage=True).stage_id = stages[self.pnt_type]
        task_id.pnt_reason_id = self.pnt_reason_id
