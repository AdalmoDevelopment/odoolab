from lxml import etree
from odoo import fields, models, api, _

class AccountMove(models.Model):
    _inherit = "account.move"

    imagedata = fields.Binary(
        string='Dígital signature',
        track_visibility='onchange',
    )
    rawdata = fields.Text(
        string='Biometric data',
    )

    @api.model
    def signature_assign(self, args):
         invoice_id = self.env['account.move'].search([('id','=',args['invoice_id'])],limit=1)
         if invoice_id:
             invoice_id.write({
                 'imagedata': args['imagedata'],
                 'rawdata': args['rawdata'],
             })