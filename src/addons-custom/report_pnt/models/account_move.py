from odoo import models
from operator import itemgetter
from datetime import date
from collections import OrderedDict


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_date_pick(self, order_id):
        date_pnt = (
            order_id.pnt_single_document_id.pnt_effective_date
            if order_id.pnt_single_document_id.pnt_effective_date
            else order_id.pnt_single_document_id.pnt_pickup_date
        )
        if date_pnt:
            return date_pnt
    def _return_month_name(self,date_orig):
        if not date_orig:
            result = None
        else:
            if date_orig.month == 1:
                result = "Enero"
            elif date_orig.month == 2:
                result = "Febrero"
            elif date_orig.month == 3:
                result = "Marzo"
            elif date_orig.month == 4:
                result = "Abril"
            elif date_orig.month == 5:
                result = "Mayo"
            elif date_orig.month == 6:
                result = "Junio"
            elif date_orig.month == 7:
                result = "Julio"
            elif date_orig.month == 8:
                result = "Agosto"
            elif date_orig.month == 9:
                result = "Septiembre"
            elif date_orig.month == 10:
                result = "Octubre"
            elif date_orig.month == 11:
                result = "Noviembre"
            elif date_orig.month == 12:
                result = "Diciembre"
        return result
    def _get_date_pick_str(self, order_id):
        date_pnt = (
            order_id.pnt_single_document_id.pnt_effective_date
            if order_id.pnt_single_document_id.pnt_effective_date
            else order_id.pnt_single_document_id.pnt_pickup_date
        )
        if date_pnt:
            return date_pnt.strftime("%Y%m%d")
        else:
            return ""

    def _reduce_lines(self, order_lines):
        obj_aml = self.env["account.move.line"]
        new_dict = {}
        for key, moves in order_lines.items():
            new_line = obj_aml.new(obj_aml._convert_to_write(moves[0]._cache))
            new_line.quantity = 0
            for move in moves:
                single_line = move.sale_line_ids[:1].pnt_single_document_line_id
                new_line.pnt_du_line_weight_qty += single_line.pnt_product_uom_qty
                new_line.pnt_du_line_container_qty += single_line.pnt_container_qty
                new_line.quantity += move.quantity
            new_line._onchange_price_subtotal()
            new_dict[key] = new_line
        tmp_dict = {}
        for key, moves in new_dict.items():
            tmp_dict.setdefault(key[2], [key, []])
            tmp_dict[key[2]][1].append(moves)
        final_dict = {}
        for key, values in tmp_dict.items():
            final_dict[values[0]] = values[1]
        return final_dict
    def lines_grouped_by_order(self):
        """
        :return:
        {
        'sale.order', 'date_order', 'pnt.single.document': [
            account.move.line,
            account.move.line,
            ...
        ],
        ....,
        }
        """
        self.ensure_one()
        order_list = {}
        order_list_sorted = {}
        if self.move_type in ("out_invoice", "out_refund"):
            for line in self.invoice_line_ids.filtered(lambda x: x.sale_line_ids):
                order_list.setdefault(
                    (
                        self._get_date_pick_str(line.sale_line_ids.order_id),
                        line.sale_line_ids.order_id.pnt_single_document_id.name,
                        line.sale_line_ids.order_id,
                        self._get_date_pick(line.sale_line_ids.order_id),
                        line.sale_line_ids.order_id.pnt_single_document_id,
                        line.sale_line_ids.order_id.pnt_agreement_reference,
                        line.sale_line_ids.order_id.pnt_order_reference,
                        line.product_id.id,
                        line.sale_line_ids[
                            :1
                        ].pnt_single_document_line_id.pnt_container_id.id,
                        line.price_unit,
                        tuple(line.tax_ids.ids),
                        line.sale_line_ids.order_id.pnt_has_rentals(),
                        line.sale_line_ids.order_id.date_order.date(),
                        line.sale_line_ids.order_id.partner_shipping_id.display_name,
                        self._return_month_name(
                            line.sale_line_ids.order_id.date_order.date()),
                    ),
                    [],
                ).append(line)
            order_list = self._reduce_lines(order_list)
            order_list_sorted = OrderedDict(sorted(order_list.items()))
        if self.move_type in ("in_invoice", "in_refund"):
            for line in self.invoice_line_ids.filtered(lambda x: x.purchase_line_id):
                order_list.setdefault(
                    (
                        self._get_date_pick_str(line.purchase_line_id.order_id),
                        line.purchase_line_id.order_id.pnt_single_document_id.name,
                        line.purchase_line_id.order_id,
                        self._get_date_pick(line.purchase_line_id.order_id),
                        line.purchase_line_id.order_id.pnt_single_document_id,
                        line.purchase_line_id.order_id.pnt_agreement_reference,
                        line.purchase_line_id.order_id.pnt_order_reference,
                        line.product_id.id,
                        line.purchase_line_id[
                            :1
                        ].pnt_single_document_line_id.pnt_container_id.id,
                        line.price_unit,
                        tuple(line.tax_ids.ids),
                        False,
                        False,
                        False,
                        False,
                    ),
                    [],
                ).append(line)
            order_list = self._reduce_lines(order_list)
            order_list_sorted = OrderedDict(sorted(order_list.items()))
        # without_order
        if self.move_type in ("out_invoice", "out_refund"):
            for line in self.invoice_line_ids.filtered(lambda x: not x.sale_line_ids):
                order_list_sorted.setdefault(
                    "without_order",
                    [],
                ).append(line)
        if self.move_type in ("in_invoice", "in_refund"):
            for line in self.invoice_line_ids.filtered(
                lambda x: not x.purchase_line_id
            ):
                order_list_sorted.setdefault(
                    "without_order",
                    [],
                ).append(line)
        return order_list_sorted

    def lines_grouped_by_product(self):
        self.ensure_one()
        recs = {}
        order_list = []
        for r in self.invoice_line_ids.sorted(key=lambda x: x.product_id):
            if r.display_type not in ("line_section", "line_note"):
                if r.product_id.pnt_is_container:
                    sort_priority = 0
                elif r.product_id.pnt_is_waste:
                    sort_priority = 1
                else:
                    sort_priority = 3
                container = self._pnt_get_container_line(r)
                container_name = ""
                if container:
                    container_name = container.name
                if self.move_type in ('in_invoice','in_refund'):
                    product_id = (str(r.product_id) + "-"
                                  + str(container) + "-"
                                  + str(r.price_unit))
                else:
                    product_id = (str(r.name) + "-"
                                  + str(container) + "-"
                                  + str(r.price_unit))
                if product_id in recs:
                    recs[product_id]["qty"] += r.quantity
                    recs[product_id]["amount"] += r.price_subtotal
                    recs[product_id]["amounttaxincluded"] += r.price_total
                    recs[product_id]["kg"] += self._pnt_get_weight_qty(r)
                    recs[product_id]["units"] += self._pnt_get_container_qty(r)
                else:
                    if self.move_type in ('in_invoice', 'in_refund'):
                        p_product_id = r.product_id.display_name
                        p_product_name = r.product_id.display_name
                    else:
                        p_product_id = r.name
                        p_product_name = r.name
                    recs[product_id] = {
                        "sort_priority": sort_priority,
                        "product_id": p_product_id,
                        "product_name": p_product_name,
                        "qty": r.quantity,
                        "unitprice": r.price_unit,
                        "amount": r.price_subtotal,
                        "amounttaxincluded": r.price_total,
                        "kg": self._pnt_get_weight_qty(r),
                        "uom": r.product_uom_id.name,
                        "container": container_name,
                        "units": self._pnt_get_container_qty(r),
                    }
        recs_sorted = OrderedDict(sorted(recs.items()))
        for prod in recs_sorted.keys():
            if recs[prod]["uom"] == "kg":
                pes = recs[prod]["qty"]
            else:
                pes = recs[prod]["kg"]
            order_list.append(
                (
                    recs[prod]["product_name"],
                    recs[prod]["qty"],
                    recs[prod]["unitprice"],
                    recs[prod]["amount"],
                    recs[prod]["amounttaxincluded"],
                    recs[prod]["uom"],
                    recs[prod]["container"],
                    pes,
                    recs[prod]["units"],
                ),
            )
        return order_list
    def _pnt_get_container_line(self,line):
        result = False
        if (line.sale_line_ids
    and line.sale_line_ids[0].pnt_single_document_line_id.pnt_container_id.id != 2329):
            result = line.sale_line_ids[0].pnt_single_document_line_id.pnt_container_id
        elif line.purchase_line_id:
            result = line.purchase_line_id.pnt_single_document_line_id.pnt_container_id
        return result
    def _pnt_get_product_line(self,line):
        result = False
        if line.sale_line_ids:
            result = line.sale_line_ids[0].pnt_single_document_line_id.pnt_container_id
        elif line.purchase_line_id:
            result = line.purchase_line_id.pnt_single_document_line_id.pnt_container_id
        return result
    def _pnt_get_weight_qty(self,line):
        result = 0
        if line.sale_line_ids:
            for lin in line.sale_line_ids:
                for li in lin.pnt_single_document_line_ids:
                    result += li.pnt_product_uom_qty
        elif line.purchase_line_id:
            result = line.purchase_line_id.pnt_single_document_line_id.pnt_product_uom_qty
        return result
    def _pnt_get_container_qty(self,line):
        result = 0
        if line.sale_line_ids:
            for lin in line.sale_line_ids:
                for li in lin.pnt_single_document_line_ids:
                    result += li.pnt_container_qty
        elif line.purchase_line_id:
            result = line.purchase_line_id.pnt_single_document_line_id.pnt_container_qty
        return result