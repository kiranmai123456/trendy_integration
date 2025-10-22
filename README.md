# 🛍️ Trendy Integration

## 📘 Overview

**Trendy Integration** is a custom **Frappe/ERPNext app** that connects your ERP with an external **Supplier API**.  
It automates product synchronization, supplier stock management, restocking, and purchase order generation — all inside ERPNext.

### 🔄 Core Automation
1. Syncs products from a supplier API (e.g. `https://dummyjson.com/products`)
2. Creates/updates ERPNext **Items**, **Item Prices**, and **Supplier Stock**
3. Automatically plans **Restocking** of low-stock items
4. Creates **Purchase Orders** based on restock suggestions
5. Exposes **REST APIs** for external integrations
6. Supports both **manual sync** and **daily auto sync**

---

## 🧩 Features

✅ Fetch and update supplier data automatically
✅ Create or update ERPNext Items & Prices
✅ Apply 10% markup on supplier prices
✅ Store supplier inventory in **Supplier Stock**
✅ Generate **Restock Plans** for low stock items
✅ Automatically create **Purchase Orders**
✅ Provide **REST APIs** to integrate with other systems
✅ Run **daily auto sync** via Scheduler

---

## ⚙️ Installation

You can install this app using the [bench](https://github.com/frappe/bench) CLI:

```bash
cd $PATH_TO_YOUR_BENCH
bench get-app $URL_OF_THIS_REPO --branch main
bench --site <your_site_name> install-app trendy_integration
bench --site <your_site_name> migrate
```

### License

mit
