import datetime
from datetime import timedelta, date, time, datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

PRODUCT_PRODUCT = "product.product"
class PntAppDu(models.Model):
    _name = "pnt.app.du"
    _description = "Pnt App Du"

    name = fields.Integer(
        string="Name",
    )
    transfer_id = fields.Char(
        string="Transfer Id",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    refserie = fields.Char(
        string="RefSerie",
    )
    refnum = fields.Char(
        string="RefNum",
    )
    grpid = fields.Char(
        string="GRP_ID",
    )
    justificanteg2 = fields.Char(
        string="Justificante G2",
    )
    justificanteg3 = fields.Char(
        string="Justificante G3",
    )
    justificantegx = fields.Char(
        string="Justificante GX",
    )
    firmanombre = fields.Char(
        string="Firma: Nombre",
    )
    firmadni = fields.Char(
        string="Firma: DNI",
    )
    firmaimagen = fields.Binary(
        string="Firma: Imagen",
        track_visibility="onchange",
        store=True,
        attachment=False,
    )
    firmaimagentext = fields.Char(
        string="Firma: Imagen",
        track_visibility="onchange",
        store=True,
    )
    observaciones = fields.Char(
        string="Observaciones",
    )
    varefserie = fields.Char(
        string="VA RefSerie",
    )
    varefnum = fields.Char(
        string="VA RefNum",
    )
    fecha_creacion = fields.Datetime(
        string="Fecha creacion",
        default=lambda self: fields.Datetime.now(),
    )
    aplicacion = fields.Integer(
        string="Aplicación",
        default=0,
    )
    app_application_id = fields.Many2one(
        comodel_name="pnt.app.application",
        compute="_compute_app_application",
        store=True,
    )
    justificantegp = fields.Char(
        string="Justificante GP",
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        name="DU",
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
    )
    pnt_processed = fields.Boolean(
        string="Procesado",
        default=False,
    )
    pnt_processed_date = fields.Datetime(
        string="Procesado. Fecha",
        default=lambda self: fields.Datetime.now(),
    )
    pnt_incidence = fields.Boolean(
        string="Incidencia",
        default=False,
    )
    pnt_incidence_date = fields.Datetime(
        string="Incidencia. Fecha",
        default=lambda self: fields.Datetime.now(),
    )
    pnt_incidence_text = fields.Char(
        string="Incidencia. Descripcion",
    )
    app_du_lines_count = fields.Integer(
        string="# App DU lines",
        compute="_compute_app_du_lines_count",
        copy=False,
    )
    app_du_fotos_count = fields.Integer(
        string="# App DU Fotos",
        compute="_compute_app_du_fotos_count",
        copy=False,
    )
    @api.depends("aplicacion")
    def _compute_app_application(self):
        for app_du in self:
            app_du.app_application_id = self.env["pnt.app.application"].search([
                        ('id_application','=',app_du.aplicacion)],limit=1)
    def _compute_app_du_lines_count(self):
        for rec in self:
            app_du_lines = self.env['pnt.app.du.lineas'].search([
                ('transfer_id','=',rec.transfer_id)
            ])
            rec.app_du_lines_count = len(app_du_lines)
    def _compute_app_du_fotos_count(self):
        for rec in self:
            app_du_fotos = self.env['pnt.app.du.fotos'].search([
                ('transfer_id','=',rec.transfer_id)
            ])
            rec.app_du_fotos_count = len(app_du_fotos)
    def action_view_app_du_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "app_adalmo_pnt.action_app_du_lineas_menu_pnt"
        )
        action["domain"] = [("transfer_id", "=", self.transfer_id)]
        return action
    def action_view_app_du_fotos(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "app_adalmo_pnt.action_app_du_fotos_menu_pnt"
        )
        action["domain"] = [("transfer_id", "=", self.transfer_id)]
        return action

    @api.onchange('pnt_processed')
    def _onchange_pnt_processed(self):
        if not self.pnt_processed:
            self.pnt_processed_date = None

    @api.onchange('pnt_incidence')
    def _onchange_pnt_incidence(self):
        if not self.pnt_incidence:
            self.pnt_incidence_date = None
            self.pnt_incidence_text = None

    @api.depends('pnt_single_document_id')
    def name_get(self):
        res = []
        for record in self:
            if record.pnt_single_document_id:
                name = record.pnt_single_document_id.name + "-C-" + str(record.id)
            res.append((record.id, name))
        return res

    def proces_app_du(self):
        for record in self:
            if record.pnt_processed or record.pnt_incidence:
                raise UserError(
                    _(
                        "No puede lanzarse el proceso si el registro ha sido PROCESADO o tiene INCIDENCIAS. Desmarque estas opciones y vuelva a procesarlo"
                    )
                )
            else:
                record.proces_record_app_du()
    def _proces_app_du(self):
        app_du_ids = self.env["pnt.app.du"].search(
            [
                ("pnt_processed", "=", False),
                ("pnt_incidence", "=", False),
                ("company_id", "=", self.env.company.id),
            ]
        )
        if app_du_ids:
            for record in app_du_ids:
                record.proces_record_app_du()

    def _lines_waste_without_weight(self,app_du):
        result = False
        app_du_line_ids = self.env["pnt.app.du.lineas"].search([
            ("transfer_id","=",app_du.transfer_id),
            ("kg","=","0"),
            ("esresiduo","=",1),
        ])
        if app_du_line_ids:
            result = True
        return result
    def proces_record_app_du(self):
        for app_du in self:
            if not app_du.pnt_processed and not app_du.pnt_incidence:
                # Comprobar si hay lineas de residuos con peso 0
                if not self._lines_waste_without_weight(app_du):
                    du = app_du.pnt_single_document_id
                    if du and du.state == "done" and not du.pnt_app_du_id:
                        self._eliminate_du_waste_lines(du)
                        app_du_line_ids = self.env["pnt.app.du.lineas"].search(
                            [
                                ("pnt_processed", "=", False),
                                ("pnt_incidence", "=", False),
                                ("pnt_single_document_id", "=", du.id),
                                ("company_id", "=", self.env.company.id),
                                ("transfer_id", "=", app_du.transfer_id),
                                ("esresiduo", "=", 0),
                            ]
                        )
                        lines_processed = []
                        if app_du_line_ids:
                            for line in app_du_line_ids:
                                articulo = self.env[PRODUCT_PRODUCT].search([
                                    ("default_code","=",line.articulo),
                                    ("company_id", "=", self.env.company.id)
                                ],limit=1)
                                if articulo:
                                    du_line_id = self.env["pnt.single.document.line"].search(
                                        [
                                            ("pnt_single_document_id", "=",
                                             app_du.pnt_single_document_id.id),
                                            ("pnt_product_id","=",articulo.id)
                                        ],limit=1
                                    )
                                    if du_line_id:
                                        du_line_id.pnt_container_qty = line.cantidad
                                        du_line_id.pnt_product_economic_uom_qty = line.cantidad
                                        # du_line_id.onchange_pnt_product_uom_qty()
                                        lines_processed.append(du_line_id)
                                        line.pnt_processed = True
                                        line.pnt_processed_date = fields.datetime.now()
                                    else:
                                        line.pnt_incidence = True
                                        line.pnt_incidence_date = fields.datetime.now()
                                        line.pnt_incidence_text = "Linea no encontrada en DU"
                                else:
                                    line.pnt_incidence = True
                                    line.pnt_incidence_date = fields.datetime.now()
                                    line.pnt_incidence_text = "Artículo no encontrado en Odoo"
                        self._eliminate_unprocessed_lines_of_packaging_deliveries(du,lines_processed,app_du)
                        self._update_waste_lines(app_du,du)
                        # Asignar bascula para servicios app
                        du.pnt_scales_id = self.env.company.pnt_scales_app_id
                        du.action_inplant()
                        # Asignar la bascula de sanitarios de la configuración
                        if self.env.company.pnt_scales_app_id:
                            du.pnt_scales_id = self.env.company.pnt_scales_app_id
                        du.action_received()
                        du.pnt_app_du_id = app_du
                        du.pnt_group_lines = True
                        if self.env.company.du_app_email_validation:
                            du_template = du.company_id.du_app_mail_confirmation_template_id
                            du_template.send_mail(du.id, force_send = True)
                            du_template_id = du.company_id.du_app_mail_confirmation_template_id.id
                            du.with_context(
                                force_send=False).message_post_with_template(
                                du_template_id,
                                email_layout_xmlid='mail.mail_notification_light')
                        app_du.pnt_processed = True
                        app_du.pnt_processed_date = fields.datetime.now()
                        if du.task_id:
                            du.task_id.stage_id = 7
                            du.task_id.pnt_pickup_date = fields.datetime.now()
                        # Adjuntar DU firmado
                        du.generate_app_signed_report_file()
                    else:
                        app_du.pnt_incidence = True
                        app_du.pnt_incidence_date = fields.datetime.now()
                        app_du.pnt_incidence_text = "El estado actual del DU impide que se pueda procesar"
                else:
                    app_du.pnt_incidence = True
                    app_du.pnt_incidence_date = fields.datetime.now()
                    app_du.pnt_incidence_text = "No se puede procesar debido a que hay lineas de peso a 0"

            # else:
            #     app_du.pnt_incidence = True
            #     app_du.pnt_incidence_date = fields.datetime.now()
            #     app_du.pnt_incidence_text = "El DU ya tiene un registro de traspaso de app asociado. Elimine el registro en el DU"
    def get_dangerous_item(self,qr_code):
        if qr_code:
            return self.env[PRODUCT_PRODUCT].search([
                                    ("pnt_qr_app_code","=",qr_code[2:6]),
                                    ("company_id", "=", self.env.company.id)
                                ],limit=1)
        else:
            return False
    def _eliminate_du_waste_lines(self,current_du):
        du_lines_waste_ids = current_du.pnt_single_document_line_ids.filtered(
            lambda r: r.pnt_is_waste
        )
        if du_lines_waste_ids:
            du_lines_waste_ids.unlink()
    def _eliminate_unprocessed_lines_of_packaging_deliveries(self,current_du,lines_processed,app_du):
        du_lines_container_ids = current_du.pnt_single_document_line_ids.filtered(
            lambda r: r not in lines_processed
        )
        du_lines_for_delete = None
        if app_du.aplicacion in (6, 7, 8, 9):
            du_lines_for_delete = du_lines_container_ids.filtered(
                lambda r: not r.pnt_product_id.pnt_keep_in_du_quiron
            )
        else:
            du_lines_for_delete = du_lines_container_ids
        if du_lines_for_delete:
            du_lines_for_delete.unlink()
    def _assign_waste_item(self,app_du,linew):
        if app_du.aplicacion in (1, 4, 6, 8):
            productespecial = None
            if (app_du.aplicacion == 4 and self.env.company.pnt_app_product_use_g3_ids
                    and linew.tipocontenido == "G3"):
                conten = (
                self.env.company.pnt_app_product_use_g3_ids[0].pnt_product_tmpl_container_ids)
                for art in conten:
                    if linew.articulo == art.default_code:
                        productespecial = self.env.company.pnt_app_product_use_g3_ids[0]
            if productespecial:
                return self.env[PRODUCT_PRODUCT].search([
                    ("id", "=", productespecial.id),
                    ("company_id", "=", self.env.company.id)
                ], limit=1)
            else:
                return self.env[PRODUCT_PRODUCT].search([
                    ("pnt_waste_app_code", "=", linew.tipocontenido),
                    ("company_id", "=", self.env.company.id)
                ], limit=1)
        if app_du.aplicacion in (2, 5, 7, 9):
            return self.get_dangerous_item(linew.qr)
        else:
            return False
    def _update_waste_lines(self,app_du,du):
        app_du_line_waste_ids = self.env["pnt.app.du.lineas"].search(
            [
                ("pnt_processed", "=", False),
                ("pnt_incidence", "=", False),
                ("pnt_single_document_id", "=", du.id),
                ("company_id", "=", self.env.company.id),
                ("transfer_id", "=", app_du.transfer_id),
                ("esresiduo", "=", 1),
            ]
        )
        if app_du_line_waste_ids:
            for linew in app_du_line_waste_ids:
                # Asignar articulo residuo y envase
                articulowaste = self._assign_waste_item(app_du, linew)
                articulocontainer = self.env[PRODUCT_PRODUCT].search([
                    ("default_code", "=", linew.articulo),
                    ("company_id", "=", self.env.company.id)
                ], limit=1)
                if articulowaste and articulocontainer:
                    # Añadir linea a DU
                    new_du_line = self._create_pnt_single_document_line(
                        du, articulowaste,
                        linew.qr,
                    )
                    if new_du_line:
                        new_du_line.onchange_pnt_product_id()
                        new_du_line.compute_pnt_product_id()
                        # eco_qty = 0
                        if (app_du.aplicacion in (6,7,8,9)
                                and articulocontainer.pnt_apply_gross_weight):
                            eco_qty = linew.kg
                        elif (app_du.aplicacion in (1,2)
                                and articulocontainer.pnt_apply_gross_weight_ib):
                            eco_qty = linew.kg
                        elif (app_du.aplicacion in (4,5)
                                and articulocontainer.pnt_apply_gross_weight_se):
                            eco_qty = linew.kg
                        else:
                            eco_qty = float(linew.kg) - articulocontainer.weight
                        if float(eco_qty) <= 0.0:
                            eco_qty = 0.01
                        new_du_line.pnt_product_uom_qty = eco_qty
                        new_du_line.pnt_product_economic_uom_qty = eco_qty
                        new_du_line.pnt_container_id = articulocontainer
                        new_du_line.pnt_container_qty = linew.cantidad
                        new_du_line.compute_pnt_price_unit()
                        # new_du_line.onchange_pnt_product_uom_qty()
                        linew.pnt_processed = True
                        linew.pnt_processed_date = fields.datetime.now()
    def _create_pnt_single_document_line(self, du, articulowaste, qr):
        PntSingleDocumentLine = self.env['pnt.single.document.line']
        # Create DU line
        values = {
            'pnt_single_document_id': du.id,
            'pnt_product_id': articulowaste.id,
            'name': articulowaste.display_name,
            'pnt_tag_app': qr,
        }
        dul = PntSingleDocumentLine.sudo().create(values)
        return dul
    def change_app_du(self):
        view = self.env.ref('app_adalmo_pnt.view_form_pnt_app_du_change')
        wiz = self.env['pnt.app.du.change'].create(
            {
                'pnt_current_single_document_id': self.pnt_single_document_id.id,
                'transfer_id': self.transfer_id,
             }
        )
        return {
            'name': _('Change DU in record app'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'pnt.app.du.change',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': self.env.context,
        }
class PntAppDuFotos(models.Model):
    _name = "pnt.app.du.fotos"
    _description = "Pnt App Du Fotos"

    name = fields.Integer(
        string="Name",
    )
    transfer_id = fields.Char(
        string="Transfer Id",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    refserie = fields.Char(
        string="RefSerie",
    )
    refnum = fields.Char(
        string="RefNum",
    )
    grpid = fields.Char(
        string="GRP_ID",
    )
    fecha_creacion = fields.Datetime(
        string="Fecha creacion",
        default=lambda self: fields.Datetime.now(),
    )
    foto = fields.Char(
        string="Foto",
        track_visibility="onchange",
        store=True,
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        name="DU",
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
    )

    @api.depends('pnt_single_document_id')
    def name_get(self):
        res = []
        for record in self:
            if record.pnt_single_document_id:
                name = record.pnt_single_document_id.name + "-F-" + str(record.id)
            res.append((record.id, name))
        return res

class PntAppDuLineas(models.Model):
    _name = "pnt.app.du.lineas"
    _description = "Pnt App Du Lineas"

    name = fields.Integer(
        string="Name",
    )
    transfer_id = fields.Char(
        string="Transfer Id",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    refserie = fields.Char(
        string="RefSerie",
    )
    refnum = fields.Char(
        string="RefNum",
    )
    grpid = fields.Char(
        string="GRP_ID",
    )
    articulo = fields.Char(
        string="Articulo",
    )
    tipocontenido = fields.Char(
        string="Tipo contenido",
    )
    esresiduo = fields.Integer(
        string="Es residuo",
    )
    qr = fields.Char(
        string="QR",
    )
    kg = fields.Char(
        string="Kg",
    )
    fecha_creacion = fields.Datetime(
        string="Fecha creacion",
        default=lambda self: fields.Datetime.now(),
    )
    cantidad = fields.Float(
        string="Cantidad",
    )
    pnt_processed = fields.Boolean(
        string="Procesado",
        default=False,
    )
    pnt_processed_date = fields.Datetime(
        string="Procesado. Fecha",
        default=lambda self: fields.Datetime.now(),
    )
    pnt_incidence = fields.Boolean(
        string="Incidencia",
        default=False,
    )
    pnt_incidence_date = fields.Datetime(
        string="Incidencia. Fecha",
        default=lambda self: fields.Datetime.now(),
    )
    pnt_incidence_text = fields.Char(
        string="Incidencia. Descripcion",
    )
    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        name="DU",
    )
    pnt_partner_pickup_id = fields.Many2one(
        related="pnt_single_document_id.pnt_partner_pickup_id",
    )
    @api.depends('pnt_single_document_id')
    def name_get(self):
        res = []
        for record in self:
            if record.pnt_single_document_id:
                name = record.pnt_single_document_id.name + "-L-" + str(record.id)
            res.append((record.id, name))
        return res
    @api.onchange('pnt_processed')
    def _onchange_pnt_processed(self):
        if not self.pnt_processed:
            self.pnt_processed_date = None

    @api.onchange('pnt_incidence')
    def _onchange_pnt_incidence(self):
        if not self.pnt_incidence:
            self.pnt_incidence_date = None
            self.pnt_incidence_text = None
