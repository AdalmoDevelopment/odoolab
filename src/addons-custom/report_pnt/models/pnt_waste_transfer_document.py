from odoo import models


class PntWasteTransferDocument(models.Model):
    _inherit = "pnt.waste.transfer.document"

    def get_waste_table(self, du=None):
        tables = []
        if du and du.pnt_single_document_type == "output":
            agreement_registration_ids = (
                du.pnt_partner_pickup_id.pnt_agreement_registration_ids.filtered(
                    lambda x: x.pnt_agreement_registration_type == "mgm"
                    and x.pnt_product_id.id == self.pnt_product_id.id
                    and x.pnt_state not in ("draft")
                )
            )
            if agreement_registration_ids:
                tables = [
                    agreement_registration_ids.pnt_waste_table2_ids,
                    agreement_registration_ids.pnt_waste_table5_ids,
                ]
        if not tables:
            tables = [
                self.pnt_product_id.pnt_waste_table2_ids,
                self.pnt_product_id.pnt_waste_table5_ids,
            ]
        return tables
