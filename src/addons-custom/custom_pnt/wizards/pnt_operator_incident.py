from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree
import datetime

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

class PntOperatorIncident(models.TransientModel):
    _name = "pnt.operator.incident"
    _rec_name = "pnt_single_document_id"

    pnt_state = fields.Selection(
        [
            ("oi_new", _("oi_new")),
            ("oi_du", _("oi_du")),
            ("oi_waste", _("oi_waste")),
            ("oi_images", _("oi_images")),
            ("oi_reclas", _("oi_reclas")),
            ("oi_mani", _("pi_mani")),
            ("oi_finished", _("oi_finished")),
            ("oi_cancel", _("oi_cancel")),
        ],
        string="State",
        copy=False,
        tracking=4,
        default="oi_new",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_employee_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Employee",
        domain="[('company_id', '=', company_id),"
               " ('pnt_access_incident_app', '=', True)]",
    )
    pnt_date = fields.Date(
        string="Date",
        default=fields.Date.today,
    )

    pnt_single_document_domain_ids = fields.Many2many(
        comodel_name="pnt.single.document",
        compute="_compute_pnt_single_document_id_domain_ids",
        relation="pnt_single_document_oi_domain_rel",
        store=True,
    )

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single Document",
    )
    pnt_holder_id = fields.Many2one(
        related="pnt_single_document_id.pnt_holder_id",
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
    )
    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Waste",
   )
    pnt_container_id = fields.Many2one(
        comodel_name="product.product",
        string="Container",
    )
    pnt_product_uom_qty = fields.Float(
        string="Weight",
        digits="Product Unit of Measure",
    )
    pnt_product_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
    )
    pnt_line_ids = fields.Many2many(
        comodel_name="pnt.operator.incident.line",
        inverse_name="pnt_operator_incident_id",
        compute="_compute_pnt_line_ids",
        store=True,
        string="DU waste lines",
    )
    pnt_line_id = fields.Many2one(
        comodel_name="pnt.operator.incident.line",
        string="Waste",
    )
    pnt_image_1 = fields.Binary(
        string="Photo 1",
    )
    pnt_image_2 = fields.Binary(
        string="Photo 2",
    )
    pnt_image_3 = fields.Binary(
        string="Photo 3",
    )
    pnt_manipulation = fields.Selection(
        selection=MANIPULATION,
        string="Manipulation",
    )
    pnt_waste_reclassified_ids = fields.One2many(
        comodel_name="pnt.waste.reclassified.oi",
        inverse_name="pnt_operator_incident_id",
        string="Reclassified Waste",
    )

    def pnt_add_product_waste_manipulation(self):
        for record in self:
            waste = [(6, False, [])]
            product_waste_manipulation = self.env["product.product"].search(
                [("pnt_is_waste_manipulation", "=", True)], limit=1
            )
            if product_waste_manipulation:
                waste = [
                    (
                        0,
                        0,
                        {
                            "pnt_waste_id": product_waste_manipulation.id,
                            "pnt_weight": 1,
                            "pnt_is_waste_manipulation": True,
                        },
                    )
                ]
                record.pnt_waste_reclassified_ids = waste


    @api.depends("pnt_date","pnt_employee_id")
    def _compute_pnt_single_document_id_domain_ids(self):
        for record in self:
            date_ini = datetime.datetime(record.pnt_date.year, record.pnt_date.month, record.pnt_date.day, 0, 0, 0)
            date_end = datetime.datetime(record.pnt_date.year, record.pnt_date.month, record.pnt_date.day, 23, 59, 59)
            du_ids = (
                self.env["pnt.single.document"]
                .search(
                    [
                        ('state', 'in', ['plant','received']),
                        ("company_id", "in", [False, self.env.company.id]),
                        ("pnt_date_to_plant", ">=", date_ini),
                        ("pnt_date_to_plant", "<=", date_end),
                        ("pnt_scales_id", "in", record.pnt_employee_id.pnt_scales_ids.ids),
                    ]
                )
                .ids
            )
            record.pnt_single_document_domain_ids = du_ids

    @api.onchange("pnt_employee_id")
    def onchange_pnt_employee_id(self):
        self.pnt_single_document_id = False
        self.pnt_new_form()

    def pnt_new_form(self):
        self.pnt_product_id = False
        self.pnt_container_id = False
        self.pnt_product_uom_qty = False
        self.pnt_product_uom = False
        self.pnt_line_id = False
        self.pnt_single_document_line_id = False

    @api.depends("pnt_single_document_id")
    def _compute_pnt_line_ids(self):
        for record in self:
            # self.pnt_save_form()
            if record.pnt_single_document_id:
                # devolvemos acción
                # self.reload_screen()
                # record.pnt_state = 'oi_du'
                record.pnt_line_ids.unlink()
                du_lines = (
                    record.pnt_single_document_id.pnt_single_document_line_ids.filtered(
                        lambda x: x.pnt_product_id.pnt_is_waste)
                )
                if du_lines:
                    list_lines = []
                    for lin in du_lines:
                        dict_line = {
                            "pnt_single_document_line_id": lin.id,
                            "pnt_operator_incident_id": record.id,
                        }
                        list_lines.append((0, 0, dict_line))
                    record.write({
                        "pnt_line_ids": list_lines,
                    })
        # devolvemos acción
        # self.reload_screen()
    def pnt_change_waste(self):
        for record in self:
            self.save_waste(record)
            record.pnt_state = "oi_waste"
            record.pnt_line_id = False
            record.pnt_single_document_line_id = False
            record.pnt_product_id = False
            record.pnt_container_id = False
            record.pnt_product_uom_qty = False
            record.pnt_product_uom = False
            record.pnt_image_1 = False
            record.pnt_image_2 = False
            record.pnt_image_3 = False
            record.pnt_manipulation = False
            record.pnt_waste_reclassified_ids.unlink()

    def pnt_return_to_waste(self):
        for record in self:
            record.pnt_state = "oi_waste"
            self.save_waste(record)
    def pnt_confirm_images(self):
        for record in self:
            record.pnt_state = "oi_reclas"
            self.save_waste(record)
    def pnt_confirm_reclas(self):
        for record in self:
            record.pnt_state = "oi_mani"
            self.save_waste(record)
    def pnt_return_to_images(self):
        for record in self:
            record.pnt_state = "oi_images"
            self.save_waste(record)
    def pnt_return_to_reclas(self):
        for record in self:
            record.pnt_state = "oi_reclas"
            self.save_waste(record)
    def pnt_confirm_manipulation(self):
        return True
    def reload_new_oi(self):
        view_id = self.env.ref("custom_pnt.view_form_pnt_operator_incident").id
        return {
            "type": "ir.actions.act_window",
            "name": "Load DU",
            "view_type": "form",
            "view_mode": "form",
            "view_id": view_id,
            "res_model": "pnt.operator.incident",
            "context": {
                "default_pnt_employee_id": self.pnt_employee_id.id,
                "deafult_pnt_date": self.pnt_date,
            },
            "target": "current",
        }

    def pnt_cancel(self):
        # self.reload_new_oi()
        view_id = self.env.ref("custom_pnt.view_form_pnt_operator_incident").id
        return {
            "type": "ir.actions.act_window",
            "name": "Load DU",
            "view_type": "form",
            "view_mode": "form",
            "view_id": view_id,
            "res_model": "pnt.operator.incident",
            "context": {
                "default_pnt_employee_id": self.pnt_employee_id.id,
            },
            "target": "current",
        }
    def save_waste(self,record):
        if (record.pnt_image_1 or
                record.pnt_image_2 or
                record.pnt_image_3 or
                record.pnt_manipulation or
                record.pnt_waste_reclassified_ids):
            has_incidence = True
        else:
            has_incidence = False
        list_reclas = []
        if record.pnt_waste_reclassified_ids:
            for recla in record.pnt_waste_reclassified_ids:
                dict_reclas = {
                    "pnt_line_id": record.pnt_line_id.id,
                    "pnt_waste_id": recla.pnt_waste_id.id,
                    "pnt_weight": recla.pnt_weight,
                }
                list_reclas.append((0, 0, dict_reclas))
        record.pnt_line_id.pnt_waste_reclassified_ids.unlink()
        record.pnt_line_id.write({
            'pnt_has_incidence': has_incidence,
            'pnt_image_1': record.pnt_image_1,
            'pnt_image_2': record.pnt_image_2,
            'pnt_image_3': record.pnt_image_3,
            'pnt_manipulation': record.pnt_manipulation,
            'pnt_waste_reclassified_ids': list_reclas,
        })

    @api.model
    def fields_view_get(
        self, view_id=None, view_type="form", toolbar=False, submenu=False
    ):
        res = super().fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        if view_type == "form":
            doc = etree.XML(res["arch"])
            for node in doc.xpath("//field[@name='pnt_single_document_id']"):
                node_val = node.get("context", "{}").strip()[1:-1]
                elems = node_val.split(",") if node_val else []
                to_add = ["'pnt_change_name': True"]
                node.set("context", "{" + ", ".join(elems + to_add) + "}")
            res["fields"]["arch"] = etree.tostring(doc)
        return res

    def create_incidences(self):
        for record in self:
            # Actualizar la actual linea de Residuos
            self.save_waste(record)
            # Recorrer las lineas de residuo y generar las incidencias
            project_id = self.company_id.pnt_single_document_issue_project_id
            for waste_line in record.pnt_line_ids:
                if waste_line.pnt_has_incidence:
                    self._incidence_create_task(project_id,waste_line)
            record.pnt_state = "oi_finished"
        # devolvemos acción
        view_id = self.env.ref("custom_pnt.view_form_pnt_operator_incident").id
        return {
            "type": "ir.actions.act_window",
            "name": "Load DU",
            "view_type": "form",
            "view_mode": "form",
            "view_id": view_id,
            "res_model": "pnt.operator.incident",
            "context": {
                "default_pnt_employee_id": record.pnt_employee_id.id,
            },
            "target": "current",
        }

    def _incidence_create_task_prepare_values(self, project,wastel):
        du = wastel.pnt_single_document_line_id.pnt_single_document_id
        if du.pnt_single_document_type in ("output",):
            default_user = du.pnt_scales_id.pnt_manager_responsible_id
        else:
            default_user = du.pnt_scales_id.pnt_responsible_id
        list_reclas = []
        if wastel.pnt_waste_reclassified_ids:
            for recla in wastel.pnt_waste_reclassified_ids:
                dict_reclas = {
                    "pnt_waste_id": recla.pnt_waste_id.id,
                    "pnt_weight": recla.pnt_weight,
                    "pnt_subtotal": recla.pnt_weight * recla.pnt_waste_id.lst_price
                }
                list_reclas.append((0, 0, dict_reclas))
        # Añadimos los gastos de manipulación.
        if wastel:
            maipulation_product = self.env["product.product"].browse(2680) # producto SMHORAR
            h_manipulation = int(wastel.pnt_manipulation[:2])
            m_manipulation = int(wastel.pnt_manipulation[2:])
            ttime = h_manipulation + m_manipulation / 60
            list_reclas.append((0, 0,{
                    "pnt_waste_id": maipulation_product.id,
                    "pnt_weight": ttime,
                    "pnt_subtotal": ttime * maipulation_product.lst_price
            }))
        return {
            "name": (
                "%s | %s"
                % (du.pnt_agreement_id.name, du.pnt_agreement_id.pnt_holder_id.name)
            ),
            "project_id": project.id,
            "partner_id": du.pnt_holder_id.id,
            "date_deadline": du.pnt_pickup_date,
            "pnt_single_document_id": du.id,
            "pnt_sd_line_id": wastel.pnt_single_document_line_id.id,
            "pnt_input_weight": self.pnt_product_uom_qty,
            "user_id": default_user.id or self.env.user.id,
            "pnt_du_visible": True,
            "pnt_input_weight": wastel.pnt_product_uom_qty,
            'pnt_image_1_1920': wastel.pnt_image_1,
            'pnt_image_2_1920': wastel.pnt_image_2,
            'pnt_image_3_1920': wastel.pnt_image_3,
            'pnt_manipulation': wastel.pnt_manipulation,
            "pnt_waste_reclassified_ids": list_reclas,
        }

    def _incidence_create_task(self, project, wastel):
        values = self._incidence_create_task_prepare_values(project,wastel)
        task = self.env["project.task"].sudo().create(values)
        if task:
            body = _('Incidence created by %s', self.pnt_employee_id.name)
            task.message_post(body=body)

    def reload_screen(self):
        action = self.env.ref("custom_pnt.action_pnt_operator_incident")
        action = action.read()[0]
        action.update({
            "target": "main",
            "context": self.env.context,
        })
        return action

class PntOperatorIncidentLine(models.TransientModel):
    _name = "pnt.operator.incident.line"

    pnt_operator_incident_id = fields.Many2one(
        comodel_name="pnt.operator.incident",
    )
    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_product_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_product_id",
    )
    pnt_container_id = fields.Many2one(
        related="pnt_single_document_line_id.pnt_container_id",
    )
    pnt_product_uom_qty = fields.Float(
        related="pnt_single_document_line_id.pnt_product_uom_qty",
    )
    pnt_product_uom = fields.Many2one(
        related="pnt_single_document_line_id.pnt_product_uom",
    )
    pnt_has_incidence = fields.Boolean(
        string = "Has incidence",
        default = False,
    )
    pnt_image_1 = fields.Binary(
        string="Photo 1",
    )
    pnt_image_2 = fields.Binary(
        string="Photo 2",
    )
    pnt_image_3 = fields.Binary(
        string="Photo 3",
    )
    pnt_manipulation = fields.Selection(
        selection=MANIPULATION,
        string="Manipulation",
    )
    pnt_waste_reclassified_ids = fields.One2many(
        comodel_name="pnt.waste.reclassified.oi.line",
        inverse_name="pnt_line_id",
        string="Reclassified Waste",
    )

    def pnt_save_form(self):
        return True

    def pnt_set_line(self):
        for rec in self:
            # rec.pnt_save_form()
            rec.pnt_operator_incident_id.write({
                'pnt_state': 'oi_images',
                'pnt_line_id': rec.id,
                'pnt_single_document_line_id': rec.pnt_single_document_line_id.id,
                'pnt_product_id': rec.pnt_product_id.id,
                'pnt_container_id': rec.pnt_container_id.id,
                'pnt_product_uom_qty': rec.pnt_product_uom_qty,
                'pnt_product_uom': rec.pnt_product_uom,
                'pnt_image_1': rec.pnt_image_1,
                'pnt_image_2': rec.pnt_image_2,
                'pnt_image_3': rec.pnt_image_3,
                'pnt_manipulation': rec.pnt_manipulation,
            })
            if rec.pnt_waste_reclassified_ids:
                list_reclas = []
                for recla in rec.pnt_waste_reclassified_ids:
                    dict_reclas = {
                        "pnt_operator_incident_id": rec.id,
                        "pnt_waste_id": recla.pnt_waste_id.id,
                        "pnt_weight": recla.pnt_weight,
                    }
                    list_reclas.append((0, 0, dict_reclas))
                rec.pnt_operator_incident_id.write({
                    "pnt_waste_reclassified_ids": list_reclas,
                })

class PntWasteReclassifiedOi(models.TransientModel):
    _name = "pnt.waste.reclassified.oi"
    _description = "Reclassified Waste"
    _rec_name = "pnt_waste_id"
    _sql_constraints = [
        (
            "name_uniq",
            "unique(pnt_operator_incident_id, pnt_waste_id)",
            "Waste reclassified already exist.",
        ),
    ]
    pnt_operator_incident_id = fields.Many2one(
        "pnt.operator.incident",
        "Incidence",
        required=True,
        ondelete="cascade",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_operator_incident_id.pnt_single_document_id.pnt_single_document_type",
    )
    pnt_scale_waste_ids = fields.Many2many(
        related="pnt_operator_incident_id.pnt_single_document_id.pnt_scales_id.pnt_waste_ids",
    )
    pnt_waste_domain_ids = fields.Many2many(
        comodel_name="product.product",
        compute="_compute_pnt_waste_domain_ids",
        relation="pnt_project_task_waste_oi_domain_rel",
        store=True,
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
        readonly=False,
        store=True,
    )
    pnt_is_waste_manipulation = fields.Boolean(
        default=False,
    )
    pnt_is_waste_description = fields.Char(
        string="Waste",
        compute="_compute_waste_description",
    )
    @api.depends("pnt_waste_id")
    def _compute_waste_description(self):
        for record in self:
            if record.pnt_waste_id:
                record.pnt_is_waste_description = record.pnt_waste_id.display_name
            else:
                record.pnt_is_waste_description = None
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

class PntWasteReclassifiedOiLine(models.TransientModel):
    _name = "pnt.waste.reclassified.oi.line"
    _description = "Reclassified Waste"
    _rec_name = "pnt_waste_id"
    _sql_constraints = [
        (
            "name_uniq",
            "unique(pnt_line_id, pnt_waste_id)",
            "Waste reclassified already exist.",
        ),
    ]
    pnt_line_id = fields.Many2one(
        comodel_name="pnt.operator.incident.line",
        string="Waste",
        required=True,
        ondelete="cascade",
    )
    pnt_single_document_type = fields.Selection(
        related="pnt_line_id.pnt_single_document_line_id.pnt_single_document_id.pnt_single_document_type",
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
        readonly=False,
        store=True,
    )
