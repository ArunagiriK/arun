# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError

_logger = logging.getLogger(__name__)

class common_clarify_update_wiz(models.TransientModel):
    _name = "common.clarify.update.wiz"
    _description = 'Clarification Update Wizard'
    
    @api.model
    def _get_respond_user(self):        
        return self.env.user.id
        
    @api.model
    def _get_clarif_record(self):
        clarif_line = self.env['common.clarify.line'].search([('id', '=', self.env.context.get('default_clarif_id', False))])
        if clarif_line:
            return clarif_line
        return self.env['common.clarify.line']
        
    @api.model
    def _get_clarif_return_mode(self):        
        return self.env.context.get('default_return_mode', False)
        
    @api.model
    def _get_clarif_return_state(self):
        return self.env.context.get('default_return_state', False)
        
    @api.one
    @api.depends('clarif_id', 
                 'clarif_id.date')
    def _compute_clarify(self):
        date = False
        if self.clarif_id:
            date = self.clarif_id.date        
        self.date = date
    
    name = fields.Text('Reason', required=True)
    clarif_id = fields.Many2one('common.clarify.line', readonly=True, default=_get_clarif_record)
    date = fields.Date('Date', readonly=True, compute='_compute_clarify')
    #date = fields.Date(related='clarif_id.date', string='Date', readonly=True)
    request_user_id = fields.Many2one('res.users', related='clarif_id.request_user_id',  string='Requester', readonly=True)
    respond_user_id = fields.Many2one('res.users','Responder', readonly=True, default=_get_respond_user)
    comment = fields.Text(related='clarif_id.comment', string='Clarification', readonly=True)   
    check = fields.Boolean(related='clarif_id.check', string='Check', readonly=True)
    return_mode = fields.Selection([('user','Responder'), ('state','Status'), ('both','Both')], string='Return Mode', readonly=True, default=_get_clarif_return_mode)
    previous_state = fields.Char(related='clarif_id.previous_state', string='Previous State', readonly=True)
    return_state = fields.Char('Return State', readonly=True, default=_get_clarif_return_state)
    
    @api.multi    
    def action_clarification_clear(self):        
        self.ensure_one()      
        clarification_obj = self.env['common.clarify.line']
        request_model = self.env.context.get('active_model', False)       
        record_id = self.env.context.get('active_id', False)
        uid = self.env.user.id
        request_obj = self.env[request_model]
        for record in request_obj.browse([record_id]):
            if record.state == 'clarify':
                return_state = False
                for clar_line in record.clarify_line_ids:
                    if clar_line.update == False:
                        reason = self.name
                        if clar_line.return_mode == 'user':
                            return_state = clar_line.previous_state
                        else:
                            return_state = clar_line.return_state
                        clar_line.sudo(SUPERUSER_ID).write({'respond_user_id':uid, 'update': True, 'reason': reason})
                if return_state:
                    record.sudo(SUPERUSER_ID).before_clarify_update()
                    record.sudo(SUPERUSER_ID).write({'state': return_state}) 
                    record.sudo(SUPERUSER_ID).after_clarify_update()                       
        return True
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: