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
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, AccessError, ValidationError
#from duplicity.tempdir import default

_logger = logging.getLogger(__name__)


class advance_category(models.Model):
    _name = "advance.category"
    _description = "Advance Category"
    
    name = fields.Char('Name', required=True)
    type = fields.Selection([('fixed', 'Fixed'), ('variable', 'Variable')], string='Type', default='fixed', required=True)
    amount_percentage = fields.Float('Salary(%)')
    maximum_amount = fields.Float('Amount')
    months = fields.Float('No. of Months', default=1.0)
    repayment_period = fields.Float('Deduction Period', required=True, default=6.0)
    
    
class advance_request_form(models.Model):
    _name = "advance.request.form"
    _description = "Hr Advance Request"
    _inherit = ['mail.thread', 'ir.model.role', 'common.clarify']
    _order = 'date desc, id desc'
    _rec_name = 'employee_id'    
    _employee_id = 'employee_id' 
            
    @api.multi
    def _compute_current_emp(self):         
        uid = self._uid
        user = self.env.user        
        for record in self:
            current_emp = self.env['hr.employee'].search([('user_id', '=', uid)], limit=1)
            record.current_emp_id = current_emp and current_emp.id or False
    
    @api.multi
    def _get_attached_docs(self):        
        attachment = self.env['ir.attachment']
        for rec in self:
            request_attachments = attachment.search_count([('res_model', '=', 'advance.request.form'), ('res_id', '=', rec.id)])
            rec.doc_count = request_attachments or 0
    
    @api.model
    def _default_employee(self):
        return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    
    @api.multi
    @api.depends('deduction_lines', 'deduction_lines.amount')
    def _amount_all_wrapper(self):         
        for record in self:
            amount_total = 0.0
            for line in record.deduction_lines:
                amount_total += line.amount
            record.amount_total = amount_total
    
    @api.multi
    @api.depends('amount', 'repayment_period', 'amount_required')
    def _calculate_deduction_per_month(self):         
        for record in self:
            repayment_per_month = record.amount_required
            if record.repayment_period and record.amount_required > 0:
                repayment_per_month = record.amount_required / record.repayment_period
            record.repayment_per_month = repayment_per_month
            
    @api.multi
    @api.depends('amount_required', 'currency_id')
    def _amount_word(self):         
        for record in self:
            amount_word = ''
            if record.amount_required:
                currency = record.currency_id or self.env.user.company_id.currency_id
                amount_word = currency.amount_to_text(record.amount_required)
            record.amount_word = amount_word
    
    @api.multi
    @api.depends('amount_required', 'deduction_amount')
    def _calculate_due_amount(self):
        for rec in self: 
            due_balance = rec.amount_required - rec.deduction_amount
            rec.due_balance = due_balance            
            
    @api.multi
    @api.depends('employee_id', 'employee_id.contract_ids')
    def _compute_current_contract(self):         
        for record in self:
            contract_id = False
            if record.employee_id and record.employee_id.contract_id:
                contract_id = record.employee_id.contract_id.id
            record.contract_id = contract_id
        
    state = fields.Selection([
                            ('draft', 'Draft'),
                            ('refuse', 'Refused'),
                            ('clarify', 'Clarification'),
                            ('confirm', 'Confirmed'),
                            ('verify', 'Verified'),
                            ('approve', 'Approved'),
                            ('paid', 'Paid'),
                            ('deduct', 'Deducted')
                            ], string='Status', required=True, readonly=True, copy=False,
                            default='draft', track_visibility='onchange')    
    name = fields.Char(string='Name', readonly=True, states={'draft': [('readonly', False)]})
    employee_id = fields.Many2one('hr.employee', 'Employee', required=True, default=_default_employee, readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one('hr.contract', string='Current Contract', compute='_compute_current_contract', store=True)
    amount = fields.Float('Total Monthly Salary', readonly=True, states={'draft': [('readonly', False)]})
    eligible_amount = fields.Float('Eligible Amount', readonly=True, states={'draft': [('readonly', False)]})
    amount_required = fields.Float('Amount Required', required=True, readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Date', default=fields.Date.context_today, readonly=True, states={'draft': [('readonly', False)]})
    advance_category_id = fields.Many2one('advance.category', 'Type', required=True, readonly=True, states={'draft': [('readonly', False)]})
    reason = fields.Text('Reason', readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id, readonly=True, states={'draft': [('readonly', False)]})
    advance_count = fields.Integer(compute='_count_all', string='Cons Picking List')
    paid_by_payslip = fields.Boolean('Paid', readonly=True, states={'draft': [('readonly', False)]})
    repayment_period = fields.Float('Deduction Period', readonly=True, states={'draft': [('readonly', False)]})
    repayment_per_month = fields.Float(compute='_calculate_deduction_per_month', string='Monthly Deduction Amount')
    deduction_amount = fields.Float('Amount Deducted', readonly=True, states={'draft': [('readonly', False)]})
    due_balance = fields.Float(compute='_calculate_due_amount', string='Due Amount')
    on_hold = fields.Boolean('Hold?', readonly=True, states={'draft': [('readonly', False)]})
    deduction_lines = fields.One2many('advance.deduction.line', 'advance_id', 'Lines', readonly=True, states={'draft': [('readonly', False)]})
    amount_total = fields.Float(compute='_amount_all_wrapper', string='Total')
    
    amount_word = fields.Char(compute='_amount_word', string='Amount word')
    payment_done = fields.Boolean('Payment Done', readonly=True, states={'draft': [('readonly', False)]})
    payment_type = fields.Selection([('cash', 'Cash'), ('bank', 'Bank'), ('payslip', 'Payroll'), ('others', 'Others')], 'Payment Type', default='payslip', readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Text('Description', readonly=True, states={'draft': [('readonly', False)]})
    doc_count = fields.Integer(compute='_get_attached_docs', string="Number of documents attached")
    current_emp_id = fields.Many2one("hr.employee", string="Current Employee", compute="_compute_current_emp")
    
    @api.multi
    def _track_subtype(self, init_values):
        if 'state' in init_values and self.state == 'approve':
            return 'cw_hr_advance.mt_advance_request_approved'
        elif 'state' in init_values and self.state == 'verify':
            return 'cw_hr_advance.mt_advance_request_verified'
        elif 'state' in init_values and self.state == 'confirm':
            return 'cw_hr_advance.mt_advance_request_confirmed'
        elif 'state' in init_values and self.state == 'refuse':
            return 'cw_hr_advance.mt_advance_request_refused'
        return super(advance_request_form, self)._track_subtype(init_values)

    @api.model
    def create(self, vals):        
        employee_id = vals.get('employee_id', False)
        if employee_id:
            existing_ids = self.search([('employee_id', '=', employee_id), ('state', '=', 'approved')])
            if existing_ids:
                raise ValidationError(_('This employee already have pending advances.'))
        res = super(advance_request_form, self).create(vals)
        res.rec_add_followers(employee_ids=[employee_id],
                                            extend_groups=['hr.group_hr_user', 'hr.group_hr_manager'])
        return res
    
    @api.multi
    def unlink(self):
        for item in self:
            if item.state != 'draft':
                raise ValidationError(_('You can only delete draft advance request.'))
        res = super(advance_request_form, self).unlink()
        return res
    
    @api.model
    def _needaction_domain_get(self):
        return ['|',
                '|',
                '|',
                '|',
                '&', ('is_an_employee', '=', True), ('state', 'in', ['draft', 'clarify']),
                '&', ('is_a_hr_user', '=', True), ('state', '=', 'confirm'),
                '&', ('is_a_hr_manager', '=', True), ('state', '=', 'verify'),
                '&', '&', ('is_an_employee', '=', True), ('state', '=', 'approve'), ('rec_msg_read', '=', True),
                '&', '&', ('is_an_employee', '=', True), ('state', '=', 'refuse'), ('rec_msg_read', '=', True)]
    
    @api.multi
    def attachment_tree_view(self):       
        self.ensure_one()
        res_id = self.ids and self.ids[0] or False
        domain = [('res_model', '=', 'advance.request.form'), ('res_id', '=', res_id)]
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % ('advance.request.form', res_id)
        }

    @api.onchange('advance_category_id')
    def onchange_advance_category_id(self):
        advance_category_id = self.advance_category_id
        employee_id = self.employee_id
        amount_required = 0.0
        eligible_amount = 0.0
        repayment_period = 1.0
        wage = 0.0
        if employee_id and employee_id.contract_id:
            current_contract = employee_id.contract_id
            wage = current_contract.wage or 0.0
        if advance_category_id:
            advance_category = self.env['advance.category'].browse(advance_category_id.id)
            type, months, amount, repayment_period = False, 0.0, 0.0, 0.0
            if advance_category and advance_category.type:
                type = advance_category.type
                months = advance_category.months or 1.0
                repayment_period = advance_category.repayment_period or 1.0
                if type == 'fixed':
                    eligible_amount = advance_category.maximum_amount
                if type == 'variable':
                    percentage = advance_category.amount_percentage or 100.0
                    eligible_amount = (wage / 100) * percentage * months 
        self.amount = wage
        self.amount_required = eligible_amount
        self.eligible_amount = eligible_amount
        self.repayment_period = repayment_period

    @api.onchange('employee_id')
    def onchange_employee_id(self):
        # employee_id = self.employee_id
        # employee_obj = self.env['hr.employee']
        # contract_obj = self.env['hr.contract']
        # if employee_id and employee_id.contract_id:
        #    current_contract = employee_id.contract_id
        #    self.amount = current_contract and current_contract.wage or 0.0
        #    self.eligible_amount = current_contract and ((current_contract.wage / 2) * employee_id.grade_id.sly_ded_mon) or 0.0
        self.onchange_advance_category_id()
        
    #@api.onchange('payment_type')
    #def onchange_payment_type(self):
    #    payment_type = self.payment_type
    
    @api.multi
    def action_confirm(self):
        for record in self:
            # if record.repayment_period > 6:
            #    raise ValidationError(_('Deduction Period Should be less then 7 months'))
            if record.repayment_period < 1:
                raise ValidationError(_('Please Enter the deduction period'))
            if record.amount_required < 1:
                raise ValidationError(_('Please Enter the Required Amount'))
            if record.amount_required > record.eligible_amount:
                raise ValidationError(_('Please Enter your Required Amount Less then or  Equal to Your Eligible Amount'))
            record.write({'state':'confirm'})
        return True
    
    @api.multi
    def action_verify(self):
        self.write({'state':'verify'})
        return True
    
    @api.multi
    def action_approve(self):        
        approve_template = self.env.ref('cw_hr_advance.email_template_salary_advance_approve_notifications', False)
        for record in self:
            record.write({'state': 'approve'})
            #approve_template.send_mail(record.id, force_send=True)       
        return True    
    
    @api.multi
    def action_refuse(self):
        refuse_template = self.env.ref('cw_hr_advance.email_template_salary_advance_refuse_notifications', False)
        for record in self:
            record.write({'state': 'refuse'}) 
            #refuse_template.send_mail(record.id, force_send=True)
        return True
    
    @api.multi
    def action_release_payment(self):        
        for record in self:
            record.employee_id.write({'salary_advance_received':record.employee_id.salary_advance_received + record.amount_required})
            record.write({'payment_done': True, 'state': 'paid'})
        return True
    
    

    @api.multi
    def action_set_to_draft(self):
        self.write({'state': 'draft'})
        return True    

    @api.model
    def default_get(self, fields):
        rec = super(advance_request_form, self).default_get(fields)
        employee_obj = self.env['hr.employee']
        contract_obj = self.env['hr.contract']
        advance_cate_obj = self.env['advance.category']
        advance_category = advance_cate_obj.search([], limit=1, order='id desc')
        uid = self._uid
        # To Do: Implement grade system
        # if uid:
        #    for emp in employee_obj.search([('user_id','=',uid)]):
        #        if emp.contract_id:
        #            ded_period = 6
        #            rec['employee_id'] = emp.id
        #            if emp.contract_id.net_wage:
        #                rec['amount'] = emp.contract_id.net_wage
        #            if emp.grade_id and emp.grade_id.sly_ded_mon:
        #                rec['eligible_amount'] =  (contract_bro.net_wage / 2) * emp.grade_id.sly_ded_mon
        #                ded_period = emp.grade_id.sly_ded_mon
        #            rec['repayment_period'] = ded_period
        rec['advance_category_id'] = advance_category and advance_category.id or False
        return rec


class advance_deduction_line(models.Model):
    _name = "advance.deduction.line"
    
    advance_id = fields.Many2one('advance.request.form', 'Advance')
    date_from = fields.Date('From')
    date_to = fields.Date('To')
    amount = fields.Float('Amount')
    payslip_id = fields.Many2one('hr.payslip', 'Payslip')
    
    
class hr_employee(models.Model):
    _inherit = "hr.employee"
    
    @api.multi
    @api.depends('salary_advance_received', 'salary_advance_paid')
    def _calculate_due_amount(self):         
        for record in self:
            salary_advance_balance = record.salary_advance_received - record.salary_advance_paid
            record.salary_advance_balance = salary_advance_balance
            
    advance_request_lines = fields.One2many('advance.request.form', 'employee_id', 'Advance Requests')
    salary_advance_received = fields.Float('Salary Advance Received')
    salary_advance_paid = fields.Float('Salary Advance Paid')
    salary_advance_balance = fields.Float(compute='_calculate_due_amount', string='Salary Advance Balance')

    
class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
        
    @api.model
    def get_inputs(self, contract_ids, date_from, date_to):
        result = super(HrPayslip, self).get_inputs(contract_ids, date_from, date_to)
        d_date_from = datetime.strptime(date_from, DEFAULT_SERVER_DATE_FORMAT)
        d_date_to = datetime.strptime(date_to, DEFAULT_SERVER_DATE_FORMAT)
        d_date_from = d_date_from + relativedelta(months=-1)
        d_date_from = d_date_from.replace(day=15)
        d_date_to = d_date_to.replace(day=16)
        s_dt_date_from = d_date_from.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        s_dt_date_to = d_date_to.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        s_date_tos_date_from = d_date_from.strftime(DEFAULT_SERVER_DATE_FORMAT)
        s_date_to = d_date_to.strftime(DEFAULT_SERVER_DATE_FORMAT)  
        contracts = self.env['hr.contract'].browse(contract_ids)                      
        for contract in contracts:
            employee_id = contract.employee_id and contract.employee_id.id or False
            if employee_id:
                advance_requests = self.env['advance.request.form'].search([
                                                    ('employee_id', '=', employee_id),
                                                    ('contract_id', '=', contract.id),
                                                    ('payment_done', '=', False),
                                                    ('payment_type', '=', 'payslip'),
                                                    ('state', '=', 'approve'),
                                                    ('date', '<', s_date_to)
                                                    ])
                advance_deductions = self.env['advance.request.form'].search([
                                                    ('employee_id', '=', employee_id),
                                                    ('contract_id', '=', contract.id),
                                                    ('payment_done', '=', True),
                                                    ('payment_type', '=', 'payslip'),
                                                    ('state', '=', 'paid')
                                                    ])
                for advance_request in advance_requests:
                    amount = advance_request.amount_required
                    advance_pay = {
                         'name': _("Advance Payment"),
                         'sequence': 3,
                         'code': 'ADVANCEPAY100',
                         'advance_id': advance_request.id,
                         'amount': advance_request.amount_required,
                         'contract_id': contract.id,
                    }
                    result.append(advance_pay)
                for advance_deduction in advance_deductions:
                    print ("advance_deduction.due_balance",advance_deduction.due_balance)
                    if advance_deduction.due_balance > 0:
                        ded_advance_pay = {
                         'name': _("Advance Deduction"),
                         'sequence': 3,
                         'code': 'ADVANCEDED100',
                         'advance_id': advance_deduction.id,
                         'amount': advance_deduction.repayment_per_month,
                         'contract_id': contract.id,
                            }
                        result.append(ded_advance_pay)
        return result
    
    @api.multi
    def action_payslip_done(self):
        result = super(HrPayslip, self).action_payslip_done()
        for payslip in self:
            # for worked_days_line in payslip.worked_days_line_ids:
            #    pass
            for input_line in payslip.input_line_ids:
                if input_line.code == 'ADVANCEPAY100':                   
                    payslip.employee_id.write({'salary_advance_received':input_line.advance_id.employee_id.salary_advance_received + input_line.advance_id.amount_required})
                    input_line.advance_id.write({'payment_done': True, 'state': 'paid'})
                if input_line.code == 'ADVANCEDED100':
                    deduction_val = {
                                'advance_id': input_line.advance_id.id,
                                'date_from': payslip.date_from,
                                'date_to': payslip.date_to,
                                'payslip_id': payslip.id,
                                'amount': input_line.amount
                                }
                    self.env['advance.deduction.line'].create(deduction_val)
                    input_line.advance_id.write({'deduction_amount': (input_line.advance_id.deduction_amount + input_line.amount)})
                    payslip.employee_id.write({'salary_advance_paid': (payslip.employee_id.salary_advance_paid + input_line.amount)})
                    if input_line.advance_id.due_balance <= 0:
                        input_line.advance_id.write({'state': 'deduct'})                    
        # self.write({'paid': True, 'state': 'done'})
        return result

    
class hr_payslip_input(models.Model):
    _inherit = 'hr.payslip.input'
        
    advance_id = fields.Many2one('advance.request.form', 'Hr Advance Request')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
