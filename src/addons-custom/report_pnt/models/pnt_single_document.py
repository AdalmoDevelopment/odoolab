from odoo import fields, models
import pytz
import time
from datetime import datetime



class PntSingleDocuemnt(models.Model):
    _inherit = "pnt.single.document"

    def get_app_sd(self):
        return (
            self.env["pnt.app.du"].search(
                [("pnt_single_document_id", "=", self.id)], limit=1
            )
            or False
        )

    def lines_grouped_by_product(self):
        self.ensure_one()
        recs = {}
        order_list = []
        for r in self.pnt_single_document_line_ids.sorted(key=lambda x: x.pnt_product_id):
            product_id = (str(r.pnt_product_id.id) + "-"
                          + str(r.pnt_container_id.id)
                          + str(r.pnt_partner_delivery_id.id))
            if product_id in recs:
                recs[product_id]['pes'] += r.pnt_product_uom_qty
                recs[product_id]['qty'] += r.pnt_container_qty
            else:
                product_name = r.pnt_description_line
                # if r.pnt_monetary_waste == "inbound":
                #     product_name = r.pnt_customer_name
                # else:
                #     product_name = r.pnt_supplier_name
                perillositat = ""
                if r.pnt_product_id.pnt_waste_table5_ids:
                    for peli in r.pnt_product_id.pnt_waste_table5_ids:
                        if perillositat == "":
                            perillositat = peli.name
                        else:
                            perillositat += " " + peli.name
                tractament = ""
                if r.pnt_product_id.pnt_waste_table2_ids:
                    for tract in r.pnt_product_id.pnt_waste_table2_ids:
                        if tractament == "":
                            tractament = tract.name
                        else:
                            tractament += " " + tract.name
                envas = ""
                if r.pnt_container_id:
                    envas = r.pnt_container_id.display_name
                numdi = ""
                if r.pnt_waste_transfer_document_id:
                    numdi = r.pnt_waste_transfer_document_id[:1].pnt_legal_code[-7:]
                recs[product_id] = {
                    "product_id": r.pnt_product_id.id,
                    "product_name": product_name,
                    "ler": r.pnt_waste_ler_id.name,
                    "perillositat": perillositat,
                    "tractament": tractament,
                    "pes": r.pnt_product_uom_qty,
                    "qty": r.pnt_container_qty,
                    "envas": envas,
                    "delivery_id": r.pnt_partner_delivery_id.id,
                    "numdi": numdi,
                }
        for prod in recs.keys():
            order_list.append(
                (
                    recs[prod]['product_name'],
                    recs[prod]['ler'],
                    recs[prod]['perillositat'],
                    recs[prod]['tractament'],
                    recs[prod]['pes'],
                    recs[prod]['qty'],
                    recs[prod]['envas'],
                    recs[prod]['delivery_id'],
                    recs[prod]['numdi'],
                ),
            )
        return order_list

    def get_ticket_date(self):
        for record in self:
            result = ""
            if record.pnt_effective_date:
                result = record.pnt_effective_date.strftime("%d/%m/%Y")
            hora = ""
            lines = record.pnt_single_document_line_ids.filtered(
                lambda r: r.pnt_scales_record_id
            )
            for line in lines:
                if line.pnt_scales_record_id.pnt_first_weighing_date:
                    ts = line.pnt_scales_record_id.pnt_first_weighing_date.timestamp()
                    dt = datetime.fromtimestamp(ts,pytz.timezone('Europe/Madrid'))
                    hora = dt.strftime("%H:%M:%S")
                    break
            if hora:
                result += " " + hora
            return result

