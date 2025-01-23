# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Company(models.Model):
    _inherit = "res.company"

    pnt_delay_days_due_date_circulation_permit = fields.Integer(
        string="Delay days for expiration circulation permit"
    )
    pnt_delay_days_due_date_cpa = fields.Integer(
        string="Delay days for expiration CPA",
    )
    pnt_delay_days_due_date_tachograph = fields.Integer(
        string="Delay days for expiration tachograph"
    )
    pnt_delay_days_due_date_adr = fields.Integer(string="Delay days for expiration ADR")
    pnt_delay_days_due_agreement_to_renew = fields.Integer(
        string="Delay days for change agreement state",
    )
    pnt_single_document_project_id = fields.Many2one(
        string="Logistics Project",
        comodel_name="project.project",
    )
    pnt_single_document_default_portal_id = fields.Many2one(
        string="Default Portal agreement",
        comodel_name="pnt.agreement.agreement",
        domain="[('pnt_agreement_type', '=', 'portal'),('state', 'in', ('active','done'))]",
    )
    pnt_agreement_bulk_product_id = fields.Many2one(
        string="Bulk item for single contract",
        comodel_name="product.product",
    )

    pnt_single_document_portal_partner_pickup_id = fields.Many2one(
        string="Portal Partner pickup",
        comodel_name="res.partner",
    )
    pnt_single_document_portal_partner_delivery_id = fields.Many2one(
        string="Portal Partner delivery",
        comodel_name="res.partner",
    )
    pnt_waste_order_purchase_id = fields.Many2one(
        string="Waste order (purchase)",
        comodel_name="purchase.order.type",
        domain=[
            ("pnt_is_DU", "=", True),
        ],
    )
    pnt_waste_order_sale_id = fields.Many2one(
        string="Waste order (sale)",
        comodel_name="sale.order.type",
        domain=[
            ("pnt_is_DU", "=", True),
        ],
    )
    pnt_scale_host = fields.Char(
        string="Scale Host",
    )
    pnt_scale_port = fields.Char(
        string="Scale Port",
    )
    pnt_metal_scale_agreement_id = fields.Many2one(
        string="Metal scale agreement",
        comodel_name="pnt.agreement.agreement",
        domain="[('pnt_agreement_type', '=', 'portal')]",
    )
    pnt_single_document_metal_partner_pickup_id = fields.Many2one(
        string="Metal scale Partner pickup",
        comodel_name="res.partner",
        domain="[('type', '=', 'delivery')]",
    )
    pnt_scales_metal_id = fields.Many2one(
        string="Scales for Metal scales",
        comodel_name="pnt.scales",
    )

    pnt_logo_ids = fields.One2many(
        comodel_name="pnt.res.company.logo",
        inverse_name="pnt_company",
        string="Logo",
    )
    pnt_obligations_of_the_parties = fields.Text(
        string="Obligations of the parties",
    )
    pnt_single_document_issue_project_id = fields.Many2one(
        string="Single Document Issue Project",
        comodel_name="project.project",
    )

    pnt_stock_picking_type_purchase_du_id = fields.Many2one(
        string="Stock picking type purchase DU",
        comodel_name="stock.picking.type",
    )
    pnt_stock_picking_type_sale_du_id = fields.Many2one(
        string="Stock picking type sale DU",
        comodel_name="stock.picking.type",
    )
    pnt_stock_location_vendors_du_id = fields.Many2one(
        string="Stock picking type sale DU",
        comodel_name="stock.location",
    )
    pnt_rental_generation_day = fields.Selection(
        string="Rental Generation Day",
        selection=[(str(i), str(i)) for i in range(1, 32)],
        required=True,
        default="1",
    )
    pnt_agree_reg_producer_default_manager_id = fields.Many2one(
        comodel_name="res.partner",
        string="Default manager form Producer CT agreements",
        domain="[('type', '=', 'delivery')]",
    )

    du_app_mail_confirmation_template_id = fields.Many2one(
        comodel_name="mail.template",
        string="Email Template confirmation app DU",
        domain="[('model', '=', 'pnt.single.document')]",
        help="Email sent to the customer once the app processes the DU.",
    )
    du_app_email_validation = fields.Boolean(
        string="Email Confirmation app DU",
        default=False,
    )
    du_app_tag_generic_number = fields.Integer(
        string="Generic Tag QR number",
        default=1,
    )
    du_di_partner_default_nima_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner DI dafault NIMA",
        domain="[('type', '=', 'delivery')]",
    )
    pnt_scales_app_id = fields.Many2one(
        string="Scales for app services",
        comodel_name="pnt.scales",
    )
    pnt_logo_general_conditions = fields.Binary(
        string="Logo General Conditions",
        help="Logo to include in the General Conditions",
    )
    pnt_symbol_general_conditions = fields.Binary(
        string="Symbol General Conditions",
        help="Symbol to include in the General Conditions",
    )
    pnt_sign_general_conditions = fields.Binary(
        string="Sign General Conditions",
        help="Sign to include in the General Conditions",
    )
    pnt_seal_general_conditions = fields.Binary(
        string="Seal General Conditions",
        help="Seal to include in the General Conditions",
    )
    pnt_scale_general_conditions = fields.Binary(
        string="Scale General Conditions",
        help="Scale to include in the General Conditions",
    )
    pnt_inscription_general_conditions = fields.Binary(
        string="Inscription General Conditions",
        help="Inscription to include in the General Conditions",
    )
    pnt_sign_name_general_conditions = fields.Text(
        string="Manager Sign", help="Person signs the general conditions"
    )
    pnt_sign_position_general_conditions = fields.Text(
        string="Position Sign", help="Position signs the general conditions"
    )
    pnt_sign_customer_general_conditions = fields.Text(
        string="Customer Sign", help="Customer signs the general conditions"
    )
    pnt_email_logistics_general_conditions = fields.Char(
        string="Logistics email", help="Logistics email the general conditions"
    )
    pnt_phone_logistics_general_conditions = fields.Char(
        string="Logistics phone", help="Logistics phone the general conditions"
    )
    pnt_scales_app_id_amianto = fields.Many2one(
        string="Scales for app services",
        comodel_name="pnt.scales",
    )
    pnt_logo_general_conditions_amianto = fields.Binary(
        string="Logo Amianto ",
    )
    pnt_symbol_general_conditions_amianto = fields.Binary(
        string="Symbol Amianto Conditions",
    )
    pnt_sign_general_conditions_amianto = fields.Binary(
        string="Sign Amianto Conditions",
    )
    pnt_seal_general_conditions_amianto = fields.Binary(
        string="Seal Amianto Conditions",
    )
    pnt_scale_general_conditions_amianto = fields.Binary(
        string="Scale Amianto Conditions",
    )
    pnt_inscription_general_conditions_amianto = fields.Binary(
        string="Inscription Amianto Conditions",
    )
    pnt_page_general_conditions_amianto = fields.Text(
        string="Report Amianto",
    )
    pnt_sign_name_general_conditions_amianto = fields.Text(
        string="Manager Sign Amianto",
    )
    pnt_sign_position_general_conditions_amianto = fields.Text(
        string="Position Sign Amianto",
    )
    pnt_sign_customer_general_conditions_amianto = fields.Text(
        string="Customer Sign Amianto",
    )
    pnt_text_customer_general_conditions_amianto = fields.Text(
        string="Customer Text Amianto",
    )
    pnt_invoice_send_email = fields.Char(
        "Invoice send mail",
    )
    pnt_notdangerous_image = fields.Binary(
        string="Non-hazardous labels pictogram",
    )
    pnt_app_product_use_g3_ids = fields.Many2many(
        comodel_name="product.product",
        string="Sanitary Product not GIII used as GIII in app",
        domain=[("pnt_is_sanitary", "=", True)],
    )
    @api.model
    def _get_default_address_format(self):
        return f"{self._get_default_street()}, {self.zip if self.zip else ''}, {self.city if self.city else ''}"

    @api.model
    def _get_default_street(self):
        return f"{self.street if self.street else ''} {self.street2 if self.street2 else ''}"

    def write(self, values):
        res = super(Company, self).write(values)
        if "pnt_scales_metal_id" in values:
            self.env["pnt.scales"].sudo().pnt_set_company_default(
                self, values["pnt_scales_metal_id"]
            )
        return res

