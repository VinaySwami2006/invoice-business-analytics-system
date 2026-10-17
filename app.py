import streamlit as st
import pandas as pd
import sqlite3
import uuid

from datetime import datetime
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

from src.database import initialize_database, get_connection


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Invoice & Business Analytics System",
    page_icon="📊",
    layout="wide"
)


# Initialize database
initialize_database()


# =========================================================
# PDF INVOICE GENERATOR
# =========================================================

def generate_invoice_pdf(
    invoice_number,
    invoice_date,
    customer_name,
    customer_phone,
    customer_email,
    customer_city,
    items,
    subtotal,
    tax_amount,
    total_amount
):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()
    content = []

    # Heading
    content.append(
        Paragraph("INVOICE", styles["Title"])
    )

    content.append(Spacer(1, 8 * mm))

    # Invoice information
    content.append(
        Paragraph(
            f"<b>Invoice Number:</b> {escape(str(invoice_number))}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"<b>Invoice Date:</b> {escape(str(invoice_date))}",
            styles["Normal"]
        )
    )

    content.append(Spacer(1, 5 * mm))

    # Customer information
    content.append(
        Paragraph("BILL TO", styles["Heading2"])
    )

    content.append(
        Paragraph(
            f"<b>Customer:</b> {escape(str(customer_name))}",
            styles["Normal"]
        )
    )

    if customer_phone:
        content.append(
            Paragraph(
                f"<b>Phone:</b> {escape(str(customer_phone))}",
                styles["Normal"]
            )
        )

    if customer_email:
        content.append(
            Paragraph(
                f"<b>Email:</b> {escape(str(customer_email))}",
                styles["Normal"]
            )
        )

    if customer_city:
        content.append(
            Paragraph(
                f"<b>City:</b> {escape(str(customer_city))}",
                styles["Normal"]
            )
        )

    content.append(Spacer(1, 8 * mm))

    # Product table
    table_data = [
        [
            "Product",
            "Qty",
            "Unit Price (Rs.)",
            "Amount (Rs.)"
        ]
    ]

    for item in items:
        table_data.append([
            Paragraph(
                escape(str(item["product_name"])),
                styles["Normal"]
            ),
            str(item["quantity"]),
            f'{item["unit_price"]:,.2f}',
            f'{item["line_total"]:,.2f}'
        ])

    # Amount summary
    table_data.extend([
        ["", "", "Subtotal:", f"{subtotal:,.2f}"],
        ["", "", "Tax:", f"{tax_amount:,.2f}"],
        ["", "", "Grand Total:", f"{total_amount:,.2f}"]
    ])

    invoice_table = Table(
        table_data,
        colWidths=[
            75 * mm,
            20 * mm,
            35 * mm,
            35 * mm
        ],
        repeatRows=1
    )

    invoice_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#1F4E78")
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold"
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.5,
                colors.grey
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "ALIGN",
                (1, 1),
                (-1, -1),
                "RIGHT"
            ),
            (
                "BACKGROUND",
                (0, -1),
                (-1, -1),
                colors.HexColor("#D9EAF7")
            ),
            (
                "FONTNAME",
                (0, -3),
                (-1, -1),
                "Helvetica-Bold"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    content.append(invoice_table)
    content.append(Spacer(1, 12 * mm))

    content.append(
        Paragraph(
            "Thank you for your business!",
            styles["Italic"]
        )
    )

    document.build(content)

    return buffer.getvalue()


# =========================================================
# DATABASE HELPER
# =========================================================

def read_query(query, params=()):
    with get_connection() as connection:
        return pd.read_sql_query(
            query,
            connection,
            params=params
        )


# =========================================================
# APPLICATION HEADER
# =========================================================

st.title("📊 Invoice Management & Business Analytics System")

st.caption(
    "Business Operations | Invoice Management | Sales Analytics"
)

st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select Module",
    [
        "Dashboard",
        "Customer Management",
        "Product Management",
        "Invoice Generation",
        "Invoice History",
        "Packing List"
    ]
)


# =========================================================
# ADVANCED BUSINESS ANALYTICS DASHBOARD
# =========================================================

if page == "Dashboard":

    st.header("📊 Business Analytics Dashboard")

    st.caption(
        "Monitor revenue, sales performance, products "
        "and customer activity."
    )

    # -----------------------------------------------------
    # DATE FILTER
    # -----------------------------------------------------

    st.subheader("📅 Filter Sales by Date")

    col1, col2 = st.columns(2)

    with col1:
        start_date = st.date_input(
            "Start Date",
            value=datetime(2026, 1, 1).date(),
            key="dashboard_start_date"
        )

    with col2:
        end_date = st.date_input(
            "End Date",
            value=datetime.today().date(),
            key="dashboard_end_date"
        )

    if start_date > end_date:

        st.error(
            "Start date cannot be after end date."
        )

        st.stop()

    start_date_str = start_date.isoformat()
    end_date_str = end_date.isoformat()

    st.divider()

    # -----------------------------------------------------
    # OVERALL BUSINESS METRICS
    # -----------------------------------------------------

    customer_data = read_query(
        """
        SELECT COUNT(*) AS total_customers
        FROM customers
        """
    )

    product_data = read_query(
        """
        SELECT COUNT(*) AS total_products
        FROM products
        """
    )

    invoice_data = read_query(
        """
        SELECT
            COUNT(*) AS total_invoices,
            COALESCE(SUM(total_amount), 0) AS total_revenue
        FROM invoices
        WHERE status = 'Completed'
          AND invoice_date BETWEEN ? AND ?
        """,
        (start_date_str, end_date_str)
    )

    sold_data = read_query(
        """
        SELECT
            COALESCE(SUM(ii.quantity), 0) AS units_sold
        FROM invoice_items ii
        INNER JOIN invoices i
            ON ii.invoice_id = i.invoice_id
        WHERE i.status = 'Completed'
          AND i.invoice_date BETWEEN ? AND ?
        """,
        (start_date_str, end_date_str)
    )

    total_customers = int(
        customer_data.iloc[0]["total_customers"]
    )

    total_products = int(
        product_data.iloc[0]["total_products"]
    )

    total_invoices = int(
        invoice_data.iloc[0]["total_invoices"]
    )

    total_revenue = float(
        invoice_data.iloc[0]["total_revenue"]
    )

    units_sold = int(
        sold_data.iloc[0]["units_sold"]
    )

    # -----------------------------------------------------
    # KPI CARDS
    # -----------------------------------------------------

    st.subheader("📌 Business Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Customers",
        f"{total_customers:,}"
    )

    col2.metric(
        "Total Products",
        f"{total_products:,}"
    )

    col3.metric(
        "Invoices Generated",
        f"{total_invoices:,}"
    )

    col4.metric(
        "Total Revenue",
        f"₹{total_revenue:,.2f}"
    )

    col1, col2 = st.columns(2)

    col1.metric(
        "📦 Units Sold",
        f"{units_sold:,}"
    )

    if total_invoices > 0:

        average_invoice_value = (
            total_revenue / total_invoices
        )

    else:

        average_invoice_value = 0

    col2.metric(
        "🧾 Average Invoice Value",
        f"₹{average_invoice_value:,.2f}"
    )

    st.divider()

    # -----------------------------------------------------
    # MONTHLY SALES ANALYSIS
    # -----------------------------------------------------

    st.subheader("📈 Monthly Sales Analysis")

    monthly_sales = read_query(
        """
        SELECT
            SUBSTR(invoice_date, 1, 7) AS month,
            SUM(total_amount) AS revenue
        FROM invoices
        WHERE status = 'Completed'
          AND invoice_date BETWEEN ? AND ?
        GROUP BY SUBSTR(invoice_date, 1, 7)
        ORDER BY month
        """,
        (start_date_str, end_date_str)
    )

    if not monthly_sales.empty:

        monthly_sales["revenue"] = pd.to_numeric(
            monthly_sales["revenue"],
            errors="coerce"
        ).fillna(0)

        st.bar_chart(
            monthly_sales,
            x="month",
            y="revenue",
            x_label="Month",
            y_label="Revenue (₹)"
        )

        st.dataframe(
            monthly_sales.rename(
                columns={
                    "month": "Month",
                    "revenue": "Revenue (₹)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No sales found for the selected date range."
        )

    st.divider()

    # -----------------------------------------------------
    # TOP-SELLING PRODUCTS
    # -----------------------------------------------------

    st.subheader("🏆 Best-Selling Products")

    top_products = read_query(
        """
        SELECT
            ii.product_name AS product,
            SUM(ii.quantity) AS units_sold,
            SUM(ii.line_total) AS sales_amount
        FROM invoice_items ii
        INNER JOIN invoices i
            ON ii.invoice_id = i.invoice_id
        WHERE i.status = 'Completed'
          AND i.invoice_date BETWEEN ? AND ?
        GROUP BY ii.product_name
        ORDER BY units_sold DESC, sales_amount DESC
        LIMIT 10
        """,
        (start_date_str, end_date_str)
    )

    if not top_products.empty:

        st.bar_chart(
            top_products,
            x="product",
            y="units_sold",
            x_label="Product",
            y_label="Units Sold"
        )

        st.dataframe(
            top_products.rename(
                columns={
                    "product": "Product",
                    "units_sold": "Units Sold",
                    "sales_amount": "Sales Amount (₹)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "Generate invoices to see best-selling products."
        )

    st.divider()

    # -----------------------------------------------------
    # TOP CUSTOMERS
    # -----------------------------------------------------

    st.subheader("👑 Top Customers by Revenue")

    top_customers = read_query(
        """
        SELECT
            c.customer_name AS customer,
            COUNT(i.invoice_id) AS invoices,
            SUM(i.total_amount) AS total_spent
        FROM invoices i
        INNER JOIN customers c
            ON i.customer_id = c.customer_id
        WHERE i.status = 'Completed'
          AND i.invoice_date BETWEEN ? AND ?
        GROUP BY c.customer_id, c.customer_name
        ORDER BY total_spent DESC
        LIMIT 10
        """,
        (start_date_str, end_date_str)
    )

    if not top_customers.empty:

        st.bar_chart(
            top_customers,
            x="customer",
            y="total_spent",
            x_label="Customer",
            y_label="Total Spent (₹)"
        )

        st.dataframe(
            top_customers.rename(
                columns={
                    "customer": "Customer",
                    "invoices": "Number of Invoices",
                    "total_spent": "Total Spent (₹)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No customer purchase data is available "
            "for the selected dates."
        )

    st.divider()

    # -----------------------------------------------------
    # CATEGORY-WISE SALES ANALYSIS
    # -----------------------------------------------------

    st.subheader("🗂️ Category-Wise Sales")

    category_sales = read_query(
        """
        SELECT
            COALESCE(p.category, 'Other') AS category,
            SUM(ii.quantity) AS units_sold,
            SUM(ii.line_total) AS revenue
        FROM invoice_items ii
        INNER JOIN invoices i
            ON ii.invoice_id = i.invoice_id
        LEFT JOIN products p
            ON ii.product_id = p.product_id
        WHERE i.status = 'Completed'
          AND i.invoice_date BETWEEN ? AND ?
        GROUP BY COALESCE(p.category, 'Other')
        ORDER BY revenue DESC
        """,
        (start_date_str, end_date_str)
    )

    if not category_sales.empty:

        st.bar_chart(
            category_sales,
            x="category",
            y="revenue",
            x_label="Product Category",
            y_label="Revenue (₹)"
        )

        st.dataframe(
            category_sales.rename(
                columns={
                    "category": "Category",
                    "units_sold": "Units Sold",
                    "revenue": "Revenue (₹)"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

    else:

        st.info(
            "No category-wise sales data is available yet."
        )

    st.divider()

    # -----------------------------------------------------
    # INVENTORY OVERVIEW
    # -----------------------------------------------------

    st.subheader("📦 Current Inventory")

    inventory = read_query(
        """
        SELECT
            product_name,
            category,
            unit_price,
            stock_quantity
        FROM products
        ORDER BY stock_quantity ASC
        """
    )

    if not inventory.empty:

        st.dataframe(
            inventory.rename(
                columns={
                    "product_name": "Product",
                    "category": "Category",
                    "unit_price": "Unit Price (₹)",
                    "stock_quantity": "Available Stock"
                }
            ),
            use_container_width=True,
            hide_index=True
        )

        low_stock = inventory[
            inventory["stock_quantity"] <= 5
        ]

        if not low_stock.empty:

            st.warning(
                "⚠️ Some products have 5 or fewer units "
                "remaining in stock."
            )

            st.dataframe(
                low_stock.rename(
                    columns={
                        "product_name": "Product",
                        "category": "Category",
                        "unit_price": "Unit Price (₹)",
                        "stock_quantity": "Available Stock"
                    }
                ),
                use_container_width=True,
                hide_index=True
            )

    else:

        st.info(
            "No products have been added to inventory."
        )   

# =========================================================
# CUSTOMER MANAGEMENT
# =========================================================

elif page == "Customer Management":

    st.header("👥 Customer Management")

    with st.expander(
        "➕ Add New Customer",
        expanded=True
    ):

        with st.form("customer_form"):

            customer_name = st.text_input(
                "Customer Name *"
            )

            customer_phone = st.text_input(
                "Phone Number"
            )

            customer_email = st.text_input(
                "Email Address"
            )

            customer_city = st.text_input(
                "City"
            )

            customer_submit = st.form_submit_button(
                "Add Customer"
            )

            if customer_submit:

                if not customer_name.strip():

                    st.error(
                        "Customer name is required."
                    )

                else:

                    try:

                        with get_connection() as connection:

                            connection.execute(
                                """
                                INSERT INTO customers
                                (
                                    customer_name,
                                    phone,
                                    email,
                                    city
                                )
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    customer_name.strip(),
                                    customer_phone.strip(),
                                    customer_email.strip(),
                                    customer_city.strip()
                                )
                            )

                        st.success(
                            "Customer added successfully!"
                        )

                        st.rerun()

                    except sqlite3.Error as error:

                        st.error(
                            f"Database error: {error}"
                        )

    st.divider()

    st.subheader("🔍 Search Customers")

    search_customer = st.text_input(
        "Search by customer name or city",
        key="customer_search"
    )

    customer_query = """
        SELECT
            customer_id,
            customer_name,
            phone,
            email,
            city
        FROM customers
    """

    if search_customer.strip():

        customer_query += """
            WHERE customer_name LIKE ?
               OR city LIKE ?
        """

        search_value = f"%{search_customer.strip()}%"

        customer_data = read_query(
            customer_query + " ORDER BY customer_id DESC",
            (search_value, search_value)
        )

    else:

        customer_data = read_query(
            customer_query + " ORDER BY customer_id DESC"
        )

    if not customer_data.empty:

        st.dataframe(
            customer_data,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🗑️ Delete Customer")

        customer_options = {
            f'{row["customer_name"]} (ID: {row["customer_id"]})':
                int(row["customer_id"])
            for _, row in customer_data.iterrows()
        }

        selected_customer_to_delete = st.selectbox(
            "Select Customer",
            options=list(customer_options.keys()),
            key="delete_customer_selection"
        )

        confirm_customer_delete = st.checkbox(
            "I confirm that I want to delete this customer.",
            key="confirm_customer_delete"
        )

        if st.button("Delete Customer"):

            if not confirm_customer_delete:

                st.warning(
                    "Please confirm before deleting."
                )

            else:

                selected_id = customer_options[
                    selected_customer_to_delete
                ]

                try:

                    with get_connection() as connection:

                        connection.execute(
                            """
                            DELETE FROM customers
                            WHERE customer_id = ?
                            """,
                            (selected_id,)
                        )

                    st.success(
                        "Customer deleted successfully."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "This customer has existing invoices and "
                        "cannot be deleted. Keep the customer record "
                        "to preserve invoice history."
                    )

    else:

        st.info(
            "No customers found. Add a customer to get started."
        )


# =========================================================
# PRODUCT MANAGEMENT
# =========================================================

elif page == "Product Management":

    st.header("📦 Product Management")

    with st.expander(
        "➕ Add New Product",
        expanded=True
    ):

        with st.form("product_form"):

            product_name = st.text_input(
                "Product Name *"
            )

            product_category = st.selectbox(
                "Category",
                [
                    "Electronics",
                    "Accessories",
                    "Office Supplies",
                    "Furniture",
                    "Other"
                ]
            )

            product_price = st.number_input(
                "Unit Price (₹)",
                min_value=0.0,
                value=100.0,
                step=10.0
            )

            product_stock = st.number_input(
                "Stock Quantity",
                min_value=0,
                value=10,
                step=1
            )

            product_submit = st.form_submit_button(
                "Add Product"
            )

            if product_submit:

                if not product_name.strip():

                    st.error(
                        "Product name is required."
                    )

                else:

                    try:

                        with get_connection() as connection:

                            connection.execute(
                                """
                                INSERT INTO products
                                (
                                    product_name,
                                    category,
                                    unit_price,
                                    stock_quantity
                                )
                                VALUES (?, ?, ?, ?)
                                """,
                                (
                                    product_name.strip(),
                                    product_category,
                                    product_price,
                                    product_stock
                                )
                            )

                        st.success(
                            "Product added successfully!"
                        )

                        st.rerun()

                    except sqlite3.Error as error:

                        st.error(
                            f"Database error: {error}"
                        )

    st.divider()

    st.subheader("📋 Product Inventory")

    search_product = st.text_input(
        "Search products by name or category",
        key="product_search"
    )

    product_query = """
        SELECT
            product_id,
            product_name,
            category,
            unit_price,
            stock_quantity
        FROM products
    """

    if search_product.strip():

        product_query += """
            WHERE product_name LIKE ?
               OR category LIKE ?
        """

        search_value = f"%{search_product.strip()}%"

        product_data = read_query(
            product_query + " ORDER BY product_id DESC",
            (search_value, search_value)
        )

    else:

        product_data = read_query(
            product_query + " ORDER BY product_id DESC"
        )

    if not product_data.empty:

        st.dataframe(
            product_data,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("🗑️ Delete Product")

        product_options = {
            f'{row["product_name"]} (ID: {row["product_id"]})':
                int(row["product_id"])
            for _, row in product_data.iterrows()
        }

        selected_product_to_delete = st.selectbox(
            "Select Product",
            options=list(product_options.keys()),
            key="delete_product_selection"
        )

        confirm_product_delete = st.checkbox(
            "I confirm that I want to delete this product.",
            key="confirm_product_delete"
        )

        if st.button("Delete Product"):

            if not confirm_product_delete:

                st.warning(
                    "Please confirm before deleting."
                )

            else:

                selected_id = product_options[
                    selected_product_to_delete
                ]

                try:

                    with get_connection() as connection:

                        connection.execute(
                            """
                            DELETE FROM products
                            WHERE product_id = ?
                            """,
                            (selected_id,)
                        )

                    st.success(
                        "Product deleted successfully."
                    )

                    st.rerun()

                except sqlite3.IntegrityError:

                    st.error(
                        "This product is linked to an existing invoice "
                        "and cannot be deleted. Keep it to preserve "
                        "invoice history."
                    )

    else:

        st.info(
            "No products found. Add a product to get started."
        )


# =========================================================
# INVOICE GENERATION
# =========================================================

elif page == "Invoice Generation":

    st.header("🧾 Invoice Generation")

    customer_data = read_query(
        """
        SELECT
            customer_id,
            customer_name,
            phone,
            email,
            city
        FROM customers
        ORDER BY customer_name
        """
    )

    product_data = read_query(
        """
        SELECT
            product_id,
            product_name,
            category,
            unit_price,
            stock_quantity
        FROM products
        WHERE stock_quantity > 0
        ORDER BY product_name
        """
    )

    if customer_data.empty:

        st.warning(
            "Please add a customer before generating an invoice."
        )

    elif product_data.empty:

        st.warning(
            "No products with available stock. "
            "Please add products or update their stock."
        )

    else:

        customer_options = {
            (
                f'{row["customer_name"]} '
                f'(ID: {row["customer_id"]})'
            ): int(row["customer_id"])
            for _, row in customer_data.iterrows()
        }

        with st.form("invoice_form"):

            st.subheader("Customer Details")

            selected_customer_label = st.selectbox(
                "Select Customer",
                options=list(customer_options.keys())
            )

            invoice_date = st.date_input(
                "Invoice Date",
                value=datetime.today().date()
            )

            st.divider()

            st.subheader("Select Products")

            number_of_items = st.number_input(
                "Number of different products",
                min_value=1,
                max_value=min(10, len(product_data)),
                value=1,
                step=1
            )

            selected_items = []

            subtotal = 0.0

            for index in range(int(number_of_items)):

                st.markdown(
                    f"**Product {index + 1}**"
                )

                product_options = {
                    (
                        f'{row["product_name"]} '
                        f'| ₹{row["unit_price"]:.2f} '
                        f'| Stock: {row["stock_quantity"]}'
                    ): int(row["product_id"])
                    for _, row in product_data.iterrows()
                }

                selected_product_label = st.selectbox(
                    f"Select Product {index + 1}",
                    options=list(product_options.keys()),
                    key=f"invoice_product_{index}"
                )

                selected_product_id = product_options[
                    selected_product_label
                ]

                product_row = product_data[
                    product_data["product_id"]
                    == selected_product_id
                ].iloc[0]

                available_stock = int(
                    product_row["stock_quantity"]
                )

                quantity = st.number_input(
                    f"Quantity for Product {index + 1}",
                    min_value=1,
                    max_value=available_stock,
                    value=1,
                    step=1,
                    key=f"invoice_quantity_{index}"
                )

                unit_price = float(
                    product_row["unit_price"]
                )

                line_total = quantity * unit_price

                subtotal += line_total

                selected_items.append({
                    "product_id": selected_product_id,
                    "product_name": str(
                        product_row["product_name"]
                    ),
                    "quantity": int(quantity),
                    "unit_price": unit_price,
                    "line_total": line_total
                })

                st.caption(
                    f"Line Total: ₹{line_total:,.2f}"
                )

            st.divider()

            tax_rate = st.number_input(
                "Tax Rate (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0
            )

            tax_amount = subtotal * tax_rate / 100

            total_amount = subtotal + tax_amount

            st.markdown(
                f"### Subtotal: ₹{subtotal:,.2f}"
            )

            st.markdown(
                f"### Tax: ₹{tax_amount:,.2f}"
            )

            st.markdown(
                f"## Grand Total: ₹{total_amount:,.2f}"
            )

            generate_invoice_button = st.form_submit_button(
                "Generate Invoice"
            )

        # -------------------------------------------------
        # SAVE INVOICE
        # -------------------------------------------------

        if generate_invoice_button:

            customer_id = customer_options[
                selected_customer_label
            ]

            invoice_number = (
                f"INV-{datetime.now():%Y%m%d-%H%M%S}-"
                f"{uuid.uuid4().hex[:6].upper()}"
            )

            try:

                with get_connection() as connection:

                    # Enable foreign key validation
                    connection.execute(
                        "PRAGMA foreign_keys = ON"
                    )

                    cursor = connection.cursor()

                    # Validate and reduce stock
                    for item in selected_items:

                        cursor.execute(
                            """
                            UPDATE products
                            SET stock_quantity = stock_quantity - ?
                            WHERE product_id = ?
                              AND stock_quantity >= ?
                            """,
                            (
                                item["quantity"],
                                item["product_id"],
                                item["quantity"]
                            )
                        )

                        if cursor.rowcount != 1:

                            raise ValueError(
                                "Insufficient stock for "
                                f'{item["product_name"]}. '
                                "Please refresh and try again."
                            )

                    # Save invoice master record
                    cursor.execute(
                        """
                        INSERT INTO invoices
                        (
                            invoice_number,
                            customer_id,
                            invoice_date,
                            subtotal,
                            tax_amount,
                            total_amount,
                            status
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            invoice_number,
                            customer_id,
                            invoice_date.isoformat(),
                            subtotal,
                            tax_amount,
                            total_amount,
                            "Completed"
                        )
                    )

                    invoice_id = cursor.lastrowid

                    # Save invoice items
                    for item in selected_items:

                        cursor.execute(
                            """
                            INSERT INTO invoice_items
                            (
                                invoice_id,
                                product_id,
                                product_name,
                                quantity,
                                unit_price,
                                line_total
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                invoice_id,
                                item["product_id"],
                                item["product_name"],
                                item["quantity"],
                                item["unit_price"],
                                item["line_total"]
                            )
                        )

                # The database transaction has succeeded.
                # Now display the saved invoice.

                st.success(
                    "Invoice generated and saved successfully!"
                )

                st.divider()

                st.subheader("Invoice Details")

                st.write(
                    f"**Invoice Number:** {invoice_number}"
                )

                st.write(
                    f"**Invoice Date:** {invoice_date}"
                )

                st.write(
                    f"**Customer:** {selected_customer_label}"
                )

                invoice_display = pd.DataFrame([
                    {
                        "Product": item["product_name"],
                        "Quantity": item["quantity"],
                        "Unit Price (₹)": item["unit_price"],
                        "Amount (₹)": item["line_total"]
                    }
                    for item in selected_items
                ])

                st.dataframe(
                    invoice_display,
                    use_container_width=True,
                    hide_index=True
                )

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Subtotal",
                    f"₹{subtotal:,.2f}"
                )

                col2.metric(
                    "Tax",
                    f"₹{tax_amount:,.2f}"
                )

                col3.metric(
                    "Grand Total",
                    f"₹{total_amount:,.2f}"
                )

                # -----------------------------------------
                # CUSTOMER INFORMATION FOR PDF
                # -----------------------------------------

                selected_customer_row = customer_data[
                    customer_data["customer_id"] == customer_id
                ].iloc[0]

                # -----------------------------------------
                # GENERATE PDF
                # -----------------------------------------

                pdf_bytes = generate_invoice_pdf(
                    invoice_number=invoice_number,
                    invoice_date=invoice_date,
                    customer_name=selected_customer_row[
                        "customer_name"
                    ],
                    customer_phone=selected_customer_row[
                        "phone"
                    ],
                    customer_email=selected_customer_row[
                        "email"
                    ],
                    customer_city=selected_customer_row[
                        "city"
                    ],
                    items=selected_items,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    total_amount=total_amount
                )

                # -----------------------------------------
                # DOWNLOAD PDF BUTTON
                # -----------------------------------------

                st.download_button(
                    label="📥 Download PDF Invoice",
                    data=pdf_bytes,
                    file_name=f"{invoice_number}.pdf",
                    mime="application/pdf",
                    key=f"download_{invoice_number}"
                )

            except (sqlite3.Error, ValueError) as error:

                st.error(
                    f"Unable to generate invoice: {error}"
                )


# =========================================================
# INVOICE HISTORY
# =========================================================

elif page == "Invoice History":

    st.header("📋 Invoice History")

    history_data = read_query(
        """
        SELECT
            i.invoice_id,
            i.invoice_number,
            i.invoice_date,
            c.customer_name,
            i.subtotal,
            i.tax_amount,
            i.total_amount,
            i.status
        FROM invoices i
        LEFT JOIN customers c
            ON i.customer_id = c.customer_id
        ORDER BY i.invoice_id DESC
        """
    )

    if not history_data.empty:

        st.subheader("All Generated Invoices")

        st.dataframe(
            history_data,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        st.subheader("🔍 View Invoice Details")

        invoice_options = {
            (
                f'{row["invoice_number"]} '
                f'| {row["customer_name"] or "Customer unavailable"} '
                f'| ₹{row["total_amount"]:,.2f}'
            ): int(row["invoice_id"])
            for _, row in history_data.iterrows()
        }

        selected_invoice_label = st.selectbox(
            "Select Invoice",
            options=list(invoice_options.keys())
        )

        selected_invoice_id = invoice_options[
            selected_invoice_label
        ]

        selected_invoice = read_query(
            """
            SELECT
                i.*,
                c.customer_name,
                c.phone,
                c.email,
                c.city
            FROM invoices i
            LEFT JOIN customers c
                ON i.customer_id = c.customer_id
            WHERE i.invoice_id = ?
            """,
            (selected_invoice_id,)
        )

        invoice_items_data = read_query(
            """
            SELECT
                product_name,
                quantity,
                unit_price,
                line_total
            FROM invoice_items
            WHERE invoice_id = ?
            ORDER BY item_id
            """,
            (selected_invoice_id,)
        )

        if not selected_invoice.empty:

            invoice_row = selected_invoice.iloc[0]

            st.markdown(
                f"### Invoice: {invoice_row['invoice_number']}"
            )

            st.write(
                f"**Customer:** "
                f"{invoice_row['customer_name'] or 'Unavailable'}"
            )

            st.write(
                f"**Date:** {invoice_row['invoice_date']}"
            )

            st.dataframe(
                invoice_items_data,
                use_container_width=True,
                hide_index=True
            )

            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Subtotal",
                f"₹{invoice_row['subtotal']:,.2f}"
            )

            col2.metric(
                "Tax",
                f"₹{invoice_row['tax_amount']:,.2f}"
            )

            col3.metric(
                "Total",
                f"₹{invoice_row['total_amount']:,.2f}"
            )

            # Rebuild item dictionaries for PDF
            pdf_items = invoice_items_data.to_dict(
                orient="records"
            )

            pdf_bytes = generate_invoice_pdf(
                invoice_number=invoice_row["invoice_number"],
                invoice_date=invoice_row["invoice_date"],
                customer_name=(
                    invoice_row["customer_name"] or "Unavailable"
                ),
                customer_phone=invoice_row["phone"] or "",
                customer_email=invoice_row["email"] or "",
                customer_city=invoice_row["city"] or "",
                items=pdf_items,
                subtotal=float(invoice_row["subtotal"]),
                tax_amount=float(invoice_row["tax_amount"]),
                total_amount=float(invoice_row["total_amount"])
            )

            st.download_button(
                label="📥 Download This Invoice as PDF",
                data=pdf_bytes,
                file_name=f'{invoice_row["invoice_number"]}.pdf',
                mime="application/pdf",
                key=f"history_download_{selected_invoice_id}"
            )

    else:

        st.info(
            "No invoices found. Generate your first invoice "
            "to see it here."
        )

# =========================================================
# PACKING LIST MANAGEMENT
# =========================================================

elif page == "Packing List":

    st.header("📦 Packing List Management")

    st.caption(
        "Generate packing lists from existing invoices "
        "and track packing and dispatch status."
    )

    # -----------------------------------------------------
    # LOAD INVOICES
    # -----------------------------------------------------

    invoice_data = read_query(
        """
        SELECT
            i.invoice_id,
            i.invoice_number,
            i.invoice_date,
            i.total_amount,
            c.customer_name,
            c.phone,
            c.city
        FROM invoices i
        LEFT JOIN customers c
            ON i.customer_id = c.customer_id
        ORDER BY i.invoice_id DESC
        """
    )

    if invoice_data.empty:

        st.info(
            "No invoices found. Generate an invoice first."
        )

    else:

        invoice_options = {
            (
                f'{row["invoice_number"]} | '
                f'{row["customer_name"] or "Unknown Customer"}'
            ): int(row["invoice_id"])
            for _, row in invoice_data.iterrows()
        }

        selected_invoice_label = st.selectbox(
            "Select Invoice",
            options=list(invoice_options.keys()),
            key="packing_invoice_selection"
        )

        selected_invoice_id = invoice_options[
            selected_invoice_label
        ]

        selected_invoice = invoice_data[
            invoice_data["invoice_id"] == selected_invoice_id
        ].iloc[0]

        # -------------------------------------------------
        # GET OR CREATE PACKING RECORD
        # -------------------------------------------------

        try:

            with get_connection() as connection:

                connection.execute(
                    """
                    INSERT OR IGNORE INTO packing_lists
                    (invoice_id, packing_status)
                    VALUES (?, 'Pending')
                    """,
                    (selected_invoice_id,)
                )

        except sqlite3.Error as error:

            st.error(
                f"Unable to initialize packing record: {error}"
            )
            st.stop()

        packing_data = read_query(
            """
            SELECT packing_status, packing_date
            FROM packing_lists
            WHERE invoice_id = ?
            """,
            (selected_invoice_id,)
        )

        current_status = packing_data.iloc[0][
            "packing_status"
        ]

        current_packing_date = packing_data.iloc[0][
            "packing_date"
        ]

        # -------------------------------------------------
        # INVOICE AND CUSTOMER DETAILS
        # -------------------------------------------------

        st.divider()

        st.subheader("🧾 Invoice Details")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Invoice Number",
            selected_invoice["invoice_number"]
        )

        col2.metric(
            "Invoice Amount",
            f'₹{selected_invoice["total_amount"]:,.2f}'
        )

        col3.metric(
            "Invoice Date",
            selected_invoice["invoice_date"]
        )

        st.subheader("👤 Customer Details")

        st.write(
            f'**Customer:** '
            f'{selected_invoice["customer_name"] or "Unknown"}'
        )

        st.write(
            f'**Phone:** '
            f'{selected_invoice["phone"] or "Not provided"}'
        )

        st.write(
            f'**City:** '
            f'{selected_invoice["city"] or "Not provided"}'
        )

        # -------------------------------------------------
        # INVOICE ITEMS
        # -------------------------------------------------

        items_data = read_query(
            """
            SELECT
                product_name,
                quantity,
                unit_price,
                line_total
            FROM invoice_items
            WHERE invoice_id = ?
            ORDER BY item_id
            """,
            (selected_invoice_id,)
        )

        st.divider()

        st.subheader("📦 Products to Pack")

        if items_data.empty:

            st.warning(
                "No products were found for this invoice."
            )

        else:

            packing_display = items_data[
                ["product_name", "quantity"]
            ].copy()

            packing_display.columns = [
                "Product Name",
                "Quantity to Pack"
            ]

            packing_display.insert(
                0,
                "S. No.",
                range(1, len(packing_display) + 1)
            )

            st.dataframe(
                packing_display,
                use_container_width=True,
                hide_index=True
            )

        # -------------------------------------------------
        # UPDATE PACKING STATUS
        # -------------------------------------------------

        st.divider()

        st.subheader("🚚 Packing Status")

        status_options = [
            "Pending",
            "Packed",
            "Dispatched"
        ]

        status_index = status_options.index(
            current_status
        )

        with st.form("packing_status_form"):

            new_status = st.selectbox(
                "Update Status",
                options=status_options,
                index=status_index
            )

            update_status_button = st.form_submit_button(
                "Update Packing Status"
            )

            if update_status_button:

                if (
                    new_status == "Dispatched"
                    and current_status == "Pending"
                ):

                    st.warning(
                        "Please mark the invoice as Packed "
                        "before marking it as Dispatched."
                    )

                else:

                    packing_date = None

                    if new_status in ["Packed", "Dispatched"]:

                        packing_date = datetime.today().date().isoformat()

                    try:

                        with get_connection() as connection:

                            connection.execute(
                                """
                                UPDATE packing_lists
                                SET
                                    packing_status = ?,
                                    packing_date = ?,
                                    updated_at = CURRENT_TIMESTAMP
                                WHERE invoice_id = ?
                                """,
                                (
                                    new_status,
                                    packing_date,
                                    selected_invoice_id
                                )
                            )

                        st.success(
                            f"Packing status updated to: {new_status}"
                        )

                        st.rerun()

                    except sqlite3.Error as error:

                        st.error(
                            f"Unable to update status: {error}"
                        )

        # -------------------------------------------------
        # CURRENT STATUS
        # -------------------------------------------------

        if current_status == "Pending":

            st.info("🕒 Current Status: Pending")

        elif current_status == "Packed":

            st.success("✅ Current Status: Packed")

        else:

            st.success("🚚 Current Status: Dispatched")

        if current_packing_date:

            st.write(
                f"**Last recorded packing date:** "
                f"{current_packing_date}"
            )

        # -------------------------------------------------
        # GENERATE PACKING LIST PDF
        # -------------------------------------------------

        st.divider()

        st.subheader("📄 Download Packing List")

        if not items_data.empty:

            pdf_buffer = BytesIO()

            pdf_document = SimpleDocTemplate(
                pdf_buffer,
                pagesize=A4,
                rightMargin=18 * mm,
                leftMargin=18 * mm,
                topMargin=18 * mm,
                bottomMargin=18 * mm
            )

            pdf_styles = getSampleStyleSheet()

            pdf_content = []

            pdf_content.append(
                Paragraph(
                    "PACKING LIST",
                    pdf_styles["Title"]
                )
            )

            pdf_content.append(
                Spacer(1, 8 * mm)
            )

            pdf_content.append(
                Paragraph(
                    f'<b>Invoice Number:</b> '
                    f'{escape(str(selected_invoice["invoice_number"]))}',
                    pdf_styles["Normal"]
                )
            )

            pdf_content.append(
                Paragraph(
                    f'<b>Invoice Date:</b> '
                    f'{escape(str(selected_invoice["invoice_date"]))}',
                    pdf_styles["Normal"]
                )
            )

            pdf_content.append(
                Paragraph(
                    f'<b>Customer:</b> '
                    f'{escape(str(selected_invoice["customer_name"] or "Unknown"))}',
                    pdf_styles["Normal"]
                )
            )

            pdf_content.append(
                Paragraph(
                    f'<b>City:</b> '
                    f'{escape(str(selected_invoice["city"] or "Not provided"))}',
                    pdf_styles["Normal"]
                )
            )

            pdf_content.append(
                Paragraph(
                    f'<b>Packing Status:</b> '
                    f'{escape(str(current_status))}',
                    pdf_styles["Normal"]
                )
            )

            pdf_content.append(
                Spacer(1, 8 * mm)
            )

            pdf_table_data = [
                ["S. No.", "Product Name", "Quantity"]
            ]

            for index, row in items_data.iterrows():

                pdf_table_data.append([
                    str(len(pdf_table_data)),
                    Paragraph(
                        escape(str(row["product_name"])),
                        pdf_styles["Normal"]
                    ),
                    str(int(row["quantity"]))
                ])

            packing_table = Table(
                pdf_table_data,
                colWidths=[
                    25 * mm,
                    110 * mm,
                    35 * mm
                ],
                repeatRows=1
            )

            packing_table.setStyle(
                TableStyle([
                    (
                        "BACKGROUND",
                        (0, 0),
                        (-1, 0),
                        colors.HexColor("#1F4E78")
                    ),
                    (
                        "TEXTCOLOR",
                        (0, 0),
                        (-1, 0),
                        colors.white
                    ),
                    (
                        "FONTNAME",
                        (0, 0),
                        (-1, 0),
                        "Helvetica-Bold"
                    ),
                    (
                        "GRID",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.grey
                    ),
                    (
                        "ALIGN",
                        (0, 0),
                        (0, -1),
                        "CENTER"
                    ),
                    (
                        "ALIGN",
                        (2, 0),
                        (2, -1),
                        "CENTER"
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE"
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8
                    )
                ])
            )

            pdf_content.append(packing_table)

            pdf_content.append(
                Spacer(1, 12 * mm)
            )

            pdf_content.append(
                Paragraph(
                    "Packing list generated by the Invoice "
                    "Management & Business Analytics System.",
                    pdf_styles["Italic"]
                )
            )

            pdf_document.build(pdf_content)

            packing_pdf_bytes = pdf_buffer.getvalue()

            st.download_button(
                label="📥 Download Packing List PDF",
                data=packing_pdf_bytes,
                file_name=(
                    f'Packing_List_'
                    f'{selected_invoice["invoice_number"]}.pdf'
                ),
                mime="application/pdf",
                key=f"packing_pdf_{selected_invoice_id}"
            )
# =========================================================
# FOOTER
# =========================================================

st.sidebar.divider()

st.sidebar.caption(
    "Invoice Management & Business Analytics System"
)


st.sidebar.caption(
    "Developed using Python, Streamlit, SQLite and Pandas"
)
