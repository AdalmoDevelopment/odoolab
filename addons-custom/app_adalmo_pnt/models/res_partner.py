from odoo import _, api, fields, models
from odoo.addons.base.models.res_partner import WARNING_HELP, WARNING_MESSAGE
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = "res.partner"

    pnt_send_email_app = fields.Boolean(
        string="Send email app",
        default=False,
    )
    pnt_send_email_app_ref = fields.Boolean(
        string="Send email app (Reference center)",
        default=False,
    )
    pnt_dont_send_email_app_ref = fields.Boolean(
        string="Do not use sector reference center emails for app",
        default=False,
    )
    pnt_print_date_on_labels = fields.Boolean(
        string="Print date on labels",
        default=True,
    )
    def pnt_app_sector(self):
        numsector = "00"
        for record in self:
            sector = record.category_id.filtered(
                    lambda x: x.pnt_type == 'sector'
                )
            if len(sector) == 1:
                numsector = sector.name[1:3]
        return numsector
    def emails_to_send_app_service(self):
        emails = ""
        # Localizar el centro de referencia del sector
        for record in self:
            sector = record.category_id.filtered(
                    lambda x: x.pnt_type == 'sector'
                )
            if len(sector) == 1:
                # comprobar si es centro de referencia del sector
                centroref = None
                escentroref = sector.name[3:4]
                numsector = sector.name[1:3]
                if (escentroref and escentroref == "S"
                        or record.pnt_dont_send_email_app_ref):
                    centroref = record
                else:
                    # Localitzar centre de feferencia del sector
                    centroref = (self.env["res.partner"].search([
                        ("category_id.name", "=", "N" + numsector + "S")
                    ], limit=1))
                if centroref:
                    if escentroref == "S" or record.pnt_dont_send_email_app_ref:
                        emails_childs_ids = self.env["res.partner"].search([
                            ("parent_id", "=", centroref.id),
                            ("pnt_send_email_app_ref", "=", True),
                            ("type", "=", "contact"),
                        ])
                    else:
                        emails_childs_ids = self.env["res.partner"].search([
                            ("parent_id", "=", centroref.id),
                            ("pnt_send_email_app", "=", True),
                            ("type", "=", "contact"),
                        ])
                    for em in emails_childs_ids:
                        if not emails:
                            emails = em.email
                        else:
                            emails = emails + "," + em.email
        return emails
