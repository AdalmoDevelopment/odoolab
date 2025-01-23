import base64

from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.exceptions import UserError


class PntSingleDocument(models.Model):
    _inherit = "pnt.single.document"

    pnt_app_du_id = fields.Many2one(
        comodel_name="pnt.app.du",
        string="DU app record",
    )
    def generate_app_signed_report_file(self):
        self.ensure_one()
        lang = self.env.user.lang
        report_id = self.sudo().env.ref('report_pnt.pnt_du_report_grouped')
        pdf_content, mimetype = (report_id.sudo().with_context(lang=lang)
                                 ._render_qweb_pdf(res_ids=self.id))
        self.pnt_du_signed_file = base64.b64encode(pdf_content)

    def action_app_send(self):
        self.ensure_one()
        template = self.company_id.du_app_mail_confirmation_template_id
        compose_form = self.env.ref(
            "mail.email_compose_message_wizard_form",
            False,
        )
        ctx = dict(
            default_model="pnt.single.document",
            default_res_id=self.id,
            default_use_template=bool(template),
            default_template_id=template and template.id or False,
            default_composition_mode="comment",
            user_id=self.env.user.id,
        )
        return {
            "name": _("Compose Email"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "mail.compose.message",
            "views": [(compose_form.id, "form")],
            "view_id": compose_form.id,
            "target": "new",
            "context": ctx,
        }

    def action_generate_tag(self):
        docids = []
        for du in self:
            waste_lines = du.pnt_single_document_line_ids.filtered(
                lambda r: r.pnt_is_waste
                and not r.pnt_product_id.pnt_is_sanitary
                and r.pnt_product_id.pnt_is_dangerous
            )
            if waste_lines:
                for tag_qr in waste_lines:
                    if int(tag_qr.pnt_container_qty) == 0:
                        repeticions = 1
                    else:
                        repeticions = int(tag_qr.pnt_container_qty)
                    for qty in range(repeticions):
                        newtag = self.env["pnt.app.tag"].create(
                            {
                                "pnt_partner_id": du.pnt_partner_pickup_id.id,
                                "pnt_holder_id": du.pnt_holder_id.id,
                                "pnt_single_document_line_id": tag_qr.id,
                                "pnt_product_id": tag_qr.pnt_product_id.id,
                                "pnt_tag_log_type": "du",
                                "pnt_move_type": "outgoing",
                                "pnt_date": du.pnt_pickup_date.date(),
                                "pnt_print_tag_date":
                                    du.pnt_partner_pickup_id.pnt_print_date_on_labels,
                            }
                        )
                        if newtag:
                            newtag.save_tag_log(False)
                            docids.append(newtag.id)
        if docids:
            xmlid = "app_adalmo_pnt.pnt_app_tag_report"
            action = self.env.ref(xmlid).report_action(docids)
            return action
        raise UserError(_("No hay etiquetas de PELIGROSOS en el DU activo"))

    def action_generate_tag_no_dangerous(self):
        docids = []
        for du in self:
            waste_lines = du.pnt_single_document_line_ids.filtered(
                lambda r: r.pnt_is_waste
                and not r.pnt_product_id.pnt_is_sanitary
                and not r.pnt_product_id.pnt_is_dangerous
            )
            if waste_lines:
                for tag_qr in waste_lines:
                    if int(tag_qr.pnt_container_qty) == 0:
                        repeticions = 1
                    else:
                        repeticions = int(tag_qr.pnt_container_qty)
                    for qty in range(repeticions):
                        newtag = self.env["pnt.app.tag"].create(
                            {
                                "pnt_partner_id": du.pnt_partner_pickup_id.id,
                                "pnt_holder_id": du.pnt_holder_id.id,
                                "pnt_single_document_line_id": tag_qr.id,
                                "pnt_product_id": tag_qr.pnt_product_id.id,
                                "pnt_tag_log_type": "du",
                                "pnt_move_type": "outgoing",
                                "pnt_date": du.pnt_pickup_date.date(),
                                "pnt_print_tag_date":
                                    du.pnt_partner_pickup_id.pnt_print_date_on_labels,
                            }
                        )
                        if newtag:
                            newtag.save_tag_log(False)
                            docids.append(newtag.id)
        if docids:
            xmlid = "app_adalmo_pnt.pnt_app_tag_report"
            action = self.env.ref(xmlid).report_action(docids)
            return action
        raise UserError(_("No hay etiquetas de NO PELIGROSOS en el DU activo"))

    def action_generate_tag_sanitary(self):
        docids = []
        for du in self:
            waste_lines = du.pnt_single_document_line_ids.filtered(
                lambda r: r.pnt_is_waste and r.pnt_product_id.pnt_is_sanitary
            )
            if waste_lines:
                for tag_qr in waste_lines:
                    if int(tag_qr.pnt_container_qty) == 0:
                        repeticions = 1
                    else:
                        repeticions = int(tag_qr.pnt_container_qty)
                    for qty in range(repeticions):
                        newtag = self.env["pnt.app.tag"].create(
                            {
                                "pnt_partner_id": du.pnt_partner_pickup_id.id,
                                "pnt_holder_id": du.pnt_holder_id.id,
                                "pnt_single_document_line_id": tag_qr.id,
                                "pnt_product_id": tag_qr.pnt_product_id.id,
                                "pnt_tag_log_type": "du",
                                "pnt_move_type": "outgoing",
                                "pnt_date": du.pnt_pickup_date.date(),
                                "pnt_print_tag_date":
                                    du.pnt_partner_pickup_id.pnt_print_date_on_labels,
                            }
                        )
                        if newtag:
                            newtag.save_tag_log(False)
                            docids.append(newtag.id)
        if docids:
            xmlid = "app_adalmo_pnt.pnt_app_tag_sanitary_report"
            action = self.env.ref(xmlid).report_action(docids)
            return action
        raise UserError(_("No hay etiquetas de SANITARIOS en el DU activo"))


class PntSingleDocumentLine(models.Model):
    _inherit = "pnt.single.document.line"

    pnt_tag_app = fields.Char(
        string="Tag app text",
    )
    pnt_app_tag_id = fields.Many2one(
        comodel_name="pnt.app.tag",
        string="Tag app",
        compute="_pnt_line_du_tag",
        store=True,
    )
    pnt_functional_unit_id = fields.Many2one(
        related="pnt_app_tag_id.pnt_functional_unit_id",
        store=True,
    )
    @api.depends("pnt_tag_app")
    def _pnt_line_du_tag(self):
        for tag in self:
            tag.pnt_app_tag_id = None
            if tag.pnt_tag_app:
                tag_obj = self.env['pnt.app.tag'].search([
                        ('name','=',tag.pnt_tag_app)],
                    limit=1)
                if tag_obj:
                    tag.pnt_app_tag_id = tag_obj
