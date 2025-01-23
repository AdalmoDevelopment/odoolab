from odoo import api, fields, _, models
from odoo.tests import Form
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    pnt_agreement_count = fields.Integer(
        string="Agreement count",
        compute="_compute_pnt_agreement_count",
    )
    agreement_ids = fields.One2many(
        comodel_name='pnt.agreement.agreement',
        inverse_name='pnt_opportunity_id',
        string='Agreements',
    )

    user_id = fields.Many2one(default=None, readonly=False, store=True)

    @api.model
    def create(self, values):
        lead = super(CrmLead, self).create(values)
        lead.update_partner_user_id()
        return lead

    def write(self, values):
        result = super(CrmLead, self).write(values)
        self.update_partner_user_id()
        return result

    def update_partner_user_id(self):
        self.partner_id.user_id = self.user_id

    def _compute_pnt_agreement_count(self):
        for record in self:
            agreement_groups = self.env["pnt.agreement.agreement"].search([
                                       ('pnt_opportunity_id', '=', self.id),
                                       ('state', 'in', ['draft', 'sent']),])
        if agreement_groups:
            record.pnt_agreement_count = len(agreement_groups)
        else:
            record.pnt_agreement_count = 0



    def action_view_agreement_agreement(self):
        action = self.env["ir.actions.actions"]._for_xml_id("custom_pnt.action_pnt_agreement_agreement_quotation")
        action['context'] = {
            'search_default_draft': 1,
            'search_default_pnt_holder_id': self.partner_id.id,
            'default_pnt_holder_id': self.partner_id.id,
            'default_pnt_opportunity_id': self.id
        }
        action['domain'] = [('pnt_opportunity_id', '=', self.id), ('state', 'in', ['draft', 'sent'])]
        agreements = self.mapped('agreement_ids').filtered(lambda l: l.state in ('draft', 'sent'))
        if len(agreements) == 1:
            action['views'] = [(self.env.ref('custom_pnt.pnt_agreement_agreement_form_view').id, 'form')]
            action['res_id'] = agreements.id
        return action

    def action_agreement_agreement_new(self):
        if not self.partner_id:
            raise ValidationError(
                _(
                    f"¡Debe indicar un cliente (o posible cliente)!"
                )
            )
        else:
            return self.action_new_agreement_quotation()
    def action_new_agreement_quotation(self):
        action = self.env["ir.actions.actions"]._for_xml_id("custom_pnt.agreement_action_quotation_new_pnt")
        action['context'] = {
            'search_default_pnt_opportunity_id': self.id,
            'default_pnt_opportunity_id': self.id,
            'search_default_pnt_holder_id': self.partner_id.id,
            'default_pnt_holder_id': self.partner_id.id,
            'default_company_id': self.company_id.id or self.env.company.id,
        }
        # if self.team_id:
        #     action['context']['default_team_id'] = self.team_id.id,
        # if self.user_id:
        #     action['context']['default_user_id'] = self.user_id.id
        return action

    # def _prepare_customer_values(self, name, is_company=False, parent_id=False):
    #     values = super(CrmLead, self)._prepare_customer_values(
    #         name, is_company=is_company, parent_id=parent_id
    #     )
    #     values.update(
    #         {
    #             "pnt_is_lead": True,
    #         }
    #     )
    #     return values

