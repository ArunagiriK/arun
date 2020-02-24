# -*- coding: utf-8 -*-

import logging
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR, SA, SU

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError

_logger = logging.getLogger(__name__)


class HrGratutity(models.Model):
    _name = "hr.gratutity"
    _inherit = ['mail.thread', 'ir.model.role', 'common.clarify']
    _order = "id desc"
    _rec_name = "employee_id"
    _employee_id = 'employee_id'
    
    @api.multi
    def compute_settlement(self):
        slip_pool = self.env['hr.payslip']
        gratuity_pool = self.env['hr.gratuity.rule']       
        codes = ['BASIC', 'TA', 'OTH', 'HRA', ]
        payment_line = self.env['hr.gratutity.line']
        for record in self:            
            if record.payment_lines:
                for line in record.payment_lines:
                    line.unlink()                    
            if not record.payment_lines:
                from_d = datetime.strptime(record.date_from, "%Y-%m-%d").date() 
                to_d = datetime.strptime(record.date_to, "%Y-%m-%d").date() 
                num_of_days = (to_d - from_d).days
                from_date = record.date_from
                to_date = record.date_to
                emp = record.employee_id
                advance_amount = 0.0
                slip_data = slip_pool.onchange_employee_id(date_from=from_date, date_to=to_date, employee_id=emp.id, contract_id=False)
                res = {
                    'employee_id': emp.id,
                    'name': slip_data['value'].get('name', False),
                    'struct_id': slip_data['value'].get('struct_id', False),
                    'contract_id': slip_data['value'].get('contract_id', False),
                    # CHANGED Abitha 'payslip_run_id': context.get('active_id', False),
                    'payslip_run_id': slip_data['value'].get('active_id', False),
                    'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                    'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                    'date_from': from_date,
                    'date_to': to_date,
                    'credit_note': False,
                }
                slip_id = slip_pool.create(res)
                slip_id.compute_sheet()            
                # payslip created here
                for line in slip_id.line_ids:
                    if not line.code in ['GROSS', 'NET', 'ADVANCEPAY100', 'ADVANCEDED100']:
                        if line.code in codes:
                            one_day_amount = line.total / 30
                            amount = one_day_amount * num_of_days
                        else:
                            amount = line.total
                        vals = {
                            'name': line.name,
                            'code': line.code,
                            'total': amount,
                            'settlement_id': record.id
                                }
                        payment_line.create(vals)
                slip_id.unlink()                
                advance_deductions = self.env['advance.request.form'].search([('employee_id', '=', emp.id),
                                                    ('payment_done', '=', True),
                                                    ('state', '=', 'paid')])
                for advance_deduction in advance_deductions:
                    if advance_deduction.due_balance > 0:                        
                        vals = {
                            'name': _("Advance Deduction Balance"),
                            'code': 'ADVANCEDED100',
                            'total': advance_deduction.due_balance,
                            'advance_id': advance_deduction.id,
                            'settlement_id': record.id
                        }
                        payment_line.create(vals)
                if emp.contract_id:
                    contract = emp.contract_id
                    wage = contract.wage
                    print("wage...", wage)
                    # to be done later remaining_leaves = emp.cw_annual_remaining_leaves
                    remaining_leaves = 0
                    per_day = wage / 30
                    print ("per_day", per_day)
                    vals = {
                            'name': 'LEAVE SALARY',
                            'code': 'LEAVE SALARY',
                            'total': per_day * remaining_leaves,
                            'settlement_id': record.id
                                }
                    # payment_line.create(vals)
                    # calculate Gratuity
                    join_date = emp.join_date
                    join_d = datetime.strptime(str(join_date), "%Y-%m-%d").date()
                    num_of_years = relativedelta(to_d, join_d).years
                    num_of_months = relativedelta(to_d, join_d).months
                    gratuity = 0.0
                    mgratuity = 0.0
                    exp_years = range(1, num_of_years + 1)
                    for num_year in exp_years:
                        gratuity_rule = record.gratuity_rule_id.line_ids.filtered(lambda r: num_year >= r.year_from and num_year <= r.year_to)
                        if not gratuity_rule:
                            gratuity_rule = record.gratuity_rule_id.line_ids.filtered(lambda r: r.year_to == 0.0)
                        if gratuity_rule:
                            yearly_gratuity = (wage / 30) * gratuity_rule.days
                            gratuity += yearly_gratuity
                            if num_of_months and \
                                ((num_of_years >= gratuity_rule.year_from) and \
                                 (num_of_years <= gratuity_rule.year_to or gratuity_rule.year_to == 0.0)):
                                mgratuity = (wage / 30) * (gratuity_rule.days / 12) * num_of_months
                        else:
                            raise ValidationError(_('Error in Gratuity rule definition.'))
                    gratuity += mgratuity
                    vals = {
                                'name': 'Gratuity',
                                'code': 'GRATUITY',
                                'total': gratuity,
                                'settlement_id': record.id
                                    }
                    payment_line.create(vals)
        return True
    
    @api.multi
    def hr_confirm_settlement(self):
        for record in self:
            record.write({'state': 'confirm'})
        return True
    
    @api.multi
    def hr_validate_settlement(self):
        for record in self:            
            for payment_line in record.payment_lines:
                if payment_line.code == 'ADVANCEDED100':
                    deduction_val = {
                                'advance_id': payment_line.advance_id.id,
                                'date_from': record.date_from,
                                'date_to': record.date_to,
                                'amount': payment_line.total
                                }
                    self.env['advance.deduction.line'].create(deduction_val)
                    payment_line.advance_id.write({'deduction_amount': (payment_line.advance_id.deduction_amount + payment_line.total)})
                    record.employee_id.write({'salary_advance_paid': (record.employee_id.salary_advance_paid + payment_line.total)})
                    if payment_line.advance_id.due_balance <= 0:
                        payment_line.advance_id.write({'state': 'deduct'}) 
            if record.employee_id.type == 'relieved':
                record.employee_id.relived()
            elif record.employee_id.type == 'terminate':
                record.employee_id.terminate()
            else:
                record.employee_id.in_active_emp()
            record.write({'state': 'validate'})
        return True   
    
    @api.multi
    def action_refuse(self):
        for record in self:
            # To do reset all
            record.write({'state': 'refuse'}) 
        return True
    
    @api.multi
    def action_set_to_draft(self):
        self.write({'state': 'draft'})
        return True 
    
    @api.multi
    @api.depends('payment_lines',
                 'payment_lines.total')
    def _amount_all_wrapper(self):        
        for record in self:
            amount_total = 0.0
            for line in record.payment_lines:
                amount_total += line.total
            record.update({
                'amount_total': amount_total,
            })
            
    name = fields.Char(string='Name', required=True, readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True, states={'draft': [('readonly', False)]})
    type = fields.Selection([('relieved', 'Resigned'), ('terminate', 'Terminated')], string='Type', default='relieved', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date_from = fields.Date(string='From', default=time.strftime('%Y-%m-01'), readonly=True, states={'draft': [('readonly', False)]})
    # date_to = fields.Date(string='To', default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    date_to = fields.Date(string='To', default=str(datetime.now() + relativedelta(months=+1, day=1, days=-1))[:10], readonly=True, states={'draft': [('readonly', False)]})
    gratuity_rule_id = fields.Many2one('hr.gratuity.rule', string='Gratuity', required=True, readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('validate', 'Validated')], string='Status', default='draft')
    payment_lines = fields.One2many('hr.gratutity.line', 'settlement_id', string='Lines', readonly=True, states={'draft': [('readonly', False)]})    
    amount_total = fields.Float(compute='_amount_all_wrapper', string='Total')
    
    
class HrGratutityLine(models.Model):
    _name = "hr.gratutity.line"
    _order = "id desc"
    
    name = fields.Char('Name')
    code = fields.Char('Code')
    total = fields.Float('Total')
    advance_id = fields.Many2one('advance.request.form', 'Hr Advance Request')
    settlement_id = fields.Many2one('hr.gratutity', string='Settlement', required=True, ondelete='cascade')
    
    
class gratuity_rule(models.Model):
    _name = "hr.gratuity.rule"
    
    name = fields.Char('Name', required=True)
    line_ids = fields.One2many('hr.gratuity.rule.line', 'rule_id', 'Gratuity Line', required=True)
    
    
class gratuity_rule_line(models.Model):
    _name = "hr.gratuity.rule.line"
    _order = "sequence asc"
    
    @api.one
    @api.constrains('year_from', 'year_to')
    def _year_check(self):
        year_from = float(self.year_from)
        year_to = float(self.year_to)
        if year_to != 0.0 and year_from > year_to:
            raise ValidationError(_('The year to must be greater than year from.'))
    
    rule_id = fields.Many2one('hr.gratuity.rule', 'Gratuity Rule', required=True, ondelete='cascade')
    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True)
    sequence = fields.Integer('Sequence', required=True, default=10)
    year_from = fields.Float('Year From', required=True, default=0.0)
    year_to = fields.Float('Year To', default=0.0)
    days = fields.Float('Days', required=True, default=0.0)
    
