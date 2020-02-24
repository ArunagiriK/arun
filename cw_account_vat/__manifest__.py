# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2012-Today Codeware Computiung LLC (<http://www.codewareuae.com>)
#    Copyright (C) 2004 OpenERP SA (<http://www.openerp.com>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

{
    'name' : 'Codeware Accounting VAT Report',
    'version' : '1.0',
    'author' : 'Codeware',
    'category' : 'General',
    'description' : """
    This module adds VAT functionality
    
    """,
    'website': 'http://www.codewareuae.com',
    'depends' : ['account', 'l10n_ae', 'sale', 'purchase','cw_base_vat'],
    'data': [
        # 'data/account_data.xml',
        # 'wizard/add_tax_view.xml',
        'views/account_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'post_init_hook': '_auto_correct_l10n',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: