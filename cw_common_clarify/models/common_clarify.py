# -*- coding: utf-8 -*-

import logging
from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError

_logger = logging.getLogger(__name__)  
    
class common_clarify(models.AbstractModel):
    _name = 'common.clarify'
    
    @api.one
    def _compute_clarify_roles(self):
        self.is_latest_clarif_respond_user = False
        uid = self._uid
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if (self.latest_clarif_respond_uid and self.latest_clarif_respond_uid.id == uid) or is_admin:
            self.is_latest_clarif_respond_user = True
            
    @api.multi
    def _search_latest_clarify_responder(self, operator, value):     
        assert operator in ('=', '!='), 'Invalid domain operator'
        assert isinstance(value, bool), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        records = self.sudo(SUPERUSER_ID).search([('latest_clarif_respond_uid', operator, uid)])
        if records:
            return [('id', 'in', records.ids)]
        return [('id', '=', '0')]
    
    @api.one
    @api.depends('clarify_line_ids', 
                 'clarify_line_ids.respond_user_id', 
                 'clarify_line_ids.check', 
                 'clarify_line_ids.update',
                 'clarify_line_ids.previous_state',
                 'clarify_line_ids.return_state',
                 'clarify_line_ids.return_mode')
    def _compute_clarification_record(self):
        latest_clarif_record = False
        for clar_line in self.clarify_line_ids:
            if clar_line.update == False:
                latest_clarif_record = clar_line.id
        self.latest_clarif_record = latest_clarif_record
    
    @api.one
    @api.depends('latest_clarif_record',
                 'clarify_line_ids', 
                 'clarify_line_ids.respond_user_id', 
                 'clarify_line_ids.check', 
                 'clarify_line_ids.update',
                 'clarify_line_ids.previous_state',
                 'clarify_line_ids.return_state',
                 'clarify_line_ids.return_mode')
    def _compute_clarification(self):
        latest_clarif_return_mode = False
        latest_clarif_return_state = False
        latest_clarif_respond_uid = False
        for clar_line in self.clarify_line_ids:
            if clar_line.update == False:
                latest_clarif_return_mode = clar_line.return_mode
                latest_clarif_return_state = clar_line.return_state
                latest_clarif_respond_uid = clar_line.respond_user_id and clar_line.respond_user_id.id or False        
        self.latest_clarif_return_mode = latest_clarif_return_mode
        self.latest_clarif_return_state = latest_clarif_return_state
        self.latest_clarif_respond_uid = latest_clarif_respond_uid
        
    @api.multi
    def _search_latest_clarif_respond_uid(self, operator, value):    
        # To do : Test this field
        assert operator in ('=', '!=', '=?', '=like', '=ilike', 'like', 'not like', 'ilike', 'not ilike', 'in', 'not in'), 'Invalid domain operator'
        assert isinstance(value, str), 'Invalid value'        
        uid = self._uid        
        #is_admin = self.env.user._is_admin()
        is_admin = False
        if uid == SUPERUSER_ID:
            is_admin = True
        if is_admin:
            return []
        records = self.sudo(SUPERUSER_ID).search([('clarify_line_ids.update', '=', False), ('clarify_line_ids.respond_user_id', '!=', False)], order='id desc', limit=1)
        if records:
            return [('id', 'in', records.ids)]
        return [('id', '=', '0')]
    
    clarify_line_ids = fields.One2many('common.clarify.line', 'clarify_rec_id', 'Clarification Line', 
                                       auto_join=True, groups="base.group_user", 
                                       domain=lambda self: [('clarify_rec_model', '=', self._name)], context={'default_res_model': 'active_model'})
    latest_clarif_record = fields.Many2one('common.clarify.line', string='Latest Clarification Record', readonly=True, store=True, compute='_compute_clarification_record')
    latest_clarif_return_mode = fields.Selection([('user','Responder'), ('state','Status'), ('both','Both')], string='Latest Clarification Return Mode', readonly=True, store=True, compute='_compute_clarification')
    latest_clarif_return_state = fields.Char(string='Latest Clarification Return State', readonly=True, store=True, compute='_compute_clarification')
    latest_clarif_respond_uid = fields.Many2one('res.users', string='Latest Clarification Responder', readonly=True, store=True, compute='_compute_clarification')
    
    #latest_clarif_record = fields.Many2one('common.clarify.line', string='Latest Clarification Record', readonly=True, store=False, compute='_compute_clarification_record')
    #latest_clarif_return_mode = fields.Selection([('user','Responder'), ('state','Status'), ('both','Both')], string='Latest Clarification Return Mode', readonly=True, store=False, compute='_compute_clarification')
    #latest_clarif_return_state = fields.Char(string='Latest Clarification Return State', readonly=True, store=False, compute='_compute_clarification')
    #latest_clarif_respond_uid = fields.Many2one('res.users', string='Latest Clarification Responder', readonly=True, store=False, compute='_compute_clarification', search='_search_latest_clarif_respond_uid')
    
    is_latest_clarif_respond_user = fields.Boolean(string='Is latest clarification responder', readonly=True, compute='_compute_clarify_roles', search='_search_latest_clarify_responder')
    #state = fields.Selection(selection_add=[("clarify", "Clarification")])
 
    @api.multi
    def unlink(self):
        record_ids = self.ids
        result = super(common_clarify, self).unlink()
        self.env['common.clarify.line'].sudo(SUPERUSER_ID).search([('clarify_rec_model', '=', self._name), ('clarify_rec_id', 'in', record_ids)]).unlink()
        return result
    
    @api.multi
    def recompute_clarify(self):
        self.env.add_todo(self._fields['latest_clarif_record'], self)
        self.recompute()                
        return True
    
    @api.multi
    def before_clarify(self):                
        return True
    
    @api.multi
    def after_clarify(self):                
        return True
    
    @api.multi
    def before_clarify_update(self):                
        return True
    
    @api.multi
    def after_clarify_update(self):                
        return True
    
class common_clarify_line(models.Model):
    _name = 'common.clarify.line'
    _order = "id desc"
    _rec_name = 'comment'
    
    @api.model
    def default_get(self, fields):
        res = super(common_clarify_line, self).default_get(fields)
        active_model = self.env.context.get('active_model', False)
        if not fields or 'clarify_rec_model_id' in fields and res.get('clarify_rec_model'):
            res['clarify_rec_model_id'] = self.env['ir.model']._get(res['clarify_rec_model']).id
        return res
    
    def _get_request_model_state(self):
        request_model = self.env.context.get('request_model', False)   
        value = []
        if request_model: 
            value = self.env[request_model]._columns['state'].selection
        return value
    
    _request_model_state = lambda self: self._get_request_model_state()
        
    @api.depends('clarify_rec_model', 'clarify_rec_id')
    def _compute_clarify_rec_name(self):
        for clarify in self:
            clarify.clarify_rec_name = self.env[clarify.clarify_rec_model].browse(clarify.clarify_rec_id).name_get()[0][1]

    
    
    clarify_rec_id = fields.Integer('Clarify Record', index=True, required=True)
    clarify_rec_model_id = fields.Many2one('ir.model', 'Clarify Record Model', index=True, ondelete='cascade', required=True)
    clarify_rec_model = fields.Char('Clarify Record Model', index=True, related='clarify_rec_model_id.model', store=True, readonly=True)
    clarify_rec_name = fields.Char('Clarify Record Name', compute='_compute_clarify_rec_name', store=True, readonly=True)   
    
    date = fields.Date('Date')
    request_user_id = fields.Many2one('res.users','Requester')
    respond_user_id = fields.Many2one('res.users','Responder')
    comment = fields.Text('Clarification')
    reason = fields.Text('Reason')    
    check = fields.Boolean('Check', default=False)
    return_mode = fields.Selection([('user','Responder'), ('state','Status'), ('both','Both')], string='Return Mode')
    previous_state = fields.Char('Previous State')
    return_state = fields.Char('Return State')
    update = fields.Boolean('Updated', default=False)
    #previous_state = fields.Selection(selection=_request_model_state, string='Previous Status')    
    #return_state = fields.Selection(selection=_request_model_state, string='Return Status')
    
    @api.multi
    def recompute_clarify(self):
        for clarify_line in self:
            if clarify_line.clarify_rec_model and clarify_line.clarify_rec_id:
                clarify_rec = self.env[clarify_line.clarify_rec_model].browse(clarify_line.clarify_rec_id)
                clarify_rec.recompute_clarify()
                clarify_rec.env.add_todo(clarify_rec._fields['latest_clarif_record'], clarify_rec)
                clarify_rec.recompute()
        return True
                
    @api.model
    def create(self, vals):
        res = super(common_clarify_line, self).create(vals)
        res.recompute_clarify()
        return res
    
    @api.multi
    def write(self, vals):
        res = super(common_clarify_line, self).write(vals)
        self.recompute_clarify()
        return res
    
    @api.multi
    def unlink(self):
        res = super(common_clarify_line, self).unlink()
        self.recompute_clarify()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: