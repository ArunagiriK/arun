# -*- coding: utf-8 -*-

import base64
import operator
import re

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.modules import get_module_resource
from odoo.tools.safe_eval import safe_eval
from odoo import SUPERUSER_ID

class IrModelRole(models.AbstractModel):
    _name = 'ir.model.role'   
    
    _employee_id = False
    _user_id = False
    
    def _get_employee_field(self):
        employee_id = self.sudo(SUPERUSER_ID).read([self._employee_id])
        employee_model = self.sudo(SUPERUSER_ID).fields_get(allfields=[self._employee_id])
        if employee_id and employee_model:
            employee_value = employee_id[0][self._employee_id]
            employee_id = employee_value and employee_value[0] or False
            employee_model = employee_model[self._employee_id]['relation']
            employee_id = self.env[employee_model].sudo(SUPERUSER_ID).browse(employee_id)
        else:
            employee_id = False
        return employee_id
    
    def _check_employee_field(self):
        employee_field = self.sudo(SUPERUSER_ID).fields_get(allfields=[self._employee_id])
        if employee_field:
            employee_field = employee_field[self._employee_id]
        else:
            employee_field = False
        return employee_field
    
    def _get_user_field(self):
        user_id = self.sudo(SUPERUSER_ID).read([self._user_id])
        user_model = self.sudo(SUPERUSER_ID).fields_get(allfields=[self._user_id])
        if user_id and user_model:
            user_value = user_id[0][self._user_id]
            user_id = user_value and user_value[0] or False
            user_model = user_model[self._user_id]['relation']
            user_id = self.env[user_model].sudo(SUPERUSER_ID).browse(user_id)
        else:
            user_id = False
        return user_id
    
    def _check_user_field(self):
        user_field = self.sudo(SUPERUSER_ID).fields_get(allfields=[self._user_id])
        if user_field:
            user_field = user_field[self._user_id]
        else:
            user_field = False
        return user_field
        
    @api.one
    def _compute_roles(self):
        #self.comp_employee_record = self.env['hr.employee']
        self.comp_employee_record = False
        self.rec_current_user = False  
        self.is_an_employee = False      
        self.is_a_coach = False
        self.is_a_manager = False
        self.is_a_dep_manager = False
        self.is_a_acc_manager = False
        self.is_a_hr_user = False
        self.is_a_hr_manager = False
        uid = self._uid
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        employee_id = self._get_employee_field()
        if employee_id:
            self.comp_employee_record = employee_id
            if (self.env.user.has_group('base.group_user') and \
                employee_id and employee_id.user_id and \
                employee_id.user_id.id == uid) or is_admin:
                #set is an employee
                self.is_an_employee = True
            if (self.env.user.has_group('cw_hr_extended.group_emp_coach') and \
                employee_id and employee_id.coach_id and \
                employee_id.coach_id.user_id and \
                employee_id.coach_id.user_id.id == uid) or is_admin:
                #set is a supervisor
                self.is_a_coach = True
            if (self.env.user.has_group('cw_hr_extended.group_emp_manager') and \
                employee_id and employee_id.parent_id and \
                employee_id.parent_id.user_id and \
                employee_id.parent_id.user_id.id == uid) or is_admin:
                #set is a manager
                self.is_a_manager = True
            if (self.env.user.has_group('cw_hr_extended.group_dep_manager') and \
                employee_id and employee_id.department_id and \
                employee_id.department_id.manager_id and \
                employee_id.department_id.manager_id.user_id and \
                employee_id.department_id.manager_id.user_id.id == uid) or is_admin:
                #set is a dep manager
                self.is_a_dep_manager = True
            if self.env.user.has_group('cw_hr_extended.group_account_manager') or is_admin:
                #set is a acc manager
                self.is_a_acc_manager = True
            if (self.env.user.has_group('hr.group_hr_user') and \
                not self.env.user.has_group('hr.group_hr_manager')) or is_admin:
                #set is a hr user
                self.is_a_hr_user = True
            if self.env.user.has_group('hr.group_hr_manager') or is_admin:
                #set is a hr manager
                self.is_a_hr_manager = True
        current_user = self._get_user_field()
        if current_user:
            if current_user.id == uid or self.env.user.has_group('hr.group_hr_user') or is_admin:
                #set is an current record user
                self.rec_current_user = True

    @api.multi
    def _search_employee(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []   
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('base.group_user'):
                records = self.search([(self._employee_id+'.user_id', operator, uid)])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]

    @api.multi
    def _search_coach(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []  
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('cw_hr_extended.group_emp_coach'):
                records = self.search([(self._employee_id+'.coach_id.user_id', operator, uid)])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]

    @api.multi
    def _search_manager(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('cw_hr_extended.group_emp_manager'):
                records = self.search([(self._employee_id+'.parent_id.user_id', operator, uid)])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]

    @api.multi
    def _search_dep_manager(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('cw_hr_extended.group_dep_manager'):
                records = self.search([(self._employee_id+'.department_id.manager_id.user_id', operator, uid)])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]

    @api.multi
    def _search_acc_manager(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('cw_hr_extended.group_account_manager'):
                records = self.search([])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]

    @api.multi
    def _search_hr_user(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('hr.group_hr_user') and \
                not self.env.user.has_group('hr.group_hr_manager'):
                records = self.search([])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]

    @api.multi
    def _search_hr_manager(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        employee_field = self._check_employee_field()
        if employee_field:
            if self.env.user.has_group('hr.group_hr_manager'):
                records = self.search([])
                return [('id', 'in', records.ids)]
        return [('id', '=', '0')]
    
    @api.one
    def _get_rec_msg_read(self):
        for record in self:
            record.rec_msg_read = record.message_needaction

    @api.model
    @api.multi
    def _search_rec_msg_read(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'
        records = self.search([('message_needaction', operator, value)])
        return [('id', 'in', records.ids)]

    @api.multi
    def _search_user(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        if self.env.user.has_group('hr.group_hr_user'):
            records = self.search([])
            return [('id', 'in', records.ids)]  
        user_field = self._check_user_field()
        if user_field:
            records = self.search([(self._user_id, operator, uid)])
            return [('id', 'in', records.ids)]
        return [('id', '=', '0')]
        
    rec_current_user = fields.Boolean(string='Is a current user', readonly=True, compute='_compute_roles', search='_search_user')
    is_an_employee = fields.Boolean(string='Is an employee', readonly=True, compute='_compute_roles', search='_search_employee')
    is_a_coach = fields.Boolean(string='Is a supervisor', readonly=True, compute='_compute_roles', search='_search_coach')
    is_a_manager = fields.Boolean(string='Is a manager', readonly=True, compute='_compute_roles', search='_search_manager')
    is_a_dep_manager = fields.Boolean(string='Is a dep manager', readonly=True, compute='_compute_roles', search='_search_dep_manager')
    is_a_acc_manager = fields.Boolean(string='Is a acc manager', readonly=True, compute='_compute_roles', search='_search_acc_manager')
    is_a_hr_user = fields.Boolean(string='Is a hr user', readonly=True, compute='_compute_roles', search='_search_hr_user')
    is_a_hr_manager = fields.Boolean(string='Is a hr manager', readonly=True, compute='_compute_roles', search='_search_hr_manager')
    rec_msg_read = fields.Boolean(string='Record Message Read', readonly=True, compute='_get_rec_msg_read', search='_search_rec_msg_read')
    comp_employee_record = fields.Many2one('hr.employee', compute='_compute_roles')
    
    
    @api.multi
    def rec_user_has_groups(self, checking_user=False, checking_groups=[]):
        res = False
        if checking_user:
            for grp in checking_groups:
                if checking_user.has_group(grp):
                    res = True
                    break
        return res

    @api.multi
    def rec_add_followers(self, employee_ids=[], extend_groups=[], exclude_groups=[]):
        employees = self.env['hr.employee'].browse(employee_ids)
        user_ids = []
        for employee in employees:
            if employee.user_id:
                user_ids.append(employee.user_id.id)
        for grp in extend_groups:
            group = self.env.ref(grp)
            for user in group.users:
                has_group = self.rec_user_has_groups(checking_user=user, checking_groups=exclude_groups)
                if not has_group:
                    user_ids.append(user.id)
        user_ids = sorted(set(user_ids))
        self.sudo().message_subscribe_users(user_ids=user_ids)
        
        
        
