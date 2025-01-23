from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PntAuthorizationCode(models.Model):
    _name = "pnt.authorization.code"
    _description = "Pnt Authorization Code"

    name = fields.Char(
        string="Code",
        required=True,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_nima_code_id = fields.Many2one(
        string="NIMA Code",
        comodel_name="pnt.nima.code",
    )
    pnt_nima_partner_id = fields.Many2one(
        string="Partner",
        comodel_name="res.partner",
        related="pnt_nima_code_id.pnt_partner_id",
    )
    pnt_product_tmpl_waste_ler_ids = fields.Many2many(
        string="LER",
        comodel_name="pnt.product.tmpl.waste.ler",
        relation="pnt_authorization_code_ler_rel",
        column1="partner_id",
        column2="pnt_authorization_code_id",
    )
    pnt_authorization_code_type = fields.Selection(
        string="Code type",
        selection=[
            ("agent", _("Agent")),
            ("producer", _("Producer")),
            ("transport", _("Transport")),
            ("end_mgm", _("End Management")),
            ("scrap", _("SCRAP")),
        ],
        required=True,
    )
    pnt_operator_type_id = fields.Many2one(
        string="Operator type",
        comodel_name="pnt.waste.nima.operator.type",
        required=True,
    )

    @api.onchange("pnt_authorization_code_type")
    def _onchange_pnt_authorization_code_type(self):
        self.pnt_operator_type_id = False
        valids = {
            "company": ["agent", "transport", "scrap"],
            "delivery": ["producer", "end_mgm"],
        }
        for record in self.filtered("pnt_authorization_code_type"):
            if (
                record.pnt_nima_partner_id.company_type == "company"
                and record.pnt_authorization_code_type not in valids["company"]
            ):
                return {
                    "warning": {
                        "title": _("Warning"),
                        "message": _(
                            "Company contacts can only be 'Agent', 'SCRAP' or 'Transport'."
                        ),
                    }
                }
            elif (
                record.pnt_nima_partner_id.type == "delivery"
                and record.pnt_authorization_code_type not in valids["delivery"]
            ):
                return {
                    "warning": {
                        "title": _("Warning"),
                        "message": _(
                            "Delivery contacts can only be 'Producer' or 'End Manager'."
                        ),
                    }
                }

    @api.constrains("pnt_authorization_code_type")
    def _check_pnt_authorization_code_type(self):
        valids = {
            "company": ["agent", "transport", "scrap"],
            "delivery": ["producer", "end_mgm"],
        }
        for record in self:
            if (
                record.pnt_nima_partner_id.company_type == "company"
                and record.pnt_authorization_code_type not in valids["company"]
            ):
                raise ValidationError(
                    _("Company contacts can only be 'Agent','SCRAP' or 'Transport'.")
                )
            elif (
                record.pnt_nima_partner_id.type == "delivery"
                and record.pnt_authorization_code_type not in valids["delivery"]
            ):
                raise ValidationError(
                    _("Delivery contacts can only be 'Producer' or 'End Manager'.")
                )


class PntAuthorizationCodeType(models.Model):
    _name = "pnt.authorization.code.type"
    _description = "Pnt Authorization Code type"

    name = fields.Char(
        string="Name",
        required=True,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_authorization_code_type = fields.Selection(
        string="Code type",
        selection=[
            ("agent", _("Agent")),
            ("producer", _("Producer")),
            ("transport", _("Transport")),
            ("end_mgm", _("End Management")),
            ("scrap", _("SCRAP")),
        ],
        required=True,
    )
