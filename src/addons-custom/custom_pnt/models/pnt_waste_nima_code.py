from odoo import models, fields, _, api


class PntNimaCode(models.Model):
    _name = "pnt.nima.code"
    _description = "Pnt NIMA Code"

    name = fields.Char(
        string="NIMA",
        required=True,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
    )
    pnt_waste_authorization_code_ids = fields.One2many(
        string="Waste Authorizatioin Code",
        comodel_name="pnt.authorization.code",
        inverse_name="pnt_nima_code_id",
    )
    pnt_duplicate_nima_message = fields.Text(
        string="Has duplicate nima",
        store=False
    )

    @api.onchange('name')
    def _compute_has_duplicate_nima(self):
        for record in self:
            nimas = record.search([('name', '=', record.name),
                                 ('pnt_partner_id.company_type', '=', 'company')
                                 ])
            if nimas:
                message = 'Este nima se encuentra repetido en la siguientes compañías:\n'
                for nima in nimas:
                    message += f'- {nima.pnt_partner_id.name}. \n'
                record.pnt_duplicate_nima_message = message
            else:
                record.pnt_duplicate_nima_message = 'Este nima no está en otra empresa'
