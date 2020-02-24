odoo.define('cw_expiry_notifications.color', function (require) {
'use strict';

var core = require('web.core');
var session = require('web.session');
var formats = require('web.formats');
var QWeb = core.qweb;

var ColumnAnimation = core.list_widget_registry.get('field').extend({
	_format : function(row_data, options) {
		var res = this._super.apply(this, arguments);
		var oneDay = 24*60*60*1000;
		var today = new Date();
		var expiry_date = new Date(res);
		//var days_remaining = Math.round(Math.abs((today.getTime() - expiry_date.getTime())/(oneDay)));
		//var days_remaining = Math.round(Math.abs((expiry_date.getTime() - today.getTime())/(oneDay)));
		var days_remaining = Math.round((expiry_date.getTime() - today.getTime())/(oneDay));
		if (days_remaining <= 30) {
			return "<div class='red-blink'>" + (res) + "</div>";
		}
		if (days_remaining > 30) {
			return "<div class='green'>" + (res) + "</div>";
		}
		//return QWeb.render('ListView.row.animation', {widget: this, res: res});
		return res
	}
});

core.list_widget_registry
    .add('field.animation', ColumnAnimation);    


var ColumnExpired = core.list_widget_registry.get('field').extend({
	_format : function(row_data, options) {
		var res = this._super.apply(this, arguments);
		var days_remaining = parseFloat(res);
		if (days_remaining <= 30) {
			return "<div class='red-blink'>" + (res) + "</div>";
		}
		if (days_remaining > 30) {
			return "<div class='green'>" + (res) + "</div>";
		}
		return res
	}
});

core.list_widget_registry
    .add('field.expired', ColumnExpired);


var ColumnPurple = core.list_widget_registry.get('field').extend({
	_format : function(row_data, options) {
		var res = this._super.apply(this, arguments);
		res = formats.format_value(res, { type:"float_time" });
		return "<div style='color: purple; font-weight:bolder;'>" + (res) + "</div>";
	}
});

core.list_widget_registry
    .add('field.purple', ColumnPurple);

});