from odoo import _, models
from io import BytesIO

from odoo.exceptions import UserError


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, res_ids=None, data=None):
        res = super()._render_qweb_pdf(res_ids=res_ids, data=data)
        if res_ids and self.xml_id in ('report_pnt.pnt_budget_contract_report',
                                       'report_pnt.pnt_budget_contract_report_2',
                                       'report_pnt.pnt_invoice_grouped_report',):
            if self.xml_id == 'report_pnt.pnt_invoice_grouped_report':
                report_action = 'account.report_invoice_with_payments'
            else:
                report_action = 'report_pnt.report_conditions_document_adalmo'
            report_obj = self.env['ir.actions.report']._get_report_from_name(
                report_action)
            pdf_conditions, _ = report_obj._render_qweb_pdf(res_ids, data)
            streams = [BytesIO(res[0])] + [BytesIO(pdf_conditions)]
            merge = self._merge_pdfs(streams)
            return (merge, "pdf")

        return res


