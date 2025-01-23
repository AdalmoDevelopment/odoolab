from odoo import _, api, fields, models


class PntCreateDi(models.TransientModel):
    _name = "pnt.create.di"

    pnt_single_document_id = fields.Many2one(
        comodel_name="pnt.single.document",
        string="Single document",
    )
    pnt_document_type = fields.Selection(
        [
            ("nt", _("NT")),
            ("di", _("DI")),
        ],
        string="Waste transfer document type",
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_type = fields.Selection(
        [
            ("esir", _("e-SIR")),
            ("singer", _("SINGER")),
            ("other", _("Other")),
        ],
        string="Type",
        copy=True,
        index=True,
        tracking=3,
    )
    pnt_single_document_lines_ids = fields.Many2many(
        comodel_name="pnt.single.document.line",
        relation="pnt_du_line_di_rel",
        column1="single_document_line_id",
        column2="di_id",
        string="DI to create",
        compute="_compute_pnt_single_document_lines_ids",
        store=True,
    )
    pnt_date = fields.Date(
        string="Date",
        default=fields.Date.today,
    )

    # Methods
    @api.depends("pnt_single_document_id")
    def _compute_pnt_single_document_lines_ids(self):
        for record in self:
            record.pnt_single_document_lines_ids = (
                record.pnt_single_document_id.lines_without_di()
            )

    def create_dis(self):
        obj_psdl = self.env["pnt.single.document.line"]
        for record in self:
            created_dis = []
            for (
                di
            ) in record.pnt_single_document_id.pnt_single_document_line_ids.pnt_waste_transfer_document_id.filtered(
                lambda x: x.pnt_product_id.pnt_is_waste
            ):
                created_dis.append(di.pnt_product_id.id)
            final_lines = {}
            for di in record.pnt_single_document_lines_ids.filtered(
                lambda x: x.pnt_product_id.pnt_is_waste
            ):
                final_lines.setdefault(di.pnt_product_id.id, []).append(di.id)
            for k, v in final_lines.items():
                if k in created_dis:
                    continue
                newdi = self.env["pnt.waste.transfer.document"].create(
                    {
                        "pnt_document_type": record.pnt_document_type,
                        "pnt_type": record.pnt_type,
                        "pnt_single_document_line_ids": [(6, 0, v)],
                        "pnt_single_document_id": record.pnt_single_document_id.id,
                        "pnt_date": record.pnt_date,
                    }
                )
                obj_psdl.browse(v).pnt_waste_transfer_document_id = newdi
