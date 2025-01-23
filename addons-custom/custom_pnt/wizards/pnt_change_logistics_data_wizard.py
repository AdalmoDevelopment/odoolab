from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests.common import Form
from .. import DEFAULT_NEW_DU_WIZ_SCALE_PICKUP_ID, DEFAULT_NEW_DU_WIZ_SCALE_ID


class PntChangeLogisticsData(models.TransientModel):
    _name = "pnt.change.logistics.data"

    pnt_task_ids = fields.Many2many(
        string="Task",
        comodel_name="project.task",
        relation="pnt_change_logistics_data_task_rel",
    )
    pnt_task_qty = fields.Integer(
        string="Number of tasks",
        compute="_compute_pnt_task_qty",
    )
    pnt_update_transport_type = fields.Selection(
        string="Update driver type",
        selection="_compute_pnt_selection_update",
        required=True,
        default="no",
    )
    pnt_transport_id = fields.Many2one(
        string="Driver",
        comodel_name="res.partner",
        domain=[
            ("pnt_is_driver", "=", True),
        ],
    )
    pnt_update_vehicle_category_id = fields.Selection(
        string="Update vehicle category",
        selection="_compute_pnt_selection_update",
        required=True,
        default="no",
    )
    pnt_vehicle_category_id = fields.Many2one(
        string="Vehicle Category",
        comodel_name="pnt.fleet.vehicle.category",
    )
    pnt_update_vehicle_id = fields.Selection(
        string="Update vehicle",
        selection="_compute_pnt_selection_update",
        required=True,
        default="no",
    )
    pnt_vehicle_id = fields.Many2one(
        string="Vehicle",
        comodel_name="fleet.vehicle",
    )
    pnt_update_date_deadline = fields.Selection(
        string="Update Deadline",
        selection="_compute_pnt_selection_update",
        required=True,
        default="no",
    )
    date_deadline = fields.Date(
        string='Deadline',
    )
    def _compute_pnt_selection_update(self):
        return [
            ("no", _("No")),
            ("delete", _("Delete")),
            ("update", _("Update")),
        ]
    @api.depends("pnt_task_ids")
    def _compute_pnt_task_qty(self):
        for record in self:
            record.pnt_task_qty = len(record.pnt_task_ids)
    def apply_changes(self):
        for record in self:
            for task in record.pnt_task_ids:
                if record.pnt_update_transport_type == "delete":
                    task.write({
                        "pnt_transport_id": None
                    })
                elif record.pnt_update_transport_type == "update":
                    task.write({
                        "pnt_transport_id": record.pnt_transport_id.id
                    })
                if record.pnt_update_vehicle_category_id == "delete":
                    task.write({
                        "pnt_vehicle_category_id": None
                    })
                elif record.pnt_update_vehicle_category_id == "update":
                    task.write({
                        "pnt_vehicle_category_id": record.pnt_vehicle_category_id.id
                    })
                if record.pnt_update_vehicle_id == "delete":
                    task.write({
                        "pnt_vehicle_id": None
                    })
                elif record.pnt_update_vehicle_id == "update":
                    task.write({
                        "pnt_vehicle_id": record.pnt_vehicle_id.id
                    })
                if record.pnt_update_date_deadline == "delete":
                    task.write({
                        "date_deadline": None
                    })
                elif record.pnt_update_date_deadline == "update":
                    task.write({
                        "date_deadline": record.date_deadline
                    })
