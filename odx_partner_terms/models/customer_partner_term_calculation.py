from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval
import re


def is_one_value(result):
    # check if sql query returns only one value
    if type(result) is dict and 'value' in result.dictfetchone():
        return True
    elif type(result) is list and 'value' in result[0]:
        return True
    else:
        return False


RE_SELECT_QUERY = re.compile('.*(' + '|'.join((
    'INSERT',
    'UPDATE',
    'DELETE',
    'CREATE',
    'ALTER',
    'DROP',
    'GRANT',
    'REVOKE',
    'INDEX',
)) + ')')


def is_sql_or_ddl_statement(query):
    """Check if sql query is a SELECT statement"""
    return not RE_SELECT_QUERY.match(query.upper())


class PartnerTermCalculation(models.Model):
    _name = 'partner.term.calculation'
    description = 'Partner Term calculation'

    name = fields.Char('Name', required=True)
    calculation_type = fields.Selection((
        ('python', 'Python'),
        ('local', 'SQL - Local DB'),
        ('external', 'SQL - External DB')
    ), 'Computation Type', default='python', required=True)

    create_type = fields.Selection((
        ('credit_note', 'Credit Note'),
        ('vendor_bill', 'Vendor Bill'),
        ('journal', 'Journal'),
    ), 'Create', default='credit_note', required=True)

    computation_code = fields.Text(
        'Computation Code',
        help=("SQL code must return the result as 'value' "
              "(i.e. 'SELECT 5 AS value')."),
    )
    history_invoice_ids = fields.One2many(
        'account.invoice',
        'term_id',
        'History',
    )
    active = fields.Boolean('Active', default=True)
    partner_term_journal_id = fields.Many2one('account.journal', string='Journal', required=True)
    term_calculation_type = fields.Selection([
        ('on_invoice', 'On Invoice'),
        ('automatic', 'Automatic'),
    ], default='on_invoice', required=True)
    automatic_calculation_type = fields.Selection([
        ('daily','Daily'),
        ('weekly','Weakly'),
        ('monthly','Monthly'),
        ('quarterly','Quarterly'),
        ('half_yearly','Half-Yearly'),
        ('annually','Annually'),
    ], default='annually', required=True)
    partner_term_product_id = fields.Many2one('product.product', string='Associated Product', required=True,
                                              domain=[('is_term_product', '=', True)])
    debit_account_id = fields.Many2one('account.account', string='Debit Account')
    credit_account_id = fields.Many2one('account.account', string='Credit Account')
    periodic_terms = fields.Boolean(string='Periodic Invoices')
    frequency = fields.Selection([
        ('only_once','Only Once'),
        ('periodic','Periodic'),
                 ])
 

    @api.multi
    def _get_term_value(self, partner=False, invoice=False):
        self.ensure_one()
        calculation_value = 0
        if self.computation_code:
            if self.calculation_type == 'local' and is_sql_or_ddl_statement(
                    self.computation_code):
                self.env.cr.execute(self.computation_code)
                dic = self.env.cr.dictfetchall()
                if is_one_value(dic):
                    calculation_value = dic[0]['value']
            elif (self.calculation_type == 'external' and self.dbsource_id.id and
                  is_sql_or_ddl_statement(self.computation_code)):
                dbsrc_obj = self.dbsource_id
                res = dbsrc_obj.execute(self.computation_code)
                if is_one_value(res):
                    calculation_value = res[0]['value']
            elif self.calculation_type == 'python':
                calculation_value = safe_eval(self.computation_code,
                                              {'self': self, 'partner': partner, 'invoice': invoice})
                self.value = calculation_value
        return calculation_value

    # @api.onchange('term_calculation_type')
    # def onchange_term_calculation(self):
    #     if self.term_calculation_type == 'on_invoice'