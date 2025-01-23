from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form
from .. import DEFAULT_NEW_DU_WIZ_SCALE_PICKUP_ID, DEFAULT_NEW_DU_WIZ_SCALE_ID


class PntLoadDu(models.TransientModel):
    _name = "pnt.load.du"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single document",
        domain="[('pnt_load_du_visible','=',True)]",
    )
    pnt_single_document_txt = fields.Char(
        string="Single document text",
    )
    pnt_introduction_type = fields.Selection(
        selection=[("reader", _("Barcode reader")), ("manual", _("Manual"))],
        default="reader",
    )

    # Methods
    def load_du(self):
        for rec in self:
            if rec.pnt_single_document_id:
                view_id = self.env.ref(
                    "custom_pnt.pnt_single_document_form_metal_scale_view"
                ).id
                return {
                    "type": "ir.actions.act_window",
                    "name": "Single document",
                    "view_type": "form",
                    "view_mode": "form",
                    "view_id": view_id,
                    "res_model": "pnt.single.document",
                    "res_id": rec.pnt_single_document_id.id,
                    "target": "main",
                }
            else:
                raise UserError(_("Debe indicar un número de DU válido"))

    @api.onchange("pnt_single_document_txt")
    def onchange_pnt_single_document_txt(self):
        for rec in self:
            if rec.pnt_single_document_txt:
                du_obj = self.env["pnt.single.document"].search(
                    [("name", "=", rec.pnt_single_document_txt)], limit=1
                )
                if du_obj:
                    if du_obj.state in ("plant", "dispached"):
                        rec.pnt_single_document_id = du_obj.id
                    else:
                        raise UserError(
                            _(
                                "No puede cargarse el DU "
                                + du_obj.name
                                + " debido a que su estado es "
                                + du_obj.state
                            )
                        )

    def button_new_du(self):
        pickup = self.env["res.partner"].browse(DEFAULT_NEW_DU_WIZ_SCALE_PICKUP_ID)
        scale = self.env["pnt.scales"].browse(DEFAULT_NEW_DU_WIZ_SCALE_ID)
        new_du = Form(
            recordp=self.env["pnt.single.document"],
            view="custom_pnt.pnt_single_document_form_view",
        )
        new_du.pnt_single_document_type = "portal"
        new_du.pnt_partner_pickup_id = pickup
        new_du.pnt_agreement_id = self.env.company.pnt_metal_scale_agreement_id
        new_du.pnt_scales_id = scale
        new_du = new_du.save()
        self.pnt_single_document_id = new_du
        self.pnt_introduction_type = "manual"
        return self.load_du()
