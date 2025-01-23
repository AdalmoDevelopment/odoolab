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


class SingleDocument(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "single_document_count" in counters:
            values["single_document_count"] = (
                request.env["pnt.single.document"].search_count(
                    self._prepare_pnt_single_document_domain()
                )
                if request.env["pnt.single.document"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_pnt_single_document_domain(self):
        authorized_partners = self._pnt_get_authorized_partners_single_document()
        return [
            ("pnt_du_signed_file", "!=", False),
            ("pnt_holder_id.id", "in", authorized_partners),
            ("state", "in", ["finished"]),
        ]

    @http.route(
        [
            "/my/single_document/<int:single_document>",
            "/my/single_document/<int:single_document>/<string:report_type>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_single_document_detail(
        self, single_document=None, report_type=None, **kw
    ):
        try:
            single_document_sudo = self._document_check_access(
                "pnt.single.document", single_document
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=single_document_sudo,
                report_type=report_type,
                report_ref="report_pnt.pnt_du_report",
                download=False,
            )

        values = {
            "single_document": single_document_sudo,
            "page_name": "single_document_open",
        }
        # acquirers = values.get('acquirers')
        # if acquirers:
        #     country_id = values.get('pnt_holder_id') and values.get('pnt_holder_id')[0].country_id.id
        #     # values['acq_extra_fees'] = acquirers.get_acquirer_extra_fees(invoice_sudo.amount_residual, invoice_sudo.currency_id, country_id)

        return request.render("website_custom_pnt.portal_single_document_page", values)

    @http.route(
        [
            "/my/single_document",
            "/my/single_document/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_single_document(
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
        PntSingleDocument = request.env["pnt.single.document"]
        values = self._prepare_portal_layout_values()

        searchbar_sortings = dict(
            sorted(
                self._pnt_single_document_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        searchbar_inputs = self._pnt_single_document_get_searchbar_inputs()

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
            domain += self._pnt_single_document_get_search_domain(search_in, search)

        authorized_partners = self._pnt_get_authorized_partners_single_document()
        domain = [
            ("pnt_du_signed_file", "!=", False),
            ("pnt_holder_id.id", "in", authorized_partners),
            ("state", "in", ["finished"]),
        ] + domain

        # count for pager
        pnt_single_document_count = PntSingleDocument.sudo().search_count(domain)
        # pager
        pager = portal_pager(
            url="/my/single_document",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=pnt_single_document_count,
            page=page,
            step=self._items_per_page,
        )

        pnt_single_documents = PntSingleDocument.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "pnt_single_documents": pnt_single_documents,
                "page_name": "single_document",
                "default_url": "/my/single_document",
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
        return request.render("website_custom_pnt.portal_pnt_single_document", values)

    def _pnt_single_document_get_searchbar_sortings(self):
        return {
            "name": {
                "label": _("Name"),
                "order": "name desc",
                "sequence": 1,
            },
            "pnt_effective_date": {
                "label": _("Effective date"),
                "order": "pnt_effective_date desc",
                "sequence": 2,
            },
        }

    def _pnt_single_document_get_searchbar_inputs(self):
        values = {
            "all": {"input": "all", "label": _("Search in All"), "order": 1},
            "name": {
                "input": "name",
                "label": _("Search in Name"),
                "order": 2,
            },
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _pnt_single_document_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("name", "all"):
            search_domain.append([("name", "ilike", search)])
        # if search_in in ("pnt_product_brand_id", "all"):
        #     search_domain.append([("pnt_product_brand_id", "ilike", search)])
        # if search_in in ("pnt_product_categ_id", "all"):
        #     search_domain.append([("pnt_product_categ_id", "ilike", search)])
        return OR(search_domain)

    def _pnt_get_authorized_partners_single_document(self):
        user_commercial_partner_id = request.env.user.partner_id.commercial_partner_id
        authorized_partners = request.env["res.partner"].search(
            [("commercial_partner_id", "=", user_commercial_partner_id.id)]
        )
        return authorized_partners.ids
