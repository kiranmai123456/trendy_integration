import requests
import frappe
import json
from frappe.utils import now_datetime, today
from frappe import _

SUPPLIER_SETTINGS_NAME = "Supplier Settings"
 
@frappe.whitelist()
def sync_now():
    settings = frappe.get_single(SUPPLIER_SETTINGS_NAME)
    return fetch_and_sync_products(settings.api_url)
 

@frappe.whitelist()
def run_daily_supplier_sync():
    settings = frappe.get_single(SUPPLIER_SETTINGS_NAME)
    if not settings or not settings.enable_auto_sync:
        return
    fetch_and_sync_products(settings.api_url)
 

def fetch_and_sync_products(api_url=None):
    # try:
    #     response = requests.get(api_url)
    #     response.raise_for_status()
    #     data = response.json()
    # except requests.exceptions.RequestException as e:
    #     frappe.log_error(message=str(e), title="Product Sync API Error")
    #     return {"status": "error", "message": str(e)}

    data = {
        "products": [
            {
                "id": "PROD001",
                "title": "Wireless Mouse",
                "category": "Products",
                "brand" : "",
                "stock": 50,
                "price": 499.99
            },
            {
                "id": "PROD002",
                "title": "Bluetooth Speaker",
                "category": "Products",
                "brand" : "",
                "stock": 30,
                "price": 1299.00
            },
            {
                "id": "PROD003",
                "title": "Notebook",
                "category": "Products",
                "brand" : "",
                "stock": 100,
                "price": 45.00,
            }
        ]
    }

    products = data.get("products", [])

    for product in products:
        item_code = str(product.get("id"))
        item_name = product.get("title")
        category = product.get("category")
        brand = product.get("brand")
        supplier_qty = int(product.get("stock") or 0)
        supplier_price = float(product.get("price") or 0)

        # Create or update Item
        if frappe.db.exists("Item", item_code):
            item = frappe.get_doc("Item", item_code)
            item.item_name = item_name
            item.item_group = category
            item.custom_supplier_stock = supplier_qty
            item.save()
        else:
            frappe.get_doc({
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_name,
                "item_group": category,
                "is_stock_item": 1,
                "custom_supplier_stock": supplier_qty
            }).insert(ignore_permissions=True)

        # Set 10% markup in Standard Selling price list
        set_item_price(item_code, round(supplier_price * 1.1, 2))

        # Save supplier stock
        update_supplier_stock(item_code, supplier_qty)

    frappe.db.commit()
    return {"Items created/updated successfully"}


def set_item_price(item_code, price):
    existing = frappe.get_all("Item Price", filters={"item_code": item_code, "price_list": "Standard Selling"})
    if existing:
        doc = frappe.get_doc("Item Price", existing[0].name)
        doc.price_list_rate = price
        doc.save()
    else:
        frappe.get_doc({
            "doctype": "Item Price",
            "price_list": "Standard Selling",
            "price_list_rate": price,
            "item_code": item_code
        }).insert(ignore_permissions=True)


def update_supplier_stock(item_code, supplier_qty):
    record = frappe.get_all("Supplier Stock", filters={"item": item_code}, fields=["name"])
    if record:
        doc = frappe.get_doc("Supplier Stock", record[0].name)
        doc.supplier_qty = supplier_qty
        doc.last_synced = today()
        doc.save()
    else:
        frappe.get_doc({
            "doctype": "Supplier Stock",
            "item": item_code,
            "supplier_qty": supplier_qty,
            "last_synced": today()
        }).insert(ignore_permissions=True)

@frappe.whitelist()
def generate_suggestions(docname):
    doc = frappe.get_doc("Restock Plan", docname)
    bins = frappe.get_all("Bin", fields=["item_code", "actual_qty"])
    actuals = {b.item_code: b.actual_qty for b in bins}
    supplier_rows = frappe.get_all("Supplier Stock", fields=["item", "supplier_qty"])
    reorder_level = frappe.get_single(SUPPLIER_SETTINGS_NAME).reorder_level

    existing_items = {item.item_code for item in doc.restock_item}

    for supplier in supplier_rows:
        current = actuals.get(supplier.item_code, 0)
        if current < reorder_level and supplier.item_code not in existing_items:
            doc.append("restock_item", {
                "item_code": supplier.item,
                "current_qty": current,
                "reorder_level": reorder_level,
                "suggested_qty": reorder_level - current
            })

    doc.save()
    frappe.msgprint(_("Suggestions generated."))

@frappe.whitelist()
def create_purchase_orders(docname):
    doc = frappe.get_doc("Restock Plan", docname)
    settings = frappe.get_single("Supplier Settings")
    
    if not settings.default_supplier:
        frappe.throw("Please set a default supplier in Supplier Settings")

    po = frappe.get_doc({
        "doctype": "Purchase Order",
        "supplier": settings.default_supplier,
        "schedule_date": frappe.utils.nowdate(),
        "items": []
    })

    for item in doc.restock_item:
        if item.suggested_qty > 0:
            rate = frappe.db.get_value("Item Price", {"item_code": item.item_code}, "price_list_rate") or 0
            po.append("items", {
                "item_code": item.item_code,
                "qty": item.suggested_qty,
                "rate": rate,
                "warehouse": doc.warehouse
            })

    po.insert(ignore_permissions=True)
    frappe.msgprint(f"Purchase Order {po.name}</a> has been created")

# ===== REST APIs =====
 
@frappe.whitelist(allow_guest=True)
def get_restock_summary():
    bins = frappe.get_all("Bin", fields=["item_code", "actual_qty"])
    actuals = {b.item_code: b.actual_qty for b in bins}
    supplier_stocks = frappe.get_all("Supplier Stock", fields=["item", "item", "supplier_qty"])
    reorder_level = frappe.get_single(SUPPLIER_SETTINGS_NAME).reorder_level
    result = []

    for supplier in supplier_stocks:
        current = actuals.get(supplier.item_code, 0)
        if current < reorder_level:
            result.append({
                "item_code": supplier.item_code,
                "item_name": supplier.item,
                "current_qty": current,
                "supplier_qty": supplier.supplier_qty,
                "suggested_qty": reorder_level - current
            })

    return {"items": result}
 


@frappe.whitelist(allow_guest=False)
def create_restock_plan(warehouse=None, items=None):
    if not frappe.has_permission("Restock Plan", "create"):
        frappe.throw(_("You do not have permission to create a Restock Plan."), frappe.PermissionError)

    reorder_level = frappe.get_single(SUPPLIER_SETTINGS_NAME).reorder_level

    if isinstance(items, str):
        items = json.loads(items)

    doc = frappe.get_doc({
        "doctype": "Restock Plan",
        "warehouse": warehouse,
        "restock_item": []
    })

    for item in items:
        doc.append("restock_item", {
            "item_code": item.get("item_code"),
            "current_qty": item.get("current_qty", 0),
            "reorder_level": reorder_level,
            "suggested_qty": item.get("suggested_qty", 0)
        })

    doc.insert()

    return {
        "message": "Restock Plan has been created successfully",
        "id": doc.name
    }

