from odoo import models, fields, api

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self):
        res = super(StockMove, self)._action_done()
        for move in self:
            if move.product_id:
                if move.product_id.qty_available > 0:
                    move.product_id.average_landed_cost = move.product_id.stock_value / move.product_id.qty_available
        return res