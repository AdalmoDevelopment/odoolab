import socket
import telnetlib

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PntScales(models.Model):
    _name = "pnt.scales"
    _description = "Pnt Scales"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]
    _check_company_auto = True

    name = fields.Char(
        string="Scales",
        required=True,
        copy=False,
        readonly=True,
        index=True,
        # default=lambda self: _('New'),
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )
    pnt_scale_host = fields.Char(
        string="Scale Host",
    )
    pnt_scale_port = fields.Char(
        string="Scale Port",
    )
    pnt_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
    )
    pnt_location_id = fields.Many2one(
        comodel_name="stock.location",
        string="Location",
    )
    pnt_scale_uom = fields.Many2one(
        comodel_name="uom.uom",
        string="Unit of Measure",
    )
    pnt_company_default = fields.Boolean(
        string="Company default scale",
        readonly=True,
    )
    pnt_stock_picking_type_purchase_du_id = fields.Many2one(
        string="Stock picking type purchase DU",
        comodel_name="stock.picking.type",
    )
    pnt_stock_picking_type_sale_du_id = fields.Many2one(
        string="Stock picking type sale DU",
        comodel_name="stock.picking.type",
    )
    pnt_time_cron = fields.Selection(
        string="Time cron review (hours)",
        selection=[("24", "24H"), ("48", "48H")],
    )
    pnt_responsible_id = fields.Many2one(
        string="Responsible",
        comodel_name="res.users",
    )
    pnt_manager_responsible_id = fields.Many2one(
        string="Manager Responsible",
        comodel_name="res.users",
    )
    pnt_waste_ids = fields.Many2many(
        string="Wastes",
        comodel_name="product.product",
        relation="pnt_waste_scale_rel",
        domain=[("pnt_is_waste", "=", True)],
    )
    pnt_default_delivery_id = fields.Many2one(
        "res.partner",
        "Default delivery",
        domain=[
            ("type", "=", "delivery"),
        ],
        help="Only for (Portal and ToPlant)",
    )

    def scale_read(self):
        if not self.pnt_scale_host:
            raise UserError(
                _("Debe indicar una dirección IP para la báscula en configuración")
            )
        if not self.pnt_scale_port:
            raise UserError(
                _("Debe indicar un puerto para la báscula en configuración")
            )
        host = self.pnt_scale_host
        port = self.pnt_scale_port
        try:
            telnet_client = telnetlib.Telnet(host, port)
            pes = None
            telnet_client.write(b"$")
            pes = telnet_client.read_some()
            pesnumeric = int("".join(filter(str.isdigit, str(pes).split("x01", 1)[-1])))
            if pes:
                # raise UserError(_('El peso es: ' + str(pesnumeric) + 'kg'))
                # self.pnt_product_uom_qty = pesnumeric
                # self.onchange_pnt_product_uom_qty()
                return pesnumeric
            else:
                return -1
                raise UserError(
                    _("No puede leerse el peso. Revise si está conectada la báscula")
                )
            telnet_client.write(b"exit")
        except socket.error as msg:
            return -1
            raise UserError(
                _(
                    "No puede leerse el peso. Revise si la báscula está conectada - "
                    + str(msg)
                )
            )

    def test_scale(self):
        if not self.pnt_scale_host:
            raise UserError(
                _("Debe indicar una dirección IP para la báscula en configuración")
            )
        if not self.pnt_scale_port:
            raise UserError(
                _("Debe indicar un puerto para la báscula en configuración")
            )
        host = self.pnt_scale_host
        port = self.pnt_scale_port
        try:
            telnet_client = telnetlib.Telnet(host, port)
            telnet_client.write(b"$")
            pes = telnet_client.read_some()
            pesnumeric = int("".join(filter(str.isdigit, str(pes).split("x01", 1)[-1])))
            if pes:
                raise UserError(_("El peso es: " + str(pesnumeric) + "kg"))
            else:
                raise UserError(
                    _("No puede leerse el peso. Revise si está conectada la báscula")
                )
        except socket.error as msg:
            raise UserError(
                _(
                    "No puede leerse el peso. Revise si la báscula está conectada - "
                    + str(msg)
                )
            )

    @api.model
    def pnt_set_company_default(self, company, scale_default):
        old_default = self.search(
            [("company_id.id", "in", company.ids), ("pnt_company_default", "=", True)]
        )
        old_default.write({"pnt_company_default": False})
        new_default = self.search(
            [("company_id.id", "in", company.ids), ("id", "=", scale_default)]
        ).exists()
        new_default.write({"pnt_company_default": True})
        return True
