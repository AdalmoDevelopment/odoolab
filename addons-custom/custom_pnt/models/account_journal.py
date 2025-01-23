from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    pnt_supplier_account = fields.Many2one(
        string = "Default Supplier Account",
        comodel_name = 'account.account',
        check_company = True,
        copy = False,
        ondelete = 'restrict',
        domain="[('code', 'in', ['40000000', '41000000'])]"
    )
    pnt_supplier_selection = fields.Selection(
        selection=[("supplier", "Supplier"), ("vendor", "Vendor")],
        string="Selection Supplier Account",
    )
    pnt_copy_ref_to_lines = fields.Boolean(
        string="Copy reference to lines",
        default=False,
    )

    @api.constrains('pnt_supplier_selection')
    def _check_unique_supplier(self):
        for record in self:
            existing_registry = self.search([
                ('pnt_supplier_selection', '=', record.pnt_supplier_selection),
                ('id', '!=', record.id)])
            if existing_registry:
                raise ValidationError(
                    "This selection already has a registry for the selected company.")
