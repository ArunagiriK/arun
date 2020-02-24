# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 ZestyBeanz Technologies Pvt Ltd(<http://www.zbeanztech.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import _, api, fields, models

from odoo.exceptions import UserError
import math
import calendar
from datetime import date as dt
from datetime import datetime, timedelta
from odoo.exceptions import  ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.tools import float_compare, float_is_zero

class AccountAssetCategory(models.Model):
    _inherit = 'account.asset.category'
    
    @api.onchange('method_time')
    @api.model
    def _onchange_method_time(self):
        res = super(AccountAssetCategory, self)._onchange_method_time()
        if self.method_time == 'perc':
            self.method = 'linear'
            self.method_period = 12
            self.prorata = True
        return res
    
    method_time = fields.Selection([('perc', 'Percentage'),
                                    ('number','Number'),
                                    ('end','End')],
                                   help="Choose the method to use to compute the dates and number of depreciation lines.\n"
           "  * Percentage: Depreciation will be based on the amount * percentage and ends when the asset reches salvage value")
    dep_percent = fields.Float('Percent')
    dp_percent = fields.Float('Percentage per Year')
    
    @api.onchange('dp_percent', 'method_period')
    def _onchange_percent(self):
        if self.dp_percent:
            self.dep_percent = self.dp_percent/(12.00/self.method_period)
    
    @api.model
    def create(self, vals):
        method_time = vals.get('method_time',False)
        if method_time and method_time == 'perc':
            vals['prorata'] = True
            vals['method_period'] = 12
        res = super(AccountAssetCategory, self).create(vals)
        
        return res

    @api.multi
    def write(self, vals):
        method_time = vals.get('method_time',False)
        if method_time and method_time == 'perc':
            vals['prorata'] = True
            vals['method_period'] = 12
        res = super(AccountAssetCategory, self).write(vals)
        return res
    
   
class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    
    
    @api.one
    @api.constrains('prorata', 'method_time')
    def _check_prorata(self):
        if self.prorata and self.method_time not in ['number', 'perc']:
            raise ValidationError(_('Prorata temporis can be applied only for time method "number of depreciations and depreciation by percentage value".'))

    
    @api.onchange('method_time')
    def onchange_method_time(self):
        res = super(AccountAssetAsset, self).onchange_method_time()
        if self.method_time == 'perc':
            self.prorata = True
            self.method_period = 12
             
    @api.model
    def create(self, vals):
        method_time = vals.get('method_time',False)
          
        if method_time and method_time == 'perc':
            vals['prorata'] = True
            vals['method_period'] = 12
        res = super(AccountAssetAsset, self).create(vals)
          
        return res
  
    @api.multi
    def write(self, vals):
        method_time = vals.get('method_time',False)
        if method_time and method_time == 'perc':
            vals['prorata'] = True
            vals['method_period'] = 12
        res = super(AccountAssetAsset, self).write(vals)
        return res
            
    
    def onchange_category_id_values(self, category_id):
        res = super(AccountAssetAsset, self).onchange_category_id_values(category_id)
        if category_id:
            category = self.env['account.asset.category'].browse(category_id)
            res['value']['dep_percent'] = category.dep_percent
            res['value']['dp_percent'] = category.dp_percent
        return res
    
    @api.one
    def _get_tracking_value(self):
        tracking_pool = self.env['mail.tracking.value']
        tracking_ids = tracking_pool.search([('field', 'in', ['actual_value', 'value', 'dp_percent']),
                                             ('mail_message_id.model', '=', 'account.asset.asset'),
                                             ('mail_message_id.res_id', '=', self.id)])
        self.tracking_ids = tracking_ids
    
    method_time = fields.Selection([('perc', 'Percentage'),
                                    ('number','Number'),
                                    ('end','End')])
    dep_percent = fields.Float('Percent')
    actual_date = fields.Date(string="Actual Date")
    actual_value = fields.Float(string="Actual Value",required=True)
    dp_percent = fields.Float('Percentage per Year')
    related_product_id = fields.Many2one('product.product', string="Related Product")
    account_info_line_ids = fields.One2many('asset.info.lines','asset_id', string="Asset Infomations")
    tracking_ids = fields.Many2many('mail.tracking.value', compute="_get_tracking_value", string='History')
    
    
    @api.onchange('dp_percent', 'method_period')
    def _onchange_percent(self):
        if self.dp_percent:
            self.dep_percent = self.dp_percent/(12.00/self.method_period)
            
    @api.onchange('actual_date')
    def actual_date_change(self):
        self.date = self.actual_date
        
    @api.onchange('actual_value')
    def actual_value_change(self):
        self.value = self.actual_value
    
    
    def _compute_board_undone_dotation_nb(self, depreciation_date, total_days):
        res = super(AccountAssetAsset, self)._compute_board_undone_dotation_nb(depreciation_date, total_days)
        if self.method_time == 'perc':
            posted_depreciation_line_ids = self.depreciation_line_ids.filtered(lambda x: x.move_check).sorted(key=lambda l: l.depreciation_date)
            percent = self.dep_percent / 100.00
            if percent <= 0.00:
                raise UserError(_("Percentage cannot be less than or equal to 0.00 !!!"))
            undone_dotation_number = 0
            if not posted_depreciation_line_ids:
                amount = self.value
                percent_amount = (self.actual_value - self.salvage_value) * percent
                start_amount = 0
                start_count = 0
                if self.prorata:
                    start_amount = self.get_start_date(self.date, percent_amount)
                    start = False
                    if start_amount >= 0.00:
                        start_count = 1
                        start = True
                    res = 0
                    while amount > 0.00:
                        res += 1
                        if start:
                            amount -= start_amount
                            start = False
                        else:
                            amount -= percent_amount
                else:
                    amount = self.value_residual
                    percent_amount = (self.actual_value - self.salvage_value) * percent
                    undone_dotation_number = math.ceil(amount / percent_amount) + len(posted_depreciation_line_ids)
                    res = int(undone_dotation_number)
            else:
                amount = self.value_residual
                percent_amount = (self.actual_value - self.salvage_value) * percent
                undone_dotation_number = math.ceil(amount / percent_amount) + len(posted_depreciation_line_ids)
                res = int(undone_dotation_number)
            
        return res
    
    
    
    

    
    @api.multi
    def compute_depreciation_board(self):
        res = super(AccountAssetAsset, self).compute_depreciation_board()
        for asset in self:
            fiscalyear_last_day = self.company_id.fiscalyear_last_day
            fiscalyear_last_month = self.company_id.fiscalyear_last_month
            dep_start_date = str(self.date)
            start_date = datetime.strptime(dep_start_date, '%Y-%m-%d')
            start_date_date = start_date.date()
            if asset.prorata:
                for line in asset.depreciation_line_ids:
                    ### depreciation date set as end date of the selected month ###
                    depreciation_start_date = line.depreciation_date
                    if dep_start_date and dep_start_date == depreciation_start_date:
                        start_date = datetime.strptime(depreciation_start_date, '%Y-%m-%d')

                    depre_date = datetime.strptime(str(depreciation_start_date), '%Y-%m-%d')
                    date = depre_date.date()
                    month_days = calendar.monthrange(date.year, date.month)[1]
                    total_days_inmonth = month_days - date.day + 1
                    day = date.day
                    month = date.month
                    year = date.year
                    depreciation_date = date
                    if start_date_date and (start_date_date.year == year) and (fiscalyear_last_month == month):
                        depreciation_date = dt(date.year+1, fiscalyear_last_month, fiscalyear_last_day)
                    else :
                        if month > fiscalyear_last_month:
    #                         depreciation_date1 = date + timedelta(years=1)
                            depreciation_date = dt(date.year+1, fiscalyear_last_month, fiscalyear_last_day)
                        elif month and month <=fiscalyear_last_month:
                            depreciation_date = dt(year, fiscalyear_last_month, fiscalyear_last_day)
                    dep_amount = line.depreciated_value
                    if not line.move_id:
                        dep_amount += asset.actual_value - asset.value
                    line.write({'depreciation_date': depreciation_date, 'depreciated_value': dep_amount})
        return res

    def get_start_date(self, depreciation_start_date, amount):
        depre_date = datetime.strptime(depreciation_start_date, '%Y-%m-%d')
        fiscalyear_last_day = self.company_id.fiscalyear_last_day
        fiscalyear_last_month = self.company_id.fiscalyear_last_month
        date = depre_date.date()
        month_days = calendar.monthrange(date.year, date.month)[1]
        days = month_days+1-date.day
        red_days = date.day - 1.00
        per_month_rate = (amount/12 )
        per_day_rate = per_month_rate/ month_days
        res = 0.0
        if date.month>fiscalyear_last_month:
            res = (amount/12 ) *((12-date.month + 1) + fiscalyear_last_month)
        else :
            res = (amount/12 ) *((fiscalyear_last_month + 1) - date.month)
        return res
    
    def _compute_board_amount(self, sequence, residual_amount, amount_to_depr,
                              undone_dotation_number, posted_depreciation_line_ids, total_days, depreciation_date):
        if sequence == undone_dotation_number or self.method_time != 'perc':
            res = super(AccountAssetAsset, self)._compute_board_amount(sequence, residual_amount, amount_to_depr,
                                                                       undone_dotation_number, posted_depreciation_line_ids,
                                                                       total_days, depreciation_date)
        else:
            res = ((self.actual_value - self.salvage_value) * (self.dp_percent / 100.00)) / (12.00 / self.method_period)
            if sequence == 1 and self.prorata:
                res = self.get_start_date(self.date, res)
        return res
    
class AssetinfoLines(models.Model):
    _name = 'asset.info.lines'
    _description = "New model for asset informations"
    
    
    asset_id = fields.Many2one('account.asset.asset', string="Asset")
    location_id = fields.Many2one('stock.location', string="Current Location")
    user_id = fields.Many2one('res.users', string="Current User")
    serial_no = fields.Char(string="Serial No")
    

