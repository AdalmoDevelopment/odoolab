import datetime

from odoo import fields, models, _, api
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP


class ResUsers(models.Model):
    _inherit = "res.users"

    pnt_holder_id = fields.Many2one(
        string="Holder",
        comodel_name="res.partner",
        readonly=True,
        store=True,
        domain=[
            ("is_company", "=", True),
            ("pnt_is_lead", "=", False),
        ],
    )
    pnt_scales_id = fields.Many2one(
        comodel_name="pnt.scales",
        string="Default user scales",
        check_company=True,
    )
    pnt_scales_ids = fields.Many2many(
        comodel_name="pnt.scales",
        string="Scales available",
        relation="res_users_pnt_scales_rel",
        column1="scale_id",
        column2="user_id",
    )
    pnt_sign_vendor_contract = fields.Binary(
        string="Sign Vendor Contract",
    )
    pnt_default_chofer = fields.Many2many(
        "res.partner",
        "pnt_user_partner_rel",
        "user_id",
        "partner_id",
        "Default chofers",
        domain=[
            ("pnt_is_driver", "=", True),
            ("pnt_favorite_driver_asign", "=", True),
        ],
    )

    def _get_contact_person_phones(self):
        phones = ""
        if self.partner_id.phone:
            phones += self.partner_id.phone
        if self.partner_id.mobile:
            if len(phones) > 0:
                phones += "/"
            phones += self.partner_id.mobile
        return phones
