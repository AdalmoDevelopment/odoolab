import datetime
from datetime import timedelta, date, time, datetime
# import uuid
from odoo import models, fields, api, _

class PntAppSession(models.Model):
    _name = "pnt.app.session"
    _description = "Pnt App Session"
    _rec_name = 'token'
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    token = fields.Char(
        string="Token",
        readonly=True,
        # default=lambda s: uuid.uuid4().hex,
    )
    # id_usuario = fields.Integer(
    #     string="id_usuario",
    # )
    id_usuario = fields.Many2one(
        string="id_usuario",
        comodel_name="pnt.app.user",
    )
    pnt_transport_id = fields.Many2one(
        related="id_usuario.pnt_transport_id",
    )
    inicio = fields.Datetime(
        string="Inicio",
    )
    fin = fields.Datetime(
        string="Fin",
    )
    telefono = fields.Char(
        string="Teléfono",
    )
    matricula = fields.Char(
        string="Matrícula",
    )