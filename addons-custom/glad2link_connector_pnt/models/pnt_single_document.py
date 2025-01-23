import base64
import logging
from io import BytesIO

import PyPDF2
from email_validator import validate_email
import datetime

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PntSingleDocument(models.Model):
    _inherit = "pnt.single.document"

    pnt_gla2link_id = fields.Char(
        string="Glad2Link ID",
        copy=False,
        readonly=True,
    )
    pnt_gla2link_datetime = fields.Datetime(
        string="Glad2Link Datetime",
        copy=False,
        readonly=True,
    )
    pnt_du_signed_file_email_sent = fields.Boolean(
        string="Unique document signed email sent",
        copy=False,
        readonly=True,
    )

    def _data_mail(self, du):
        template_id = self.env["ir.model.data"].xmlid_to_res_id(
            "glad2link_connector_pnt.email_template_du_signed"
        )
        data = self.env["mail.compose.message"].onchange_template_id(
            template_id, "comment", "pnt.single.document", du.id
        )
        return data

    def _get_email_glad2link(self):
        contacts = self.pnt_partner_pickup_id.child_ids.filtered(
            lambda x: x.type == "contact" and x.pnt_send_du_signed
        )
        emails = "".join(contacts.filtered("email").mapped("email"))
        emails_valids = []
        for email in emails.split(","):
            try:
                validate_email(email)
                emails_valids.append(email)
            except Exception as e:
                _logger.info(e)
        return emails_valids

    def _get_dus_from_invoice(self, invoice):
        return invoice.invoice_line_ids.sale_line_ids.order_id.pnt_single_document_id

    def _send_mail_du_signed(self, values=None, force_send=False, invoice=False):
        vals = values or {}
        if not force_send and not (vals.get("pnt_du_signed_file") or vals.get("state")):
            return
        if invoice:
            dus = self._get_dus_from_invoice(invoice)
        else:
            dus = self.filtered(lambda x: x.pnt_du_signed_file)
        if not force_send:
            dus = dus.filtered(lambda x: x.state == "finished")
        if not dus:
            return
        obj_mail = self.env["mail.mail"].sudo()
        obj_attachment = self.env["ir.attachment"].sudo()
        attachment = []
        for du in dus:
            name_attachments = {}
            invoice_report_id = False
            final_pdf_id = False
            attachments = obj_attachment.search(
                [
                    ("res_model", "=", "pnt.single.document"),
                    ("res_id", "in", invoice and dus.ids or du.ids),
                    ("res_field", "=", "pnt_du_signed_file"),
                ]
            )
            for attch in attachments.sudo():
                name = self.browse(attch.res_id).pnt_filename_du_signed
                name_attachments[attch] = attch.name
                attch.name = name or attch.name
            attachments = attachments.ids
            for email in du._get_email_glad2link():
                if invoice and not invoice_report_id:
                    document, doc_format = (
                        self.env["ir.actions.report"]
                        ._get_report_from_name("account.report_invoice_with_payments")
                        ._render_qweb_pdf(res_ids=invoice.ids)
                    )
                    pdf_document = base64.b64encode(document)
                    invoice_report_id = obj_attachment.create(
                        {
                            "name": (
                                invoice.name
                                if invoice.name and invoice.name.endswith(".pdf")
                                else invoice.name + ".pdf"
                            ),
                            "type": "binary",
                            "datas": pdf_document,
                            "company_id": self.env.company.id,
                            "res_model": "account.move",
                            "res_id": invoice.id,
                            "create_uid": self.env.user.id,
                        }
                    )
                    attachment += invoice_report_id.ids
                if invoice and not final_pdf_id:
                    pdfs = obj_attachment.browse(attachments)
                    merger = PyPDF2.PdfFileMerger()
                    try:
                        for pdf in pdfs:
                            merger.append(
                                BytesIO(base64.b64decode(pdf.datas)),
                                import_bookmarks=False,
                            )
                        merged_bytes = BytesIO()
                        merger.write(merged_bytes)
                        merger.close()
                    except Exception as e:
                        raise UserError(_("Error merging PDFs: %s") % str(e))
                    final_pdf = merged_bytes.getvalue()
                    final_pdf_id = obj_attachment.create(
                        {
                            "name": _("Documents.pdf"),
                            "type": "binary",
                            "datas": base64.b64encode(final_pdf),
                            "company_id": self.env.company.id,
                            "res_model": "account.move",
                            "res_id": invoice.id,
                            "create_uid": self.env.user.id,
                        }
                    )
                    attachment += final_pdf_id.ids
                template_data = self._data_mail(du)["value"]
                mail_data = {
                    "author_id": self.env.user.partner_id.id,
                    "email_to": email,
                    "reply_to": du.company_id.pnt_invoice_send_email,
                    "attachment_ids": [(6, 0, attachment or attachments)],
                }
                template_data.update(mail_data)
                template_data["body_html"] = template_data["body"]
                mail_data = template_data
                mail = obj_mail.create(mail_data)
                mail.send()
                du.pnt_du_signed_file_email_sent = True
                du.pnt_date_email_sent = datetime.datetime.now()
            for attch in name_attachments:
                attch.name = name_attachments[attch]
            if invoice:
                break

    def write(self, vals):
        res = super().write(vals)
        self._send_mail_du_signed(vals)
        return res
