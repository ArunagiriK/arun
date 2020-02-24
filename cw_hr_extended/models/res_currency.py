# -*- coding: utf-8 -*-

import logging
import logging
import math
import re
import time

try:
    from num2words import num2words
except ImportError:
    logging.getLogger(__name__).warning("The num2words python library is not installed, l10n_mx_edi features won't be fully available.")
    num2words = None

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

CURRENCY_DISPLAY_PATTERN = re.compile(r'(\w+)\s*(?:\((.*)\))?')

class Currency(models.Model):
    _inherit = "res.currency"
    
    currency_unit_label = fields.Char(string="Currency Unit", help="Currency Unit Name")
    currency_subunit_label = fields.Char(string="Currency Subunit", help="Currency Subunit Name")

    _sql_constraints = [
        ('rounding_gt_zero', 'CHECK (rounding>0)', 'The rounding factor must be greater than 0!')
    ]

    @api.multi
    def amount_to_text(self, amount):
        self.ensure_one()
        def _num2words(number, lang):
            try:
                return num2words(number, lang=lang).title()
            except NotImplementedError:
                return num2words(number, lang='en').title()

        if num2words is None:
            logging.getLogger(__name__).warning("The library 'num2words' is missing, cannot render textual amounts.")
            return ""

        fractional_value, integer_value = math.modf(amount)
        fractional_amount = round(abs(fractional_value), self.decimal_places) * (math.pow(10, self.decimal_places))
        lang_code = self.env.context.get('lang') or self.env.user.lang
        lang = self.env['res.lang'].search([('code', '=', lang_code)])
        amount_words = tools.ustr('{amt_value} {amt_word}').format(
                        amt_value=_num2words(int(integer_value), lang=lang.iso_code),
                        amt_word=self.currency_unit_label,
                        )
        if not self.is_zero(fractional_value):
            amount_words += ' ' + _('and') + tools.ustr(' {amt_value} {amt_word}').format(
                        amt_value=_num2words(int(fractional_amount), lang=lang.iso_code),
                        amt_word=self.currency_subunit_label,
                        )
        return amount_words
    
    
    