from odoo import models, fields, api, _

class PntAppUser(models.Model):
    _name = "pnt.app.user"
    _description = "Pnt App User"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    name = fields.Char(
        string="App user",
        required=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_password = fields.Char(
        string="App password",
        required=True,
    )
    pnt_show_password = fields.Boolean(
        string="Show password",
        default=False,
    )
    pnt_transport_id = fields.Many2one(
        string="Driver",
        comodel_name="res.partner",
        domain=[
            ("pnt_is_driver", "=", True),
        ],
        copy=False,
        required=True,
    )
    pnt_applications_ids = fields.Many2many(
        comodel_name="pnt.app.application",
        relation="app_user_application_rel",
        column1="app_user_id",
        column2="app_application_id",
        string="Authorized applications",
    )

    _sql_constraints = [
        (
            "pnt_transport_id_uniq",
            "unique(company_id,pnt_transport_id)",
            "Solo puede existir un USUARIO de APP por Transportista.",
        ),
    ]
