from dateutil import tz

from odoo import fields, models


class PntGlobalTimeOffWiz(models.TransientModel):
    _name = "pnt.global.time.off.wiz"
    _description = "Global Time Off Wizard"

    company_id = fields.Many2one(
        string="Company",
        comodel_name="res.company",
        required=True,
        default=lambda self: self.env.company,
    )
    pnt_leave_id = fields.Many2one(
        string="Leaves",
        comodel_name="pnt.global.time.off",
        required=True,
    )

    def assign_leaves_resources_calendar(self):
        resource_ids = self._context.get("active_ids")
        resources = self.env["resource.calendar"].browse(resource_ids)
        to_zone = tz.gettz()
        data = [
            (
                0,
                0,
                {
                    "name": x.pnt_name,
                    "date_from": fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(x.pnt_date_from)
                    )
                    .replace(hour=0, minute=0, second=0)
                    .astimezone(to_zone)
                    .replace(tzinfo=None),
                    "date_to": fields.Datetime.context_timestamp(
                        self, fields.Datetime.to_datetime(x.pnt_date_to)
                    )
                    .replace(hour=23, minute=59, second=59)
                    .astimezone(to_zone)
                    .replace(tzinfo=None),
                },
            )
            for x in self.pnt_leave_id.pnt_line_ids
        ]
        for resource in resources:
            resource.global_leave_ids = data
