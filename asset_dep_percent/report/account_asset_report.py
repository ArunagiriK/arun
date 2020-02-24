from odoo import api, fields, models, tools

class AssetAssetReport(models.Model):
    _inherit = "asset.asset.report"

    actual_value = fields.Float(string='Actual Amount', readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'asset_asset_report')
        self._cr.execute("""
            create or replace view asset_asset_report as (
                select
                    min(dl.id) as id,
                    dl.name as name,
                    dl.depreciation_date as depreciation_date,
                    a.date as date,
                    (CASE WHEN dlmin.id = min(dl.id)
                      THEN a.value
                      ELSE 0
                      END) as gross_value,
                    (CASE WHEN dlmin.id = min(dl.id)
                      THEN a.actual_value
                      ELSE 0
                      END) as actual_value,
                    sum(dl.depreciated_value) as depreciation_value,
                    dl.amount as installment_value,
                    (CASE WHEN dl.move_check
                      THEN dl.amount
                      ELSE 0
                      END) as posted_value,
                    (CASE WHEN NOT dl.move_check
                      THEN dl.amount
                      ELSE 0
                      END) as unposted_value,
                    dl.asset_id as asset_id,
                    dl.move_check as move_check,
                    a.category_id as asset_category_id,
                    a.partner_id as partner_id,
                    a.state as state,
                    count(dl.*) as installment_nbr,
                    count(dl.*) as depreciation_nbr,
                    a.company_id as company_id
                from account_asset_depreciation_line dl
                    left join account_asset_asset a on (dl.asset_id=a.id)
                    left join (select min(d.id) as id,ac.id as ac_id from account_asset_depreciation_line as d inner join account_asset_asset as ac ON (ac.id=d.asset_id) group by ac_id) as dlmin on dlmin.ac_id=a.id
                group by
                    dl.amount,dl.asset_id,dl.depreciation_date,dl.name,
                    a.date, dl.move_check, a.state, a.category_id, a.partner_id, a.company_id,
                    a.value, a.id, a.salvage_value, dlmin.id
        )""")
