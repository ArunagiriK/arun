odoo.define('cw_expiry_notifications.color_bk', function (require) {
'use strict';

var core = require('web.core');
var session = require('web.session');
var field_registry = require('web.field_registry');
var field_utils = require('web.field_utils');
var QWeb = core.qweb;
var AbstractField = require('web.AbstractField');
var core = require('web.core');
var registry = require('web.field_registry');

var _t = core._t;

var ColumnAnimation = AbstractField.extend({
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
registry.add("animation", ColumnAnimation);   



var ColumnExpired = AbstractField.extend({
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

registry.add('expired', ColumnExpired);


var ColumnPurple = AbstractField.extend({
	_format : function(row_data, options) {
		var res = this._super.apply(this, arguments);
		float_time
		res = field_utils.format.float_time(res);
		return "<div style='color: purple; font-weight:bolder;'>" + (res) + "</div>";
	}
});

registry.add('purple', ColumnPurple);

});