from odoo import fields, models, api, _


class AccountFiscalPosition(models.Model):
    _inherit = "account.fiscal.position"

    pnt_default_in_partner = fields.Boolean(
        string="Default in partner",
        default=False,
        copy=False,
        readonly=True,
    )
    pnt_intra_extra_community = fields.Boolean(
        string="Intra/Extra Community",
    )

    @api.onchange("pnt_default_in_partner")
    def onchange_pnt_default_in_partner(self):
        if self.pnt_default_in_partner:
            io = self.check_pnt_default_in_partner()
            if io != "":
                self.pnt_default_in_partner = False
                return {
                    "value": {},
                    "warning": {
                        "Aviso": "warning",
                        "message": "Ya existe una posicion fiscal por defecto: " + io,
                    },
                }

    def check_pnt_default_in_partner(self):
        for record in self:
            prl = self.env["account.fiscal.position"].search(
                [
                    ("id", "!=", self._origin.id),
                    ("pnt_default_in_partner", "=", 1),
                    ("active", "=", 1),
                ],
                limit=1,
            )
            if prl:
                return "[" + prl.name + "] "
            else:
                return ""
