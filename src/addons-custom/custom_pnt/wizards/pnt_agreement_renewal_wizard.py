import datetime

from odoo import models, fields, api, _


class PntAgreementRenewalWizard(models.TransientModel):
    _name = "pnt.agreement.renewal.wizard"
    _description = "Pnt Agreement Renewal Wizard"

    pnt_start_date = fields.Date(
        string="Start Date",
    )
    pnt_end_date = fields.Date(
        string="End Date",
    )
    pnt_agreement_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.agreement",
    )

    @api.model
    def default_get(self, values):
        record_ids = self._context.get("active_ids")
        result = super(PntAgreementRenewalWizard, self).default_get(values)
        if record_ids:
            pnt_agreement_id = self.env["pnt.agreement.agreement"].browse(record_ids[0])
            result["pnt_agreement_id"] = pnt_agreement_id.id
            date = fields.Date.context_today(self)
            if pnt_agreement_id.pnt_end_date:
                date = pnt_agreement_id.pnt_end_date + datetime.timedelta(days=1.0)
            result["pnt_start_date"] = date
        return result

    def do_process(self):
        ids_agreement_created = []
        for record in self:
            if record.pnt_agreement_id:
                agreement_id = record.pnt_agreement_id.copy(
                    {
                        "pnt_start_date": record.pnt_start_date,
                        "pnt_end_date": record.pnt_end_date or False,
                    }
                )
                ids_agreement_created.append(agreement_id.id)
        if ids_agreement_created:
            action = self.env.ref(
                "custom_pnt.action_pnt_agreement_agreement_quotation"
            ).read()[0]
            action["domain"] = [("id", "in", ids_agreement_created)]
            action["context"] = dict(self._context, create=False)
            return action
