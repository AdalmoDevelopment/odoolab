from odoo import api, fields, _, models
from odoo.tests import Form
from odoo.exceptions import ValidationError

class Stage(models.Model):
    _inherit = "crm.stage"

    pnt_is_pending_confirm = fields.Boolean('Is Pending Stage?')

    @api.constrains('pnt_is_pending_confirm')
    def _check_unique_pnt_is_pending_confirm(self):
        if self.search_count([('pnt_is_pending_confirm','=',True)]) > 1 :
            raise ValidationError(_("Can't mark two stages at the same time!"))


