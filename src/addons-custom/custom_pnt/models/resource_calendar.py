import datetime
from datetime import date

from dateutil import relativedelta
from odoo.addons.resource.models.resource import float_to_time

from odoo import _, api, fields, models


class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    pnt_external = fields.Boolean(
        string="External",
    )
    pnt_partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self._context.get("default_pnt_partner_id"):
            partner_id = self.env["res.partner"].browse(
                self._context.get("default_pnt_partner_id")
            )
            res["name"] = _(
                "Working Hours of %s (%s)",
                partner_id.name or partner_id.commercial_partner_id.name,
                dict(partner_id._fields["type"]._description_selection(self.env)).get(
                    partner_id.type, ""
                ),
            )
        return res

    def action_set_leaves_calendar(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "custom_pnt.pnt_global_time_off_wizz_action"
        )
        action["context"] = self._context
        return action

    def action_set_renew_attendance(self):
        self.action_archive_attendance()
        self.action_archive_leaves()
        for attendance in self.attendance_ids.filtered(
            lambda x: x.date_from and x.date_to
        ):
            attendance.copy(
                {
                    "date_from": attendance.date_from
                    + relativedelta.relativedelta(years=1),
                    "date_to": attendance.date_to
                    + relativedelta.relativedelta(years=1),
                }
            )
        for leave in self.global_leave_ids.filtered(
            lambda x: x.date_from and x.date_to
        ):
            leave.copy(
                {
                    "date_from": leave.date_from + relativedelta.relativedelta(years=1),
                    "date_to": leave.date_to + relativedelta.relativedelta(years=1),
                }
            )

    def action_archive_attendance(self):
        today = date.today()
        first_day = today.replace(day=1, month=1)
        resource_calendar = self.env["resource.calendar"].search(
            [
                ("pnt_external", "=", True),
            ]
        )
        resource_calendar.attendance_ids.filtered(
            lambda x: x.date_from and x.date_to and x.date_from < first_day
        ).write(
            {
                "active": False,
            }
        )

    def action_archive_leaves(self):
        today = datetime.datetime.today()
        first_day = today.replace(day=31, month=12, year=today.year - 1)
        resource_calendar = self.env["resource.calendar"].search(
            [
                ("pnt_external", "=", True),
            ]
        )
        resource_calendar.global_leave_ids.filtered(
            lambda x: x.date_from and x.date_to and x.date_from < first_day
        ).write(
            {
                "active": False,
            }
        )


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    pnt_custom_name = fields.Char(
        string="Custom name",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    name = fields.Char(
        compute="_pnt_compute_name",
        store=True,
        readonly=False,
    )

    @api.depends("dayofweek", "day_period")
    def _pnt_compute_name(self):
        for record in self:
            record.name = "%s (%s)" % (
                dict(record._fields["dayofweek"]._description_selection(self.env)).get(
                    record.dayofweek, ""
                ),
                dict(record._fields["day_period"]._description_selection(self.env)).get(
                    record.day_period, ""
                ),
            )

    def _get_cr_custom_name(self):
        self._get_custom_name("cr_custom_name")

    def _get_wr_custom_name(self):
        self._get_custom_name("wr_custom_name")

    def _get_custom_name(self, ctx):
        # dayofweek: [hour_from - hour_to, hour_from - hour_to ...]
        if self._context.get(ctx):
            return
        for record in self:
            context = self.env.context.copy()
            context[ctx] = True
            self.env.context = context
            if record.dayofweek and record.date_from and record.date_to:
                lines = self.env["resource.calendar.attendance"].search(
                    [
                        (
                            "calendar_id.pnt_partner_id",
                            "=",
                            record.calendar_id.pnt_partner_id.id,
                        ),
                        ("date_from", "=", record.date_from),
                        ("date_to", "=", record.date_to),
                        ("calendar_id.company_id", "=", self.env.company.id),
                    ]
                )
                daysofweek = sorted(list(set(lines.mapped("dayofweek"))))
                custom_name = ""
                for day in daysofweek:
                    custom_name += "%s: " % dict(
                        lines._fields["dayofweek"]._description_selection(self.env)
                    ).get(day, "")
                    custom_name += ", ".join(
                        [
                            "%s-%s"
                            % (
                                str(float_to_time(l.hour_from))[0:5],
                                str(float_to_time(l.hour_to))[0:5],
                            )
                            for l in lines.filtered(lambda x: x.dayofweek == day)
                        ]
                    )
                    custom_name += " // "
                lines.update({"pnt_custom_name": custom_name})

    def copy_line(self):
        self.copy()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list=vals_list)
        res._get_cr_custom_name()
        return res

    def write(self, vals):
        res = super().write(vals=vals)
        self._get_wr_custom_name()
        return res


class ResourceCalendarLeaves(models.Model):
    _inherit = "resource.calendar.leaves"

    active = fields.Boolean(
        string="Active",
        default=True,
    )
