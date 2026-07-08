# Copyright 2026 Moduon Team - Rafael Blasco <rafael@moduon.team>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book"

    def upsert_book_line_tax(self, move_line, vat_book_line, implied_taxes):
        tax_lines = vat_book_line["tax_lines"]
        default_dict = {
            "base_amount": 0,
            "tax_amount": 0,
            "deductible_amount": 0,
            "base_move_line_ids": [],
            "move_line_ids": [],
            "special_tax_group": False,
        }
        sign = -1
        if vat_book_line["line_type"] in ["received", "rectification_received"]:
            sign = 1
        if move_line.tax_line_id:
            res = {}
            move_line._process_aeat_tax_fee_info(res, move_line.tax_line_id, sign)
            for child_tax, info in res.items():
                key = self.get_book_line_tax_key(move_line, child_tax)
                value = tax_lines.setdefault(
                    key, default_dict | {"tax_id": child_tax.id}
                )
                value["tax_amount"] += info["amount"]
                value["deductible_amount"] += info["deductible_amount"]
                value["move_line_ids"].append((4, move_line.id))
        for i, tax in enumerate(move_line.tax_ids):
            res = {}
            move_line._process_aeat_tax_base_info(res, tax, sign)
            if i == 0:
                vat_book_line["base_amount"] += next(iter(res.values()))["base"]
            for child_tax, info in res.items():
                if child_tax not in implied_taxes:
                    continue
                key = self.get_book_line_tax_key(move_line, child_tax)
                value = tax_lines.setdefault(
                    key, default_dict | {"tax_id": child_tax.id}
                )
                value["base_amount"] += info["base"]
                value["base_move_line_ids"].append((4, move_line.id))
                # For later matching special taxes
                value["other_tax_ids"] = (move_line.tax_ids - tax).ids
