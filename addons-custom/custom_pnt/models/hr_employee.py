import datetime

from odoo import fields, models, api, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    pnt_is_driver = fields.Boolean(
        string="Is Driver",
        related="address_id.pnt_is_driver",
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
    pnt_due_date_identification_id = fields.Date(
        string="Expiration Date Identification",
    )
    pnt_due_date_circulation_permit = fields.Date(
        string="Expiration Date Circulation Permit"
    )
    pnt_due_date_cpa = fields.Date(
        string="Expiration Date CPA",
    )
    pnt_due_date_tachograph = fields.Date(
        string="Expiration Date Tachograph",
    )
    pnt_due_date_adr = fields.Date(
        string="Expiration Date ADR",
    )
    pnt_circulation_permit_class_id = fields.Many2one(
        string="Circulation Permit", comodel_name="pnt.circulation.permit.class"
    )

    @api.depends(
        "pnt_is_driver",
        "pnt_due_date_circulation_permit",
        "pnt_due_date_cpa",
        "pnt_due_date_tachograph",
        "pnt_due_date_adr",
    )
    def _compute_pnt_get_renovation_state(self):
        for record in self:
            state_list = []
            if record.pnt_due_date_circulation_permit:
                state_list.append(
                    self._pnt_get_renovation_state(
                        record.pnt_due_date_circulation_permit,
                        record.company_id.pnt_delay_days_due_date_circulation_permit,
                    )
                )
            if record.pnt_due_date_cpa:
                state_list.append(
                    self._pnt_get_renovation_state(
                        record.pnt_due_date_cpa,
                        record.company_id.pnt_delay_days_due_date_cpa,
                    )
                )
            if record.pnt_due_date_tachograph:
                state_list.append(
                    self._pnt_get_renovation_state(
                        record.pnt_due_date_tachograph,
                        record.company_id.pnt_delay_days_due_date_tachograph,
                    )
                )
            if record.pnt_due_date_adr:
                state_list.append(
                    self._pnt_get_renovation_state(
                        record.pnt_due_date_adr,
                        record.company_id.pnt_delay_days_due_date_adr,
                    )
                )
            if "expire" in state_list or not state_list:
                record.pnt_renovation_state = "expire"
            elif "todo" in state_list:
                record.pnt_renovation_state = "todo"
            else:
                record.pnt_renovation_state = "done"

    def _pnt_get_renovation_state(self, date, delay_days):
        self.ensure_one()
        renovation_state = "expire"
        if date <= datetime.date.today():
            renovation_state = "expire"
        elif (date - datetime.timedelta(days=delay_days)) <= datetime.date.today():
            renovation_state = "todo"
        else:
            renovation_state = "done"
        return renovation_state
