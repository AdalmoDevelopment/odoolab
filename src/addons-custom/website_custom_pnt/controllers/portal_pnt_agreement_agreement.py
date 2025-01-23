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


class AgreementAgreement(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "agreement_agreement_count" in counters:
            values["agreement_agreement_count"] = (
                request.env["pnt.agreement.agreement"].search_count(
                    self._prepare_pnt_agreement_agreement_domain()
                )
                if request.env["pnt.agreement.agreement"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_pnt_agreement_agreement_domain(self):
        authorized_partners = self._pnt_get_authorized_partners()
        return [
            ("state", "in", ["done"]),
            ("pnt_holder_id.id", "in", authorized_partners),
        ]

    @http.route(
        [
            "/my/agreement_agreement/<int:agreement>",
            "/my/agreement_agreement/<int:agreement>/<string:report_type>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_agreement_agreement_detail(
        self, agreement=None, report_type=None, **kw
    ):
        try:
            agreement_sudo = self._document_check_access(
                "pnt.agreement.agreement", agreement
            )
        except (AccessError, MissingError):
            return request.redirect("/my")

        if report_type in ("html", "pdf", "text"):
            return self._show_report(
                model=agreement_sudo,
                report_type=report_type,
                report_ref="report_pnt.pnt_budget_contract_report_2",
                download=False,
            )

        values = {
            "pnt_agreement_agreement": agreement_sudo,
            "page_name": "agreement_agreement_open",
        }
        return request.render(
            "website_custom_pnt.portal_agreement_agreement_page", values
        )

    @http.route(
        [
            "/my/agreement_agreement",
            "/my/agreement_agreement/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_agreement_agreement(
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
        PntAgreementAgreement = request.env["pnt.agreement.agreement"]
        values = self._prepare_portal_layout_values()

        searchbar_sortings = dict(
            sorted(
                self._pnt_agreement_agreement_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        searchbar_inputs = self._pnt_agreement_agreement_get_searchbar_inputs()

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
            domain += self._pnt_agreement_agreement_get_search_domain(search_in, search)

        authorized_partners = self._pnt_get_authorized_partners()
        domain = [
            ("state", "in", ["done"]),
            ("pnt_holder_id.id", "in", authorized_partners),
        ] + domain

        # count for pager
        pnt_agreement_agreement_count = PntAgreementAgreement.sudo().search_count(
            domain
        )
        # pager
        pager = portal_pager(
            url="/my/agreement_agreement",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=pnt_agreement_agreement_count,
            page=page,
            step=self._items_per_page,
        )

        pnt_agreement_agreements = PntAgreementAgreement.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "pnt_agreement_agreements": pnt_agreement_agreements,
                "page_name": "agreement_agreement",
                "default_url": "/my/agreement_agreement",
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
            "website_custom_pnt.portal_pnt_agreement_agreement", values
        )

    def _pnt_agreement_agreement_get_searchbar_sortings(self):
        return {
            "name": {
                "label": _("Name"),
                "order": "name desc",
                "sequence": 1,
            },
        }

    def _pnt_agreement_agreement_get_searchbar_inputs(self):
        values = {
            "all": {"input": "all", "label": _("Search in All"), "order": 1},
            "name": {
                "input": "name",
                "label": _("Search in Name"),
                "order": 2,
            },
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _pnt_agreement_agreement_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("name", "all"):
            search_domain.append([("name", "ilike", search)])
        # if search_in in ("pnt_product_brand_id", "all"):
        #     search_domain.append([("pnt_product_brand_id", "ilike", search)])
        # if search_in in ("pnt_product_categ_id", "all"):
        #     search_domain.append([("pnt_product_categ_id", "ilike", search)])
        return OR(search_domain)

    def _pnt_get_authorized_partners(self):
        authorized_partners = request.env.user.partner_id
        if request.env.user.partner_id.parent_id:
            authorized_partners += request.env.user.partner_id.parent_id
        # if request.env.user.partner_id.child_ids:
        #     authorized_partners += request.env.user.partner_id.child_ids
        return authorized_partners.ids
