from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PntCarrierRate(models.Model):
    _name = "pnt.carrier.rate"
    _description = "Pnt Carrier Rate"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True,
        copy=False,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        "Active",
        default=True,
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
    pnt_vehicle_category_id = fields.Many2one(
        string="Vehicle Category",
        comodel_name="pnt.fleet.vehicle.category",
    )
    pnt_rate_type = fields.Selection(
        selection=[
            ("hour", _("Hours")),
            ("zone", _("Zones")),
            ("fromto", _("From/to")),
        ],
        default=False,
        help="Technical field for UX purpose.",

    )
    pnt_product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    pnt_price_hour = fields.Monetary(
        string="Price per hour",
        digits="Product Price",
        default=0.0,
        readonly=False,
    )
    pnt_carrier_rate_zone_ids = fields.One2many(
        comodel_name="pnt.carrier.rate.zone.price",
        inverse_name="pnt_carrier_rate_id",
        string="Carrier rate zone",
        copy=True,
        auto_join=True,
    )
    pnt_carrier_rate_fromto_ids = fields.One2many(
        comodel_name="pnt.carrier.rate.fromto.price",
        inverse_name="pnt_carrier_rate_id",
        string="Carrier rate From/to",
        copy=True,
        auto_join=True,
    )

    @api.onchange("pnt_rate_type")
    def onchange_pnt_rate_type(self):
        # if self.pnt_rate_type:
        #     if self.pnt_rate_type not in ("hour"):
        self.pnt_price_hour = 0.0
        self.pnt_carrier_rate_zone_ids.unlink()
        self.pnt_carrier_rate_fromto_ids.unlink()

    @api.depends("pnt_carrier_id",
                 "pnt_vehicle_category_id",
                 "pnt_rate_type",
                 "pnt_product_id")
    def _compute_name(self):
        for record in self:
            name = ""
            if record.pnt_carrier_id:
                name = record.pnt_carrier_id.name
            if record.pnt_vehicle_category_id:
                name = name + " | " + record.pnt_vehicle_category_id.name
            if record.pnt_rate_type:
                name = name + " | " + record.pnt_rate_type
            if record.pnt_product_id:
                name = name + " | " + record.pnt_product_id.display_name
            record.name = name

class PntCarrierRateZonePrice(models.Model):
    _name = "pnt.carrier.rate.zone.price"
    _sql_constraints = [
        ("zip_unique", "UNIQUE (pnt_carrier_rate_id,zip)", "Zip must be unique"),
    ]

    pnt_carrier_rate_id = fields.Many2one(
        comodel_name="pnt.carrier.rate",
        string="Carrier rate",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    pnt_carrier_zone_id = fields.Many2one(
        comodel_name="pnt.carrier.zone",
        string="Carrier zone",
    )
    zip = fields.Char(
        related="pnt_carrier_zone_id.zip",
        store=True,
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    pnt_price_zone = fields.Monetary(
        string="Price",
        digits="Product Price",
        default=0.0,
        readonly=False,
    )

class PntCarrierRateFromtoPrice(models.Model):
    _name = "pnt.carrier.rate.fromto.price"
    _sql_constraints = [
        ("fromto_unique",
         "UNIQUE (pnt_carrier_rate_id,pnt_partner_from_id,pnt_partner_to_id)",
         "From/to must be unique"),
    ]

    pnt_carrier_rate_id = fields.Many2one(
        comodel_name="pnt.carrier.rate",
        string="Carrier rate",
        required=True,
        ondelete="cascade",
        index=True,
        copy=False,
    )
    pnt_partner_from_id = fields.Many2one(
        string="From",
        comodel_name="res.partner",
        domain=[
            ("type", "=", "delivery"),
        ],
    )
    pnt_partner_to_id = fields.Many2one(
        string="To",
        comodel_name="res.partner",
        domain=[
            ("type", "=", "delivery"),
        ],
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.user.company_id.currency_id,
    )
    pnt_price_fromto = fields.Monetary(
        string="Price",
        digits="Product Price",
        default=0.0,
        readonly=False,
    )




