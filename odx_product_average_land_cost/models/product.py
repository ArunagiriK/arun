from odoo import fields, models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    average_landed_cost = fields.Float('Average Landed Cost', compute='_get_average_land_cost')

    @api.multi
    @api.depends('product_variant_ids.average_landed_cost')
    def _get_average_land_cost(self):
        for product in self:
            product.average_landed_cost = sum([p.average_landed_cost
                                               for p in product.with_context(active_test=False).product_variant_ids]) \
                                          / len(product.product_variant_ids)


class ProductProduct(models.Model):
    _inherit = 'product.product'
    average_landed_cost = fields.Float('Average Landed Cost')

    @api.multi
    def _compute_average_stock_value(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')
        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                        FROM account_move_line AS aml
                       WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                    GROUP BY aml.product_id, aml.account_id"""
        params = (self.env.user.company_id.id,)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)

        res = self.env.cr.fetchall()
        for row in res:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        for product in self:
            if product.cost_method in ['standard', 'average']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                stock_value = price_used * qty_available
                qty_at_date = qty_available
                if qty_at_date:
                    product.average_landed_cost = stock_value / qty_at_date
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        domain = [('product_id', '=', product.id),
                                  ('date', '<=', to_date)] + StockMove._get_all_base_domain()
                        moves = StockMove.search(domain)
                        stock_value = sum(moves.mapped('value'))
                        qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                        if qty_at_date:
                            product.average_landed_cost = stock_value / qty_at_date
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                            0, 0, [])
                        stock_value = value
                        qty_at_date = quantity
                        if qty_at_date:
                            product.average_landed_cost = stock_value / qty_at_date
                else:
                    stock_value, moves = product._sum_remaining_values()
                    qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    if qty_at_date:
                        product.average_landed_cost = stock_value / qty_at_date
