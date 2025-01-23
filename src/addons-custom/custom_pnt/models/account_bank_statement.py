from odoo import models, api


class AccountBankStmtCashWizard(models.Model):
    _inherit = "account.bank.statement.cashbox"

    @api.model
    def default_get(self, fields):
        vals = super(AccountBankStmtCashWizard, self).default_get(fields)
        balance = self.env.context.get("balance")
        statement_id = self.env.context.get("statement_id")
        if statement_id:
            statement_id = self.env["account.bank.statement"].browse(statement_id)
            lines = {}
            if statement_id.previous_statement_id:
                prev_statement_id = statement_id.previous_statement_id
                if balance == "open":
                    lines = prev_statement_id.cashbox_end_id.cashbox_lines_ids
                else:
                    if statement_id.cashbox_start_id:
                        lines = statement_id.cashbox_start_id.cashbox_lines_ids
                    else:
                        lines = prev_statement_id.cashbox_end_id.cashbox_lines_ids
            if lines:
                vals["cashbox_lines_ids"] = [
                    [
                        0,
                        0,
                        {
                            "coin_value": line.coin_value,
                            "number": 0 if balance == "close" else line.number,
                            "subtotal": 0.0 if balance == "close" else line.subtotal,
                        },
                    ]
                    for line in lines
                ]
        return vals
