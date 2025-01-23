from odoo import fields, models, api, SUPERUSER_ID, _


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    pnt_image_128 = fields.Image(
        "Vehicle",
        max_width=128,
        max_height=128,
    )
    pnt_mma = fields.Integer(
        string="MMA (kg)",
    )
    pnt_height = fields.Integer(
        string="Height (mm)",
    )
    pnt_width = fields.Integer(
        string="Width (mm)",
    )
    pnt_length = fields.Integer(
        string="Length (mm)",
    )
    pnt_length2 = fields.Integer(
        string="Length2 (mm)",
        help="Can be used for a long second, e.g. long with container",
    )
    pnt_wheels = fields.Integer(
        string="Wheels",
    )
    pnt_wheels_type = fields.Char(string="Wheels type")
    pnt_account_analytic_id = fields.Many2one(
        string="Account analytic", comodel_name="account.analytic.account"
    )
    pnt_renovation_state = fields.Selection(
        string="Renovation state",
        selection=[
            ("done", _("Done")),
            ("todo", _("Renovation")),
            ("expire", _("Expire")),
        ],
        compute="_compute_pnt_get_renovation_state",
        store=True,
    )
    pnt_transport_card_id = fields.Many2one(
        string="Transport Card",
        comodel_name="pnt.transport.card",
        domain=[
            ("pnt_vehicle_ids", "=", False),
        ],
    )
    pnt_category_ids = fields.Many2many(
        comodel_name="pnt.fleet.vehicle.category",
        string="Fleet Vehicle Category",
        relation="pnt_fleet_vehicle_category_rel",
        column1="pnt_fleet_vehicle_id",
        column2="pnt_category_id",
    )
    pnt_category_id = fields.Many2one(
        comodel_name="pnt.fleet.vehicle.category",
        string="Fleet Vehicle Category",
    )
    pnt_carrier_id = fields.Many2one(
        string="Carrier",
        comodel_name="res.partner",
        domain=[
            ("is_company", "=", True),
            ("category_id", "=", 9),
        ],
        copy=False,
        check_company=True,
    )

    @api.depends("log_services.pnt_renovation_state")
    def _compute_pnt_get_renovation_state(self):
        for record in self:
            renovation_state = "expire"
            date_renovation = record.log_services.filtered(
                lambda x: x.state not in ("done", "cancelled")
            ).sorted(key=lambda r: r.date)
            if date_renovation:
                renovation_state = date_renovation[0].pnt_renovation_state
            record.pnt_renovation_state = renovation_state

    # @api.model
    # def _read_group_category_ids(self, categories, domain, order):
    #     category_ids = categories._search([], order=order,
    #                                       access_rights_uid=SUPERUSER_ID)
    #     return categories.browse(category_ids)


class FleetServiceType(models.Model):
    _inherit = "fleet.service.type"

    pnt_delay_days = fields.Integer(
        string="Delay days",
        default=0,
    )
