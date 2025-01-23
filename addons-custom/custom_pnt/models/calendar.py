from odoo import models, fields, api

class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    @api.model
    def create(self, values):
        return super(
            CalendarEvent, self.with_context(no_mail_to_attendees=True)
        ).create(values)

    def write(self, values):
        return super(
            CalendarEvent, self.with_context(no_mail_to_attendees=True)
        ).write(values)