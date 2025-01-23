from odoo import models, fields


class PntCirculationPermitClass(models.Model):
    _name = "pnt.circulation.permit.class"
    _description = "Pnt Circulation Permit Class"

    code = fields.Char(
        string="Code",
    )
    name = fields.Char(
        string="Name",
    )
    active = fields.Boolean(
        "Active",
        default=True,
    )

    def name_get(self):
        res = []
        for record in self:
            name = record.name
            if record.code:
                name = "[%s] %s" % (record.code, record.name)
            res.append((record.id, name))
        return res
