# -*- coding: utf-8 -*-
import logging
import werkzeug

from odoo import http, tools, _
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home, SIGN_UP_REQUEST_PARAMS
from odoo.exceptions import UserError
from odoo.addons.website.controllers.main import Website
from collections import OrderedDict
from operator import itemgetter

from odoo import _, http
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.osv.expression import AND, OR
from odoo.tools import groupby as groupbyelem

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager

_logger = logging.getLogger(__name__)


class SingleDocumentLine(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "single_document_line_count" in counters:
            values["single_document_line_count"] = (
                request.env["pnt.single.document.line"].search_count(
                    self._prepare_pnt_single_document_line_domain()
                )
                if request.env["pnt.single.document.line"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_pnt_single_document_line_domain(self):
        authorized_partners = self._pnt_get_authorized_partners_single_document_line()
        return [
            "|",
            ("pnt_product_id.pnt_is_waste", "!=", False),
            ("pnt_product_id.pnt_is_container", "!=", False),
            ("pnt_holder_id.id", "in", authorized_partners),
            ("state", "in", ["finished"]),
            ("pnt_single_document_id.pnt_du_signed_file", "!=", False),
        ]

    @http.route(
        [
            "/my/single_document_line/<int:single_document_line>",
            "/my/single_document_line/<int:single_document_line>/<string:report_type>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_single_document_line_detail(
        self, single_document_line=None, report_type=None, **kw
    ):
        try:
            single_document_line_sudo = self._document_check_access(
                "pnt.single.document.line", single_document_line
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=single_document_line_sudo,
                report_type=report_type,
                report_ref="report_pnt.pnt_du_report",
                download=False,
            )

        values = {
            "single_document_line": single_document_line_sudo,
            "page_name": "single_document_line_open",
        }
        # acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('pnt_holder_id') and values.get('pnt_holder_id')[0].country_id.id
        #     # values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id)

        return request.render(
            "website_custom_pnt.portal_single_document_line_page", values
        )

    @http.route(
        [
            "/my/single_document_line",
            "/my/single_document_line/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_single_document_line(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in=None,
        groupby=None,
        **kw
    ):
        PntSingleDocumentLine = request.env["pnt.single.document.line"]
        values = self._prepare_portal_layout_values()

        searchbar_sortings = dict(
            sorted(
                self._pnt_single_document_line_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        filter_single_document_lines = PntSingleDocumentLine.sudo().search(
            self._prepare_pnt_single_document_line_domain(),
        )
        #for delivery_id in filter_single_document_lines.mapped(
        #    "pnt_partner_delivery_id"
        #):
        #    searchbar_filters[str(delivery_id.id)] = {
        #        "label": delivery_id.name,
        #        "domain": [("pnt_partner_delivery_id.id", "=", delivery_id.id)],
        #    }
        for pickup_id in filter_single_document_lines.mapped(
                "pnt_single_document_id").mapped("pnt_partner_pickup_id"):
            searchbar_filters[str(pickup_id.id)] = {
                "label": _("Pickup: %s") % pickup_id.display_name,
                "domain": [
                    ("pnt_single_document_id.pnt_partner_pickup_id.id", "=", pickup_id.id)
                ],
            }
        searchbar_inputs = self._pnt_single_document_line_get_searchbar_inputs()

        if not sortby:
            sortby = "name"
        order = searchbar_sortings[sortby]["order"]

        if not filterby:
            filterby = "all"
        domain = searchbar_filters.get(filterby, searchbar_filters.get("all"))["domain"]

        if not groupby:
            groupby = "none"

        if date_begin and date_end:
            domain += [
                ("create_date", ">", date_begin),
                ("create_date", "<=", date_end),
            ]

        if not search_in:
            search_in = "all"
        if search:
            domain += self._pnt_single_document_line_get_search_domain(
                search_in, search
            )

        authorized_partners = self._pnt_get_authorized_partners_single_document_line()
        domain = [
            "|",
            ("pnt_product_id.pnt_is_waste", "!=", False),
            ("pnt_product_id.pnt_is_container", "!=", False),
            ("pnt_holder_id.id", "in", authorized_partners),
            ("state", "in", ["finished"]),
            ("pnt_single_document_id.pnt_du_signed_file", "!=", False),
        ] + domain

        # count for pager
        pnt_single_document_line_count = PntSingleDocumentLine.sudo().search_count(
            domain
        )
        # pager
        pager = portal_pager(
            url="/my/single_document_line",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=pnt_single_document_line_count,
            page=page,
            step=self._items_per_page,
        )

        pnt_single_document_lines = PntSingleDocumentLine.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "pnt_single_document_lines": pnt_single_document_lines,
                "page_name": "single_document_line_open",
                "default_url": "/my/single_document_line",
                "pager": pager,
                "searchbar_sortings": searchbar_sortings,
                "searchbar_groupby": False,
                "searchbar_inputs": searchbar_inputs,
                "search_in": search_in,
                "search": search,
                "sortby": sortby,
                "groupby": groupby,
                "searchbar_filters": OrderedDict(sorted(searchbar_filters.items())),
                "filterby": filterby,
            }
        )
        return request.render(
            "website_custom_pnt.portal_pnt_single_document_line", values
        )

    def _pnt_single_document_line_get_searchbar_sortings(self):
        return {
            "name": {
                "label": _("Name"),
                "order": "pnt_single_document_id desc",
                "sequence": 1,
            },
            "pnt_effective_date": {
                "label": _("Effective date"),
                "order": "pnt_effective_date desc",
                "sequence": 2,
            },
        }

    def _pnt_single_document_line_get_searchbar_inputs(self):
        values = {
            "all": {"input": "all", "label": _("Search in All"), "order": 1},
            "pnt_single_document_id": {
                "input": "pnt_single_document_id",
                "label": _("Search in DU"),
                "order": 1,
            },
            "pnt_product_id": {
                "input": "pnt_product_id",
                "label": _("Search in Waste"),
                "order": 2,
            },
            "pnt_container_id": {
                "input": "pnt_container_id",
                "label": _("Search in Container"),
                "order": 3,
            },
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _pnt_single_document_line_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("pnt_single_document_id", "all"):
            search_domain.append([("pnt_single_document_id", "ilike", search)])
        if search_in in ("pnt_product_id", "all"):
            search_domain.append([("pnt_product_id", "ilike", search)])
        if search_in in ("pnt_container_id", "all"):
            search_domain.append([("pnt_container_id", "ilike", search)])
        return OR(search_domain)

    def _pnt_get_authorized_partners_single_document_line(self):
        user_commercial_partner_id = request.env.user.partner_id.commercial_partner_id
        authorized_partners = request.env["res.partner"].search(
            [("commercial_partner_id", "=", user_commercial_partner_id.id)]
        )
        return authorized_partners.ids
