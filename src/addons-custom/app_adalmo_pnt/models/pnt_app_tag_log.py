from odoo import models, fields, api, _

class PntAppTagLog(models.Model):
    _name = "pnt.app.tag.log"
    _description = "Pnt App Tag Log"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    name = fields.Char(
        string="Tag",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )
    pnt_functional_unit_id = fields.Many2one(
        comodel_name="pnt.functional.unit",
        string="Functional unit",
    )
    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_single_document_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id",
    )
    pnt_app_du_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_single_document_id.pnt_app_du_id",
    )
    pnt_tag_log_type = fields.Selection(
        [
            ("du", _("DU")),
            ("manual", _("Manual")),
            ("app", _("App")),
            ("imported", _("Imported")),
            ("others", _("Others")),
        ],
        string="Tag Log type",
        copy=False,
        index=True,
        tracking=3,
    )
    pnt_move_type = fields.Selection(
        [
            ("outgoing", _("Outgoing")),
            ("incoming", _("Incoming")),
        ],
        string="Move type",
        copy=False,
        index=True,
        tracking=3,
    )


