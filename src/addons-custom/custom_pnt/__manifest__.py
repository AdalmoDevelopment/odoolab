{
    "name": "Personalizaciones del cliente",
    "summary": "Personalizaciones de cliente",
    "version": "14.0.1.0.5",
    "category": "Hidden",
    "website": "https://www.puntsistemes.es",
    "author": "Punt Sistemes",
    "maintainers": [
        "Rafa Martínez",
        "Tolo Torres",
        "Pedro Montagud",
    ],
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "account_fleet",
        "account_payment_mode",
        "base_address_city",
        "hr_employee_ppe",
        "hr_fleet",
        "l10n_eu_product_adr",
        "purchase_stock",
        "sale_crm",
        "sale_order_line_menu",
        "sale_order_type",
        "sale_stock",
        "mail_activity_team",
        "extra_info_sale_pnt",
        "l10n_es_facturae",
    ],
    "qweb": ["static/src/xml/chatter.xml"],
    "data": [
        "data/pnt_day_order.xml",
        "data/fleet_data.xml",
        "data/fleet_service_type_data.xml",
        "data/fleet_vehicle_tag_data.xml",
        "data/ir_sequence_data.xml",
        "data/pnt_circulation_permit_class_data.xml",
        "data/pnt_product_tmpl_waste_ler_data.xml",
        "data/pnt_product_tmpl_waste_table_data.xml",
        "data/ir_cron.xml",
        "data/pnt_week_day_data.xml",
        "data/pnt_week_month_data.xml",
        "data/pnt_month_year_data.xml",
        "data/mail_data.xml",
        # "data/resource_calendar_actions.xml",
        "security/res_groups.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        "wizards/pnt_agreement_renewal_wizard_views.xml",
        "wizards/pnt_update_partner_pickup_du_wizard_views.xml",
        "wizards/pnt_payment_wizard_views.xml",
        "wizards/pnt_return_wizard_views.xml",
        "wizards/pnt_load_du_wizard_views.xml",
        "wizards/pnt_assign_services_wizard_views.xml",
        "wizards/pnt_agreement_advance_payment_inv.xml",
        "wizards/pnt_global_time_off_wiz.xml",
        "wizards/pnt_create_di_wizard_views.xml",
        "wizards/pnt_rental_manual.xml",
        "wizards/pnt_change_logistics_data_wizard_views.xml",
        "wizards/pnt_du_observations_wizard.xml",
        "wizards/pnt_operator_incident_views.xml",
        "views/account_move_views.xml",
        "views/fleet_vehicle_views.xml",
        "views/fleet_vehicle_cost_views.xml",
        "views/res_partner_views.xml",
        "views/hr_employee_views.xml",
        "views/res_config_settings_views.xml",
        "views/pnt_circulation_permit_class_views.xml",
        "views/pnt_transport_card_views.xml",
        "views/pnt_fleet_vehicle_category_views.xml",
        "views/product_template_views.xml",
        "views/product_product_views.xml",
        "views/pnt_authorization_code_views.xml",
        "views/pnt_product_marpol_waste_category_views.xml",
        "views/pnt_product_waste_table_views.xml",
        "views/pnt_product_tmpl_waste_ler_views.xml",
        "views/pnt_nima_code_views.xml",
        "views/pnt_authorization_code_views.xml",
        "views/pnt_partner_waste_table_views.xml",
        "views/pnt_agreement_agreement_views.xml",
        "views/pnt_single_document_views.xml",
        "views/pnt_general_conditions_views.xml",
        "views/project_task_views.xml",
        "views/purchase_order_views.xml",
        "views/stock_picking_views.xml",
        "views/resource_calendar_views.xml",
        "views/sale_order_views.xml",
        "views/account_bank_statement_views.xml",
        "views/account_fiscal_position_views.xml",
        "views/pnt_scales_views.xml",
        "views/pnt_scales_record_views.xml",
        "views/pnt_container_movement_views.xml",
        "views/account_payment_mode.xml",
        "views/pnt_project_task_form2.xml",
        "views/pnt_res_company.xml",
        "views/account_tax_views.xml",
        "views/pnt_agreement_lot_views.xml",
        "views/pnt_logistic_route_views.xml",
        "views/pnt_waste_nima_operator_type.xml",
        "views/crm_lead_views.xml",
        "views/pnt_agreement_registration.xml",
        "wizards/pnt_du_confirm_timesheet.xml",
        "views/pnt_global_time_off.xml",
        "views/pnt_waste_transfer_document_views.xml",
        "wizards/pnt_task_reason_wiz.xml",
        "views/pnt_project_task_reason.xml",
        "views/res_users_views.xml",
        "views/pnt_boat_type.xml",
        "views/pnt_product_marpol_waste_annex.xml",
        "views/crm_stage_views.xml",
        "views/stock_move.xml",
        "views/product_uom_views.xml",
        "views/report_facturae.xml",
        "views/account_asset_views.xml",
        "views/account_journal.xml",
        "views/pnt_carrier_zone_views.xml",
        "views/pnt_carrier_rate_views.xml",
    ],
}
