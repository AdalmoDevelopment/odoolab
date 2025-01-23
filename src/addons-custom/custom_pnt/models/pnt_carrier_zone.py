from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PntCarrierZone(models.Model):
    _name = "pnt.carrier.zone"
    _description = "Pnt Carrier Zone"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Name",
        required=True,
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
    zip_id = fields.Many2one(
        comodel_name="res.city.zip",
        string="ZIP Location",
        index=True,
        compute="_compute_zip_id",
        readonly=False,
        store=True,
    )
    city_id = fields.Many2one(
        comodel_name="res.city",
        index=True,  # add index for performance
        compute="_compute_city_id",
        readonly=False,
        store=True,
    )
    zip = fields.Char(
        string = "Pnt Zip",
        change_default=True,
    )
    city = fields.Char()
    state_id = fields.Many2one(
        comodel_name="res.country.state",
        string='State',
        ondelete='restrict',
        domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one(
        'res.country',
        string='Country',
        ondelete='restrict'
    )
    @api.depends("state_id", "country_id", "city_id", "zip")
    def _compute_zip_id(self):
        """Empty the zip auto-completion field if data mismatch when on UI."""
        for record in self.filtered("zip_id"):
            fields_map = {
                "zip": "name",
                "city_id": "city_id",
                "state_id": "state_id",
                "country_id": "country_id",
            }
            for rec_field, zip_field in fields_map.items():
                if (
                    record[rec_field]
                    and record[rec_field] != record._origin[rec_field]
                    and record[rec_field] != record.zip_id[zip_field]
                ):
                    record.zip_id = False
                    break

    @api.depends("zip_id")
    def _compute_city_id(self):
        for record in self:
            if record.zip_id:
                record.city_id = record.zip_id.city_id
                record.city = record.zip_id.city_id.name
                record.zip = record.zip_id.name
                if record.zip_id.city_id.country_id:
                    record.country_id = record.zip_id.city_id.country_id
                elif record.state_id:
                    record.country_id = record.state_id.country_id
                state = record.zip_id.city_id.state_id
                if state and record.state_id != state:
                    record.state_id = record.zip_id.city_id.state_id
            else:
                record.city_id = False
                record.city = False
                record.zip = False
                record.country_id = False
                record.state_id = False

