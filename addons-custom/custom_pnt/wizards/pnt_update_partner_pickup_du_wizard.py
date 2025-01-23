import datetime
from odoo import api, fields, models, exceptions, _
from odoo.exceptions import UserError


class PntUpdatePartnerPickupDu(models.TransientModel):
    _name = "pnt.update.partner.pickup.du"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single document",
    )

    current_pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
        string="Current pickup",
    )

    pnt_partner_pickup_id = fields.Many2one(
        comodel_name="res.partner",
        string="New pickup",
    )

    # Methods
    # @api.multi
    def update_pickup(self):
        if self.pnt_partner_pickup_id:
            if self.pnt_partner_pickup_id.pnt_dni_date_validity:
                date_val = self.pnt_partner_pickup_id.pnt_dni_date_validity
            else:
                date_val = datetime(1900, 1, 1, 00, 00, 00, 00000).date()
            if date_val < fields.Date.today():
                self.pnt_partner_pickup_id = None
                raise UserError(
                    _(
                        "El DNI que se tiene en la base de datos tiene la fecha de Validez vencida o la fecha de validez está en blanco"
                    )
                )
            # Comprobar que esté subida la imagen del DNI
            if not self.pnt_partner_pickup_id.pnt_dni_image:
                self.pnt_partner_pickup_id = None
                raise UserError(_("El partner no tienen subida la imagen del DNI"))
            # Actualizar recogida en DU
            self.pnt_single_document_id.pnt_partner_pickup_id = (
                self.pnt_partner_pickup_id
            )
            # Asignar recogida a tercero
            self.pnt_single_document_id.add_tercero()
            # Actualizar precios en funcion del muevo partner asignado
            for line in self.pnt_single_document_id.pnt_single_document_line_ids:
                line.compute_pnt_price_unit()
                line.compute_pnt_price_subtotal()
        else:
            raise UserError(
                _("Debe indicar una RECOGIDA NUEVA para poder actualizar el DU")
            )
