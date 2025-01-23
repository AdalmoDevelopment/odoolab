from odoo import _, fields, models


class PntPrintTagFormat(models.TransientModel):
    _name = "pnt.print.tag.format"

    pnt_task_ids = fields.Many2many(
        string="Task",
        comodel_name="project.task",
        relation="pnt_print_tag_format_task_rel",
    )
    pnt_select_report = fields.Selection(
        [
            ("sanitary", _("Sanitary Tag")),
            ("dangerous", _("Dangerous Tag")),
            ("no_dangerous", _("No Dangerous Tag")),
            ("format", _("Format")),
        ],
        string="Select report",
        copy=False,
        default="sanitary",
        index=True,
        tracking=3,
    )

    def send_to_print(self):
        dus = self.pnt_task_ids.pnt_single_document_id
        if self.pnt_select_report == "dangerous":
            return dus.action_generate_tag()
        if self.pnt_select_report == "no_dangerous":
            return dus.action_generate_tag_no_dangerous()
        if self.pnt_select_report == "sanitary":
            return dus.action_generate_tag_sanitary()
        return self.env.ref("report_pnt.pnt_du_report_from_task").report_action(
            self.pnt_task_ids.ids
        )
