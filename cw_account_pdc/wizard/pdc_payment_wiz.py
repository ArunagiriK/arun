# -*- encoding: utf-8 -*-

from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class PdcPayment(models.TransientModel):

    _name = 'wiz.pdc.payment'

    effective_date = fields.Date(string='Effective Date')

    @api.model
    def default_get(self, fields):
        rec = super(PdcPayment, self).default_get(fields)
        context = dict(self._context or {})
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        records = self.env[active_model].browse(active_ids)
        rec.update({'effective_date': records[0].cheque_date})
        return rec

    @api.multi
    def proceed(self):
        for wiz in self:
            act_id = self._context.get('active_id')
            act_mdl = self._context.get('active_model')
            acc_payment_obj = self.env[act_mdl]
            acc_payment = acc_payment_obj.browse(act_id)

            if wiz.effective_date < acc_payment.cheque_date:
                raise ValidationError(
                    _('You cannot clear cheque before %s' %
                      (acc_payment.cheque_date)))
            if not acc_payment.related_journal:
                raise ValidationError(_('Please enter Related Journal!'))
            acc_payment.write({'effective_date': wiz.effective_date,
                               'cheque_clear':True})
            account_pdc_type = acc_payment.company_id.pdc_type
            # account_pdc_type = self.env['res.config.settings'].search([
            #     ('pdc_type', '=', 'manual')])
            if account_pdc_type and account_pdc_type == 'manual':
                rec = self.env[act_mdl].browse(act_id)
                moves = acc_payment.create_move(rec)
                return acc_payment.write({'cheque_move_line_ids': moves})
