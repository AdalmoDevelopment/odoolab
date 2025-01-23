from odoo import api, fields, models, _


class ProductCategory(models.Model):
    _inherit = "product.category"

    pnt_is_sanitary = fields.Boolean(
        string="Is Sanitary",
        compute="_compute_pnt_parent_sanitary",
        readonly=False,
        copy=False,
        store=True,
    )
    pnt_parent_is_sanitary = fields.Boolean(
        string="Parent Is Sanitary",
        related="parent_id.pnt_is_sanitary",
    )
    pnt_is_container = fields.Boolean(
        string="Is Container",
        compute="_compute_pnt_parent_container",
        readonly=False,
        copy=False,
        store=True,
    )
    pnt_parent_is_container = fields.Boolean(
        string="Parent Is Container",
        related="parent_id.pnt_is_container",
    )
    pnt_service = fields.Boolean(
        string="Account Services",
    )
    pnt_order_budget_format = fields.Selection(
        string="Order budget format",
        selection=[
            ("1", _("1")),
            ("2", _("2")),
            ("3", _("3")),
        ],
        default='2',
    )

    @api.depends("pnt_parent_is_sanitary")
    def _compute_pnt_parent_sanitary(self):
        for record in self:
            is_sanitary = False
            if record.parent_id:
                is_sanitary = record.parent_id.pnt_is_sanitary
            record.pnt_is_sanitary = is_sanitary

    @api.depends("pnt_parent_is_container")
    def _compute_pnt_parent_container(self):
        for record in self:
            is_container = False
            if record.parent_id:
                is_container = record.parent_id.pnt_is_container
            record.pnt_is_container = is_container
