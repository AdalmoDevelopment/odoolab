# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ReportTagApp(models.AbstractModel):
    _name = "report.app_adalmo_pnt.pnt_report_app_tag"
    _description = "Format for app tag"

    def _get_value(self, id_tag, field):
        value = ""
        tag_id = self.env["pnt.app.tag"].browse(id_tag)
        if tag_id:
            value = tag_id[field]
        return value

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env["pnt.app.tag"].browse(docids)
        return {
            "doc_ids": docs.ids,
            "doc_model": "pnt.app.tag",
            "docs": docs,
            "proforma": True,
        }
