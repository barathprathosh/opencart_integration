// Copyright (c) 2022, Barath Prathosh and contributors
// For license information, please see license.txt

frappe.ui.form.on('Opencart Settings', {
	refresh: function(frm) {
		if (frm.doc.enable){
			frm.trigger("enable_custom_button");
		}		
	},
	enable:function(frm){
		if (frm.doc.enable){
			frm.trigger("enable_custom_button");
		}
		else{
			frm.trigger("disable_custom_button");
		}
	},
	enable_custom_button:function(frm){
		frm.add_custom_button(__("Sync Item"), function() {
			frappe.call({
				method:"opencart_integration.item.item.fetch_oc_items",
				args:{
				},
				callback: function(r){
				}
			})
		});
		frm.add_custom_button(__("Sync Customer"), function() {
			frappe.call({
				method:"opencart_integration.customer.customer.fetch_oc_customers",
				args:{
				},
				callback: function(r){
				}
			})
		});
	},
	disable_custom_button:function(frm){
		frm.remove_custom_button(__("Sync Item"));
		frm.remove_custom_button(__("Sync Customer"));
	}
});
