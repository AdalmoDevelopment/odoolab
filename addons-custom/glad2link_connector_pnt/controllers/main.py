import base64
from io import BytesIO

from PyPDF2 import PdfFileReader
from werkzeug.exceptions import BadRequest, NotFound, NotImplemented

from odoo import fields, http
from odoo.http import JsonRequest, request

ffields = ["du_name", "du_pdf", "gladtolink_id"]


def _custom_json_response(self, result=None, error=None):
    if (
        error
        and isinstance(error, dict)
        and error.get("data", {}).get("name") == "werkzeug.exceptions.BadRequest"
    ):
        error["code"] = 400
        error["message"] = "Bad Request"
    return original_json(self, result=result, error=error)


original_json = JsonRequest._json_response
JsonRequest._json_response = _custom_json_response


class Glad2Link(http.Controller):
    def _raise_error(self, code, msg=None):
        errors = {
            400: BadRequest(msg),
            404: NotFound(msg),
            501: NotImplemented(msg),
        }
        raise errors[code]

    def _check_valid_pdf(self, data_pdf_b64):
        try:
            decoded_data = base64.b64decode(data_pdf_b64)
        except:
            return self._raise_error(
                code=400, msg="Invalid PDF data. Only base64 encoded data is allowed."
            )
        try:
            pdf_stream = BytesIO(decoded_data)
            PdfFileReader(pdf_stream)
        except:
            return self._raise_error(
                code=400, msg="Invalid PDF. PDF file is corrupted."
            )
        return True

    def _check_valid_post(self, data_post):
        if not data_post:
            return self._raise_error(code=400, msg="No data found in the request.")
        if not isinstance(data_post, dict):
            return self._raise_error(
                code=400, msg="Invalid data format. Only JSON format is allowed."
            )
        for field in ffields:
            if not data_post.get(field):
                return self._raise_error(
                    code=400, msg=f"Field {field} is required in the request."
                )
        return True

    @http.route(
        route="/api/gla2link/v1/du/register",
        auth="api_key",
        website=False,
        sitemap=False,
        type="json",
        method="post",
        csrf=True,
        multilang=False,
    )
    def du_register(self):
        now = fields.Datetime.now()
        data = request.jsonrequest
        self._check_valid_post(data)
        post_fields = {}
        for field in ffields:
            post_fields[field] = data.get(field)
        self._check_valid_pdf(post_fields["du_pdf"])
        try:
            du = (
                request.env["pnt.single.document"]
                .sudo()
                .search([("name", "=", post_fields["du_name"])])
            )
            if len(du) > 1:
                return self._raise_error(
                    code=501, msg="Found more than one DU with the same name."
                )
            if not du:
                return self._raise_error(code=404, msg="DU not found.")
        except:
            return self._raise_error(code=404, msg="DU not found.")
        du.write(
            {
                "pnt_gla2link_id": post_fields["gladtolink_id"],
                "pnt_gla2link_datetime": now,
                "pnt_du_signed_file": post_fields["du_pdf"],
            }
        )
        attachment = (
            request.env["ir.attachment"]
            .sudo()
            .search(
                [
                    ("res_model", "=", "pnt.single.document"),
                    ("res_id", "=", du.id),
                    ("res_field", "=", "pnt_du_signed_file"),
                ]
            )
        )
        attachment.name = du.name + ".pdf"
        return {"status": "success"}
