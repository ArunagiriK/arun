# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, RedirectWarning


class AccountFiscalYear(models.Model):

    _name = 'account.fiscalyear'
    _description = 'Account FiscalYear'
    _order = 'date_start, id'

    name = fields.Char(string='Fiscal Year')
    code = fields.Char(string='Code', size=6)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id.id)
    date_start = fields.Date(string='Start Date')
    date_stop = fields.Date(string='End Date')
    period_ids = fields.One2many('account.period', 'fiscalyear_id', 'Periods')
    state = fields.Selection(
        [('draft', 'Open'), ('done', 'Closed')], string='Status',
        readonly=True, copy=False, default='draft')

    @api.multi
    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_stop:
                if record.date_start > record.date_stop:
                    raise ValidationError(
                        _('The start date of a fiscal year must precede its '
                          'end date.'))

    @api.multi
    def create_period(self):
        context = dict(self._context) or {}
        interval = context.get('interval', 1)
        period_obj = self.env['account.period']
        for fy in self:
            ds = datetime.strptime(str(fy.date_start), '%Y-%m-%d')
            while ds.strftime('%Y-%m-%d') < str(fy.date_stop):
                de = ds + relativedelta(months=interval, days=-1)
                if de.strftime('%Y-%m-%d') > str(fy.date_stop):
                    de = datetime.strptime(fy.date_stop, '%Y-%m-%d')
                period_obj.create({
                    'name': ds.strftime('%m/%Y'),
                    'code': ds.strftime('%m/%Y'),
                    'date_start': ds.strftime('%Y-%m-%d'),
                    'date_stop': de.strftime('%Y-%m-%d'),
                    'fiscalyear_id': fy.id,
                })
                ds = ds + relativedelta(months=interval)
        return True

    @api.multi
    def find(self, dt=None, exception=True, context=None):
        res = self.finds(dt, exception)
        return res and res[0] or False

    @api.multi
    def finds(self, dt=None, exception=True):
        if not dt:
            dt = fields.Date.context_today(self)
        args = [('date_start', '<=', dt), ('date_stop', '>=', dt)]
        if self.env.context.get('company_id', False):
            company_id = self.env.context['company_id']
        else:
            company_id = self.env.user.company_id.id
        args.append(('company_id', '=', company_id))
        ids = self.search(args)
        if not ids:
            if exception:
                action_id = self.env.ref(
                    'accoun_fiscalyear.action_account_fiscalyear')
                msg = (_(
                    'There is no period defined for this date: %s.\nPlease go '
                    'to configuration/periods and configure a fiscal year.')
                    % dt)
                raise RedirectWarning(
                    msg, action_id, _('Go to the configuration panel'))
            else:
                return []
        return ids

#     @api.multi
#     def name_get(self):
#         result = []
#         for fy in self:
#             name = fy.company_id.code and (
#                 fy.company_id.code + ' - ' + fy.name) or fy.name
#             result.append((fy.id, name))
#         return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('code', operator, name), ('name', operator, name)]
        else:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        recs = self.search(expression.AND([domain, args]), limit=limit)
        return recs.name_get()


class AccountPeriod(models.Model):

    _name = "account.period"
    _description = "Account period"
    _order = "date_start"

    name = fields.Char(string='Period Name')
    code = fields.Char(string='Code', size=12)
    date_start = fields.Date(string='Start of Period', states={
                             'done': [('readonly', True)]})
    date_stop = fields.Date(string='End of Period', states={
                            'done': [('readonly', True)]})
    fiscalyear_id = fields.Many2one('account.fiscalyear', string='Fiscal Year',
                                    ondelete='cascade',
                                    states={'done': [('readonly', True)]})
    state = fields.Selection(
        [('draft', 'Open'), ('done', 'Closed')], string='Status',
        readonly=True, copy=False, default='draft',
        help='When monthly periods are created. '
        'The status is \'Draft\'. At the end of monthly period it is '
        'in \'Done\' status.')
    company_id = fields.Many2one(
        related="fiscalyear_id.company_id", string='Company', store=True,
        readonly=True)

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)',
         'The name of the period must be unique per company!')]

    @api.multi
    @api.constrains('date_start', 'date_stop')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_stop:
                if record.date_start > record.date_stop:
                    raise ValidationError(
                        _('Error!\nThe duration of the period(s) '
                          'is/are invalid.'))
                if record.fiscalyear_id.date_stop < record.date_stop or \
                        record.fiscalyear_id.date_stop < record.date_start or \
                        record.fiscalyear_id.date_start > \
                        record.date_start or \
                        record.fiscalyear_id.date_start > record.date_stop:
                    raise ValidationError(
                        _('Error!\nThe period is invalid. Either some periods'
                          'are overlapping or the period\'s dates are not '
                          'matching the scope of the fiscal year.'))
                period_ids = self.search([
                    ('date_stop', '>=', record.date_start),
                    ('date_start', '<=', record.date_stop),
                    ('id', '<>', record.id)])
                for period in period_ids:
                    if period.fiscalyear_id.company_id.id ==\
                            record.fiscalyear_id.company_id.id:
                        raise ValidationError(
                            _('Error!\nThe period is invalid. '
                              'Either some periods are overlapping or the '
                              'period\'s dates are not matching the scope '
                              'of the fiscal year.'))

    @api.multi
    def find(self, dt=None):
        if not dt:
            dt = fields.Date.context_today(self)
        args = [('date_start', '<=', dt), ('date_stop', '>=', dt)]
        if self.env.context.get('company_id', False):
            args.append(('company_id', '=', self.env.context['company_id']))
        else:
            company_id = self.env.user.company_id.id
            args.append(('company_id', '=', company_id))
        result = []
        if not result:
            result = self.search(args)
        if not result:
            action_id = self.env.ref(
                'account_fiscalyear.action_account_period')
            msg = _(
                'There is no period defined for this date: %s.'
                '\nPlease go to Configuration/Periods.') % dt
            raise RedirectWarning(
                msg, action_id, _('Go to the configuration panel'))
        return result

    @api.multi
    def action_draft(self):
        mode = 'draft'
        for period in self:
            fy_id = period.fiscalyear_id
            period_recs = self.search([('date_stop', '<', period.date_stop),
                                       ('state', '=', 'draft'),
                                       ('fiscalyear_id', '=', fy_id.id)],
                                      limit=1)
            self._cr.execute(
                'update account_period set state=%s where id = %s',
                (mode, period.id))
            if not period_recs:
                period.company_id.period_lock_date =\
                    period.company_id.fiscalyear_lock_date = period.date_stop
            else:
                date_stop = datetime.strptime(
                    period_recs.date_start, DEFAULT_SERVER_DATE_FORMAT)
                lock_date = (date_stop + relativedelta(days=-1)).\
                    strftime('%Y-%m-%d')
                period.company_id.period_lock_date = \
                    period.company_id.fiscalyear_lock_date = lock_date
            self.invalidate_cache()
        return True

#     @api.multi
#     def name_get(self):
#         result = []
#         for period in self:
#             name = period.company_id.code and (
#                 period.company_id.code + ' - ' + period.name) or period.name
#             result.append((period.id, name))
#         return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        if args is None:
            args = []
        if operator in expression.NEGATIVE_TERM_OPERATORS:
            domain = [('code', operator, name), ('name', operator, name)]
        else:
            domain = ['|', ('code', operator, name), ('name', operator, name)]
        recs = self.search(expression.AND([domain, args]), limit=limit)
        return recs.name_get()
