from odoo import models, fields, api, _
from datetime import date

class PntAppTag(models.Model):
    _name = "pnt.app.tag"
    _description = "Pnt App Tag"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    name = fields.Char(
        string="QR code",
        compute="_compute_qr_code",
        store=True,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_partner_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )
    pnt_holder_id = fields.Many2one(
        comodel_name="res.partner",
        string="Partner",
    )
    pnt_functional_unit_id = fields.Many2one(
        comodel_name="pnt.functional.unit",
        string="Functional unit",
    )
    pnt_single_document_line_id = fields.Many2one(
        comodel_name="pnt.single.document.line",
    )
    pnt_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Product",
        change_default=True,
        check_company=True,  # Unrequired company
    )
    pnt_date = fields.Date(
        string="Tag date",
        default=lambda self: date.today(),
    )
    pnt_print_tag = fields.Boolean(
        string="Print tag",
        default=False,
    )
    pnt_print_tag_date = fields.Boolean(
        string="Print tag date",
        default=True,
    )
    pnt_tag_log_type = fields.Selection(
        [
            ("du", _("DU")),
            ("manual", _("Manual")),
            ("app", _("App")),
            ("imported", _("Imported")),
            ("others", _("Others")),
        ],
        string="Tag Log type",
        copy=False,
        index=True,
        tracking=3,
    )
    pnt_move_type = fields.Selection(
        [
            ("outgoing", _("Outgoing")),
            ("incoming", _("Incoming")),
        ],
        string="Move type",
        copy=False,
        index=True,
        tracking=3,
    )
    def pnt_app_sector_tag(self):
        sector = "00"
        for record in self:
            if record.pnt_holder_id:
                sector = record.pnt_holder_id.pnt_app_sector()
            elif record.pnt_partner_id:
                sector = record.pnt_partner_id.pnt_app_sector()
        return sector

    def name_partner_tag(self):
        for record in self:
            if (record.pnt_holder_id and record.pnt_holder_id.name
                    and record.pnt_partner_id and record.pnt_partner_id.name):
                return record.pnt_holder_id.name + " - " + record.pnt_partner_id.name
            elif record.pnt_partner_id and record.pnt_partner_id.name:
                return record.pnt_partner_id.name
            elif record.pnt_holder_id and record.pnt_holder_id.name:
                return record.pnt_holder_id.name

    @api.depends("pnt_product_id")
    def _compute_qr_code(self):
        for du in self:
            if not du.name:
                if du.pnt_product_id.pnt_is_sanitary:
                    if du.pnt_product_id.pnt_waste_app_code:
                        du.name = (du.pnt_product_id.pnt_waste_app_code
                                   + ("000000000000" +
                                str(du.pnt_product_id.pnt_waste_app_code_number))[-12:])
                        # Actualitzar contador sanitaris
                        du.pnt_product_id.pnt_waste_app_code_number += 1
                    else:
                        # cercar si te un codi asginat a GIII a configuració
                        if (du.pnt_product_id in
                                self.env.company.pnt_app_product_use_g3_ids):
                            g3 = self.env["product.product"].search([
                                ('pnt_waste_app_code','=','G3')
                            ])
                            if g3:
                                du.name = (g3.pnt_waste_app_code
                                           + ("000000000000" + str(
                                            g3.pnt_waste_app_code_number))[-12:])
                                # Actualitzar contador sanitaris
                                g3.pnt_waste_app_code_number += 1
                        else:
                            du.name = ("GN" + ("000000000000" + str(
                                    self.env.company.du_app_tag_generic_number))[-12:])
                            # Actualitzar contador generico
                            self.env.company.du_app_tag_generic_number += 1
                elif du.pnt_product_id.pnt_is_dangerous:
                    # elif du.pnt_product_id.product_tmpl_id.is_dangerous:
                    if du.pnt_product_id.pnt_qr_app_code:
                        du.name = ("GP" + du.pnt_product_id.pnt_qr_app_code
                                   + ("00000000" +
                                    str(du.pnt_product_id.pnt_qr_app_code_number))[-8:])
                        # Actualitzar contador perillosos
                        du.pnt_product_id.pnt_qr_app_code_number += 1
                    else:
                        du.name = ("GN" + ("000000000000" + str(
                                    self.env.company.du_app_tag_generic_number))[-12:])
                        # Actualitzar contador generico
                        self.env.company.du_app_tag_generic_number += 1
                else:
                    du.name = ("GN" + ("000000000000" + str(
                                self.env.company.du_app_tag_generic_number))[-12:])
                    # Actualitzar contador generico
                    self.env.company.du_app_tag_generic_number += 1

    def print_tag(self):
        self.ensure_one()
        xmlid = "app_adalmo_pnt.pnt_app_tag_report"
        action = self.env.ref(xmlid).report_action(self)
        return action

    def save_tag_log(self,print_tag):
        newtaglog = self.env["pnt.app.tag.log"].create(
            {
                "name": self.name,
                "pnt_partner_id": self.pnt_partner_id.id,
                "pnt_functional_unit_id": self.pnt_functional_unit_id.id,
                "pnt_single_document_line_id": self.pnt_single_document_line_id.id,
                "pnt_tag_log_type": self.pnt_tag_log_type,
                "pnt_move_type": self.pnt_move_type,
            }
        )
        return newtaglog

    def get_partner_waste_codes_tags(self, typeinfo, typepartner, end_mgm_id=0):
        # typeinfo -> nima | rpgr | srap
        # typepartner -> agent | producer | transport | end_mgm
        # end_mgm_id -> solo se utiliza cuando typepartner es end_mgm
        result = ""
        partner = self.pnt_partner_id
        if typepartner == "end_mgm":
            partner = self.env["res.partner"].search([("id", "=", end_mgm_id)], limit=1)
        if partner:
            if partner.pnt_waste_nima_code_ids:
                if typeinfo == "nima":
                    agent = (
                        partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids)
                else:
                    agent = partner.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                        lambda x: x.pnt_authorization_code_type == typepartner
                    )
                if agent:
                    if typeinfo == "nima":
                        result = agent[0].pnt_nima_code_id.name
                    elif typeinfo == "rpgr":
                        result = agent[0].display_name
                    elif typeinfo == "srap":
                        result = agent[0].pnt_operator_type_id.pnt_type_operator
            else:
                # Comprobar so el partner selecctonado tiene datso de gestor de residuos
                # en caso contrario, comprobar si tiene un padre y si es así asignarle el padre
                if partner.parent_id:
                    if typeinfo == "nima":
                        agent = (
                            partner.parent_id.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids)
                    else:
                        agent = partner.parent_id.pnt_waste_nima_code_ids.pnt_waste_authorization_code_ids.filtered(
                            lambda x: x.pnt_authorization_code_type == typepartner
                        )
                    if agent:
                        if typeinfo == "nima":
                            result = agent[0].pnt_nima_code_id.name
                        elif typeinfo == "rpgr":
                            result = agent[0].display_name
                        elif typeinfo == "srap":
                            result = agent[0].pnt_operator_type
        return result
