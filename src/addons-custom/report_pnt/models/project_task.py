from odoo import _, api, fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"

    def _send_tag(self,docids):
        xmlid = "app_adalmo_pnt.pnt_app_tag_sanitary_report"
        action = self.env.ref(xmlid).report_action(docids)
        return action

    def pnt_print_tag_format_sanitary(self):
        # self.pnt_print_tags()
        docids = []
        for pt in self:
            waste_lines = (
                pt.pnt_single_document_id.pnt_single_document_line_ids.filtered(
                lambda r: r.pnt_is_waste and r.pnt_product_id.pnt_is_sanitary
            ))
            if waste_lines:
                for tag_qr in waste_lines:
                    newtag = self.env["pnt.app.tag"].create(
                        {
                            "pnt_partner_id":
                                pt.pnt_single_document_id.pnt_partner_pickup_id.id,
                            "pnt_single_document_line_id": tag_qr.id,
                            "pnt_product_id": tag_qr.pnt_product_id.id,
                            "pnt_tag_log_type": "du",
                            "pnt_move_type": "outgoing",
                            "pnt_date":
                                pt.pnt_single_document_id.pnt_pickup_date.date(),
                        }
                    )
                    if newtag:
                        newtag.save_tag_log(False)
                        docids.append(newtag.id)
        self._send_tag(docids)
        # view = self.env.ref('report_pnt.view_form_pnt_print_tag_format')
        # wiz = self.env['pnt.print.tag.format'].create({})
        # return {
        #     'name': _('Print Tags/Format'),
        #     'type': 'ir.actions.act_window',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'pnt.print.tag.format',
        #     'views': [(view.id, 'form')],
        #     'view_id': view.id,
        #     'target': 'new',
        #     'context': self.env.context,
        # }

    def pnt_print_tags(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'pnt.print.tag.format',
            'view_mode': 'form',
            'context': {
                'active_model': 'project.task',
                'active_ids': self.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

