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


class WasteTransferDocument(CustomerPortal):
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if "waste_transfer_document_count" in counters:
            values["waste_transfer_document_count"] = (
                request.env["pnt.waste.transfer.document"].search_count(
                    self._prepare_pnt_waste_transfer_document_domain()
                )
                if request.env["pnt.waste.transfer.document"].check_access_rights(
                    "read", raise_exception=False
                )
                else 0
            )
        return values

    def _prepare_pnt_waste_transfer_document_domain(self):
        single_document_ids = request.env["pnt.single.document"].search(
            self._prepare_pnt_single_document_domain()
        )
        return [
            ("pnt_single_document_id", "in", single_document_ids.ids or []),
        ]
    @http.route(
        [
            "/my/waste_transfer_document",
            "/my/waste_transfer_document/page/<int:page>",
            "/my/waste_transfer_document/<int:waste_transfer_document>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_waste_transfer_document_home(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in=None,
        groupby=None,
        waste_transfer_document=None,
        **kw
    ):
        if waste_transfer_document:
            try:
                document_sudo = self._document_check_access(
                    "pnt.waste.transfer.document", waste_transfer_document
                )
            except (AccessError, MissingError):
                return request.redirect("/my")
            authorized_partners = self._pnt_get_authorized_partners()
            if document_sudo.pnt_single_document_id.pnt_holder_id.id in authorized_partners:
                return self._show_report(
                    model=document_sudo.pnt_single_document_id,
                    report_type="pdf",
                    report_ref="report_pnt.action_report_document_identification",
                    download=False,
                )

        PntWasteTransferDocument = request.env["pnt.waste.transfer.document"]
        values = self._prepare_portal_layout_values()

        searchbar_sortings = dict(
            sorted(
                self._pnt_waste_transfer_document_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        searchbar_inputs = self._pnt_waste_transfer_document_get_searchbar_inputs()

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
            domain += self._pnt_waste_transfer_document_get_search_domain(
                search_in, search
            )

        domain = self._prepare_pnt_waste_transfer_document_domain() + domain

        # count for pager
        pnt_waste_transfer_document_count = (
            PntWasteTransferDocument.sudo().search_count(domain)
        )
        # pager
        pager = portal_pager(
            url="/my/waste_transfer_document",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=pnt_waste_transfer_document_count,
            page=page,
            step=self._items_per_page,
        )

        pnt_waste_transfer_documents = PntWasteTransferDocument.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "pnt_waste_transfer_documents": pnt_waste_transfer_documents,
                "page_name": "waste_transfer_document_home",
                "default_url": "/my/waste_transfer_document",
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
            "website_custom_pnt.portal_pnt_waste_transfer_document", values
        )

    @http.route(
        [
            "/my/single_document/<int:id_single_document>/waste_transfer_document",
            "/my/single_document/<int:id_single_document>/waste_transfer_document/<string:report_type>",
            "/my/single_document/<int:id_single_document>/waste_transfer_document/page/<int:page>",
        ],
        type="http",
        auth="user",
        website=True,
    )
    def portal_my_waste_transfer_document(
        self,
        page=1,
        date_begin=None,
        date_end=None,
        sortby=None,
        filterby=None,
        search=None,
        search_in=None,
        groupby=None,
        id_single_document=None,
        report_type=None,
        **kw
    ):
        if report_type and id_single_document:
            try:
                document_sudo = self._document_check_access(
                    "pnt.single.document", id_single_document
                )
            except (AccessError, MissingError):
                return request.redirect("/my")
            authorized_partners = self._pnt_get_authorized_partners()
            if document_sudo.pnt_holder_id.id in authorized_partners:
                return self._show_report(
                    model=document_sudo,
                    report_type="pdf",
                    report_ref="report_pnt.action_report_document_identification",
                    download=False,
                )

        if id_single_document:
            document_sudo = self._document_check_access(
                "pnt.single.document", id_single_document
            )
            authorized_partners = self._pnt_get_authorized_partners()
            if document_sudo.pnt_holder_id.id not in authorized_partners:
                id_single_document = False

        PntWasteTransferDocument = request.env["pnt.waste.transfer.document"]
        values = self._prepare_portal_layout_values()

        searchbar_sortings = dict(
            sorted(
                self._pnt_waste_transfer_document_get_searchbar_sortings().items(),
                key=lambda item: item[1]["sequence"],
            )
        )
        searchbar_filters = {
            "all": {"label": _("All"), "domain": []},
        }
        searchbar_inputs = self._pnt_waste_transfer_document_get_searchbar_inputs()

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
            domain += self._pnt_waste_transfer_document_get_search_domain(
                search_in, search
            )

        if id_single_document:
            domain = [("pnt_single_document_id", "=", id_single_document)] + domain
        else:
            domain = [("id", "=", False)] + domain

        # count for pager
        pnt_waste_transfer_document_count = (
            PntWasteTransferDocument.sudo().search_count(domain)
        )
        # pager
        pager = portal_pager(
            url="/my/waste_transfer_document",
            url_args={
                "date_begin": date_begin,
                "date_end": date_end,
                "sortby": sortby,
                "filterby": filterby,
                "groupby": groupby,
                "search": search,
                "search_in": search_in,
            },
            total=pnt_waste_transfer_document_count,
            page=page,
            step=self._items_per_page,
        )

        pnt_waste_transfer_documents = PntWasteTransferDocument.sudo().search(
            domain,
            order=order,
            limit=self._items_per_page,
            offset=pager["offset"],
        )
        values.update(
            {
                "date": date_begin,
                "date_end": date_end,
                "pnt_waste_transfer_documents": pnt_waste_transfer_documents,
                "page_name": "waste_transfer_document",
                "default_url": "/my/waste_transfer_document",
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
            "website_custom_pnt.portal_pnt_waste_transfer_document", values
        )

    def _pnt_waste_transfer_document_get_searchbar_sortings(self):
        return {
            "name": {
                "label": _("Name"),
                "order": "name desc",
                "sequence": 1,
            },
            "pnt_date": {
                "label": _("Date"),
                "order": "pnt_date desc",
                "sequence": 2,
            },
        }

    def _pnt_waste_transfer_document_get_searchbar_inputs(self):
        values = {
            "all": {"input": "all", "label": _("Search in All"), "order": 1},
            "name": {
                "input": "name",
                "label": _("Search in Name"),
                "order": 2,
            },
        }
        return dict(sorted(values.items(), key=lambda item: item[1]["order"]))

    def _pnt_waste_transfer_document_get_search_domain(self, search_in, search):
        search_domain = []
        if search_in in ("name", "all"):
            search_domain.append([("name", "ilike", search)])
        # if search_in in ("pnt_product_brand_id", "all"):
        #     search_domain.append([("pnt_product_brand_id", "ilike", search)])
        # if search_in in ("pnt_product_categ_id", "all"):
        #     search_domain.append([("pnt_product_categ_id", "ilike", search)])
        return OR(search_domain)

    # def _pnt_get_authorized_partners(self):
    #     authorized_partners = request.env.user.partner_id
    #     if request.env.user.partner_id.parent_id:
    #         authorized_partners += request.env.user.partner_id.parent_id
    #     # if request.env.user.partner_id.child_ids:
    #     #     authorized_partners += request.env.user.partner_id.child_ids
    #     return authorized_partners.ids
