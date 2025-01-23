from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class PntFleetVehicleCategory(models.Model):
    _name = "pnt.fleet.vehicle.category"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Pnt Fleet Category"
    _order = "pnt_complete_name"

    name = fields.Char(
        string="Category Name",
        required=True,
        translate=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
    )
    pnt_color = fields.Integer(
        "Color Index",
    )
    pnt_note = fields.Text(
        string="Comments",
        translate=True,
    )
    parent_id = fields.Many2one(
        comodel_name="pnt.fleet.vehicle.category",
        string="Parent Category",
        index=True,
        ondelete="cascade",
    )
    pnt_parent_path = fields.Char(index=True)
    pnt_complete_name = fields.Char(
        "Complete Name", compute="_compute_complete_name", store=True
    )
    pnt_fleet_vehicle_count = fields.Integer(
        string="Fleet",
        compute="_compute_fleet_vehicle_count",
    )

    @api.depends("name", "parent_id.pnt_complete_name")
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.pnt_complete_name = "%s / %s" % (
                    category.parent_id.pnt_complete_name,
                    category.name,
                )
            else:
                category.pnt_complete_name = category.name

    @api.model
    def name_create(self, name):
        return self.create({"name": name}).name_get()[0]

    @api.constrains("parent_id")
    def _check_category_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_("You cannot create recursive categories."))
        return True

    def name_get(self):
        res = []
        for record in self:
            name = "%s" % record.pnt_complete_name
            res.append((record.id, name))
        return res

    def _compute_fleet_vehicle_count(self):
        fleet_data = self.env["fleet.vehicle"].read_group(
            [("pnt_category_id", "in", self.ids)],
            ["pnt_category_id"],
            ["pnt_category_id"],
        )
        mapped_data = dict(
            [(m["pnt_category_id"][0], m["pnt_category_id_count"]) for m in fleet_data]
        )
        for category in self:
            category.pnt_fleet_vehicle_count = mapped_data.get(category.id, 0)

    def unlink(self):
        for category in self:
            if category.pnt_fleet_ids:
                raise UserError(
                    _("You cannot delete an fleet category containing fleet requests.")
                )
        return super(PntFleetVehicleCategory, self).unlink()
