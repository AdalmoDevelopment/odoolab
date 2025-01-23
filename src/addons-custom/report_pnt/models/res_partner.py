from odoo import models


PARTNER = "res.partner"

class ResPartner(models.Model):
    _inherit = PARTNER

    def _get_sign(self):
        # return list [it's image sign (bool), image sign]
        its_sign = False
        logo = False
        if self.id == self.env.company.partner_id.id:
            its_sign = self.env.company.pnt_logo_ids.filtered(
                lambda x: x.pnt_type == "sign"
            )
            if its_sign:
                logo = its_sign[0].pnt_logo
        return [bool(its_sign), logo]
