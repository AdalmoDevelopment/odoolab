from odoo import fields, models, _


class PntManualMaintenanceLocation(models.Model):
    _name = "pnt.waste.nima.operator.type"
    _description = "Waste Operator Type"
    _rec_name = "pnt_type_operator"
    _order = "pnt_type_code,pnt_type_operator"
    _sql_constraints = [
        (
            "name_uniq",
            "unique (pnt_type_code, pnt_type_operator, company_id)",
            "Code and operator name already exists.",
        )
    ]
    pnt_type_code = fields.Selection(
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
    pnt_type_operator = fields.Char(
        string="Type Operator",
        required=True,
    )
    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
