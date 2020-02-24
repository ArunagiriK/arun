# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError

_logger = logging.getLogger(__name__)

class common_clarify_wiz(models.TransientModel):
    _name = "common.clarify.wiz"
    _description = 'Clarification Wizard'
    
    @api.model
    def _get_employee_user(self):
        respond_user_id = False 
        user_id = self.env.context.get('default_user_id', False)
        employee_id = self.env.context.get('default_employee_id', False)
        if user_id:
            respond_user_id = user_id
        elif employee_id:
            emp_obj = self.env['ir.model'].search([('model', '=', 'hr.employee')])
            if emp_obj:
                emp = self.env['hr.employee'].search([('id', '=', employee_id)])
                respond_user_id = emp and emp.user_id and emp.user_id.id or False
        return respond_user_id
    
    @api.model    
    def _get_previous_state(self):        
        return self.env.context.get('default_state', False)

    @api.model    
    def _get_eligible_users(self):
        request_model = self.env.context.get('active_model', False)       
        #record_id = self.env.context.get('active_id', False)     
        record_ids = self.env.context.get('active_ids', False)
        res_usrs = self.env['res.users'].search([])
        usrs = [] 
        uid = self._uid
        if request_model and record_ids:      
            for record in self.env[request_model].browse(record_ids):
                for usr in res_usrs:
                    try:
                        # To Do : Check for "state" access rules
                        read_access_right = record.sudo(usr.id).check_access_rights('read', raise_exception=False)
                        read_access_rule = record.sudo(usr.id).check_access_rule('read')
                        write_access_right = record.sudo(usr.id).check_access_rights('write', raise_exception=False)
                        write_access_rule = record.sudo(usr.id).check_access_rule('write')
                        if read_access_right and read_access_rule == None and write_access_right and write_access_rule == None:
                            usrs.append(usr.id)                            
                    except (AccessError, UserError):
                        pass
        else:
            for usr in res_usrs:
                usrs.append(usr.id)
        if self._get_employee_user():
            usrs.append(self._get_employee_user())     
        usrs = list(set(usrs))
        if 1 in usrs:
            usrs.remove(1)
        if uid in usrs:
            usrs.remove(uid)
            #del usrs[uid]        
        return usrs
        

    def _get_incoming_state(self):
        request_model = self.env.context.get('active_model', False)   
        value = []
        if request_model: 
            value = self.env[request_model].fields_get(allfields=['state'])['state']['selection']
            current_state = self._get_previous_state()
            #value = self.env[request_model]._columns['state'].selection
            current_index = False
            try:
                #current_index = value.index(current_state) + 1
                current_index = [value.index(sel_tup) for sel_tup in value if sel_tup[0] == current_state] 
                clarification_index = [value.index(sel_tup) for sel_tup in value if sel_tup[0] == 'clarify']
                cancel_index = [value.index(sel_tup) for sel_tup in value if sel_tup[0] == 'cancel']
                refuse_index = [value.index(sel_tup) for sel_tup in value if sel_tup[0] == 'refuse']
                reject_index = [value.index(sel_tup) for sel_tup in value if sel_tup[0] == 'reject']           
            except (ValueError, e):
                current_index = False
            if current_index:
                current_index = current_index[0] + 1
                #current_index = [current_index[0] + 1]
                value = value[:current_index]   
                #del_index = current_index + clarification_index + cancel_index + refuse_index + reject_index
                del_index = clarification_index + cancel_index + refuse_index + reject_index
                for index in sorted(del_index, reverse=True):
                    try:
                        rem_item = value[index]
                        value.remove(rem_item)
                    except IndexError:
                        pass                   
        return value
                    
    _incoming_state = lambda self: self._get_incoming_state()   
    
    name = fields.Text('Clarification', required=True)
    date = fields.Date('Date', default=fields.Date.today()) #fields.Date.context_today
    previous_state = fields.Char('Previous State', default=_get_previous_state)
    eligible_respond_users = fields.Many2many('res.users', string='Eligible Responders', default=_get_eligible_users)
    respond_user_id = fields.Many2one('res.users', 'Responder', domain="[('id', 'in', eligible_respond_users)]", default=_get_employee_user)
    return_state = fields.Selection(selection=_incoming_state, string='Return Status', default=_get_previous_state, required=True)
    return_mode = fields.Selection([('user','Responder'), ('state','Status'), ('both','Both')], string='Return Mode', required=True, default='user')
    
    @api.onchange('return_mode')
    def _onchange_return_mode(self):
        respond_user_id = self._get_employee_user()
        previous_state = self._get_previous_state()
        if self.return_mode not in ['user', 'both']:
            self.respond_user_id = respond_user_id
        if self.return_mode not in ['state', 'both']:
            self.return_state = previous_state
            
    @api.multi    
    def action_clarification(self):        
        self.ensure_one()
        clarification_obj = self.env['common.clarify.line']  
        common_clarify = True     
        request_model = self.env.context.get('active_model', False)       
        record_id = self.env.context.get('active_id', False)
        ir_model_fields = self.env['ir.model.fields']
        request_model_record = self.env['ir.model'].search([('model', '=', request_model)])
        clarification_model_id = self.env['ir.model'].search([('model', '=', 'common.clarify.line')])
        field_id = ir_model_fields.search([
                                ('model_id','=', clarification_model_id.id),
                                ('ttype','=','many2one'),
                                ('relation', '=', request_model)
                            ], limit=1)        
        for comment in self:
            respond_user_id = comment.respond_user_id and comment.respond_user_id.id or False
            comments = comment.name        
            if comments and request_model and record_id and request_model_record:
                request_obj = self.env[request_model]
                return_mode = comment.return_mode
                previous_state = comment.previous_state or 'draft'
                return_state = comment.return_state or 'draft'
                if self.return_mode == 'state' and self._get_employee_user():
                    respond_user_id = self._get_employee_user()
                if self.return_mode == 'user':
                    #return_state = 'draft'
                    return_state = previous_state
                #field_id.name: record_id,
                clarify_dict = {                        
                        'clarify_rec_id': record_id,    
                        'clarify_rec_model_id': request_model_record.id,
                        'date': comment.date,
                        'request_user_id': self.env.uid,
                        'comment': comments,
                        'respond_user_id': respond_user_id,
                        'check': True,
                        'previous_state': previous_state,
                        'return_state': return_state,
                        'return_mode': return_mode,
                    }
                clarify_line_ids = (0, 0,  clarify_dict)
                common_clarify = clarification_obj.with_context(request_model=request_model).create(clarify_dict)  
                request_record = request_obj.search([('id', '=', record_id)])
                request_record.before_clarify()
                #request_record.write({'state':'clarify', 'clarify_line_ids': clarify_line_ids})
                request_record.write({'state':'clarify'})
                request_record.after_clarify()
        return common_clarify
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: