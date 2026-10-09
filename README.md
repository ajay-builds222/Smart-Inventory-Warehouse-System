# Smart Inventory & Warehouse Management System

## 1. Project Overview

The Smart Inventory & Warehouse Management System is a backend application designed to manage warehouse operations, inventory levels, suppliers, customers, purchase orders, sales orders, and stock movements.

The application uses FastAPI to provide REST APIs, MySQL to store application data, SQLAlchemy for database operations, Alembic for schema migrations, and JWT-based authentication with role-based access control.

The project supports inventory tracking across warehouses and provides APIs for managing the movement of products through purchasing and sales workflows.

## 2. Objectives

* Maintain product, category, warehouse, supplier, and customer information.
* Track inventory quantities and reserved stock.
* Manage purchase orders and stock receipts.
* Manage sales orders through confirmation, picking, packing, dispatch, and delivery.
* Record inventory movements for traceability.
* Authenticate users and restrict operations according to their roles.
* Provide a dashboard summary of inventory and order information.
* Maintain database schema changes through Alembic migrations.

## 3. Technology Stack

| Technology                     | Purpose                                 |
| ------------------------------ | --------------------------------------- |
| Python                         | Backend programming language            |
| FastAPI                        | REST API development                    |
| Pydantic                       | Request validation and response schemas |
| SQLAlchemy                     | Database ORM                            |
| MySQL                          | Relational database                     |
| Alembic                        | Database schema migrations              |
| JWT                            | Authentication tokens                   |
| Passlib / bcrypt               | Password hashing                        |
| Uvicorn                        | ASGI application server                 |
| pytest                         | Automated testing                       |
| SMTP / FastAPI BackgroundTasks | Optional email notifications            |

## 4. Main Modules

### Authentication and Authorization

* User registration and login.
* JWT bearer-token authentication.
* Current-user information.
* Role-based access restrictions.

### Product and Category Management

* Create and view categories.
* Update and deactivate categories.
* Create, view, update, and deactivate products.
* Store product information such as SKU, pricing, category, and reorder thresholds.

### Warehouse Management

* Create and view warehouses.
* Update warehouse details and deactivate warehouses.
* View warehouse inventory.
* Associate inventory quantities with individual warehouses.

### Supplier Management

* Create and view suppliers.
* Update supplier details.
* Deactivate suppliers where supported.

### Customer Management

* Create and view customers.
* Update customer details.
* Store customer codes, contact information, addresses, and credit limits where supported.

### Inventory Management

* View inventory balances.
* Track quantity on hand and reserved quantity.
* Calculate available quantity as quantity on hand minus reserved quantity.
* Filter inventory records, including low-stock records.
* View recorded stock movements.

### Purchase Order Management

* Create and view purchase orders.
* Approve or cancel purchase orders.
* Process purchase receipts through the receiving workflow.
* Track supplier-related purchasing activity.

### Sales Order Management

* Create and view sales orders.
* Confirm or cancel orders.
* Pick and pack orders.
* Dispatch orders with courier and tracking information.
* Mark orders as delivered.

### Reporting and Audit

* Retrieve a dashboard summary.
* View stock movement history.
* Access audit logs where authorized.

The exact behavior and availability of each operation should be verified in the running Swagger documentation.

## 5. Project Structure

The project uses an application package, database models, schemas, routers, utilities, migration files, and tests.

A typical structure is:

```
Smart_Inventory_Warehouse_System/
├── app/
│   ├── main.py
│   ├── models/
│   ├── schemas/
│   ├── routers/
│   ├── utils/
│   └── ...
├── alembic/
│   └── versions/
├── tests/
├── .env.example
├── .gitignore
├── alembic.ini
├── requirements.txt
└── README.md
```

The exact directory contents may vary according to the current implementation.

## 6. Prerequisites

Install the following before running the application:

* Python 3.9 or later, compatible with the installed dependencies.
* MySQL Server.
* Visual Studio Code or another Python editor.
* Git, if you want to submit the project through GitHub.

## 7. Installation and Setup

Run these commands in Windows PowerShell from the project root directory.

### Step 1: Create the database

Open MySQL Workbench or another MySQL client and execute:

```
CREATE DATABASE smart_inventory
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

If the database already exists, do not recreate it unnecessarily.

### Step 2: Create a virtual environment

```
py -m venv .venv
```

Activate it:

```
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run this command in the current terminal:

```
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

### Step 3: Install dependencies

```
pip install -r requirements.txt
```

Ensure that the required application and testing dependencies are listed in `requirements.txt`.

### Step 4: Configure environment variables

Create a local environment file from the example:

```
Copy-Item .env.example .env
```

Open `.env` and configure the required database connection, JWT secret, and other settings expected by the application.

Use strong, private credentials. If a database password contains URL-special characters, encode those characters correctly in the database connection URL.

Never commit `.env` to GitHub.

## 8. Database Migrations with Alembic

Alembic manages database schema changes.

Check the current migration version:

```
alembic current
```

View migration history:

```
alembic history
```

Apply existing migrations:

```
alembic upgrade head
```

Create a migration after changing SQLAlchemy models:

```
alembic revision --autogenerate -m "describe schema change"
```

Review the generated migration before applying it:

```
alembic upgrade head
```

To downgrade one migration when appropriate:

```
alembic downgrade -1
```

**Important:** Do not generate duplicate initial migrations or downgrade a database containing data unless you understand the consequences. Use the existing migration history when setting up an already-migrated project.

## 9. Running the Application

From the project root, activate the virtual environment and run:

```
uvicorn app.main:app --reload
```

The local API server should be available at:

```
http://127.0.0.1:8000
```

Interactive Swagger API documentation:

```
http://127.0.0.1:8000/docs
```

Alternative ReDoc documentation:

```
http://127.0.0.1:8000/redoc
```

Swagger displays available endpoints, required request fields, response schemas, and authentication requirements.

## 10. Authentication

The API uses JWT bearer tokens for authenticated operations.

Typical authentication flow:

1. Create an authorized user account using the configured registration or administrator-bootstrap process.
2. Submit login credentials to `POST /auth/login`.
3. Copy the returned access token.
4. Select **Authorize** in Swagger.
5. Enter the token in the format expected by the Swagger bearer authentication scheme.
6. Execute protected endpoints according to the user's role.

The configured access-token lifetime is 30 minutes.

Authentication endpoints:

* `POST /auth/login` — authenticate a user.
* `POST /auth/register` — register users subject to the application's authorization rules.
* `GET /auth/me` — retrieve the authenticated user's information.

The first administrator must be provisioned using the project's supported bootstrap process. Do not expose an unrestricted public administrator-registration mechanism.

## 11. API Endpoint Reference

The following is a high-level endpoint group reference. Open `/docs` to confirm the exact HTTP methods, paths, request bodies, and authorization rules in the current code.

| Endpoint group       | Purpose                                           |
| -------------------- | ------------------------------------------------- |
| `/health`            | Health check                                      |
| `/auth`              | Registration, login, and current-user information |
| `/categories`        | Category management                               |
| `/products`          | Product management                                |
| `/warehouses`        | Warehouse management                              |
| `/suppliers`         | Supplier management                               |
| `/customers`         | Customer management                               |
| `/inventory`         | Inventory balances and filtering                  |
| `/stock-movements`   | Stock movement history                            |
| `/purchase-orders`   | Purchase order creation and processing            |
| `/sales-orders`      | Sales order lifecycle                             |
| `/reports/dashboard` | Dashboard summary                                 |
| `/audit-logs`        | Audit log access where authorized                 |

Purchase order operations may include approval, cancellation, and receiving. Sales order operations may include confirmation, cancellation, picking, packing, dispatch, and delivery.

Do not assume that every possible CRUD operation or workflow is implemented simply because an endpoint group exists. Confirm the available operations in Swagger and test them before submission.

## 12. User Roles

The application uses role-based access control.

* **Admin:** Administrative operations and authorized access to management features.
* **Inventory Manager:** Catalog, supplier, purchase, sales, and reporting operations permitted by the configured role rules.
* **Warehouse Staff:** Warehouse operational tasks permitted by the configured permissions.

The actual permissions are determined by the role dependencies and checks implemented in the application. Test unauthorized and cross-warehouse access before claiming that all restrictions have been verified.

## 13. Inventory Calculation

The inventory model distinguishes between physical stock, reserved stock, and available stock.

```
Available Quantity = Quantity on Hand - Quantity Reserved
```

For example, if a warehouse has 50 units on hand and 2 units reserved:

```
Available Quantity = 50 - 2 = 48 units
```

Inventory changes should be performed through controlled business operations that maintain consistent stock balances and record stock movements.

## 14. Dashboard and Reports

The dashboard endpoint is:

```
GET /reports/dashboard
```

The currently observed response includes:

* Total product count.
* Low-stock count.
* Pending purchase order count.
* Pending sales order count.
* A note identifying reporting metrics that remain incomplete.

The currently observed dashboard response indicates that complete inventory valuation and today's dispatch metrics are not yet implemented in that response.

Other reporting requirements should be listed as complete only after their endpoints, filters, and calculations have been implemented and tested.

## 15. Email Notifications

Email notifications are optional and have not been included in the current verified workflow.

If SMTP functionality is enabled in a future iteration, configure the SMTP host, port, username, password, and sender address using private environment variables.

Use a test SMTP service for development. Never publish real SMTP credentials or application passwords.

## 16. Testing

Run the automated tests from the project root:

```
pytest -q
```

Review the test results and fix any failures before submission.

Manual API testing can be performed using Swagger at `/docs`.

Recommended test scenarios include:

* Successful and unsuccessful login.
* Missing or invalid authentication tokens.
* Role-based access restrictions.
* Duplicate product SKU, supplier, or customer records.
* Valid and invalid purchase order operations.
* Stock receipt and inventory balance changes.
* Sales order confirmation, picking, packing, and dispatch.
* Stock movement history after inventory changes.
* Low-stock filtering.
* Dashboard calculations.
* Invalid request data and boundary conditions.

A successful server startup is not proof that all workflows work correctly. Record which tests have actually passed.

## 17. Security Practices

* Keep `.env` out of version control.
* Store password hashes rather than plain-text passwords.
* Use a strong JWT signing secret.
* Do not publish real passwords, tokens, database credentials, or SMTP app passwords.
* Use role checks on protected endpoints.
* Validate request data with Pydantic.
* Apply database migrations deliberately.
* Avoid exposing sensitive information in API error responses or logs.
* Rotate credentials immediately if they have been exposed.

## 18. Known Limitations and Remaining Verification

The following areas require confirmation against the actual code and tests before being described as complete:

* Full return and refund processing.
* Stock transfers and manual stock adjustments.
* All reporting metrics and report filters.
* Complete audit-event coverage.
* Transaction safety under concurrent inventory operations.
* Comprehensive integration and end-to-end testing.
* Email notifications and email screenshots.
* Verification of all role and warehouse restrictions.

The README should be updated as these features are implemented and tested. A database model or route alone does not establish that the complete business workflow is finished.

## 19. Screenshots for Submission

Capture genuine screenshots from Swagger after testing the corresponding endpoint.

Suggested screenshots:

* Successful login and authorization.
* Product and category creation.
* Warehouse creation.
* Supplier and customer creation.
* Inventory listing.
* Purchase order approval and receipt.
* Sales order creation and lifecycle operations.
* Stock movement history.
* Low-stock filtering.
* Dashboard response.
* Automated test results.

Save them in a project folder named `screenshots` if your submission requirements allow it. Only include screenshots that represent actual test results.

## 20. GitHub Submission

Before pushing the project:

1. Check `.gitignore`.
2. Ensure `.env`, virtual environments, caches, and other local secrets are excluded.
3. Include application source code, migration files, tests, `requirements.txt`, `.env.example`, and this README.
4. Run the application and the available tests.
5. Review the Git status and inspect staged files.
6. Commit and push the verified project to your GitHub repository.

Example commands:

```
git status
git add .
git status
git commit -m "Update Smart Inventory project documentation"
git push
```

Review the staged file list before committing to ensure that no secrets or private data are included.

## 21. Conclusion

The Smart Inventory & Warehouse Management System provides a FastAPI-based foundation for inventory, warehouse, purchasing, sales, and user-access management. Its API structure, relational database, migration workflow, and stock movement tracking support the core inventory-management use case.

The final submission should accurately distinguish implemented functionality from features that still require development or testing.
