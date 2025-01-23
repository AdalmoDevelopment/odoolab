from odoo.addons.custom_pnt.__init__ import TASK_STAGES

from odoo import api, models


class ReportTicketDU(models.AbstractModel):
    _name = "report.report_pnt.pnt_report_du"
    _description = "Ticket para DU"

    def _get_value(self, id_du, field):
        value = ""
        du_id = self.env["pnt.single.document"].browse(id_du)
        if du_id:
            value = du_id[field]
        return value

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "report_pnt.pnt_report_du"
        )
        records = self.env[report.model].browse(docids)
        for record in records:
            if (record.task_id.stage_id.id not in
                    (TASK_STAGES["cancelled"],TASK_STAGES["done"])):
                record.task_id.stage_id = TASK_STAGES["process"]
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "docs": records,
            "proforma": True,
        }
