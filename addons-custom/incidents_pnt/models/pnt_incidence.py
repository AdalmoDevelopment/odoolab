from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PntIncidence(models.Model):
    _name = "pnt.incidence"
    _description = "Incidence"
    _rec_name = "name"

    name = fields.Char(string="Name", compute="_compute_name", store=True)
    date = fields.Date(string="Date")
    material_id = fields.Many2one(
        string="Material",
        comodel_name="product.product",
        domain=[("pnt_is_waste", "=", True)],
    )
    equipment_id = fields.Many2one(
        string="Equipment",
        comodel_name="product.product",
    )
    input_weight = fields.Float(string="Declared net weight")
    output_weight = fields.Float(string="Real weight",compute="_compute_output_weight")
    manipulation = fields.Selection(
        string="Manipulation",
        selection=[
            ("00:00", "00:00"),
            ("00:15", "00:15"),
            ("00:30", "00:30"),
            ("00:45", "00:45"),
            ("01:00", "01:00"),
            ("01:15", "01:15"),
            ("01:30", "01:30"),
            ("01:45", "01:45"),
            ("02:00", "02:00"),
            ("02:15", "02:15"),
            ("02:30", "02:30"),
            ("02:45", "02:45"),
            ("03:00", "03:00"),
            ("03:15", "03:15"),
            ("03:30", "03:30"),
            ("03:45", "03:45"),
            ("04:00", "04:00"),
            ("04:15", "04:15"),
            ("04:30", "04:30"),
            ("04:45", "04:45"),
            ("05:00", "05:00"),
            ("05:15", "05:15"),
            ("05:30", "05:30"),
            ("05:45", "05:45"),
            ("06:00", "06:00"),
            ("06:15", "06:15"),
            ("06:30", "06:30"),
            ("06:45", "06:45"),
            ("07:00", "07:00"),
            ("07:15", "07:15"),
            ("07:30", "07:30"),
            ("07:45", "07:45"),
            ("08:00", "08:00"),
            ("08:15", "08:15"),
            ("08:30", "08:30"),
            ("08:45", "08:45"),
            ("09:00", "09:00"),
            ("09:15", "09:15"),
            ("09:30", "09:30"),
            ("09:45", "09:45"),
            ("10:00", "10:00"),
            ("10:15", "10:15"),
            ("10:30", "10:30"),
            ("10:45", "10:45"),
            ("11:00", "11:00"),
            ("11:15", "11:15"),
            ("11:30", "11:30"),
            ("11:45", "11:45"),
            ("12:00", "12:00"),
            ("12:15", "12:15"),
            ("12:30", "12:30"),
            ("12:45", "12:45"),
            ("13:00", "13:00"),
            ("13:15", "13:15"),
            ("13:30", "13:30"),
            ("13:45", "13:45"),
            ("14:00", "14:00"),
            ("14:15", "14:15"),
            ("14:30", "14:30"),
            ("14:45", "14:45"),
            ("15:00", "15:00"),
            ("15:15", "15:15"),
            ("15:30", "15:30"),
            ("15:45", "15:45"),
            ("16:00", "16:00"),
            ("16:15", "16:15"),
            ("16:30", "16:30"),
            ("16:45", "16:45"),
            ("17:00", "17:00"),
            ("17:15", "17:15"),
            ("17:30", "17:30"),
            ("17:45", "17:45"),
            ("18:00", "18:00"),
            ("18:15", "18:15"),
            ("18:30", "18:30"),
            ("18:45", "18:45"),
            ("19:00", "19:00"),
            ("19:15", "19:15"),
            ("19:30", "19:30"),
            ("19:45", "19:45"),
            ("20:00", "20:00"),
            ("20:15", "20:15"),
            ("20:30", "20:30"),
            ("20:45", "20:45"),
            ("21:00", "21:00"),
            ("21:15", "21:15"),
            ("21:30", "21:30"),
            ("21:45", "21:45"),
            ("22:00", "22:00"),
            ("22:15", "22:15"),
            ("22:30", "22:30"),
            ("22:45", "22:45"),
            ("23:00", "23:00"),
            ("23:15", "23:15"),
            ("23:30", "23:30"),
            ("23:45", "23:45"),
        ],
    )
    comment = fields.Text(string="Comment")
    incidence_cost = fields.Monetary(
        string="Incidence cost €",
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )
    delivery_note_number = fields.Char(string="Nº Delivery note")
    customer_id = fields.Many2one(string="Customer", comodel_name="res.partner")
    commercial_account_id = fields.Many2one(
        string="Commercial account", related="customer_id.user_id"
    )
    pnt_single_document_id = fields.Many2one(
        string="Single document",
        comodel_name="pnt.single.document",
        required=True,
    )
    pnt_single_document_line_id = fields.Many2one(
        string="Lines DU",
        comodel_name="pnt.single.document.line",
        required=True,
    )
    pnt_task_id = fields.Many2one(
        string="Task",
        comodel_name="project.task",
    )
    pnt_image_1 = fields.Binary(string="Image 1")
    pnt_image_2 = fields.Binary(string="Image 2")
    pnt_image_3 = fields.Binary(string="Image 3")
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_waste_reclassified_ids = fields.One2many(
        string="Reclassified Waste",
        comodel_name="pnt.incidence.reclassified",
        inverse_name="pnt_incidence_id",
    )

    @api.depends("pnt_single_document_id", "pnt_single_document_line_id")
    def _compute_name(self):
        for incident in self:
            incident.name = f"INC {incident.pnt_single_document_id.name} - {incident.pnt_single_document_line_id.id}"

    @api.depends("input_weight", "pnt_waste_reclassified_ids.pnt_weight")
    def _compute_output_weight(self):
        for record in self:
            record.output_weight = record.input_weight - sum(
                record.pnt_waste_reclassified_ids.mapped("pnt_weight")
            )

    @api.onchange("pnt_customer_id")
    def _onchange_pnt_customer_id(self):
        self.commercial_account_id = self.customer_id.user_id

    @api.constrains("pnt_single_document_line_id")
    def _check_du(self):
        for incident in self:
            if len(incident.pnt_single_document_line_id.pnt_incidence_ids) > 1:
                raise ValidationError(
                    _("There can be only one incidence per DU line.")
                )

    @api.model_create_multi
    def create(self, values):
        res = super().create(values)
        for incidence in res:
            line_du = incidence.pnt_single_document_line_id
            if line_du:
                line_du._create_task_incidence(incidence)
        return res


class PntIncidenceReclassified(models.Model):
    _name = "pnt.incidence.reclassified"
    _description = "Reclassified Incidence"
    _rec_name = "pnt_waste_id"
    _sql_constraints = [
        (
            "name_uniq",
            "unique(pnt_incidence_id, pnt_waste_id)",
            "Waste reclassified already exist.",
        ),
    ]

    pnt_incidence_id = fields.Many2one(
        string="Incidence",
        comodel_name="pnt.incidence",
        required=True,
        ondelete="cascade",
    )
    pnt_waste_id = fields.Many2one(
        string="Waste",
        comodel_name="product.template",
        domain=[("pnt_is_waste", "=", True)],
        required=True,
    )
    pnt_weight = fields.Float(string="Weight")
