# Invoice Management and Business Analytics System

## Project Overview

The Invoice Management and Business Analytics System is a Python-based application designed to manage business invoices, customers, products, inventory, and sales analytics through a user-friendly interface.

The application helps organize business information, generate invoices, monitor inventory, and understand sales performance using dashboards and reports.

## Features

### 1. Dashboard
- View key business performance indicators.
- Analyze monthly sales.
- Identify best-selling products.
- View top customers.
- Analyze sales by product category.
- Monitor inventory and low-stock products.
- Filter dashboard data by date.

### 2. Customer Management
- Add customer records.
- Search for customers.
- Delete customer records.

### 3. Product Management
- Add products and maintain product information.
- Search for products.
- Delete products.
- Track product stock.

### 4. Invoice Generation
- Generate invoices for customers.
- Calculate invoice totals and taxes.
- Save invoice information in the database.
- Update inventory after invoice generation.
- Generate downloadable PDF invoices.

### 5. Invoice History
- View previously generated invoices.
- Check invoice details.
- Download invoice PDFs again.

### 6. Packing List Management
- Create and manage packing lists.
- Track packing status: Pending, Packed, or Dispatched.
- Generate packing list PDFs.

## Technologies Used

- **Python** — Application logic
- **Streamlit** — User interface
- **SQLite** — Database management
- **Pandas** — Data processing and analysis
- **Matplotlib** — Data visualization
- **ReportLab** — PDF generation

## Project Structure

```text
Invoice_Business_Analytics_System/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
│
├── data/
│   └── business.db
│
├── notebooks/
├── pages/
├── reports/
└── src/
    └── database.py
```

*Note: The folder structure above is a simplified overview. Additional files may be present in individual folders.*

## Installation and Setup

### Prerequisites

- Python installed on your system
- Visual Studio Code or another Python editor

### Step 1: Clone the Repository

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
```

Replace `YOUR_GITHUB_REPOSITORY_URL` with your repository URL.

### Step 2: Open the Project Folder

```bash
cd invoice-business-analytics-system
```

### Step 3: Create a Virtual Environment

```bash
python -m venv .venv
```

### Step 4: Activate the Virtual Environment

**Windows:**

```bash
.venv\Scripts\activate
```

### Step 5: Install Dependencies

```bash
python -m pip install -r requirements.txt
```

### Step 6: Run the Application

```bash
python -m streamlit run app.py
```

Streamlit will provide a local URL in the terminal. Open that URL in your browser to use the application.

## Deploying to Streamlit Community Cloud

This project uses Streamlit and should be deployed to a Streamlit-compatible host,
not as a Vercel Python function.

1. Push the project to a GitHub repository.
2. In [Streamlit Community Cloud](https://share.streamlit.io/), create an app from
   that repository and select `app.py` as the entry point.
3. Deploy. Streamlit Cloud installs the packages listed in `requirements.txt`.

The app creates its SQLite tables when it starts. SQLite data is stored on the
app's local filesystem and is not durable across all redeployments or host
restarts. Use a persistent database service for business data that must be kept.

## Database

The application uses SQLite to store business information such as customers, products, invoices, and invoice items.

The application initializes its tables on startup. The database file is local to
the running environment; deploy to a host with persistent storage or use an
external database if the data must survive restarts and redeployments.

## Project Purpose

This project demonstrates the practical use of Python, database management, data analysis, visualization, and PDF generation in a business-oriented application.

## Future Improvements

- Excel export for business reports
- User authentication and role-based access
- Advanced sales analytics
- Automated backup and restore
- Improved reporting and filtering options

## Author

Developed as an academic project to demonstrate Python programming, database management, and business analytics.