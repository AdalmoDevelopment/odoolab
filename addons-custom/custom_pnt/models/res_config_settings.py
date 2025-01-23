# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pnt_delay_days_due_date_circulation_permit = fields.Integer(
        string="Delay days for expiration",
        related="company_id.pnt_delay_days_due_date_circulation_permit",
        readonly=False,
    )
    pnt_delay_days_due_date_cpa = fields.Integer(
        string="Delay days for expiration",
        related="company_id.pnt_delay_days_due_date_cpa",
        readonly=False,
    )
    pnt_delay_days_due_date_tachograph = fields.Integer(
        string="Delay days for expiration",
        related="company_id.pnt_delay_days_due_date_tachograph",
        readonly=False,
    )
    pnt_delay_days_due_date_adr = fields.Integer(
        string="Delay days for expiration",
        related="company_id.pnt_delay_days_due_date_adr",
        readonly=False,
    )
    pnt_delay_days_due_agreement_to_renew = fields.Integer(
        string="Delay days for change agreement state",
        related="company_id.pnt_delay_days_due_agreement_to_renew",
        readonly=False,
    )
    pnt_single_document_project_id = fields.Many2one(
        string="Delay days for change agreement state",
        related="company_id.pnt_single_document_project_id",
        readonly=False,
    )
    pnt_agreement_bulk_product_id = fields.Many2one(
        string="Bulk item for single contract",
        related="company_id.pnt_agreement_bulk_product_id",
        readonly=False,
    )
    pnt_single_document_default_portal_id = fields.Many2one(
        string="Default Portal Agreement for DU",
        related="company_id.pnt_single_document_default_portal_id",
        readonly=False,
    )

    pnt_single_document_portal_partner_pickup_id = fields.Many2one(
        string="Default Portal partner pickup for DU",
        related="company_id.pnt_single_document_portal_partner_pickup_id",
        readonly=False,
    )

    pnt_single_document_portal_partner_delivery_id = fields.Many2one(
        string="Default Portal partner delivery for DU",
        related="company_id.pnt_single_document_portal_partner_delivery_id",
        readonly=False,
    )

    pnt_waste_order_purchase_id = fields.Many2one(
        string="Waste order (purchase)",
        related="company_id.pnt_waste_order_purchase_id",
        readonly=False,
    )
    pnt_waste_order_sale_id = fields.Many2one(
        string="Waste order (sale)",
        related="company_id.pnt_waste_order_sale_id",
        readonly=False,
    )
    pnt_scale_host = fields.Char(
        string="Scale Host", related="company_id.pnt_scale_host", readonly=False
    )
    pnt_scale_port = fields.Char(
        string="Scale Port", related="company_id.pnt_scale_port", readonly=False
    )
    pnt_metal_scale_agreement_id = fields.Many2one(
        string="Metal scale agreement",
        related="company_id.pnt_metal_scale_agreement_id",
        readonly=False,
    )
    pnt_single_document_metal_partner_pickup_id = fields.Many2one(
        string="Metal scale Partner pickup",
        related="company_id.pnt_single_document_metal_partner_pickup_id",
        readonly=False,
    )
    pnt_scales_metal_id = fields.Many2one(
        string="Scales for Metal scales",
        related="company_id.pnt_scales_metal_id",
        readonly=False,
    )
    pnt_obligations_of_the_parties = fields.Text(
        related="company_id.pnt_obligations_of_the_parties",
        string="Obligations of the parties",
        readonly=False,
    )
    pnt_single_document_issue_project_id = fields.Many2one(
        string="Single Document Issue Project",
        related="company_id.pnt_single_document_issue_project_id",
        readonly=False,
    )
    pnt_stock_picking_type_purchase_du_id = fields.Many2one(
        string="Stock picking type purchase DU",
        related="company_id.pnt_stock_picking_type_purchase_du_id",
        readonly=False,
    )
    pnt_stock_picking_type_sale_du_id = fields.Many2one(
        string="Stock picking type sale DU",
        related="company_id.pnt_stock_picking_type_sale_du_id",
        readonly=False,
    )
    pnt_stock_location_vendors_du_id = fields.Many2one(
        string="Stock location vendors DU",
        related="company_id.pnt_stock_location_vendors_du_id",
        readonly=False,
    )
    pnt_rental_generation_day = fields.Selection(
        string="Rental Generation Day",
        related="company_id.pnt_rental_generation_day",
        readonly=False,
    )
    pnt_agree_reg_producer_default_manager_id = fields.Many2one(
        related="company_id.pnt_agree_reg_producer_default_manager_id",
        readonly=False,
    )
    du_app_mail_confirmation_template_id = fields.Many2one(
        comodel_name='mail.template',
        related="company_id.du_app_mail_confirmation_template_id",
        readonly=False,
    )
    du_app_email_validation = fields.Boolean(
        related='company_id.du_app_email_validation',
        readonly=False
    )
    du_app_tag_generic_number = fields.Integer(
        related='company_id.du_app_tag_generic_number',
        readonly=False
    )
    du_di_partner_default_nima_id = fields.Many2one(
        related='company_id.du_di_partner_default_nima_id',
        readonly=False
    )
    pnt_scales_app_id = fields.Many2one(
        related='company_id.pnt_scales_app_id',
        readonly=False
    )
    pnt_notdangerous_image = fields.Binary(
        related='company_id.pnt_notdangerous_image',
        readonly=False,
    )
    pnt_app_product_use_g3_ids = fields.Many2many(
        related='company_id.pnt_app_product_use_g3_ids',
        readonly=False
    )


