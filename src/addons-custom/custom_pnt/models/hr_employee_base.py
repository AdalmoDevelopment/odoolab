# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    pnt_access_incident_app = fields.Boolean(
        string="Access incident app",
        deafult=False,
    )
    pnt_scales_ids = fields.Many2many(
        comodel_name="pnt.scales",
        string="Scales available",
        relation="hr_employee_public_pnt_scales_rel",
        column1="scale_id",
        column2="employee_id",
    )
