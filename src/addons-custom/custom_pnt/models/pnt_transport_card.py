from odoo import models, fields


class PntTransportCard(models.Model):
    _name = "pnt.transport.card"
    _description = "Pnt Transport Card"

    name = fields.Char(
        string="Name",
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_tag_ids = fields.Many2many(
        "fleet.vehicle.tag",
        "pnt_transport_card_vehicle_tag_rel",
        "pnt_transport_card_tag_id",
        "tag_id",
        "Tags",
        copy=False,
    )
    pnt_date_of_affiliation = fields.Date("Date of affiliation", copy=False)
    # Este campos solo puede tener un vehículo
    pnt_vehicle_ids = fields.One2many(
        "fleet.vehicle",
        "pnt_transport_card_id",
        "Vehicle",
        readonly=True,
    )
    pnt_license_plate = fields.Char(
        string="License plate",
        compute="_compute_pnt_get_vehicle_data",
    )
    pnt_next_assignation_date = fields.Date(
        string="Next Assignation Date",
        compute="_compute_pnt_get_vehicle_data",
    )

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            res.append((record.id, name))
        return res

    def _compute_pnt_get_vehicle_data(self):
        for record in self:
            license_plate = False
            next_assignation_date = False
            if record.pnt_vehicle_ids and len(record.pnt_vehicle_ids) == 1:
                vehicle_id = self.env["fleet.vehicle"].browse(
                    record.pnt_vehicle_ids[0].id
                )
                license_plate = vehicle_id[0].license_plate
                next_assignation_date = vehicle_id[0].next_assignation_date
            record.pnt_license_plate = license_plate
            record.pnt_next_assignation_date = next_assignation_date
