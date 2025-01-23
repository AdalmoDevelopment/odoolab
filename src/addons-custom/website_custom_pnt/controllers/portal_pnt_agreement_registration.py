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


class AgreementRegistration(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "agreement_registration_count" in counters:
            values["agreement_registration_count"] = (
                request.env["pnt.agreement.registration"].search_count(
                    self._prepare_pnt_agreement_registration_domain()
                )
                if request.env["pnt.agreement.registration"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_pnt_agreement_registration_domain(self):
        authorized_partners = self._pnt_get_authorized_partners_agreement_registration()
        return [
            ("pnt_pickup_id.id", "in", authorized_partners),
            ("pnt_state", "in", ["active"]),
        ]

    @http.route(
        [
            "/my/agreement_registration",
            "/my/agreement_registration/<int:agreement_registration>/<string:report_type>",
            "/my/agreement_registration/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_agreement_registration(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in=None,
        groupby=None,
        agreement_registration=None,
        report_type=None,
        **kw
    ):
        PntAgreementRegistration = request.env["pnt.agreement.registration"]
        values = self._prepare_portal_layout_values()

        if report_type and agreement_registration:
            try:
                document_sudo = self._document_check_access(
                    "pnt.agreement.registration", agreement_registration
                )
            except (AccessError, MissingError):
                return request.redirect("/my")
            authorized_partners = (
                self._pnt_get_authorized_partners_agreement_registration()
            )
            if document_sudo.pnt_pickup_id.id in authorized_partners:
                return self._show_report(
                    model=document_sudo,
                    report_type="pdf",
                    report_ref="report_pnt.pnt_du_report",
                    download=False,
                )

        searchbar_sortings = dict(
            sorted(
                self._pnt_agreement_registration_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        searchbar_inputs = self._pnt_agreement_registration_get_searchbar_inputs()

        if not sortby:
            sortby = "number"
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
            domain += self._pnt_agreement_registration_get_search_domain(
                search_in, search
            )

        authorized_partners = self._pnt_get_authorized_partners_agreement_registration()
        domain = [
            ("pnt_pickup_id.id", "in", authorized_partners),
            ("pnt_state", "in", ["active"]),
        ] + domain

        # count for pager
        pnt_agreement_registration_count = PntAgreementRegistration.sudo().search_count(
            domain
        )
        # pager
        pager = portal_pager(
            url="/my/agreement_registration",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=pnt_agreement_registration_count,
            page=page,
            step=self._items_per_page,
        )

        pnt_agreement_registrations = PntAgreementRegistration.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "pnt_agreement_registrations": pnt_agreement_registrations,
                "page_name": "agreement_registration",
                "default_url": "/my/agreement_registration",
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
            "website_custom_pnt.portal_pnt_agreement_registration", values
        )

    def _pnt_agreement_registration_get_searchbar_sortings(self):
        return {
            "number": {
                "label": _("Number"),
                "order": "pnt_agreement_sequence desc",
                "sequence": 1,
            },
            "pnt_agreement_date": {
                "label": _("Agreement date"),
                "order": "pnt_agreement_date desc",
                "sequence": 2,
            },
        }

    def _pnt_agreement_registration_get_searchbar_inputs(self):
        values = {
            "all": {"input": "all", "label": _("Search in All"), "order": 1},
            "number": {
                "input": "pnt_agreement_sequence",
                "label": _("Search in pnt_agreement_sequence"),
                "order": 2,
            },
            "pnt_pickup_id": {
                "input": "pnt_pickup_id",
                "label": _("Search in Productor"),
                "order": 3,
            },
            "pnt_product_id": {
                "input": "pnt_product_id",
                "label": _("Search in Waste"),
                "order": 4,
            },
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _pnt_agreement_registration_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("number", "all"):
            search_domain.append([("pnt_agreement_sequence", "ilike", search)])
        if search_in in ("pnt_pickup_id", "all"):
            search_domain.append([("pnt_pickup_id.name", "ilike", search)])
        if search_in in ("pnt_product_id", "all"):
            search_domain.append([("pnt_product_id", "ilike", search)])
        return OR(search_domain)

    def _pnt_get_authorized_partners_agreement_registration(self):
        user_commercial_partner_id = request.env.user.partner_id.commercial_partner_id
        authorized_partners = request.env["res.partner"].search(
            [("commercial_partner_id", "=", user_commercial_partner_id.id)]
        )
        return authorized_partners.ids
