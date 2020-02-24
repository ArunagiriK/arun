from odoo import api, fields, models, _


class AssetModify(models.TransientModel):
    _inherit = 'asset.modify'

    dep_percent = fields.Float('Percent')
    dep_amount = fields.Float('Asset Value')

#     @api.model
#     def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
#         result = super(AssetModify, self).fields_view_get(view_id, view_type, toolbar=toolbar, submenu=submenu)
#         asset_id = self.env.context.get('active_id')
#         active_model = self.env.context.get('active_model')
#         if active_model == 'account.asset.asset' and asset_id:
#             asset = self.env['account.asset.asset'].browse(asset_id)
#             doc = etree.XML(result['arch'])
#             if asset.method_time == 'number' and doc.xpath("//field[@name='method_end']"):
#                 node = doc.xpath("//field[@name='method_end']")[0]
#                 node.set('invisible', '1')
#                 setup_modifiers(node, result['fields']['method_end'])
#             elif asset.method_time == 'end' and doc.xpath("//field[@name='method_number']"):
#                 node = doc.xpath("//field[@name='method_number']")[0]
#                 node.set('invisible', '1')
#                 setup_modifiers(node, result['fields']['method_number'])
#             result['arch'] = etree.tostring(doc)
#         return result
# 
    @api.model
    def default_get(self, fields):
        res = super(AssetModify, self).default_get(fields)
        asset_id = self.env.context.get('active_id')
        asset = self.env['account.asset.asset'].browse(asset_id)
        if asset.method_time == 'perc':
            res.update({'dep_percent': asset.dp_percent, 'dep_amount': asset.actual_value})
        return res
 
    @api.multi
    def modify(self):
        """ Modifies the duration of asset for calculating depreciation
        and maintains the history of old values, in the chatter.
        """
        asset_id = self.env.context.get('active_id', False)
        asset = self.env['account.asset.asset'].browse(asset_id)
        if asset.method_time == 'perc':
            old_values = {
                'dp_percent': asset.dp_percent,
                'dep_percent': asset.dep_percent,
                'method_period': asset.method_period,
                'actual_value': asset.actual_value,
                'value': asset.value
            }
            asset_diff = self.dep_amount - asset.actual_value
            asset_vals = {
                'dp_percent': self.dep_percent,
                'dep_percent': self.dep_percent / 12.00,
                'method_period': self.method_period,
                'actual_value': asset.actual_value + asset_diff,
                'value': asset.value + asset_diff
            }
            asset.write(asset_vals)
            asset.compute_depreciation_board()
            tracked_fields = self.env['account.asset.asset'].fields_get(['dp_percent', 'method_period', 'actual_value', 'value'])
            changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
            if changes:
                asset.message_post(subject=_('Depreciation board modified'), body=self.name, tracking_value_ids=tracking_value_ids)
            res = {'type': 'ir.actions.act_window_close'}
            
        else:
            res = super(AssetModify, self).modify()
        return res
