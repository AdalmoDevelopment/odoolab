from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tests import Form
from odoo.tools.misc import clean_context


class PntRentalManual(models.TransientModel):
    _name = "pnt.rental.manual"
    _description = "Wizard Rental"
    _rec_name = "pnt_name"

    pnt_name = fields.Char(
        string="Name",
        default=_("Rental Manual"),
        required=True,
    )
    pnt_rental_line_ids = fields.One2many(
        string="Rental Lines",
        comodel_name="pnt.rental.manual.line",
        inverse_name="pnt_rental_manual_id",
    )
    pnt_rental_sale_ids = fields.Many2many(
        string="Sale Rentals",
        comodel_name="sale.order",
    )
    pnt_domain_waste_ids = fields.Many2many(
        string="Domain Waste",
        comodel_name="product.product",
    )
    pnt_domain_pickup_ids = fields.Many2many(
        string="Domain Pickup",
        comodel_name="res.partner",
    )

    def _validate_repeat_rentals(self, agreement):
        if self._context.get("origin_wizard"):
            return
        sales = agreement.pnt_sale_rental_ids.filtered("pnt_is_rental_manual_active")
        sales_created = {}
        for line in sales.order_line:
            key = (
                line.order_id.partner_shipping_id.id,
                line.product_id.id,
                line.pnt_rental_manual_container_id.id,
                line.pnt_rental_manual_waste_id.id,
            )
            sales_created.setdefault(key, []).append(line.order_id.name)
        for line in self.pnt_rental_line_ids:
            key = (
                line.pnt_pickup_id.id,
                line.pnt_product_id.id,
                line.pnt_container_id.id,
                line.pnt_waste_id.id,
            )
            if key in sales_created:
                action = self.env["ir.actions.actions"]._for_xml_id(
                    "custom_pnt.pnt_rental_manual_action"
                )
                view_id = self.env.ref(
                    "custom_pnt.pnt_rental_manual_warning_view_form"
                ).id
                action["name"] = _("Warning")
                action["views"] = [(view_id, "form")]
                action["view_id"] = view_id
                msg = _(
                    "Rental to %s already exists (%s).\n\nProduct: %s\nContainer: "
                    "%s\nWaste: %s",
                    line.pnt_pickup_id.display_name,
                    ", ".join(sales_created[key]),
                    line.pnt_product_id.display_name,
                    line.pnt_container_id.display_name,
                    line.pnt_waste_id.display_name,
                )
                ctx = dict(self.env.context)
                ctx = clean_context(ctx)
                ctx["default_pnt_name"] = msg
                ctx["origin_wizard"] = self.id
                action["context"] = ctx
                return action

    def button_create_rental(self):
        def _prepare_confirmation_values(self):
            res = super(self.__class__, self)._prepare_confirmation_values()
            res["date_order"] = date_order
            return res

        agreement = self.env["pnt.agreement.agreement"].browse(
            self._context["active_ids"]
        )
        action = self._validate_repeat_rentals(agreement)
        if action:
            return action
        date_order = fields.Datetime.now()
        detail_lines = "<br></br>"
        for line in self.pnt_rental_line_ids:
            sale = Form(recordp=self.env["sale.order"], view="sale.view_order_form")
            sale.partner_id = agreement.pnt_holder_id
            sale.date_order = date_order
            with sale.order_line.new() as line_form:
                sale.partner_shipping_id = line.pnt_pickup_id
                line_form.product_id = line.pnt_product_id
                line_form.product_uom_qty = line.pnt_quantity
                line_form.price_unit = line.pnt_price_unit
                line_desc = (
                    f"{line_form.name}\n{line.pnt_container_id.display_name}"
                    f"\n{line.pnt_waste_id.display_name}"
                )
                line_form.name = line_desc
            sale = sale.save()
            sale.order_line.pnt_rental_manual_container_id = line.pnt_container_id
            sale.order_line.pnt_rental_manual_waste_id = line.pnt_waste_id
            sale._patch_method(
                "_prepare_confirmation_values",
                _prepare_confirmation_values,
            )
            sale.action_confirm()
            sale._revert_method("_prepare_confirmation_values")
            sale.pnt_rental_manual_agreement_line_id = line.pnt_line_agreement_id
            sale.pnt_is_created_rental_manual = True
            sale.pnt_is_rental_manual_active = True
            sale.pnt_rental_manual_date_origin = line.pnt_date_origin
            sale.pnt_rental_manual_description = line_desc
            sale.pnt_agreement_id = agreement.id
            agreement.pnt_sale_rental_ids = [(4, sale.id)]
            detail_lines += (" - " + line.pnt_container_id.display_name + " | "
                                   + str(line.pnt_date_origin) + " | "
                                   + line.pnt_waste_id.display_name + " | "
                                   + line.pnt_pickup_id.display_name
                                   + "<br></br>")
        # Escribir en el Chatter que se ha creado un contrato de alquiler manual
        body = _('Se ha creado un alquiler manual de: <br></br>%s', detail_lines)
        agreement.message_post(body=body)

    def button_stop_rental(self):
        self.pnt_rental_sale_ids.pnt_is_rental_manual_active = False
        self.pnt_rental_sale_ids.pnt_rental_manual_processed = True
        detail_lines = "<br></br>"
        for line in self.pnt_rental_sale_ids:
            detail_lines += (" - " + line.partner_shipping_id.display_name + " | "
                                   + line.name + " | "
                                   + line.pnt_rental_manual_description + " | "
                                   + str(line.date_order) + " | "
                                   + str(line.pnt_rental_manual_date_origin)
                                   + "<br></br>")
        agreement = self.env["pnt.agreement.agreement"].browse(
            self._context["active_ids"]
        )
        # Escribir en el Chatter que se ha parado un contrato de alquiler manual
        body = _('Se ha detenido el alquiler de: <br></br>%s', detail_lines)
        agreement.message_post(body=body)

    def button_continue_rental(self):
        wizard = self.env["pnt.rental.manual"].browse(self._context["origin_wizard"])
        wizard.button_create_rental()


class PntRentalManualLine(models.TransientModel):
    _name = "pnt.rental.manual.line"
    _description = "Wizard Rental Line"
    _rec_name = "pnt_rental_manual_id"

    pnt_rental_manual_id = fields.Many2one(
        string="Rental",
        comodel_name="pnt.rental.manual",
        ondelete="cascade",
        required=True,
    )
    pnt_line_agreement_id = fields.Many2one(
        string="Agreement",
        comodel_name="pnt.agreement.line",
        required=True,
    )
    pnt_product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
        readonly=True,
        required=True,
    )
    pnt_quantity = fields.Float(
        string="Quantity",
        readonly=True,
    )
    pnt_price_unit = fields.Float(
        string="Price Unit",
        readonly=True,
    )
    pnt_container_id = fields.Many2one(
        string="Container",
        comodel_name="product.product",
        readonly=True,
    )
    pnt_date_origin = fields.Date(
        string="Date origin",
    )
    pnt_waste_id = fields.Many2one(
        string="Waste",
        comodel_name="product.product",
    )
    pnt_pickup_id = fields.Many2one(
        string="Pickup",
        comodel_name="res.partner",
    )
    pnt_exist_waste = fields.Boolean(
        string="Exist Waste",
    )
    pnt_exist_pickup = fields.Boolean(
        string="Exist Pickup",
    )

    @api.constrains("pnt_rental_manual_id")
    def _check_all_fields(self):
        for record in self:
            if not record.pnt_container_id:
                raise ValidationError(_("Container is required."))
            if not record.pnt_date_origin:
                raise ValidationError(_("Date origin is required."))
            if not record.pnt_waste_id:
                raise ValidationError(_("Waste is required."))
            if not record.pnt_pickup_id:
                raise ValidationError(_("Pickup is required."))
