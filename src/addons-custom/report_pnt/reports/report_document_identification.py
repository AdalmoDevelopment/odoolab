from odoo import _, api, models
from odoo.exceptions import UserError


class ReportDocumentIdentification(models.AbstractModel):
    _name = "report.report_pnt.report_document_identification"
    _description = "Report DI"

    def get_type_operator(self, partner, ttype, ler=False):
        if ler:
            return (
                partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == ttype and
                              ler.id in x.pnt_product_tmpl_waste_ler_ids.ids
                )[:1].pnt_operator_type_id.pnt_type_operator
            )
        else:
            return (
                partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == ttype
                )[:1].pnt_operator_type_id.pnt_type_operator
            )

    def get_nima(self, partner, ttype, ler=False, starting_point=False):
        if ler:
            nima = (
                partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == ttype and
                              ler.id in x.pnt_product_tmpl_waste_ler_ids.ids
                )[:1].pnt_nima_code_id.name
            )
            if starting_point == "origin" and ttype != "producer" and not nima:
                nima = (
                    partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                        lambda x: x.pnt_authorization_code_type == "producer" and
                                  ler.id in x.pnt_product_tmpl_waste_ler_ids.ids
                    )[:1].pnt_nima_code_id.name
                )
            return nima
        else:
            return (
                partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == ttype
                )[:1].pnt_nima_code_id.name
            )

    def get_pgr(self, partner, ttype, ler=False, starting_point=False):
        if ler:
            pgr = (
                partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == ttype and
                              ler.id in x.pnt_product_tmpl_waste_ler_ids.ids
                )[:1].display_name
            )
            if starting_point == "origin" and ttype != "producer" and not pgr:
                pgr = (
                    partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                        lambda x: x.pnt_authorization_code_type == "producer" and
                              ler.id in x.pnt_product_tmpl_waste_ler_ids.ids
                    )[:1].display_name
                )
            return pgr
        else:
            return (
                partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                    lambda x: x.pnt_authorization_code_type == ttype
                )[:1].display_name
            )

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "report_pnt.report_document_identification"
        )
        records = self.env[report.model].browse(docids)
        if any(not x.pnt_di_ids for x in records):
            raise UserError(
                _("No Document Identification found for all the selected documents.")
            )
        return {
            "doc_ids": docids,
            "doc_model": report.model,
            "data": data,
            "docs": records,
            "get_type_operator": self.get_type_operator,
            "get_nima": self.get_nima,
            "get_pgr": self.get_pgr,
        }
