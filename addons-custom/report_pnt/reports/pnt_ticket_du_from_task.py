from odoo.addons.custom_pnt.__init__ import TASK_STAGES

from odoo import api, models


class ReportTicketDUFromTask(models.AbstractModel):
    _inherit = "report.report_pnt.pnt_report_du"
    _name = "report.report_pnt.pnt_report_du_from_task"
    _description = "Ticket DU (task)"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "report_pnt.pnt_report_du_from_task"
        )
        records = self.env[report.model].browse(docids)
        for record in records:
            if (record.filtered("pnt_single_document_id").stage_id.id not in
                    (TASK_STAGES["cancelled"],TASK_STAGES["done"])):
                record.filtered("pnt_single_document_id").stage_id \
                    = TASK_STAGES["process"]
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "docs": records,
            "proforma": True,
        }
