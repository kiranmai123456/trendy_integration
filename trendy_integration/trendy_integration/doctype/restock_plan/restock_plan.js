// Copyright (c) 2025, Kiranmai and contributors
// For license information, please see license.txt

frappe.ui.form.on("Restock Plan", {
    refresh(frm) {
        if(frm.doc.docstatus==0){
            frm.set_intro("<i>Submit this form to generate the suggestions for items which need restocking.</i>");
        }
        if(frm.doc.docstatus==1){
            frm.add_custom_button("Generate Suggestions", function() {
                frappe.call({
                    method: "trendy_integration.api.generate_suggestions",
                    args: {
                        docname : frm.doc.name
                    }
                })
            });
            if(frm.doc.restock_item.length > 0){
                frm.add_custom_button("Create Purchase Orders", function() {
                    frappe.call({
                        method: "trendy_integration.api.create_purchase_orders",
                        args: {
                            docname : frm.doc.name
                        }
                    })
                });
            }
        }
    }
});

