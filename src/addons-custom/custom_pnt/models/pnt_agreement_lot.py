import calendar
import logging
from datetime import datetime, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tests import Form
from .. import DEFAULT_DELIVERY_PARTNER_ID, GROUPS, TASK_STAGES


class PntAgreementLot(models.Model):
    _name = "pnt.agreement.lot"
    _description = "Pnt agreement lot"
    _inherit = ["mail.thread"]

    pnt_agreement_id = fields.Many2one(
        "pnt.agreement.agreement",
        string="Agreement",
    )
    name = fields.Char(
        string="Name",
        default=lambda self: _("New"),
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )
    state = fields.Selection(
        [
            ("draft", _("Draft")),
            ("active", _("Active")),
            ("done", _("Done")),
        ],
        string="State",
        readonly=True,
        required=True,
        default="draft",
        compute="_pnt_compute_state",
    )
    pnt_agreement_pickup_ids = fields.Many2many(
        related="pnt_agreement_id.pnt_partner_pickup_ids"
    )
    pnt_pickup_id = fields.Many2one(
        "res.partner",
        string="Pickups",
    )
    pnt_type = fields.Selection(
        [
            ("diary", _("Diary")),
            ("weekly", _("Weekly")),
            ("monthly", _("Monthly")),
            ("yearly", _("Yearly")),
        ]
    )
    pnt_interval = fields.Integer(
        string="Interval",
        default=1,
    )
    pnt_visibility_previous_days = fields.Boolean(
        string="Visibility previous days",
        compute="_pnt_compute_visibility_previous_days",
    )
    pnt_previous_days = fields.Integer(
        string="Previous days",
        default=0,
    )
    pnt_week_day_month_ids = fields.One2many(
        "pnt.agreement.lot.week.day.month.line",
        "pnt_week_day_month_id",
    )
    pnt_week_day_ids = fields.Many2many(
        "pnt.week.day",
        "pnt_lot_week_day_rel",
        "pnt_lot_id",
        "pnt_week_day_id",
        string="Week days",
    )
    pnt_month_year_ids = fields.Many2many(
        "pnt.month.year",
        "pnt_lot_month_year_rel",
        "pnt_lot_id",
        "pnt_month_year_id",
        string="Month year",
    )
    pnt_partner_pickup_id = fields.Many2one(
        "res.partner",
    )
    pnt_category_id = fields.Many2one(
        "pnt.fleet.vehicle.category",
        string="Category",
    )
    pnt_logistic_route_id = fields.Many2one(
        "pnt.logistic.route",
        string="Logistic route",
        tracking=True,
    )
    pnt_driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        compute="_pnt_compute_driver_id",
        readonly=False,
        store=True,
    )
    pnt_resource_calendar_id = fields.Many2one(
        "resource.calendar",
        string="Resource",
        domain=[
            ("pnt_external", "=", True),
        ],
        compute="_compute_pnt_resource_calendar",
        store=True,
        readonly=False,
    )
    pnt_hour = fields.Float(
        string="Hour",
    )
    pnt_product_delivered_ids = fields.One2many(
        "pnt.lot.product.delivered",
        "pnt_lot_id",
        string="Products",
        ondelete="cascade",
    )
    pnt_agreement_lot_line_ids = fields.One2many(
        "pnt.agreement.lot.line",
        "pnt_agreement_lot_id",
        string="Lot lines",
    )
    company_id = fields.Many2one(
        "res.company",
        related="pnt_agreement_id.company_id",
    )
    pnt_fleet_id = fields.Many2one(
        string="Vehicle",
        comodel_name="fleet.vehicle",
        compute="_compute_fleet_id",
        store=True,
        readonly=False,
    )
    pnt_field_readonly = fields.Boolean(
        string="Field readonly",
        compute="_pnt_compute_field_readonly",
    )
    pnt_holder_id = fields.Many2one(
        related="pnt_agreement_id.pnt_holder_id",
        store=True,
    )

    @api.depends("pnt_agreement_id")
    def _pnt_compute_field_readonly(self):
        group_ids = self.env.user.groups_id.ids
        for record in self:
            record.pnt_field_readonly = (
                GROUPS["agreement_manager_commercial"] not in group_ids
            )

    @api.depends("pnt_driver_id")
    def _compute_fleet_id(self):
        obj_fleet = self.env["fleet.vehicle"]
        for record in self:
            if not record.pnt_driver_id:
                record.pnt_fleet_id = False
                continue
            fleet_id = obj_fleet.search(
                [
                    ("driver_id", "=", record.pnt_driver_id.id),
                ],
                limit=1,
            )
            record.pnt_fleet_id = fleet_id

    @api.depends(
        "pnt_type",
        "pnt_week_day_month_ids",
        "pnt_week_day_ids",
        "pnt_month_year_ids",
    )
    def _pnt_compute_visibility_previous_days(self):
        for record in self:
            record.pnt_visibility_previous_days = False
            if (record.pnt_type in ("diary", "yearly")) or (
                record.pnt_week_day_month_ids
                or record.pnt_week_day_ids
                or record.pnt_month_year_ids
            ):
                record.pnt_visibility_previous_days = True

    @api.depends(
        "pnt_logistic_route_id",
    )
    def _pnt_compute_driver_id(self):
        for record in self:
            record.pnt_driver_id = False
            if record.pnt_logistic_route_id:
                record.pnt_driver_id = record.pnt_logistic_route_id.pnt_driver_id

    def _check_is_leave(
        self,
        dtt,
        resource_calendar,
    ):
        """
        Check if a day is like leave in a resource_calendar
        """
        check = False
        if resource_calendar.global_leave_ids:
            for line in resource_calendar.global_leave_ids:
                if not check:
                    if (
                        fields.Datetime.context_timestamp(self, line.date_from)
                        <= dtt
                        <= fields.Datetime.context_timestamp(self, line.date_to)
                    ):
                        check = True
        if not check:
            tz = dtt.tzinfo
            tz_user = pytz.timezone(self._context.get("tz", "Europe/Madrid"))
            dtt.replace(tzinfo=tz_user)
            check = dtt.weekday() == 6
            dtt.replace(tzinfo=tz)
        return check

    def _pnt_prepare_lot_line_values(
        self,
        dtt,
        previous_days=0,
    ):
        previous_dt = dtt - timedelta(days=previous_days)
        is_leave = self._check_is_leave(dtt, self.pnt_resource_calendar_id) or False
        return {
            "pnt_previous_date": previous_dt,
            "pnt_datetime": fields.Datetime.to_string(dtt),
            "pnt_is_leave": is_leave,
        }

    def pnt_line_date_values(
        self,
        interval_type,
        interval,
        start_date,
        end_date,
        **kwargs,
    ):
        """
        dtt: start datetime
        interval_type: different interval types

        return: list of days for this interval type
        """

        interval = interval or 1

        def _num_week_month(
            ddatime,
        ):
            day = ddatime.day
            first_day_pos = calendar.monthrange(ddatime.year, ddatime.month)[0]
            week = [0] * 7
            for i in range(first_day_pos, 7):
                week[i] = i - first_day_pos + 1
            if day in week:
                return 1
            day_start = week[-1:][0] + 1
            for index, num in enumerate(range(day_start, 45, 7), start=2):
                if day in [x for x in range(num, num + 7)]:
                    return index

        wizard = kwargs["wizard"]
        mapped_days = {"m": 0, "t": 1, "w": 2, "th": 3, "f": 4, "s": 5, "su": 6}
        mapped_month = {
            "j": 1,
            "f": 2,
            "m": 3,
            "a": 4,
            "ma": 5,
            "ju": 6,
            "jul": 7,
            "au": 8,
            "s": 9,
            "o": 10,
            "n": 11,
            "d": 12,
        }
        list_dates = []
        if interval_type == "diary":
            list_dates.append(start_date)
            while start_date <= end_date:
                start_date += timedelta(days=interval)
                list_dates.append(start_date)
        elif interval_type == "weekly":
            valid_days = [
                mapped_days[x] for x in wizard.pnt_week_day_ids.mapped("code")
            ]
            max_day = max(valid_days)
            while start_date <= end_date:
                start_date.weekday() in valid_days and list_dates.append(start_date)
                if start_date.weekday() is max_day:
                    start_date += timedelta(weeks=interval)
                    start_date -= timedelta(days=start_date.weekday())
                    continue
                start_date += timedelta(days=1)
        elif interval_type == "monthly":
            interval_month = max(0, interval - 1)
            for line in wizard.pnt_week_day_month_ids:
                init_date = start_date.replace(day=1)
                days = [mapped_days[x] for x in line.pnt_week_day_ids.mapped("code")]
                days_order = [int(x) for x in line.pnt_day_order_ids.mapped("pnt_name")]
                month = init_date.month
                count_days = {}
                while init_date < end_date:
                    if init_date.month != month:
                        count_days = {}
                        init_date = init_date + relativedelta(months=interval_month)
                        month = init_date.month
                        continue
                    month = init_date.month
                    date_weekday = init_date.weekday()
                    if date_weekday not in days:
                        init_date += timedelta(days=1)
                        continue
                    count_days.setdefault(date_weekday, 0)
                    count_days[date_weekday] += 1
                    if init_date >= start_date:
                        count_days[date_weekday] in days_order and list_dates.append(
                            init_date
                        )
                    init_date += timedelta(days=1)
        else:
            valid_month = [
                mapped_month[x] for x in wizard.pnt_month_year_ids.mapped("code")
            ]
            max_month = max(valid_month)
            start_date = start_date.replace(day=1)
            while start_date <= end_date:
                start_date.month in valid_month and list_dates.append(start_date)
                if start_date.month == max_month:
                    start_date += relativedelta(years=interval)
                    start_date = start_date.replace(month=1)
                    continue
                start_date += relativedelta(months=1)
        # Revisar si la fecha ya esta en la lista de programaciones y si es así debe
        # eliminarla de list_dates y actualizar DUs existentes
        for rec in self.pnt_agreement_lot_line_ids:
            ts = rec.pnt_datetime.timestamp()
            dt = datetime.fromtimestamp(ts, pytz.timezone('Europe/Madrid'))
            date_def = datetime(dt.date().year,dt.date().month,dt.date().day)
            if date_def in list_dates:
                # Actualizar DUs ya creados con los nuevos datos de la programacion
                self.pnt_update_existing_du(rec)
                # Eliminar la fecha de la lista de nuevas programaciones
                list_dates.remove(date_def)
        return list_dates

    def pnt_update_existing_du(self,lot_line):
        for record in self:
            if lot_line.pnt_sd_id:
                if (not lot_line.pnt_sd_id.task_id
                        or lot_line.pnt_sd_id.task_id.stage_id.id
                        in (TASK_STAGES["planned"],TASK_STAGES["pendingassig"])):
                    # Actualitzar dades capçalera
                    lot_line.pnt_sd_id.write({
                        'pnt_vehicle_category_id': record.pnt_category_id.id,
                        'pnt_logistic_route_id': record.pnt_logistic_route_id,
                        'pnt_transport_id': record.pnt_driver_id.id,
                        'pnt_carrier_id': record.pnt_driver_id.parent_id.id,
                        'pnt_vehicle_id': record.pnt_fleet_id,
                    })
                    if lot_line.pnt_sd_id.task_id:
                        lot_line.pnt_sd_id.task_id.write({
                            'pnt_logistic_route_id': record.pnt_logistic_route_id,
                        })
                    # Actualitzar les linees de productes
                    # Eliminar les linees del DU
                    lot_line.pnt_sd_id.pnt_single_document_line_ids.unlink()
                    # Crear les noves linees
                    for lin in record.pnt_product_delivered_ids:
                        pntsingledocumentline = self.env['pnt.single.document.line']
                        # Create DU line
                        values = {
                            'pnt_single_document_id': lot_line.pnt_sd_id.id,
                            'pnt_product_id': lin.pnt_product_id.pnt_product_id.id,
                            'name': lin.pnt_product_id.display_name,
                            'pnt_partner_delivery_id': lin.pnt_partner_delivery_id.id,
                        }
                        new_du_line = pntsingledocumentline.sudo().create(values)
                        new_du_line.onchange_pnt_product_id()
                        new_du_line.compute_pnt_product_id()
                        new_du_line.pnt_product_uom_qty = lin.pnt_estimated_amount_qty
                        new_du_line.pnt_product_economic_uom_qty = (
                            lin.pnt_estimated_amount_qty)
                        if lin.pnt_container_id:
                            new_du_line.pnt_container_id = lin.pnt_container_id.id
                        if lin.pnt_waste_id:
                            new_du_line.pnt_waste_id = lin.pnt_waste_id.id
                        new_du_line.compute_pnt_price_unit()
                    # Generar los DI de las nuevas lineas
                    if (lot_line.pnt_sd_id.pnt_single_document_type
                            in ["pickup", "marpol"]):
                        lot_line.pnt_sd_id.auto_create_di()

    def _pnt_lines_date(
        self, interval_type, interval, start_date, end_date, time, **kwargs
    ):
        dtt = fields.Datetime.to_datetime(start_date)
        dtt = dtt + timedelta(seconds=time * 3600)
        edt = fields.Datetime.to_datetime(end_date)
        list_dates = self.pnt_line_date_values(
            interval_type, interval, dtt, edt, **kwargs
        )
        pytzz = pytz.timezone(self._context.get("tz", "Europe/Madrid"))
        return list(
            map(
                lambda x: pytzz.localize(x).astimezone(pytz.UTC),
                list_dates,
            )
        )

    def _check_valid_fields(self):
        if self.pnt_type == "weekly" and not self.pnt_week_day_ids:
            raise UserError(_("You must select at least one day."))
        if self.pnt_type == "monthly" and not self.pnt_week_day_month_ids:
            raise UserError(_("You must select at least one day."))
        if self.pnt_type == "yearly" and not self.pnt_month_year_ids:
            raise UserError(_("You must select at least one month."))

    def pnt_programing_draft(self):
        [x._check_valid_fields() for x in self]
        for record in self:
            end_date = record.pnt_agreement_id.pnt_end_date
            ddate_start = fields.Date.today()
            if not end_date:
                # if not end_date give today year
                end_year = fields.Date.today().year + 1
                end_date = datetime(
                    end_year,
                    12,
                    31,
                    23,
                    59,
                    59,
                    999999,
                )
            if record.pnt_agreement_id.pnt_start_date > ddate_start:
                ddate_start = record.pnt_agreement_id.pnt_start_date
            dates = self._pnt_lines_date(
                record.pnt_type,
                record.pnt_interval,
                ddate_start,
                end_date,
                record.pnt_hour,
                wizard=record,
            )
            lines = []
            if dates:
                lines += [
                    (
                        0,
                        0,
                        self._pnt_prepare_lot_line_values(x, record.pnt_previous_days),
                    )
                    for x in dates
                ]
            record.button_remove_lines()
            record.pnt_agreement_lot_line_ids = lines

    @api.depends("pnt_pickup_id")
    def _compute_pnt_resource_calendar(self):
        for record in self:
            if not record.pnt_resource_calendar_id and record.pnt_pickup_id:
                record.pnt_resource_calendar_id = (
                    record.pnt_pickup_id.pnt_resource_pick_id.id
                )

    @api.depends(
        "pnt_agreement_lot_line_ids.pnt_sd_id",
    )
    def _pnt_compute_state(self):
        for record in self:
            len_line = len(record.pnt_agreement_lot_line_ids)
            len_not_sd = len(
                record.pnt_agreement_lot_line_ids.filtered(
                    lambda x: not x.pnt_sd_id
                ).ids
            )
            if len_line == len_not_sd:
                record.state = "draft"
            elif len_not_sd == 0:
                record.state = "done"
            else:
                record.state = "active"

    def button_remove_lines(self):
        self.pnt_agreement_lot_line_ids.filtered(lambda x: not x.pnt_sd_id).unlink()

    @api.model
    def create(self, vals):
        if "company_id" in vals:
            self = self.with_company(vals["company_id"])
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            vals["name"] = self.env["ir.sequence"].next_by_code(
                "pnt.agreement.lot",
            ) or _("New")
        result = super(PntAgreementLot, self).create(vals)
        return result


class PntWeekDay(models.Model):
    _name = "pnt.week.day"
    _description = "Pnt week day"
    _order = "sequence"
    _rec_name = "code"

    code = fields.Char(
        string="Code",
    )
    name = fields.Char(
        string="Name",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )


class PntWeekMonth(models.Model):
    _name = "pnt.week.month"
    _description = "Pnt week month"
    _order = "sequence"

    code = fields.Char(
        string="Code",
    )
    name = fields.Char(
        string="Name",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )


class PntMonthYear(models.Model):
    _name = "pnt.month.year"
    _description = "Pnt month year"
    _order = "sequence"

    code = fields.Char(
        string="Code",
    )
    name = fields.Char(
        string="Name",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
    )


class PntWeekDayMonth(models.Model):
    _name = "pnt.agreement.lot.week.day.month.line"
    _description = "Pnt week day month line"

    name = fields.Char(
        string="Name",
    )
    pnt_week_day_month_id = fields.Many2one(
        "pnt.agreement.lot",
        string="Agreement lot",
    )
    pnt_week_month_ids = fields.Many2many(
        "pnt.week.month",
        "pnt_lot_month_line_w_d_m_week_month_rel",
        "pnt_lot_month_line_w_d_m_id",
        "pnt_month_line_w_d_m_id",
        string="Week month",
    )
    pnt_week_day_ids = fields.Many2many(
        "pnt.week.day",
        "pnt_lot_day_line_w_d_m_line_week_day_rel",
        "pnt_lot_day_line_w_d_m_id",
        "pnt_day_line_w_d_m_id",
        string="Week days",
    )
    pnt_day_order_ids = fields.Many2many(
        string="Day order",
        comodel_name="pnt.day.order",
        required=True,
    )


class PntDayOrder(models.Model):
    _name = "pnt.day.order"
    _description = "Day order"
    _rec_name = "pnt_name"

    pnt_name = fields.Selection(
        string="Day order",
        selection=[
            ("0", "0"),
            ("1", "1"),
            ("2", "2"),
            ("3", "3"),
            ("4", "4"),
            ("5", "5"),
            ("6", "6"),
            ("7", "7"),
        ],
    )


class PntLotProductDelivered(models.Model):
    _name = "pnt.lot.product.delivered"
    _description = "Pnt Lot Product Delivered"

    pnt_lot_id = fields.Many2one(
        "pnt.agreement.lot",
        string="Lot id",
    )
    pnt_agreement_id = fields.Many2one(
        "pnt.agreement.agreement",
        related="pnt_lot_id.pnt_agreement_id",
        string="Agreement",
    )
    pnt_product_id = fields.Many2one(
        comodel_name="pnt.agreement.line", string="Product", domain="_compute_domains"
    )
    pnt_estimated_amount_qty = fields.Float(
        string="Estimated amount",
        default=0,
    )
    pnt_estimated_economic_uom = fields.Many2one(
        comodel_name="uom.uom",
        related="pnt_product_id.pnt_product_economic_uom",
        # string="Unit of Measure",
        # default=lambda self: self.env["uom.uom"].search([("name", "=", "kg")], limit=1),
    )
    pnt_partner_delivery_id = fields.Many2one(
        string="Partner delivery",
        comodel_name="res.partner",
        readonly=False,
        default=lambda self: self._default_partner_delivery_id(),
        domain=[
            ("type", "=", "delivery"),
        ],
    )
    company_id = fields.Many2one(
        "res.company",
        related="pnt_agreement_id.company_id",
    )
    pnt_container_id = fields.Many2one(
        comodel_name="product.product",
        string="Container",
        compute="_compute_default_values_line",
        store=True,
        readonly=False,
    )
    pnt_waste_id = fields.Many2one(
        comodel_name="product.product",
        string="Waste",
        compute="_compute_default_values_line",
        store=True,
        readonly=False,
    )
    pnt_container_ids = fields.Many2many(
        string="Container domain",
        comodel_name="product.product",
        compute="_compute_domains",
    )
    pnt_waste_ids = fields.Many2many(
        string="Waste domain",
        comodel_name="product.product",
        compute="_compute_domains",
    )
    pnt_domain_product_ids = fields.Many2many(
        string="Product domain",
        comodel_name="pnt.agreement.line",
        compute="_compute_domains",
    )

    def _default_partner_delivery_id(self):
        partner = self.env["res.partner"].browse([DEFAULT_DELIVERY_PARTNER_ID])
        return partner.exists() or False

    @api.depends("pnt_product_id")
    def _compute_default_values_line(self):
        for record in self:
            record.pnt_container_id = record.pnt_product_id.pnt_container_id
            record.pnt_waste_id = record.pnt_product_id.pnt_product_waste_id

    @api.depends("pnt_agreement_id")
    def _compute_domains(self):
        for record in self:
            pickup = record.pnt_lot_id.pnt_pickup_id
            agreements = record.pnt_agreement_id.pnt_agreement_line_ids
            record.pnt_container_ids = [
                (
                    6,
                    False,
                    agreements.pnt_container_id.ids,
                )
            ]
            agreement_lines = self.env["pnt.agreement.line"].search(
                [
                    ("id", "in", record.pnt_agreement_id.pnt_agreement_line_ids.ids),
                    "|",
                    ("pnt_partner_pickup_id", "=", pickup.id),
                    ("pnt_partner_pickup_id", "=", False),
                ]
            )
            waste_ids = (
                agreement_lines.pnt_product_id.filtered("pnt_is_waste").ids
                + agreements.pnt_product_waste_id.ids
            )
            record.pnt_waste_ids = [
                (
                    6,
                    False,
                    waste_ids,
                )
            ]
            if not pickup:
                agreements = [(6, False, agreements.ids)]
            else:
                new_agreements = dict()
                for line in agreements.filtered(
                    lambda x, pick=pickup: x.pnt_partner_pickup_id == pick
                ):
                    key = (line.pnt_product_id.id, line.pnt_container_id.id)
                    if key not in new_agreements:
                        new_agreements.setdefault(key, line)
                for line in agreements.filtered(lambda x: not x.pnt_partner_pickup_id):
                    key = (line.pnt_product_id.id, line.pnt_container_id.id)
                    if key not in new_agreements:
                        new_agreements.setdefault(key, line)
                agreements = [(6, False, [x.id for x in new_agreements.values()])]
            record.pnt_domain_product_ids = agreements


class PntAgreementLotLine(models.Model):
    _name = "pnt.agreement.lot.line"
    _description = "Pnt agreement lot line"

    pnt_agreement_lot_id = fields.Many2one(
        "pnt.agreement.lot",
        string="Lot",
        ondelete="cascade",
    )
    name = fields.Char(
        string="Name",
    )
    pnt_previous_date = fields.Date(
        string="Previous date",
    )
    pnt_datetime = fields.Datetime(
        string="Datetime",
    )
    pnt_sd_id = fields.Many2one(
        "pnt.single.document",
        string="Single document",
    )
    pnt_is_leave = fields.Boolean(
        string="Is leave",
    )
    pnt_partner_pickup_id = fields.Many2one(
        "res.partner",
        related="pnt_agreement_lot_id.pnt_pickup_id",
        store=True,
    )
    pnt_agreement_id = fields.Many2one(
        "pnt.agreement.agreement",
        related="pnt_agreement_lot_id.pnt_agreement_id",
        store=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="pnt_agreement_id.company_id",
    )
    pnt_cron_error = fields.Boolean(
        string="Error CRON",
    )
    pnt_error = fields.Text(
        string="Error"
    )

    def pnt_sd_create(self):
        partner = self.env.company.partner_id
        for record in self:
            sd_form = Form(self.env["pnt.single.document"])
            sd_form.pnt_single_document_type = "pickup"
            sd_form.pnt_holder_id = (
                record.pnt_agreement_lot_id.pnt_agreement_id.pnt_holder_id
            )
            sd_form.pnt_agreement_id = record.pnt_agreement_lot_id.pnt_agreement_id
            sd_form.pnt_partner_pickup_id = record.pnt_agreement_lot_id.pnt_pickup_id
            # sd_form.pnt_partner_delivery_id = (
            #     record.pnt_agreement_lot_id.pnt_agreement_id.company_id.partner_id
            # )
            sd_form.pnt_pickup_date_type = "date"
            sd_form.pnt_pickup_date = record.pnt_datetime
            sd_form.pnt_vehicle_category_id = (
                record.pnt_agreement_lot_id.pnt_category_id
            )
            sd_form.pnt_operator_id = partner
            sd_form.pnt_logistic_route_id = (
                record.pnt_agreement_lot_id.pnt_logistic_route_id
            )
            try:
                sd_form.pnt_user_id = (
                    record.pnt_agreement_lot_id.pnt_agreement_id.pnt_holder_id.user_id
                )
            except AssertionError:
                pass
            for products in record.pnt_agreement_lot_id.pnt_product_delivered_ids:
                with sd_form.pnt_single_document_line_ids.new() as line_form:
                    line_form.pnt_product_id = products.pnt_product_id.pnt_product_id
                    try:
                        line_form.pnt_container_id = products.pnt_container_id
                    except AssertionError:
                        pass
                    try:
                        line_form.pnt_product_waste_id = products.pnt_waste_id
                    except AssertionError:
                        pass
                    line_form.pnt_product_uom_qty = products.pnt_estimated_amount_qty
                    line_form.pnt_monetary_waste = (
                        products.pnt_product_id.pnt_monetary_waste
                    )
                    line_form.pnt_partner_delivery_id = products.pnt_partner_delivery_id
            sd_id = sd_form.save()
            # check if lot has category vehicle and driver
            # if it's ok create service in SD and assign driver
            if (
                self.pnt_agreement_lot_id.pnt_category_id
                and self.pnt_agreement_lot_id.pnt_driver_id
            ):
                sd_id.action_done()
                if sd_id.task_id:
                    tk_form = Form(sd_id.task_id)
                    tk_form.pnt_transport_id = self.pnt_agreement_lot_id.pnt_driver_id
                    tk_form.pnt_vehicle_id = self.pnt_agreement_lot_id.pnt_fleet_id
                    tdate = fields.Datetime.context_timestamp(self, record.pnt_datetime)
                    tk_form.date_deadline = tdate
                    tk_form.save()
            record.write(
                {
                    "pnt_sd_id": sd_id.id,
                }
            )

    def _pnt_cron_new_sd(self, ddate=False, limit=None):
        """
        params:
        ddate: date to filtered and create sd
        """
        if not ddate:
            ddate = fields.Date.today()
        else:
            ddate = datetime.strptime(ddate, "%Y-%m-%d").date()
        ddatetime = fields.Date.today()
        sd_ids = (
            self.env["pnt.agreement.lot.line"]
            .search([])
            .filtered(
                lambda x:
                not x.pnt_sd_id
                and x.pnt_agreement_lot_id.pnt_agreement_id.state == "done"
                and x.pnt_previous_date <= ddate
                and x.company_id.id == 1
                and not x.pnt_cron_error
                and fields.Datetime.context_timestamp(self, x.pnt_datetime).date()
                >= ddatetime
            )
        )
        record_init = len(sd_ids)
        sd_ids = sd_ids[:limit]
        log_ok = 0
        log_ko = 0
        aux = 0
        records = len(sd_ids)
        logging.warning("\nPROGRAMMING START (%s):" % record_init)
        for record in sd_ids:
            aux += 1
            logging.warning("\nLot - %s of %s" % (aux, records))
            try:
                record.pnt_sd_create()
                record.pnt_cron_error = False
                log_ok += 1
            except Exception as e:
                logging.warning(
                    _("\nWARNING LOG: \n\tLot: %s\n\tContrat: %s\n\tHolder: %s\n\t\t%s" % (
                        record.pnt_agreement_lot_id.name,
                        record.pnt_agreement_id.name,
                        record.pnt_agreement_id.pnt_holder_id.name,
                        e
                    )))
                record.pnt_cron_error = True
                record.pnt_error = str(e)
                log_ko += 1
        logging.warning(
            "\nDU OK: %s of %s\nDU KO: %s of %s\nPROGRAMMING END" % (
                log_ok, records, log_ko, records)
        )

    def unlink(self):
        if any(x.pnt_sd_id for x in self):
            raise UserError(
                _("You cannot delete programmed lines that are linked to DU.")
            )
        return super().unlink()
