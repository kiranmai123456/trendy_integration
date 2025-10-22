// Copyright (c) 2025, Kiranmai and contributors
// For license information, please see license.txt

frappe.ui.form.on("Supplier Settings", {
    refresh: function(frm) {
        frm.add_custom_button(__('Sync Now'), function() {
            frappe.call({
                method: "trendy_integration.api.sync_now",
                callback(response){
                    if(response){
                        frm.set_value("last_sync", new Date())
                        frm.save();
                    }
                }
            })
        });
    }
});

