# © 2014-2016 Camptocamp SA
# @author: Nicolas Bessi
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Partner address with Region',
    'summary': 'Add a region to the address and change the position',
    'license': 'AGPL-3',
    'version': '12.0.1.0.0',
    'author': 'Codeware/Niyas',
    'website': 'www.codewareuae.com',
    'maintainer': 'Codeware',
    'category': 'Sales',
    'depends': ['base'],
    'data': ['view/partner_view.xml',
             'security/ir.model.access.csv'],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
}
