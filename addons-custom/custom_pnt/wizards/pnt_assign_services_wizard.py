from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PntAssignServices(models.TransientModel):
    _name = "pnt.assign.services"

    pnt_service_date = fields.Date(
        string="Service date",
    )
    pnt_transport_ids = fields.Many2many(
        comodel_name="res.partner",
        relation="partner_assign_rel",
        column1="partner_id",
        column2="assign_id",
        string="Partners to assign",
        domain=[
            ("pnt_is_driver", "=", True),
        ],
        default=lambda self: self._get_favorite_divers(),
    )
    pnt_vehicle_category_ids = fields.Many2many(
        comodel_name="pnt.fleet.vehicle.category",
        relation="pnt_category_assign_rel",
        column1="category_id",
        column2="assign_id",
        string="Categories to assign",
        default=lambda self: self._get_categories(),
    )

    @api.model
    def _get_categories(self):
        return self.env["pnt.fleet.vehicle.category"].search([]).ids

    @api.model
    def _get_favorite_divers(self):
        return self.env.user.pnt_default_chofer.ids or (
            self.env["res.partner"]
            .search(
                [("pnt_is_driver", "=", True), ("pnt_favorite_driver_asign", "=", True)]
            )
            .ids
        )

    # Methods
    def load_services(self):
        for rec in self:
            project = self.env.company.pnt_single_document_project_id
            if rec.pnt_service_date and project:
                categ = ""
                if rec.pnt_vehicle_category_ids:
                    for category in rec.pnt_vehicle_category_ids:
                        if categ == "":
                            categ = " - (" + category.name
                        else:
                            categ = categ + " | " + category.name
                    if categ != "":
                        categ = categ + ")"
                    dominio = [
                        ("project_id", "=", project.id),
                        "|",
                        ("stage_id", "in", [1]),
                        "&",
                        ("stage_id", "in", [2]),
                        ("date_deadline", "=", rec.pnt_service_date),
                        "|",
                        (
                            "pnt_vehicle_category_id",
                            "in",
                            rec.pnt_vehicle_category_ids.ids,
                        ),
                        ("pnt_vehicle_category_id", "=", False),
                        "|",
                        ("pnt_transport_id", "in", rec.pnt_transport_ids.ids),
                        ("pnt_transport_id", "=", False),
                    ]
                else:
                    dominio = [
                        ("project_id", "=", project.id),
                        "|",
                        ("stage_id", "in", [1]),
                        "&",
                        ("stage_id", "in", [2]),
                        ("date_deadline", "=", rec.pnt_service_date),
                        "|",
                        ("pnt_transport_id", "in", rec.pnt_transport_ids.ids),
                        ("pnt_transport_id", "=", False),
                    ]
                # Crear tareas patron para choferes seleccionados si estos no existen
                for chofer_id in rec.pnt_transport_ids.ids:
                    chofer = self.env["res.partner"].search([("id", "=", chofer_id)])
                    task_chofer = self.env["project.task"].search(
                        [
                            ("project_id", "=", project.id),
                            ("pnt_is_transport_template", "=", True),
                            ("pnt_transport_id", "=", chofer.id),
                        ]
                    )
                    if task_chofer:
                        task_chofer.unlink()
                    # Crear la tarea plantilla para el chofer si esta no existe
                    values = self._timesheet_create_task_prepare_values(
                        project.id, chofer
                    )
                    new_task = self.env["project.task"].sudo().create(values)

                    # if not task_chofer:
                    #     # Crear la tarea plantilla para el chofer si esta no existe
                    #     values = self._timesheet_create_task_prepare_values(project.id,chofer)
                    #     new_task = self.env["project.task"].sudo().create(values)
                    # else:
                    #     task_chofer.unlink()
                context = self._context.copy()
                if context is None:
                    context = {}
                context.update({"assign_date": rec.pnt_service_date})
                view_id = self.env.ref("custom_pnt.view_task_kanban_transport_pnt").id
                return {
                    "type": "ir.actions.act_window",
                    "name": "Asignar servicios para el día "
                    + rec.pnt_service_date.strftime("%d/%m/%Y")
                    + categ,
                    "view_type": "kanban",
                    "view_mode": "kanban,tree,form,calendar",
                    # 'domain': [('stage_id', 'in', [1,2]),
                    #            ('project_id','=',project.id)],
                    "domain": dominio,
                    "view_id": view_id,
                    "views": [
                        [view_id, "kanban"],
                        [self.env.ref("project.view_task_tree2").id, "list"],
                        [self.env.ref("project.view_task_form2").id, "form"],
                        [self.env.ref("project.view_task_calendar").id, "calendar"],
                    ],
                    "res_model": "project.task",
                    "context": context,
                    "target": "main",
                }
            else:
                raise UserError(_("Debe indicar la Fecha que se quiere programar"))

    def _timesheet_create_task_prepare_values(self, project, chofer):
        self.ensure_one()
        currentproject = self.env["project.project"].search([("id", "=", project)])
        title = chofer.name
        return {
            "name": title,
            "project_id": currentproject.id,
            "pnt_transport_id": chofer.id,
            "pnt_is_transport_template": True,
            "user_id": False,  # force non assigned task, as created as sudo()
        }
