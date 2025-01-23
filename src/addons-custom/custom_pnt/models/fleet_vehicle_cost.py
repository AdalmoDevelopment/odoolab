import datetime

from odoo import fields, models, api, _


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle.log.services"

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

    @api.depends("date", "state")
    def _compute_pnt_get_renovation_state(self):
        for record in self:
            renovation_state = "expire"
            if record.date <= datetime.date.today():
                renovation_state = "expire"
            elif (
                record.date
                - datetime.timedelta(days=record.service_type_id.pnt_delay_days)
            ) <= datetime.date.today():
                renovation_state = "todo"
            else:
                renovation_state = "done"
            record.pnt_renovation_state = renovation_state
