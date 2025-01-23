from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form


class PntDuConfirmTimesheet(models.TransientModel):
    _name = "pnt.du.confirm.timesheet"
    _description = "Confirm timesheet when service is generated"
    _sql_constraints = [
        (
            "check_hours",
            "check(pnt_hours>0)",
            "The hours must be a value greater than zero.",
        )
    ]

    pnt_hours = fields.Float(
        string="Hours",
        default=0,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )

    def button_register_timesheet(self):
        du = self.env["pnt.single.document"].browse(self.env.context["active_ids"])
        du.write({'pnt_hours': self.pnt_hours})
        # [HU55459] - Tolo - 28/08/2024 - Operativa crear timesheets deshabilitada
        # task = du.task_id
        # employee_task = task.pnt_transport_id
        # employee = (
        #     self.env["hr.employee"]
        #     .sudo()
        #     .search(
        #         [
        #             ("company_id", "=", task.company_id.id),
        #             ("address_id", "!=", False),
        #             ("address_id", "=", employee_task.id),
        #         ]
        #     )
        # )
        # if not employee_task or not employee:
        #     raise UserError(
        #         _("No carrier or no employee linked to the carrier has been found.")
        #     )
        # form_task = Form(recordp=task, view="project.view_task_form2")
        # with form_task.timesheet_ids.new() as line_form:
        #     line_form.date = task.pnt_pickup_date
        #     line_form.employee_id = employee
        #     line_form.name = task.name
        #     line_form.unit_amount = self.pnt_hours
        # form_task.save()
