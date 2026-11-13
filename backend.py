from contextlib import contextmanager
from datetime import date, datetime
import sqlite3
from typing import Dict, List, Literal, Optional
import uuid

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from src.database import get_connection, initialize_database


class CustomerCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=254)
    city: Optional[str] = Field(default=None, max_length=100)


class CustomerUpdate(BaseModel):
    customer_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=254)
    city: Optional[str] = Field(default=None, max_length=100)


class ProductCreate(BaseModel):
    product_name: str = Field(min_length=1, max_length=150)
    category: Optional[str] = Field(default=None, max_length=100)
    unit_price: float = Field(ge=0, allow_inf_nan=False)
    stock_quantity: int = Field(ge=0)


class ProductUpdate(BaseModel):
    product_name: Optional[str] = Field(default=None, min_length=1, max_length=150)
    category: Optional[str] = Field(default=None, max_length=100)
    unit_price: Optional[float] = Field(default=None, ge=0, allow_inf_nan=False)
    stock_quantity: Optional[int] = Field(default=None, ge=0)


class InvoiceItemInput(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class InvoiceCreate(BaseModel):
    customer_id: int = Field(gt=0)
    invoice_date: date = Field(default_factory=date.today)
    tax_rate: float = Field(default=0, ge=0, le=100, allow_inf_nan=False)
    items: List[InvoiceItemInput] = Field(min_length=1)


class PackingStatusUpdate(BaseModel):
    packing_status: Literal["Pending", "Packed", "Dispatched"]


@contextmanager
def database_connection():
    connection = get_connection()
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        with connection:
            yield connection
    finally:
        connection.close()


def row_as_dict(row: sqlite3.Row) -> Dict[str, object]:
    return dict(row)


def require_nonblank(values: dict, field: str) -> None:
    if field in values and (values[field] is None or not values[field].strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"{field} cannot be blank",
        )


app = FastAPI(
    title="Invoice Business Analytics API",
    description="Local REST API backed by the application's SQLite database.",
    version="1.0.0",
)


@app.on_event("startup")
def startup() -> None:
    initialize_database()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/customers")
def list_customers() -> List[dict]:
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM customers ORDER BY customer_id"
        ).fetchall()
    return [row_as_dict(row) for row in rows]


@app.post("/customers", status_code=status.HTTP_201_CREATED)
def create_customer(customer: CustomerCreate) -> dict:
    values = customer.dict()
    require_nonblank(values, "customer_name")
    values["customer_name"] = values["customer_name"].strip()
    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO customers (customer_name, phone, email, city)
            VALUES (:customer_name, :phone, :email, :city)
            """,
            values,
        )
        row = connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return row_as_dict(row)


@app.get("/customers/{customer_id}")
def get_customer(customer_id: int) -> dict:
    with database_connection() as connection:
        row = connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Customer not found")
    return row_as_dict(row)


@app.patch("/customers/{customer_id}")
def update_customer(customer_id: int, customer: CustomerUpdate) -> dict:
    values = customer.dict(exclude_unset=True)
    require_nonblank(values, "customer_name")
    if "customer_name" in values:
        values["customer_name"] = values["customer_name"].strip()
    if not values:
        raise HTTPException(status_code=400, detail="No fields to update")

    assignments = ", ".join(f"{field} = :{field}" for field in values)
    values["customer_id"] = customer_id
    with database_connection() as connection:
        cursor = connection.execute(
            f"UPDATE customers SET {assignments} WHERE customer_id = :customer_id",
            values,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        row = connection.execute(
            "SELECT * FROM customers WHERE customer_id = ?",
            (customer_id,),
        ).fetchone()
    return row_as_dict(row)


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int) -> Response:
    try:
        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM customers WHERE customer_id = ?",
                (customer_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Customer not found")
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Customer has invoices and cannot be deleted",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/products")
def list_products() -> List[dict]:
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM products ORDER BY product_id"
        ).fetchall()
    return [row_as_dict(row) for row in rows]


@app.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate) -> dict:
    values = product.dict()
    require_nonblank(values, "product_name")
    values["product_name"] = values["product_name"].strip()
    with database_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO products
                (product_name, category, unit_price, stock_quantity)
            VALUES
                (:product_name, :category, :unit_price, :stock_quantity)
            """,
            values,
        )
        row = connection.execute(
            "SELECT * FROM products WHERE product_id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return row_as_dict(row)


@app.get("/products/{product_id}")
def get_product(product_id: int) -> dict:
    with database_connection() as connection:
        row = connection.execute(
            "SELECT * FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return row_as_dict(row)


@app.patch("/products/{product_id}")
def update_product(product_id: int, product: ProductUpdate) -> dict:
    values = product.dict(exclude_unset=True)
    require_nonblank(values, "product_name")
    for field in ("unit_price", "stock_quantity"):
        if field in values and values[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )
    if "product_name" in values:
        values["product_name"] = values["product_name"].strip()
    if not values:
        raise HTTPException(status_code=400, detail="No fields to update")

    assignments = ", ".join(f"{field} = :{field}" for field in values)
    values["product_id"] = product_id
    with database_connection() as connection:
        cursor = connection.execute(
            f"UPDATE products SET {assignments} WHERE product_id = :product_id",
            values,
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        row = connection.execute(
            "SELECT * FROM products WHERE product_id = ?",
            (product_id,),
        ).fetchone()
    return row_as_dict(row)


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int) -> Response:
    try:
        with database_connection() as connection:
            cursor = connection.execute(
                "DELETE FROM products WHERE product_id = ?",
                (product_id,),
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Product not found")
    except sqlite3.IntegrityError as error:
        raise HTTPException(
            status_code=409,
            detail="Product appears on invoices and cannot be deleted",
        ) from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/invoices")
def list_invoices() -> List[dict]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT i.*, c.customer_name
            FROM invoices i
            JOIN customers c ON c.customer_id = i.customer_id
            ORDER BY i.invoice_id DESC
            """
        ).fetchall()
    return [row_as_dict(row) for row in rows]


@app.post("/invoices", status_code=status.HTTP_201_CREATED)
def create_invoice(invoice: InvoiceCreate) -> dict:
    invoice_number = (
        f"INV-{datetime.now():%Y%m%d-%H%M%S}-{uuid.uuid4().hex[:6].upper()}"
    )
    try:
        with database_connection() as connection:
            customer = connection.execute(
                "SELECT customer_id FROM customers WHERE customer_id = ?",
                (invoice.customer_id,),
            ).fetchone()
            if customer is None:
                raise HTTPException(status_code=404, detail="Customer not found")

            items = []
            subtotal = 0.0
            for item in invoice.items:
                product = connection.execute(
                    "SELECT product_name, unit_price FROM products "
                    "WHERE product_id = ?",
                    (item.product_id,),
                ).fetchone()
                if product is None:
                    raise HTTPException(
                        status_code=404,
                        detail=f"Product {item.product_id} not found",
                    )

                line_total = round(float(product["unit_price"]) * item.quantity, 2)
                subtotal += line_total
                items.append({
                    "product_id": item.product_id,
                    "product_name": product["product_name"],
                    "quantity": item.quantity,
                    "unit_price": float(product["unit_price"]),
                    "line_total": line_total,
                })

            subtotal = round(subtotal, 2)
            tax_amount = round(subtotal * invoice.tax_rate / 100, 2)
            total_amount = round(subtotal + tax_amount, 2)

            for item in items:
                cursor = connection.execute(
                    """
                    UPDATE products
                    SET stock_quantity = stock_quantity - ?
                    WHERE product_id = ? AND stock_quantity >= ?
                    """,
                    (
                        item["quantity"],
                        item["product_id"],
                        item["quantity"],
                    ),
                )
                if cursor.rowcount != 1:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Insufficient stock for {item['product_name']}",
                    )

            cursor = connection.execute(
                """
                INSERT INTO invoices
                    (invoice_number, customer_id, invoice_date, subtotal,
                     tax_amount, total_amount, status)
                VALUES (?, ?, ?, ?, ?, ?, 'Completed')
                """,
                (
                    invoice_number,
                    invoice.customer_id,
                    invoice.invoice_date.isoformat(),
                    subtotal,
                    tax_amount,
                    total_amount,
                ),
            )
            invoice_id = cursor.lastrowid
            for item in items:
                connection.execute(
                    """
                    INSERT INTO invoice_items
                        (invoice_id, product_id, product_name, quantity,
                         unit_price, line_total)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        invoice_id,
                        item["product_id"],
                        item["product_name"],
                        item["quantity"],
                        item["unit_price"],
                        item["line_total"],
                    ),
                )
            connection.execute(
                """
                INSERT INTO packing_lists (invoice_id, packing_status)
                VALUES (?, 'Pending')
                """,
                (invoice_id,),
            )
            created = connection.execute(
                """
                SELECT i.*, c.customer_name
                FROM invoices i
                JOIN customers c ON c.customer_id = i.customer_id
                WHERE i.invoice_id = ?
                """,
                (invoice_id,),
            ).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Invoice could not be saved") from error

    return {
        **row_as_dict(created),
        "items": items,
    }


@app.get("/invoices/{invoice_id}")
def get_invoice(invoice_id: int) -> dict:
    with database_connection() as connection:
        invoice = connection.execute(
            """
            SELECT i.*, c.customer_name, c.phone, c.email, c.city
            FROM invoices i
            JOIN customers c ON c.customer_id = i.customer_id
            WHERE i.invoice_id = ?
            """,
            (invoice_id,),
        ).fetchone()
        if invoice is None:
            raise HTTPException(status_code=404, detail="Invoice not found")
        items = connection.execute(
            "SELECT * FROM invoice_items WHERE invoice_id = ? ORDER BY item_id",
            (invoice_id,),
        ).fetchall()
    return {
        **row_as_dict(invoice),
        "items": [row_as_dict(item) for item in items],
    }


@app.get("/packing-lists")
def list_packing_lists() -> List[dict]:
    with database_connection() as connection:
        rows = connection.execute(
            """
            SELECT p.packing_id, i.invoice_id,
                   COALESCE(p.packing_status, 'Pending') AS packing_status,
                   p.packing_date, p.updated_at,
                   i.invoice_number, i.invoice_date, c.customer_name
            FROM invoices i
            LEFT JOIN packing_lists p ON p.invoice_id = i.invoice_id
            JOIN customers c ON c.customer_id = i.customer_id
            ORDER BY i.invoice_id DESC
            """
        ).fetchall()
    return [row_as_dict(row) for row in rows]


@app.patch("/packing-lists/{invoice_id}")
def update_packing_status(
    invoice_id: int, update: PackingStatusUpdate
) -> dict:
    try:
        with database_connection() as connection:
            invoice = connection.execute(
                "SELECT invoice_id FROM invoices WHERE invoice_id = ?",
                (invoice_id,),
            ).fetchone()
            if invoice is None:
                raise HTTPException(status_code=404, detail="Invoice not found")

            current = connection.execute(
                "SELECT packing_status FROM packing_lists WHERE invoice_id = ?",
                (invoice_id,),
            ).fetchone()
            if current is None:
                connection.execute(
                    """
                    INSERT INTO packing_lists (invoice_id, packing_status)
                    VALUES (?, 'Pending')
                    """,
                    (invoice_id,),
                )
                current_status = "Pending"
            else:
                current_status = current["packing_status"]

            if (
                update.packing_status == "Dispatched"
                and current_status == "Pending"
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Mark the invoice as Packed before dispatching it",
                )

            packing_date = (
                date.today().isoformat()
                if update.packing_status != "Pending"
                else None
            )
            connection.execute(
                """
                UPDATE packing_lists
                SET packing_status = ?, packing_date = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE invoice_id = ?
                """,
                (update.packing_status, packing_date, invoice_id),
            )
            row = connection.execute(
                "SELECT * FROM packing_lists WHERE invoice_id = ?",
                (invoice_id,),
            ).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Packing status could not be saved") from error

    return row_as_dict(row)
