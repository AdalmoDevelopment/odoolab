from odoo import _, fields, models


class PntSingleDocument(models.Model):
    _inherit = "pnt.single.document"
    _description = "Pnt single document"

    pnt_incidence_ids = fields.One2many(
        comodel_name="pnt.incidence",
        string="Incidence",
        inverse_name="pnt_single_document_id",
        copy=False,
    )

    incidence_count = fields.Integer(
        string="# Incidences",
        compute="_compute_incidence_count",
    )

    def _compute_incidence_count(self):
        for rec in self:
            rec.incidence_count = len(rec.pnt_incidence_ids)

    def action_view_incidences(self):
        self.ensure_one()
        return {
            "name": _("Incidences"),
            "type": "ir.actions.act_window",
            "res_model": "pnt.incidence",
            "view_mode": "tree,form",
            "domain": [("pnt_single_document_id", "=", self.id)],
            "context": {
                "default_pnt_single_document_id": self.id,
                "default_delivery_note_number": self.name,
                "default_customer_id": self.pnt_holder_id.id,
            },
        }


class PntSIngleDocumentLine(models.Model):
    _inherit = "pnt.single.document.line"

    pnt_incidence_ids = fields.One2many(
        comodel_name="pnt.incidence",
        string="Incidence",
        inverse_name="pnt_single_document_line_id",
        copy=False,
    )

    def show_form_incidence(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "incidents_pnt.action_pnt_incidence"
        )
        action["target"] = "new"
        action["views"] = [
            (self.env.ref("incidents_pnt.pnt_incidence_view_form").id, "form")
        ]
        action["context"] = dict(self._context)
        action["context"][
            "default_name"
        ] = f"INC {self.pnt_single_document_id.name} - {self.id}"
        action["context"][
            "default_customer_id"
        ] = self.pnt_single_document_id.pnt_holder_id.id
        action["context"][
            "default_date"
        ] = self.pnt_single_document_id.task_id.pnt_pickup_date
        action["context"]["default_material_id"] = self.pnt_product_id.id
        action["context"]["default_equipment_id"] = self.pnt_container_id.id
        action["context"]["default_input_weight"] = self.pnt_product_uom_qty
        action["context"][
            "default_pnt_single_document_id"
        ] = self.pnt_single_document_id.id
        action["context"]["default_pnt_single_document_line_id"] = self.id
        return action

    def _create_task_incidence(self, incidence):
        incident = [(4, incidence.id)]
        return self.env["project.task"].create(
            {
                "project_id": self.env.company.pnt_single_document_issue_project_id.id,
                "name": f"INC {self.pnt_single_document_id.name} - {self.id}",
                "pnt_single_document_id": self.pnt_single_document_id.id,
                "pnt_single_document_line_id": self.id,
                "pnt_incidence_ids": incident,
            }
        )
