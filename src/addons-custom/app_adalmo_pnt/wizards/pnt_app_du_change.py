import datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError
from datetime import date

class PntAppDuChange(models.TransientModel):
    _name = "pnt.app.du.change"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    transfer_id = fields.Char(
        string="Transfer Id",
    )
    pnt_current_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Current single document",
    )
    pnt_new_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="New single document",
        domain="[('pnt_single_document_type', '=', 'pickup'), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    # Methods
    def action_change_du(self):
        for du in self:
            # Cabeceras
            app_du_ids = self.env["pnt.app.du"].search([
                ("transfer_id","=",self.transfer_id)
            ])
            if app_du_ids:
                for app_du in app_du_ids:
                    app_du.pnt_single_document_id = self.pnt_new_single_document_id
            # Lineas
            app_du_lineas_ids = self.env["pnt.app.du.lineas"].search([
                ("transfer_id","=",self.transfer_id)
            ])
            if app_du_lineas_ids:
                for app_du_lineas in app_du_lineas_ids:
                    app_du_lineas.pnt_single_document_id = self.pnt_new_single_document_id
            # Fotos
            app_du_fotos_ids = self.env["pnt.app.du.fotos"].search([
                ("transfer_id","=",self.transfer_id)
            ])
            if app_du_fotos_ids:
                for app_du_fotos in app_du_fotos_ids:
                    app_du_fotos.pnt_single_document_id = self.pnt_new_single_document_id
            return True

    # def action_generate_tags(self):
    #     for tag in self:
    #         if tag.pnt_tag_waste_ids:
    #             docids = []
    #             for tag_qr in tag.pnt_tag_waste_ids:
    #                 for qty in range(tag_qr.pnt_quantity):
    #                     newtag = self.env["pnt.app.tag"].create(
    #                         {
    #                             "pnt_partner_id": tag.pnt_partner_id.id,
    #                             "pnt_holder_id": tag.pnt_holder_id.id,
    #                             "pnt_product_id": tag_qr.pnt_product_id.id,
    #                             "pnt_functional_unit_id": tag.pnt_functional_unit_id.id,
    #                             "pnt_tag_log_type": "manual",
    #                             "pnt_move_type": "outgoing",
    #                             "pnt_print_tag_date": tag.pnt_print_date,
    #                             "pnt_date": tag.pnt_date,
    #                         }
    #                     )
    #                     if newtag:
    #                         newtag.save_tag_log(False)
    #                         docids.append(newtag.id)
    #             if tag.pnt_tag_type in ('dangerous','notdangerous'):
    #                 xmlid = "app_adalmo_pnt.pnt_app_tag_report"
    #             else:
    #                 xmlid = "app_adalmo_pnt.pnt_app_tag_sanitary_report"
    #             action = self.env.ref(xmlid).report_action(docids)
    #             return action
    #         else:
    #             raise UserError(
    #                 _(
    #                     "Debe introducir residuos para poder generar las etiquetas"
    #                 )
    #             )
