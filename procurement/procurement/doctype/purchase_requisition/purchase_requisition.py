# Copyright (c) 2025, Isambane Mining (Pty) Ltd and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import add_days, today, nowdate, getdate
from frappe import _

class PurchaseRequisition(Document):
	pass

@frappe.whitelist()
def get_company_details(company=None):
    """Fetches default_letter_head and company_abbr based on the selected company."""
    if not company:
        # Fetch the default company from Global Defaults
        company = frappe.db.get_single_value("Global Defaults", "default_company")
        if not company:
            frappe.throw("Default company is not set in Global Defaults.")

    # Get the default_letter_head from the Company DocType
    default_letter_head = frappe.db.get_value("Company", company, "default_letter_head")

    # Get the company_abbr (document name is the same as the value of company_abbr)
    company_abbr = frappe.db.get_value(
        "Company Abbreviations",
        {"company": company},
        "company_abbr"
    )

    if not company_abbr:
        frappe.throw(f"No abbreviation found for the company: {company}")

    return {
        "default_letter_head": default_letter_head,
        "company_abbr": company_abbr,  # This is the document name as well
    }

@frappe.whitelist()
def update_employee_names(doc, method):
    # Helper function to get employee name from Employee DocType
    def get_employee_name(employee_id):
        employee = frappe.get_doc("Employee", employee_id)
        return employee.employee_name if employee else ""

    # Update the read-only fields based on linked Employee documents
    doc.req_name = get_employee_name(doc.requested_by)
    doc.del_name = get_employee_name(doc.deliver_to)
    doc.auth_name = get_employee_name(doc.authorized_by)
    
    # Save the updated document
    doc.save()

# Trigger the update on document save
@frappe.whitelist()
def on_update(doc, method):
    update_employee_names(doc, method)

@frappe.whitelist()
def make_purchase_order(source_name, target_doc=None):
    source_doc = frappe.get_doc("Purchase Requisition", source_name)

    if not source_doc.official_company_order_no:
        frappe.throw(_("Please generate the Official Company Order No before creating a Purchase Order."))

    purchase_order_name = source_doc.official_company_order_no

    if frappe.db.exists("Purchase Order", purchase_order_name):
        return purchase_order_name

    def set_missing_values(source, target):
        target.name = purchase_order_name
        target.naming_series = "PUR-ORD-.YYYY.-"
        target.company = source.company
        target.supplier = source.supplier
        target.transaction_date = source.date or today()
        target.schedule_date = add_days(today(), 7)
        target.letter_head = source.letter_head

        for item in target.items:
            item.schedule_date = target.schedule_date

            if source.account:
                item.expense_account = source.account

            if not item.uom:
                item.uom = frappe.db.get_value("Item", item.item_code, "stock_uom") or "Nos"

    doclist = get_mapped_doc(
        "Purchase Requisition",
        source_name,
        {
            "Purchase Requisition": {
                "doctype": "Purchase Order",
                "field_map": {
                    "company": "company",
                    "supplier": "supplier",
                    "date": "transaction_date",
                    "letter_head": "letter_head"
                }
            },
            "Purchase Requisition List": {
                "doctype": "Purchase Order Item",
                "field_map": {
                    "item": "item_code",
                    "description_and_part_no": "description",
                    "qty": "qty",
                    "unit_price": "rate"
                },
                "condition": lambda doc: doc.item
            }
        },
        target_doc,
        set_missing_values
    )

    doclist.name = purchase_order_name
    doclist.flags.name_set = True
    doclist.flags.ignore_permissions = True
    doclist.insert(ignore_permissions=True)

    return doclist.name

@frappe.whitelist()
def generate_order_number(doc):
    doc = frappe.get_doc("Purchase Requisition", doc)

    if not doc.site_code:
        frappe.throw(_("Site is required before generating an order number."))

    if doc.official_company_order_no:
        frappe.throw(_("Order Number has already been generated and cannot be changed."))

    if not doc.company_abbr:
        frappe.throw(_("Company abbreviation is required before generating an order number."))

    current_date = getdate(nowdate())
    year_last_two_digits = str(current_date.year)[-2:]
    month_abbr = current_date.strftime("%b").upper()
    date_two_digits = current_date.strftime("%d")
    company_letter = doc.company_abbr[0].upper()
    site_code = doc.site_code

    sequence_number = get_next_sequence_number(
        year_last_two_digits,
        company_letter,
        month_abbr,
        site_code
    )

    order_number = f"{year_last_two_digits}{company_letter}{month_abbr}{date_two_digits}{sequence_number:06d}/{site_code}"

    doc.official_company_order_no = order_number
    doc.save()

    frappe.msgprint(_("Order Number generated successfully: {0}").format(order_number))

def get_next_sequence_number(year_last_two_digits, company_letter, month_abbr, site_code):
    sequence_key = f"{year_last_two_digits}{company_letter}{month_abbr}%/{site_code}"

    last_sequence = frappe.db.sql("""
        SELECT official_company_order_no
        FROM `tabPurchase Requisition`
        WHERE official_company_order_no LIKE %s
        ORDER BY official_company_order_no DESC
        LIMIT 1
    """, (sequence_key,), as_dict=True)

    if last_sequence:
        last_order_number = last_sequence[0]["official_company_order_no"]

        try:
            number_before_site = last_order_number.split("/")[0]
            sequence_part = int(number_before_site[-6:])
            next_sequence_number = sequence_part + 1
        except (IndexError, ValueError):
            next_sequence_number = 1
    else:
        next_sequence_number = 1

    if next_sequence_number > 999999:
        frappe.throw(_("Order number sequence exceeded 999999 for this site and month."))

    return next_sequence_number

@frappe.whitelist()
def validate_before_submit(doc, method):
    if not doc.invoice_received or not doc.grn_completed:
        frappe.throw(_("You cannot submit this Purchase Requisition unless both 'Invoice Received' and 'GRN Completed' are checked."))

@frappe.whitelist()
def get_buyer_for_site(site_code):
    # Get Buyer Site Allocation records
    allocations = frappe.get_all("Buyer Site Allocation", fields=["name", "buyer"])

    for allocation in allocations:
        # Check if site_code exists in the child table
        child_sites = frappe.get_all("Site Code List", 
                                     filters={"parent": allocation.name, "site_code": site_code}, 
                                     fields=["site_code"])
        if child_sites:
            return allocation.buyer  # Return the first matching buyer

    return None  # No matching allocation found



@frappe.whitelist()
def get_latest_machine_hours_for_asset(asset):
    if not asset:
        return None

    row = frappe.db.sql("""
        SELECT
            COALESCE(pa.eng_hrs_end, pa.eng_hrs_start) AS machine_hours
        FROM `tabPre-use Assets` pa
        INNER JOIN `tabPre-Use Hours` puh ON puh.name = pa.parent
        WHERE pa.asset_name = %s
          AND COALESCE(pa.eng_hrs_end, pa.eng_hrs_start) IS NOT NULL
        ORDER BY
            puh.shift_date DESC,
            CASE puh.shift
                WHEN 'Night' THEN 3
                WHEN 'Afternoon' THEN 2
                WHEN 'Morning' THEN 1
                WHEN 'Day' THEN 1
                ELSE 0
            END DESC,
            puh.creation DESC
        LIMIT 1
    """, (asset,), as_dict=True)

    return row[0].machine_hours if row else None



    
@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_available_parts_requisitions(doctype, txt, searchfield, start, page_len, filters):
    site_code = filters.get("site_code")
    asset = filters.get("asset")
    current_purchase_requisition = filters.get("current_purchase_requisition")

    if not site_code or not asset:
        return []

    parts_req_meta = frappe.get_meta("Parts Requisition Form")

    site_field = None
    asset_field = None

    for field in parts_req_meta.fields:
        if field.options == "Site Code" or field.fieldname in ("site_code", "site"):
            site_field = field.fieldname

        if field.options == "Asset" or field.fieldname in ("asset", "plant_no", "asset_name"):
            asset_field = field.fieldname

    if not site_field:
        frappe.throw(_("Could not find Site Code field on Parts Requisition Form."))

    if not asset_field:
        frappe.throw(_("Could not find Asset field on Parts Requisition Form."))

    return frappe.db.sql(f"""
        SELECT
            pr.name,
            pr.creation
        FROM `tabParts Requisition Form` pr
        WHERE pr.`{site_field}` = %(site_code)s
          AND pr.`{asset_field}` = %(asset)s
          AND pr.docstatus < 2
          AND pr.name LIKE %(txt)s
          AND pr.name NOT IN (
              SELECT parts_requisition
              FROM `tabPurchase Requisition`
              WHERE parts_requisition IS NOT NULL
                AND parts_requisition != ''
                AND docstatus < 2
                AND name != %(current_purchase_requisition)s
          )
        ORDER BY pr.creation DESC
        LIMIT %(start)s, %(page_len)s
    """, {
        "site_code": site_code,
        "asset": asset,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len,
        "current_purchase_requisition": current_purchase_requisition
    })


@frappe.whitelist()
def get_parts_requisition_items(parts_requisition):
    if not parts_requisition:
        return []

    return frappe.db.sql("""
        SELECT
            qty,
            item_code,
            item_group,
            part_name,
            part_no
        FROM `tabParts Requisition Item`
        WHERE parent = %s
        ORDER BY idx ASC
    """, parts_requisition, as_dict=True)


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_items_by_expense_account(doctype, txt, searchfield, start, page_len, filters):
    expense_account = filters.get("expense_account")

    if not expense_account:
        return frappe.db.sql("""
            SELECT name, item_name
            FROM `tabItem`
            WHERE disabled = 0
              AND (name LIKE %(txt)s OR item_name LIKE %(txt)s)
            ORDER BY name
            LIMIT %(start)s, %(page_len)s
        """, {
            "txt": f"%{txt}%",
            "start": start,
            "page_len": page_len
        })

    return frappe.db.sql("""
        SELECT i.name, i.item_name
        FROM `tabItem` i
        INNER JOIN `tabItem Default` id ON id.parent = i.name
        WHERE i.disabled = 0
          AND id.expense_account = %(expense_account)s
          AND (i.name LIKE %(txt)s OR i.item_name LIKE %(txt)s)
        ORDER BY i.name
        LIMIT %(start)s, %(page_len)s
    """, {
        "expense_account": expense_account,
        "txt": f"%{txt}%",
        "start": start,
        "page_len": page_len
    })