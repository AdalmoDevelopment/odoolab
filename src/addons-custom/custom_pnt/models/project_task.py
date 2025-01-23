from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError, except_orm
from odoo.tests import Form
from .. import ACTIVITY_TEAMS, PROJECTS, TASK_STAGES

MANIPULATION = [
    ("0000", "00:00"),
    ("0015", "00:15"),
    ("0030", "00:30"),
    ("0045", "00:45"),
    ("0100", "01:00"),
    ("0115", "01:15"),
    ("0130", "01:30"),
    ("0145", "01:45"),
    ("0200", "02:00"),
    ("0215", "02:15"),
    ("0230", "02:30"),
    ("0245", "02:45"),
    ("0300", "03:00"),
    ("0315", "03:15"),
    ("0330", "03:30"),
    ("0345", "03:45"),
    ("0400", "04:00"),
    ("0415", "04:15"),
    ("0430", "04:30"),
    ("0445", "04:45"),
    ("0500", "05:00"),
    ("0515", "05:15"),
    ("0530", "05:30"),
    ("0545", "05:45"),
    ("0600", "06:00"),
    ("0615", "06:15"),
    ("0630", "06:30"),
    ("0645", "06:45"),
    ("0700", "07:00"),
    ("0715", "07:15"),
    ("0730", "07:30"),
    ("0745", "07:45"),
    ("0800", "08:00"),
    ("0815", "08:15"),
    ("0830", "08:30"),
    ("0845", "08:45"),
    ("0900", "09:00"),
    ("0915", "09:15"),
    ("0930", "09:30"),
    ("0945", "09:45"),
    ("1000", "10:00"),
    ("1015", "10:15"),
    ("1030", "10:30"),
    ("1045", "10:45"),
    ("1100", "11:00"),
    ("1115", "11:15"),
    ("1130", "11:30"),
    ("1145", "11:45"),
    ("1200", "12:00"),
    ("1215", "12:15"),
    ("1230", "12:30"),
    ("1245", "12:45"),
    ("1300", "13:00"),
    ("1315", "13:15"),
    ("1330", "13:30"),
    ("1345", "13:45"),
    ("1400", "14:00"),
    ("1415", "14:15"),
    ("1430", "14:30"),
    ("1445", "14:45"),
    ("1500", "15:00"),
    ("1515", "15:15"),
    ("1530", "15:30"),
    ("1545", "15:45"),
    ("1600", "16:00"),
    ("1615", "16:15"),
    ("1630", "16:30"),
    ("1645", "16:45"),
    ("1700", "17:00"),
    ("1715", "17:15"),
    ("1730", "17:30"),
    ("1745", "17:45"),
    ("1800", "18:00"),
    ("1815", "18:15"),
    ("1830", "18:30"),
    ("1845", "18:45"),
    ("1900", "19:00"),
    ("1915", "19:15"),
    ("1930", "19:30"),
    ("1945", "19:45"),
    ("2000", "20:00"),
    ("2015", "20:15"),
    ("2030", "20:30"),
    ("2045", "20:45"),
    ("2100", "21:00"),
    ("2115", "21:15"),
    ("2130", "21:30"),
    ("2145", "21:45"),
    ("2200", "22:00"),
    ("2215", "22:15"),
    ("2230", "22:30"),
    ("2245", "22:45"),
    ("2300", "23:00"),
    ("2315", "23:15"),
    ("2330", "23:30"),
    ("2345", "23:45"),
]


class ProjectTask(models.Model):
    _inherit = "project.task"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single Document",
        help="Single Document to which the task is linked.",
        domain="[('company_id', '=', company_id)]",
        ondelete="cascade",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_single_document_id.pnt_single_document_type",
    )
    pnt_is_transport_template = fields.Boolean(
        string="Is transport template",
    )
    pnt_holder_id = fields.Many2one(
        related="pnt_single_document_id.pnt_holder_id",
        store=True,
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
        store=True,
    )
    pnt_partner_pickup_city = fields.Char(
        related="pnt_partner_pickup_id.city",
        store=True,
    )
    pnt_carrier_id = fields.Many2one(
        string="Carrier",
        comodel_name="res.partner",
        domain=[
            ("is_company", "=", True),
            ("category_id", "=", 9),
        ],
        copy=False,
        check_company=True,
        compute='_compute_pnt_carrier_id',
        store=True,
    )
    pnt_transport_id = fields.Many2one(
        string="Driver",
        comodel_name="res.partner",
    )
    pnt_vehicle_category_id = fields.Many2one(
        string="Vehicle Category",
        comodel_name="pnt.fleet.vehicle.category",
    )
    pnt_vehicle_id = fields.Many2one(
        string="Vehicle",
        comodel_name="fleet.vehicle",
    )
    pnt_vehicle_license_plate = fields.Char(
        related="pnt_vehicle_id.license_plate",
        store=True,
    )
    pnt_domain_vehicle_ids = fields.Many2many(
        string="Domain vehicles",
        comodel_name="fleet.vehicle",
        compute="_compute_pnt_domain_vehicle_ids",
    )
    pnt_domain_transport_ids = fields.Many2many(
        string="Domain transports",
        comodel_name="res.partner",
        compute="_compute_pnt_domain_transport_ids",
    )
    pnt_pickup_date = fields.Datetime(
        string="Made Pickup Date",
        index=True,
        readonly=False,
    )
    pnt_expected_pickup_date = fields.Datetime(
        string="Expected Pickup Date",
    )
    pnt_product_ids = fields.Many2many(
        comodel_name="product.product",
        relation="task_product_du_rel",
        column1="task_id",
        column2="product_id",
        string="Products",
    )
    pnt_transport_purchase_order_id = fields.Many2one(
        comodel_name="purchase.order",
        string="Transport purchase order",
    )
    pnt_product_container_ids = fields.One2many(
        comodel_name="pnt.product.container.task",
        inverse_name="pnt_task_id",
        string="Products",
    )
    pnt_product_container_ids_kanban = fields.Html(
        compute="_compute_pnt_product_container_ids",
    )
    pnt_logistic_route_id = fields.Many2one(
        "pnt.logistic.route",
        string="Logistic route",
    )
    ### ISSUE ###
    pnt_issue_flag_page = fields.Boolean(
        string="Issue flag page",
        compute="_compute_pnt_issue_flag_page",
    )
    pnt_sd_line_id = fields.Many2one(
        "pnt.single.document.line",
        "SD line",
    )
    pnt_product_id = fields.Many2one(
        "product.product",
        related="pnt_sd_line_id.pnt_product_id",
    )
    pnt_container_id = fields.Many2one(
        comodel_name="product.product",
        related="pnt_sd_line_id.pnt_container_id",
    )
    pnt_partner_user_id = fields.Many2one(
        string="Commercial account",
        related="partner_id.user_id",
    )
    pnt_manipulation = fields.Selection(
        selection=MANIPULATION,
        string="Manipulation",
    )
    currency_id = fields.Many2one(
        "res.currency",
        "Currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    pnt_input_weight = fields.Float(
        string="Declared net weight",
    )
    pnt_output_weight = fields.Float(
        string="Real weight",
        compute="_compute_output_weight",
    )
    pnt_waste_reclassified_ids = fields.One2many(
        "pnt.waste.reclassified",
        "pnt_task_id",
        "Reclassified Waste",
    )
    pnt_image_1_1920 = fields.Image(
        "Image 1 1920",
        max_width=1920,
        max_height=1920,
    )
    pnt_image_1_1024 = fields.Image(
        "Image 1 1024",
        related="pnt_image_1_1920",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    pnt_image_1_512 = fields.Image(
        "Image 1 512",
        related="pnt_image_1_1920",
        max_width=512,
        max_height=512,
        store=True,
    )
    pnt_image_1_256 = fields.Image(
        "Image 1 256",
        related="pnt_image_1_1920",
        max_width=256,
        max_height=256,
        store=True,
    )
    pnt_image_1_128 = fields.Image(
        "Image 1 128",
        related="pnt_image_1_1920",
        max_width=128,
        max_height=128,
        store=True,
    )
    pnt_image_2_1920 = fields.Image(
        "Image 2 1920",
        max_width=1920,
        max_height=1920,
    )
    pnt_image_2_1024 = fields.Image(
        "Image 2 1024",
        related="pnt_image_2_1920",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    pnt_image_2_512 = fields.Image(
        "Image 2 512",
        related="pnt_image_2_1920",
        max_width=512,
        max_height=512,
        store=True,
    )
    pnt_image_2_256 = fields.Image(
        "Image 2 256",
        related="pnt_image_2_1920",
        max_width=256,
        max_height=256,
        store=True,
    )
    pnt_image_2_128 = fields.Image(
        "Image 2 128",
        related="pnt_image_2_1920",
        max_width=128,
        max_height=128,
        store=True,
    )
    pnt_image_3_1920 = fields.Image(
        "Image 3 1920",
        max_width=1920,
        max_height=1920,
    )
    pnt_image_3_1024 = fields.Image(
        "Image 3 1024",
        related="pnt_image_3_1920",
        max_width=1024,
        max_height=1024,
        store=True,
    )
    pnt_image_3_512 = fields.Image(
        "Image 3 512",
        related="pnt_image_3_1920",
        max_width=512,
        max_height=512,
        store=True,
    )
    pnt_image_3_256 = fields.Image(
        "Image 3 256",
        related="pnt_image_3_1920",
        max_width=256,
        max_height=256,
        store=True,
    )
    pnt_image_3_128 = fields.Image(
        "Image 3 128",
        related="pnt_image_3_1920",
        max_width=128,
        max_height=128,
        store=True,
    )
    pnt_du_visible = fields.Boolean()
    pnt_reason_id = fields.Many2one(
        string="Reason close",
        comodel_name="pnt.project.task.reason",
    )
    pnt_sale_order_count = fields.Integer(
        string="Sale Order Count",
        compute="_compute_pnt_sale_order_count",
    )
    pnt_sale_order_ids = fields.One2many(
        string="Sale Order",
        comodel_name="sale.order",
        inverse_name="pnt_incidence_task_id",
    )
    pnt_is_driver_plate = fields.Boolean(
        default=False,
    )
    pnt_vehicle_changed = fields.Boolean(
        default=False,
        string="Vehicle cahnged",
    )
    pnt_city = fields.Char(
        string="Population",
        related="partner_id.city",
        store=True,
    )
    pnt_observations = fields.Html(
        related="pnt_single_document_id.pnt_observations",
    )
    pnt_has_du_obervations = fields.Boolean(
        compute="_compute_has_pnt_observations",
    )

    @api.depends("pnt_single_document_id.pnt_observations")
    def _compute_has_pnt_observations(self):
        for record in self:
            result = False
            if record.pnt_single_document_id:
                if (record.pnt_single_document_id.pnt_observations
                  and record.pnt_single_document_id.pnt_observations != '<p><br></p>'):
                    result = True
            record.pnt_has_du_obervations = result
    def show_du_pnt_observations(self):
        return {
            'name': _('DU Observations'),
            'type': 'ir.actions.act_window',
            'res_model': 'pnt.du.observations.wiz',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
               'default_pnt_observations': self.pnt_single_document_id.pnt_observations,
            },
            'target': 'new'
        }

    def _compute_pnt_sale_order_count(self):
        for task in self:
            task.pnt_sale_order_count = len(task.pnt_sale_order_ids)

    # ISSUE
    @api.depends("project_id", "pnt_transport_id")
    def _compute_stage_id(self):
        res = super(ProjectTask, self)._compute_stage_id()
        for task in self:
            if task.pnt_single_document_id:
                if task.pnt_transport_id:
                    sequence = 20
                    # Comprobar si existe fecha asignación en contexto
                    date_assig = self._context.get("assign_date", False)
                    if date_assig:
                        task.date_deadline = date_assig
                else:
                    sequence = 10
                task_asign = self.env["project.task.type"].search(
                    [
                        ("project_ids", "=", task.project_id.id),
                        ("sequence", "=", sequence),
                        ("active", "=", True),
                    ],
                    limit=1,
                )
                if task_asign:
                    task.stage_id = task_asign
        return res

    @api.depends("pnt_product_container_ids")
    def _compute_pnt_product_container_ids(self):
        for rec in self:
            result = ""
            for prod in rec.pnt_product_container_ids:
                if result != "":
                    result = result + "<br> - " + prod.display_name
                else:
                    result = "<b>Productos:</b><br> - " + prod.display_name
            rec.pnt_product_container_ids_kanban = result

    def create_purchase_from_task(self, values=None):
        if self._context.get("skip_create_purchase_from_task"):
            return
        if values and "pnt_transport_id" not in values:
            return
        self = self.with_context(skip_create_purchase_from_task=True)
        for ta in self:
            if not ta.pnt_is_transport_template:
                ta.pnt_single_document_id.pnt_transport_id = ta.pnt_transport_id
                ta.pnt_single_document_id.pnt_vehicle_id = ta.pnt_vehicle_id

    def action_view_sale_order(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "sale.action_quotations_with_onboarding"
        )
        action["domain"] = [("id", "in", self.pnt_sale_order_ids.ids)]
        action["context"] = self._context
        return action

    def _transport_purchase_order_create_prepare_values(self):
        self.ensure_one()
        prod = self.env["product.product"].search(
            [
                ("product_tmpl_id.categ_id", "=", 24),
                ("product_tmpl_id.company_id", "=", self.company_id.id),
            ],
            limit=1,
        )
        if prod:
            return {
                "partner_id": self.pnt_transport_id.id,
                "company_id": self.company_id.id,
                "date_order": self.pnt_expected_pickup_date,
                "project_task_id": self.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "name": prod.name,
                            "product_id": prod.id,
                            "product_qty": 1,
                            "product_uom": prod.uom_id.id,
                            "price_unit": 10,
                        },
                    )
                ],
            }
        else:
            return {
                "partner_id": self.pnt_transport_id.id,
                "company_id": self.company_id.id,
                "date_order": self.pnt_expected_pickup_date,
                "project_task_id": self.id,
            }

    def _transport_purchase_order_create(self):
        values = self._transport_purchase_order_create_prepare_values()
        pu = self.env["purchase.order"].sudo().create(values)
        self.write({"pnt_transport_purchase_order_id": pu.id})
        return pu

    def reset_transport_vehicle(self, vals_ori, values):
        stage_assign_id = self.env["ir.model.data"].xmlid_to_res_id(
            "project_task_default_stage.project_tt_analysis"
        )
        if values.get("stage_id") != stage_assign_id or self._context.get(
            "reset_transport_vehicle"
        ):
            return
        stage_plan_id = self.env["ir.model.data"].xmlid_to_res_id(
            "project_task_default_stage.project_tt_specification"
        )
        for record in self.with_context(reset_transport_vehicle=True):
            if vals_ori.get(record.id) == stage_plan_id:
                record.write(
                    {
                        "pnt_transport_id": False,
                        "pnt_vehicle_id": False,
                    }
                )
                purchase = record.pnt_transport_purchase_order_id
                if purchase and purchase.state in (
                    "draft",
                    "to approve",
                    "sent",
                    "purchase",
                ):
                    purchase.button_cancel()
                    record.pnt_transport_purchase_order_id = False

    @api.constrains(
        "project_id",
        "user_id",
        "parent_id",
        "date_deadline",
        "tag_ids",
        "partner_id",
        "pnt_vehicle_category_id",
        "pnt_expected_pickup_date",
    )
    def _check_fields_stage(self):
        stage_process = self.env["ir.model.data"].xmlid_to_res_id(
            "project_task_default_stage.project_tt_design"
        )
        stage_plan_id = self.env["ir.model.data"].xmlid_to_res_id(
            "project_task_default_stage.project_tt_deployment"
        )
        if any(x.stage_id.id in (stage_process, stage_plan_id) for x in self):
            raise ValidationError(
                _(
                    "To modify any of the fields you have edited, change the task to "
                    "the planned state."
                )
            )

    @api.depends("pnt_input_weight", "pnt_waste_reclassified_ids.pnt_weight")
    def _compute_output_weight(self):
        for record in self:
            record.pnt_output_weight = record.pnt_input_weight - sum(
                record.pnt_waste_reclassified_ids.filtered(
                    "pnt_waste_id.pnt_is_waste"
                ).mapped("pnt_weight")
            )
    @api.depends("pnt_transport_id")
    def _compute_pnt_carrier_id(self):
        for record in self:
            if (not record.pnt_carrier_id
                    and record.pnt_transport_id
                    and record.pnt_transport_id.parent_id):
                record.pnt_carrier_id=record.pnt_transport_id.parent_id
    @api.depends("project_id")
    def _compute_pnt_issue_flag_page(self):
        for record in self:
            record.pnt_issue_flag_page = (
                record.project_id.id
                == record.company_id.pnt_single_document_issue_project_id.id
            )

    @api.onchange("pnt_vehicle_category_id")
    def onchange_pnt_vehicle_category_id(self):
        self.pnt_vehicle_id = None
        self.pnt_transport_id = None
        self.pnt_carrier_id = None
        self.pnt_vehicle_changed = False

    @api.onchange("pnt_carrier_id")
    def onchange_pnt_carrier_id(self):
        self.pnt_vehicle_changed = True
        self.pnt_vehicle_id = None
        if (not self.pnt_carrier_id or
                self.pnt_carrier_id
                and self.pnt_transport_id
                and self.pnt_transport_id.parent_id):
            if self.pnt_carrier_id != self.pnt_transport_id.parent_id:
                self.pnt_transport_id = None

    @api.onchange("pnt_transport_id")
    def onchange_pnt_transport_id(self):
        self.pnt_vehicle_id = False
        if not self.pnt_vehicle_category_id or not self.pnt_transport_id:
            return
        domain = [("pnt_category_ids", "in", self.pnt_vehicle_category_id.ids)]
        if self.pnt_transport_id:
            domain.append(("driver_id", "=", self.pnt_transport_id.id))
        if self.pnt_carrier_id:
            domain.append(("pnt_carrier_id", "=", self.pnt_carrier_id.id))
        vehicle = self.env["fleet.vehicle"].search(domain, limit=1)
        if vehicle:
            self.pnt_vehicle_id = vehicle
        elif self.pnt_domain_vehicle_ids:
            self.pnt_vehicle_id = self.pnt_domain_vehicle_ids[:1]

    @api.depends("pnt_vehicle_category_id")
    def _compute_pnt_domain_vehicle_ids(self):
        self.pnt_domain_vehicle_ids = False
        for record in self:
            if not record.pnt_vehicle_category_id:
                continue
            domain = [("pnt_category_ids", "in", record.pnt_vehicle_category_id.ids)]
            record.pnt_domain_vehicle_ids = self.env["fleet.vehicle"].search(domain).ids

    @api.depends("pnt_vehicle_category_id", "pnt_carrier_id")
    def _compute_pnt_domain_transport_ids(self):
        self.pnt_domain_transport_ids = False
        for record in self:
            if not record.pnt_vehicle_category_id:
                continue
            if not record.pnt_carrier_id:
                record.pnt_domain_transport_ids = (
                    self.env["res.partner"]
                    .search(
                        [
                            ("pnt_is_driver", "=", True),
                            ("company_id", "in", [False, record.company_id.id]),
                        ]
                    )
                    .ids
                )
                continue
            domain = [
                ("pnt_carrier_id", "=", record.pnt_carrier_id.id),
            ]
            record.pnt_domain_transport_ids = (
                self.env["fleet.vehicle"].search(domain).driver_id.ids
            )

    def set_date_pickup_du(self, values=None):
        if self._context.get("skip_set_date_pickup_du") or (
            isinstance(values, dict) and "pnt_expected_pickup_date" not in values
        ):
            return
        for record in self.with_context(skip_set_date_pickup_du=True):
            if (
                record.pnt_single_document_id.pnt_pickup_date_type == "soon"
                and record.pnt_expected_pickup_date
            ):
                record.pnt_single_document_id.pnt_pickup_date = (
                    record.pnt_expected_pickup_date
                )

    @api.constrains("stage_id", "pnt_sd_line_id")
    def _check_stage(self):
        if self._context.get("allow_stage"):
            return
        stages_close = (
            self.env["project.task.type"].search([("is_closed", "=", True)]).ids
        )
        for record in self:
            if (
                record.stage_id.id in stages_close
                and record.pnt_sd_line_id
                and not self._context.get("control_stage")
            ):
                raise ValidationError(
                    _("You can only change stages using the buttons.")
                )

    def button_create_sale_incidence(self):
        sale = Form(recordp=self.env["sale.order"], view="sale.view_order_form")
        sale.partner_id = self.partner_id
        product_id = self.env["product.product"].search(
            [("pnt_is_product_incidence", "=", True)], limit=1
        )
        if not product_id:
            raise UserError(_("You must have a product with the incidence flag."))
        total = sum(self.pnt_waste_reclassified_ids.mapped("pnt_subtotal"))
        with sale.order_line.new() as line_form:
            line_form.product_id = product_id
            line_form.price_unit = total
        sale = sale.save()
        sale.pnt_incidence_task_id = self
        action = self.action_view_sale_order()
        action["domain"] = [("id", "=", sale.id)]
        action["context"] = self._context
        return action

    def _create_activities_group(self, task):
        act_type_id = self.env["ir.model.data"].xmlid_to_res_id(
            "mail.mail_activity_data_todo"
        )
        group_id = ACTIVITY_TEAMS["accounting"]
        model_id = self.env["ir.model"]._get("project.task").id
        new_activity = self.env["mail.activity"].new(
            {
                "activity_type_id": act_type_id,
                "res_id": task.id,
                "team_id": group_id,
                "team_user_id": False,
                "user_id": False,
                "res_model_id": model_id,
            }
        )
        data = new_activity._convert_to_write(new_activity._cache)
        return self.env["mail.activity"].create(data)

    def create_activities_to_group(self, original_values, new_values):
        if self._context.get("create_activities_to_group"):
            return
        if new_values.get("stage_id") != TASK_STAGES["invoiced"]:
            return
        for task in self.with_context(create_activities_to_group=True):
            if original_values.get(task.id) == TASK_STAGES["commercial"]:
                task._create_activities_group(task)

    def show_wizard_reason(self, domain):
        ctx = dict(self.env.context, default_pnt_type=domain, task_id=self.id)
        view_id = self.env.ref("custom_pnt.pnt_task_reason_wiz_view_form").id
        return {
            "name": _("Reason"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "pnt.task.reason.wiz",
            "views": [(view_id, "form")],
            "view_id": view_id,
            "target": "new",
            "context": ctx,
        }

    def button_stage_discount(self):
        return self.show_wizard_reason("discount")

    def button_stage_invoice(self):
        return self.show_wizard_reason("invoice")

    def button_stage_close(self):
        return self.show_wizard_reason("close")

    def change_stage_logistic(self, values):
        if self._context.get("skip_change_stage_logistic"):
            return
        if not values.get("pnt_transport_id"):
            return
        if (
            self.pnt_single_document_id
            and self.pnt_single_document_id.pnt_app_du_id
            and self.pnt_single_document_id.pnt_app_du_id.pnt_processed
        ):
            return
        for task in self.with_context(skip_change_stage_logistic=True):
            if (
                task.project_id.id == PROJECTS["logistics"]
                and task.stage_id.id not in (TASK_STAGES["planned"],
                                             TASK_STAGES["cancelled"],
                                             TASK_STAGES["done"])
                and task.pnt_single_document_id.state
                not in ("received", "finished", "cancel")
            ):
                task.stage_id = TASK_STAGES["planned"]

    @api.model_create_multi
    def create(self, values):
        for vals in values:
            vals.pop("pnt_du_visible", None)
            vals.get("pnt_sd_line_id") and vals.pop("stage_id", None)
        ctx = dict(self.env.context, default_pnt_du_visible=False, allow_stage=True)
        if self._context.get("default_pnt_du_visible"):
            res = super(ProjectTask, self.sudo().with_context(ctx)).create(values)
        else:
            res = super(ProjectTask, self.with_context(ctx)).create(values)
        res.set_date_pickup_du()
        res.create_purchase_from_task()
        return res

    def write(self, values):
        vals_ori = {x.id: x.stage_id.id for x in self}
        res = super().write(values)
        self.reset_transport_vehicle(vals_ori, values)
        self.set_date_pickup_du(values)
        self.change_stage_logistic(values)
        self.create_activities_to_group(vals_ori, values)
        if values.get("pnt_carrier_id"):
            vtran = values.get("pnt_carrier_id")
            if vtran and self.pnt_single_document_id.pnt_carrier_id.id != vtran:
                self.pnt_single_document_id.pnt_carrier_id = vtran
        if values.get("pnt_vehicle_category_id"):
            vcat = values.get("pnt_vehicle_category_id")
            if vcat and self.pnt_single_document_id.pnt_vehicle_category_id.id != vcat:
                self.pnt_single_document_id.pnt_vehicle_category_id = vcat
        if values.get("pnt_vehicle_id"):
            veh = values.get("pnt_vehicle_id")
            if veh and self.pnt_single_document_id.pnt_vehicle_id.id != veh:
                self.pnt_single_document_id.pnt_vehicle_id = veh
                self.pnt_single_document_id.pnt_vehicle_aux_id = veh
            # else:
            #     self.pnt_single_document_id.pnt_vehicle_id = False
        self.create_purchase_from_task(values)
        return res


class PntProductContainerTask(models.Model):
    _name = "pnt.product.container.task"
    _description = "List of product/container in task"

    color = fields.Integer(
        string="Color Index",
        default=0,
        compute="onchange_pnt_container_id",
    )
    pnt_container_movement_id = fields.Many2one(
        comodel_name="pnt.container.movement",
        string="Container movement",
    )
    pnt_task_id = fields.Many2one(
        comodel_name="project.task",
        required=True,
        ondelete="cascade",
    )

    pnt_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
    )
    pnt_container_id = fields.Many2one(
        comodel_name="product.product",
        string="Container",
        domain=[("pnt_is_container", "=", True)],
        change_default=True,
        ondelete="restrict",
        check_company=True,  # Unrequired company
    )

    @api.onchange("pnt_container_id")
    def onchange_pnt_container_id(self):
        for ta in self:
            ta.color = 0
            if ta.pnt_container_id:
                if ta.pnt_container_id.pnt_container_color:
                    ta.color = ta.pnt_container_id.pnt_container_color

    @api.depends("pnt_product_id", "pnt_container_id")
    def name_get(self):
        res = []
        for record in self:
            name = record.pnt_product_id.display_name
            if record.pnt_container_id:
                name = name + " | " + record.pnt_container_id.display_name
            res.append((record.id, name))
        return res


class PntWasteReclassified(models.Model):
    _name = "pnt.waste.reclassified"
    _description = "Reclassified Waste"
    _rec_name = "pnt_waste_id"
    _sql_constraints = [
        (
            "name_uniq",
            "unique(pnt_task_id, pnt_waste_id)",
            "Waste reclassified already exist.",
        ),
    ]
    pnt_task_id = fields.Many2one(
        "project.task",
        "Incidence",
        required=True,
        ondelete="cascade",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_task_id.pnt_single_document_type",
    )
    pnt_waste_id = fields.Many2one(
        string="Waste",
        comodel_name="product.product",
        domain=[("pnt_is_waste", "=", True)],
        required=True,
    )
    pnt_weight = fields.Float(
        string="Weight",
        digits="Stock Weight",
        compute="_compute_line",
        readonly=False,
        store=True,
    )
    pnt_price_unit = fields.Float(
        string="Unit Price",
        digits="Product Price",
        compute="_compute_pnt_price_unit",
        readonly=False,
        store=True,
    )
    pnt_uom_id = fields.Many2one(
        related="pnt_waste_id.uom_id",
    )
    pnt_subtotal = fields.Float(
        string="Subtotal",
        compute="_compute_line",
        store=True,
    )
    pnt_scale_waste_ids = fields.Many2many(
        related="pnt_task_id.pnt_single_document_id.pnt_scales_id.pnt_waste_ids",
    )
    pnt_waste_domain_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_pnt_waste_domain_ids",
        relation="pnt_project_task_waste_domain_rel",
        store=True,
    )

    @api.depends("pnt_single_document_type")
    def _compute_pnt_waste_domain_ids(self):
        for record in self:
            if record.pnt_single_document_type != "output":
                record.pnt_waste_domain_ids = record.pnt_scale_waste_ids
            else:
                product_ids = (
                    self.env["product.product"]
                    .search(
                        [
                            ("pnt_is_waste", "=", True),
                            ("company_id", "in", [False, self.env.company.id]),
                        ]
                    )
                    .ids
                )
                record.pnt_waste_domain_ids = product_ids

    @api.depends("pnt_waste_id")
    def _compute_pnt_price_unit(self):
        for record in self:
            record.pnt_price_unit = record.pnt_waste_id.lst_price

    @api.depends(
        "pnt_waste_id",
        "pnt_weight",
        "pnt_price_unit",
        "pnt_task_id.pnt_manipulation",
    )
    def _compute_line(self):
        for record in self:
            task = record.pnt_task_id
            if record.pnt_waste_id.pnt_is_waste_manipulation and task.pnt_manipulation:
                h_manipulation = int(task.pnt_manipulation[:2]) * 60
                m_manipulation = int(task.pnt_manipulation[2:4])
                record.pnt_weight = (h_manipulation + m_manipulation) / 60
            record.pnt_subtotal = record.pnt_price_unit * record.pnt_weight
