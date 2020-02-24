# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)
    
class hr_department(models.Model):
    _inherit = "hr.department"
    _parent_name = "parent_id"
    #~ _parent_store = True
    #~ _parent_order = 'code, name'
    #~ _order = 'parent_left'

    @api.one
    @api.depends('parent_id', 'child_ids')
    def _compute_all_parent_childs(self):
        #parent_deps=[self.id]
        #child_deps=[self.id]
        parent_deps=[]
        child_deps=[]
        self.get_all_parent_departments(parent_departments=parent_deps)
        self.get_all_child_departments(child_departments=child_deps)
        self.all_parent_ids = self.browse(list(set(parent_deps)))
        self.all_child_ids = self.browse(list(set(child_deps)))   
    
    code = fields.Char(string='Code')
    all_parent_ids = fields.Many2many(comodel_name='hr.department', relation='all_parent_dep_rel', column1='department_id', column2='parent_id', string='All Parent Departments', compute='_compute_all_parent_childs', store=True)
    all_child_ids = fields.Many2many(comodel_name='hr.department', relation='all_child_dep_rel', column1='department_id', column2='child_id', string='All Child Departments', compute='_compute_all_parent_childs', store=True)
    
    parent_id = fields.Many2one('hr.department', 'Parent Department', index=True, ondelete='cascade')
    parent_left = fields.Integer('Left Parent', index=True)
    parent_right = fields.Integer('Right Parent', index=True)
    attendance_cutoff_hrs = fields.Integer("Cut Off Hrs (Attendance)", default=1)
    exclude_annual_leave = fields.Boolean(string='Exclude Annual Leave')
    
    
    _sql_constraints = [
        #('code_company_uniq', 'unique (code, company_id)', 'The code of the department must be unique per company!'),
    ]
       
    @api.one
    def get_all_child_departments(self, browse=False, child_departments=[]):              
        for child_dep in self.child_ids:
            child_dep.get_all_child_departments(browse=browse, child_departments=child_departments)
            if browse:
                child_departments.append(child_dep)
            else:
                child_departments.append(child_dep.id)                
        return child_departments
        
    @api.one
    def get_all_parent_departments(self, browse=False, parent_departments=[]):
        if self.parent_id:
            self.parent_id.get_all_parent_departments(browse=browse, parent_departments=parent_departments)            
            if browse:
                parent_departments.append(self.parent_id)
            else:
                parent_departments.append(self.parent_id.id)
        return parent_departments
    
    @api.one
    def get_consolidate_children(self):
        childs2 = self.search([('parent_id', 'child_of', self.id)])
        child_ids2 = childs2.mapped('id')
        childs_ids3 = []
        childs3 = []
        for child_dep in childs2:
            for child in child_dep.child_ids:
                childs_ids3.append(child.id)
                childs3.append(child)
        if childs3:
            childs_ids3 = self.get_consolidate_children(childs3)
        return child_ids2 + childs_ids3

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:      
