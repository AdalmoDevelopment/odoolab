from odoo import fields, models, api, _, tools


class PntResCompanyLogo(models.Model):
    _name = "pnt.res.company.logo"

    pnt_logo = fields.Binary(
        string="Logo",
    )
    pnt_company = fields.Many2one(
        "res.company",
        string="Company id",
    )
    pnt_type = fields.Selection(
        [
            ("sign", _("Sign")),
            ("other", _("Other")),
        ],
        "Image type",
        default="other",
    )
    name = fields.Char(
        string="Name",
    )
