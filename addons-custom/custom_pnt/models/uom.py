# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class Uom(models.Model):
    _inherit = 'uom.uom'

    pnt_use_marpol_m3 = fields.Boolean(
        string = "Use M3 in MARPOL DU",
        default = False,
        help="If this check is checked, the content of the pnt_m3 field is applied.",
    )
