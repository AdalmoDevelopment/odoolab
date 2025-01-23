import json
import requests
import time
from requests import auth, exceptions as http_exceptions
from odoo.exceptions import UserError

from odoo import models, fields, api, _

class PntPaymentMachine(models.Model):
    _name = "pnt.payment.machine"
    _description = "Pnt Payment Machine"
    _inherit = ["portal.mixin", "mail.thread", "mail.activity.mixin", "utm.mixin"]

    name = fields.Char(
        string="Name",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
    )
    pnt_description = fields.Char(
        string="Description",
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )
    pnt_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        domain=[
            ("type", "in", ["cash"]),
        ],
    )
    pnt_machine_type = fields.Many2one(
        string="Machine Type",
        comodel_name="pnt.payment.machine.type",
        required=True,
    )
    pnt_machine_manufacturer = fields.Selection(
        related="pnt_machine_type.pnt_machine_manufacturer",
    )
    pnt_machine_user = fields.Char(
        string="Machine user",
    )
    pnt_machine_user_pwd = fields.Char(
        string="Machine user password",
    )
    pnt_machine_url = fields.Char(
        string="Machine URL",
    )
    pnt_machine_port = fields.Integer(
        string="Machine port",
        default=0,
    )
    pnt_tid = fields.Char(
        string="tid",
        default="100",
    )
    pnt_msgid = fields.Char(
        string="msgid",
        default="100",
    )
    pnt_locid = fields.Char(
        string="locid",
        default="100",
    )
    pnt_warehouse_id = fields.Many2one(
        comodel_name="stock.warehouse",
        string="Warehouse",
    )
    def name_get(self):
        res = []
        for record in self:
            code = record.name
            name = code
            if record.pnt_description:
                name = "[" + record.name + "] " + record.pnt_description
            res.append((record.id, name))
        return res
    def close_payment_machine(self):
        for record in self:
            if record.pnt_machine_type.pnt_machine_manufacturer in ('cashguard'):
                respostaAskStatusCG = self.pnt_ask_status_cg()
                if respostaAskStatusCG["externalStatus"] == 5:
                    raise UserError(
                        _("El dispositivo ya se encuentra cerrado")
                    )
                else:
                    RespostaLogoutCG = self.pnt_logout_cg()
                    if RespostaLogoutCG != 0:
                        raise UserError(
                            _("No se ha podido cerrar el dispositivo CashGuard: " + self.name)
                        )
            else:
                raise UserError(
                    _("Esta utilidad solo está disponible para dispositivos de tipo CashGuard")
                )
    def send_pay_to_machine(self,amount,type):
        for record in self:
            if record.pnt_machine_type.pnt_machine_manufacturer in ('cashguard'):
                # Configurar métodos envio pago
                import_pagament=amount * 100
                if type=='outbound':
                    import_pagament=import_pagament * (-1)
                    # provestolo = str(int(import_pagament)).replace('.0','')
                    # print(provestolo)
                if import_pagament != 0.0:
                    # Realitzar pagament mitjançant CashGuard
                    # Comprobar si el dispositiu esta connectat, si no hi está, s'ha de connectar
                    respostaAskStatusCG = self.pnt_ask_status_cg()
                    if respostaAskStatusCG["externalStatus"]==5:
                        self.pnt_login_cg()
                        time.sleep(15)
                    RespostaIsAvailableCG = self.pnt_is_available_cg()
                    if RespostaIsAvailableCG==True:
                        Resposta = self.pnt_balance_due_cg(str(int(import_pagament)).replace('.0',''),
                                                           self.pnt_tid,self.pnt_msgid,
                                                           self.pnt_locid)
                        # Comprobar Estat del dispositiu fins que el valor de AskStatusCG.externatStatus=3 (-> OK) o 4 (-> paiment Fail)
                        respostaAskStatusCG = self.pnt_ask_status_cg()
                        resultatpagament = respostaAskStatusCG["externalStatus"]
                        while resultatpagament in (1,2):
                            time.sleep(0.2)
                            respostaAskStatusCG = self.pnt_ask_status_cg()
                            resultatpagament = respostaAskStatusCG["externalStatus"]
                        if resultatpagament==3:
                            return True
                        elif resultatpagament==4:
                            raise UserError(
                                _("El dispositivo CashGuard no ha podido realizar el pago. "
                                  + "Revise si tiene Efecivo suficiente")
                            )
                        # print("Importe: " + str(import_pagament).replace('.0',''))
                    else:
                        raise UserError(
                            _("El dispositivo CashGuard no ha podido realizar el pago. "
                              + "Revise si está Disponible")
                        )
                else:
                    raise UserError(
                        _("No puede realizarse el pago porque el importe es 0")
                    )
            else:
                raise UserError(
                    _("Solo puede realizar el pago si el dispositivo es tipo CashGuard")
                )

    # Métodes CashGuard
    def _execute_request(self, method="get", call="", params=None, data=None):
        url = (self.pnt_machine_url + ':' + str(self.pnt_machine_port) + "/"
                 + self.pnt_machine_type.pnt_webapi) + call
        data_user = auth._basic_auth_str(self.pnt_machine_user, self.pnt_machine_user_pwd)
        headers = {
            "Authorization": data_user,
        }
        if method == "get":
            return requests.get(
                url=url,
                headers=headers,
                params=params,
            ).json()
        if method == "post":
            return requests.post(
                url=url,
                headers=headers,
                json=data or {},
            ).json()
        if method == "patch":
            return requests.patch(
                url=url,
                headers=headers,
                json=data or {},
            ).json()
    def pnt_ask_status_cg(self):
        call = '/askStatusCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_login_cg(self):
        call = '/loginCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_logout_cg(self):
        call = '/logoutCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_is_available_cg(self):
        call = '/isAvailableCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_init_cg(self):
        call = '/initCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_get_levels_cg(self):
        call = '/getLevelsCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_get_error_cg(self):
        call = '/getErrorCG/?cID=' + self.name
        method = "post"
        return self._execute_request(call=call, method=method)
    def pnt_balance_due_cg(self,amount,tid,msgid,locid):
        call = ('/balanceDueCG/?amount=' + amount + '&cID=' + self.name + '&tID=' + tid
                + '&msgID=' + msgid + '&locID=' + locid)
        method = "post"
        return self._execute_request(call=call, method=method)

