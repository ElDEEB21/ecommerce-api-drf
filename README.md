<p align="center">
  <img src="https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white" alt="Django 6.0" />
  <img src="https://img.shields.io/badge/DRF-3.16-ff1709?style=for-the-badge&logo=django&logoColor=white" alt="DRF 3.16" />
  <img src="https://img.shields.io/badge/Stripe-Payment-635BFF?style=for-the-badge&logo=stripe&logoColor=white" alt="Stripe Payment" />
  <img src="https://img.shields.io/badge/JWT-Auth-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white" alt="JWT Auth" />
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.14" />
</p>

# 🛒 E-Commerce REST API

A **production-ready**, fully-featured E-Commerce RESTful API built with **Django REST Framework**. This project
demonstrates clean architecture, secure authentication, real payment processing with Stripe, and follows industry best
practices for building scalable backend services.

> 💡 **Project idea & description from [roadmap.sh — E-Commerce API](https://roadmap.sh/projects/ecommerce-api)**

> **🔗 [Full API Documentation →](./API_DOCUMENTATION.md)**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Features (المميزات)](#-key-features-المميزات)
- [Architecture & Design Patterns](#-architecture--design-patterns)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Database Schema](#-database-schema)
- [API Endpoints](#-api-endpoints)
- [Getting Started](#-getting-started)
- [Environment Variables](#-environment-variables)
- [Current Limitations](#-current-limitations)
- [Future Work](#-future-work)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🔎 Overview

This project is a **backend API** for an e-commerce platform that handles the full shopping lifecycle — from user
registration and product browsing, to cart management, order placement, and payment processing via **Stripe**.

It is designed with a **service-oriented architecture** that separates business logic from API views and data access,
making the codebase maintainable, testable, and easy to extend.

### What Can This API Do?

| Capability                 | Description                                                                 |
|----------------------------|-----------------------------------------------------------------------------|
| 🔐 **User Authentication** | Register, login, logout, change password with JWT (access + refresh tokens) |
| 🍪 **Cookie-Based Auth**   | Optional HTTP-only cookie delivery for frontend SPAs                        |
| 📦 **Product Management**  | Full CRUD for products, categories, and product images                      |
| 🛒 **Shopping Cart**       | Add/update/remove items, automatic price snapshots                          |
| 📝 **Order Processing**    | Place orders from cart with stock validation and deduction                  |
| 💳 **Stripe Payments**     | Create payment intents, confirm payments, handle webhooks                   |
| 🔄 **Webhook Handling**    | Secure Stripe webhook integration for real-time payment status updates      |
| 📄 **Auto-Generated Docs** | Interactive Swagger UI via `drf-spectacular`                                |
| 🔍 **Filtering & Search**  | Filter products by category, search by name, order by price/date            |
| 📑 **Pagination**          | Consistent paginated responses across all list endpoints                    |

---

## ✨ Key Features

### 🏗️ Clean Architecture

- **Service Layer Pattern** — All business logic lives in dedicated `services.py` files, not in views
- **Selector Layer Pattern** — Data retrieval logic is separated into `selectors.py` files
- **Thin Views** — API views only handle request/response, delegating logic to services
- **Modular Apps** — Each domain (accounts, products, cart, orders, payments) is a self-contained Django app

### 🔐 Security

- **JWT Authentication** with access/refresh token rotation
- **Token Blacklisting** — Refresh tokens are blacklisted after rotation to prevent reuse
- **HTTP-Only Cookie Support** — Secure cookie-based token delivery for browser clients
- **Password Validation** — Django's built-in password validators (similarity, minimum length, common passwords,
  numeric)
- **Stripe Webhook Signature Verification** — All webhook events are cryptographically verified
- **CORS Configuration** — Separate dev/prod CORS settings
- **Environment Variables** — All secrets are loaded from `.env` files, never hardcoded

### 💳 Payment Processing

- **Stripe Integration** — Full payment flow with PaymentIntent API
- **Idempotency Keys** — Prevents duplicate charges on retry
- **Multi-Currency Support** — Handles both standard and zero-decimal currencies
- **Automatic Stock Restoration** — Stock is restored if payment fails or is cancelled
- **Webhook-Driven Status Updates** — Payment status is synced in real-time via Stripe webhooks

### 📦 Product & Inventory

- **Category-Based Organization** — Products are organized by categories with slug-based URLs
- **Stock Management** — Automatic stock deduction on order placement
- **Product Images** — Support for multiple images per product with primary image flag
- **Active/Inactive Products** — Soft visibility control for products

### 🛒 Cart & Orders

- **Price Snapshots** — Cart items and order items store the price at the time of addition (protects against price
  changes)
- **Cart-to-Order Conversion** — Seamless checkout flow from cart to order with stock validation
- **Order Status Tracking** — Full lifecycle: Pending → Processing → Shipped → Delivered / Cancelled
- **Unique Constraints** — Prevents duplicate products in the same cart or order

### 🛠️ Developer Experience

- **Split Settings** — Separate `base.py`, `dev.py`, and `prod.py` settings for different environments
- **Swagger/OpenAPI Docs** — Auto-generated interactive API documentation at `/api/docs/`
- **Consistent Error Responses** — Standardized error format across all endpoints
- **Custom User Model** — Email-based authentication (no username)

---

## 🏛️ Architecture & Design Patterns

```
┌─────────────────────────────────────────────────┐
│                   Client (Frontend / Mobile)     │
└────────────────────────┬────────────────────────┘
                         │  HTTP Request
                         ▼
┌─────────────────────────────────────────────────┐
│              Django REST Framework               │
│                                                  │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │  Views   │→ │ Services  │→ │  Selectors   │  │
│  │ (API)    │  │ (Business │  │ (Data Access) │  │
│  │          │  │  Logic)   │  │              │  │
│  └──────────┘  └───────────┘  └──────────────┘  │
│       ↑              ↓              ↓            │
│  ┌──────────┐  ┌───────────┐  ┌──────────────┐  │
│  │Serializers│  │  Models   │←─│  Database    │  │
│  └──────────┘  └───────────┘  └──────────────┘  │
└─────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────┐
│              Stripe Payment Gateway              │
└─────────────────────────────────────────────────┘
```

| Layer           | Responsibility                                              | File                 |
|-----------------|-------------------------------------------------------------|----------------------|
| **Views**       | Handle HTTP requests/responses, authentication, permissions | `api/views.py`       |
| **Serializers** | Validate input, serialize output                            | `api/serializers.py` |
| **Services**    | Business logic, orchestration, transactions                 | `services.py`        |
| **Selectors**   | Read-only data queries and retrieval                        | `selectors.py`       |
| **Models**      | Database schema, field definitions                          | `models.py`          |

---

## 🧰 Tech Stack

| Technology                     | Purpose                         |
|--------------------------------|---------------------------------|
| **Python 3.14**                | Programming Language            |
| **Django 6.0**                 | Web Framework                   |
| **Django REST Framework 3.16** | REST API Framework              |
| **PostgreSQL**                 | Relational Database             |
| **SimpleJWT**                  | JWT Authentication              |
| **Stripe**                     | Payment Processing              |
| **drf-spectacular**            | OpenAPI/Swagger Documentation   |
| **django-filter**              | Advanced Filtering              |
| **django-cors-headers**        | Cross-Origin Resource Sharing   |
| **python-dotenv**              | Environment Variable Management |
| **psycopg2**                   | PostgreSQL Adapter              |

---

## 📁 Project Structure

```
ecommerce-api-drf/
│
├── config/                     # Project configuration
│   ├── settings/
│   │   ├── base.py             # Common settings
│   │   ├── dev.py              # Development settings (DEBUG, CORS *)
│   │   └── prod.py             # Production settings (security, SSL)
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py
│   └── asgi.py
│
├── apps/
│   ├── accounts/               # User authentication & management
│   │   ├── models.py           # CustomUser (email-based auth)
│   │   ├── services.py         # Registration, login, token logic
│   │   ├── selectors.py        # User queries
│   │   └── api/
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   │
│   ├── products/               # Products & categories
│   │   ├── models.py           # Product, Category, ProductImage
│   │   ├── services.py         # CRUD operations
│   │   ├── selectors.py        # Filtering, search queries
│   │   └── api/
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   │
│   ├── cart/                   # Shopping cart
│   │   ├── models.py           # Cart, CartItem
│   │   ├── services.py         # Add/update/remove items
│   │   ├── selectors.py        # Cart queries
│   │   └── api/
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   │
│   ├── orders/                 # Order management
│   │   ├── models.py           # Order, OrderItem
│   │   ├── services.py         # Order placement, status updates
│   │   ├── selectors.py        # Order queries
│   │   └── api/
│   │       ├── views.py
│   │       ├── serializers.py
│   │       └── urls.py
│   │
│   └── payments/               # Stripe payment processing
│       ├── models.py           # Payment model
│       ├── services.py         # Stripe integration, webhooks
│       ├── selectors.py        # Payment queries
│       └── api/
│           ├── views.py
│           ├── serializers.py
│           └── urls.py
│
├── API_DOCUMENTATION.md        # Comprehensive API docs
├── requirements.txt
├── manage.py
└── README.md
```

---

## 🗄️ Database Schema

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  CustomUser  │     │   Category   │     │ ProductImage │
│──────────────│     │──────────────│     │──────────────│
│ email (PK)   │     │ name         │     │ image_url    │
│ first_name   │     │ slug (unique)│     │ is_primary   │
│ last_name    │     │ created_at   │     │ product (FK) │
│ password     │     │ updated_at   │     │ created_at   │
│ is_active    │     └──────┬───────┘     └──────┬───────┘
│ is_staff     │            │ 1:N                │ N:1
│ date_joined  │     ┌──────┴───────┐     ┌──────┴───────┐
└──────┬───────┘     │   Product    │─────│   Product    │
       │             │──────────────│     └──────────────┘
       │             │ name         │
       │ 1:N         │ slug (unique)│
       │             │ description  │
┌──────┴───────┐     │ price        │
│    Cart      │     │ stock_qty    │
│──────────────│     │ is_active    │
│ user (FK)    │     │ category(FK) │
│ created_at   │     └──────┬───────┘
│ updated_at   │            │
└──────┬───────┘            │
       │ 1:N                │
┌──────┴───────┐            │
│  CartItem    │────────────┘ N:1
│──────────────│
│ cart (FK)    │
│ product (FK) │
│ quantity     │
│ price_snap   │
└──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Order     │     │  OrderItem   │     │   Payment    │
│──────────────│     │──────────────│     │──────────────│
│ user (FK)    │──┐  │ order (FK)   │     │ order (1:1)  │
│ status       │  └──│ product (FK) │     │ stripe_id    │
│ total_amount │     │ quantity     │     │ status       │
│ ship_address │     │ price_snap   │     │ amount       │
│ created_at   │     │ created_at   │     │ currency     │
│ updated_at   │     └──────────────┘     │ client_secret│
└──────────────┘                          │ created_at   │
                                          └──────────────┘
```

---

## 🔌 API Endpoints

### Authentication (`/auth/`)

| Method  | Endpoint                 | Description                 | Auth |
|---------|--------------------------|-----------------------------|------|
| `POST`  | `/auth/register/`        | Create a new account        | ❌    |
| `POST`  | `/auth/login/`           | Login & get JWT tokens      | ❌    |
| `POST`  | `/auth/logout/`          | Blacklist refresh token     | ✅    |
| `POST`  | `/auth/token/refresh/`   | Refresh access token        | ❌    |
| `POST`  | `/auth/change-password/` | Change password             | ✅    |
| `GET`   | `/auth/me/`              | Get current user profile    | ✅    |
| `PATCH` | `/auth/me/`              | Update current user profile | ✅    |

### Products (`/products/`)

| Method      | Endpoint                | Description                                | Auth    |
|-------------|-------------------------|--------------------------------------------|---------|
| `GET`       | `/products/`            | List all products (filterable, searchable) | ❌       |
| `POST`      | `/products/`            | Create a product                           | ✅ Admin |
| `GET`       | `/products/{slug}/`     | Get product details                        | ❌       |
| `PUT/PATCH` | `/products/{slug}/`     | Update a product                           | ✅ Admin |
| `DELETE`    | `/products/{slug}/`     | Delete a product                           | ✅ Admin |
| `GET`       | `/products/categories/` | List all categories                        | ❌       |
| `POST`      | `/products/categories/` | Create a category                          | ✅ Admin |

### Cart (`/cart/`)

| Method   | Endpoint            | Description             | Auth |
|----------|---------------------|-------------------------|------|
| `GET`    | `/cart/`            | Get current user's cart | ✅    |
| `POST`   | `/cart/items/`      | Add item to cart        | ✅    |
| `PATCH`  | `/cart/items/{id}/` | Update item quantity    | ✅    |
| `DELETE` | `/cart/items/{id}/` | Remove item from cart   | ✅    |
| `DELETE` | `/cart/clear/`      | Clear the entire cart   | ✅    |

### Orders (`/orders/`)

| Method  | Endpoint               | Description              | Auth    |
|---------|------------------------|--------------------------|---------|
| `GET`   | `/orders/`             | List user's orders       | ✅       |
| `POST`  | `/orders/`             | Place an order from cart | ✅       |
| `GET`   | `/orders/{id}/`        | Get order details        | ✅       |
| `PATCH` | `/orders/{id}/status/` | Update order status      | ✅ Admin |

### Payments (`/payments/`)

| Method | Endpoint                   | Description                 | Auth |
|--------|----------------------------|-----------------------------|------|
| `POST` | `/payments/create-intent/` | Create Stripe PaymentIntent | ✅    |
| `POST` | `/payments/confirm/`       | Confirm a payment           | ✅    |
| `GET`  | `/payments/{id}/`          | Get payment details         | ✅    |
| `POST` | `/payments/webhook/`       | Stripe webhook handler      | ❌    |

> 📄 For complete request/response examples, see the **[Full API Documentation](./API_DOCUMENTATION.md)**

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- Stripe Account (for payments)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/ecommerce-api-drf.git
cd ecommerce-api-drf
```

### 2. Create a Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```env
# Django
SECRET_KEY=your-super-secret-key
DJANGO_SETTINGS_MODULE=config.settings.dev

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=ecommerce_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_CURRENCY=usd
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Create a Superuser

```bash
python manage.py createsuperuser
```

### 7. Start the Development Server

```bash
python manage.py runserver
```

### 8. Explore the API

- **Swagger UI:** [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)
- **Admin Panel:** [http://localhost:8000/admin/](http://localhost:8000/admin/)

---

## 🔑 Environment Variables

| Variable                 | Description                                                            | Required |
|--------------------------|------------------------------------------------------------------------|----------|
| `SECRET_KEY`             | Django secret key                                                      | ✅        |
| `DJANGO_SETTINGS_MODULE` | Settings module path (`config.settings.dev` or `config.settings.prod`) | ✅        |
| `DB_ENGINE`              | Database engine                                                        | ✅        |
| `DB_NAME`                | Database name                                                          | ✅        |
| `DB_USER`                | Database user                                                          | ✅        |
| `DB_PASSWORD`            | Database password                                                      | ✅        |
| `DB_HOST`                | Database host                                                          | ✅        |
| `DB_PORT`                | Database port (default: `5432`)                                        | ❌        |
| `STRIPE_SECRET_KEY`      | Stripe secret API key                                                  | ✅        |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key                                                 | ✅        |
| `STRIPE_WEBHOOK_SECRET`  | Stripe webhook signing secret                                          | ✅        |
| `STRIPE_CURRENCY`        | Default currency (default: `usd`)                                      | ❌        |
| `ALLOWED_HOSTS`          | Comma-separated allowed hosts (prod only)                              | ✅ (prod) |

---

## ⚠️ Current Limitations

While this project demonstrates solid backend fundamentals, there are some known limitations:

| #  | Limitation                    | Details                                                                                                  |
|----|-------------------------------|----------------------------------------------------------------------------------------------------------|
| 1  | **No Automated Tests**        | The project currently lacks unit tests and integration tests. The `tests.py` files exist but are empty.  |
| 2  | **No Email Verification**     | Users can register with any email without verification. No email confirmation or "forgot password" flow. |
| 3  | **No Rate Limiting**          | API endpoints are not rate-limited, making them vulnerable to brute-force attacks.                       |
| 4  | **No Caching Layer**          | No Redis/Memcached caching is implemented, which could be a bottleneck at scale.                         |
| 5  | **No Image Upload**           | Product images are stored as URLs only — no actual file upload handling (e.g., S3, Cloudinary).          |
| 6  | **No Logging to File**        | Logging is configured at a basic level without structured logging or external log management.            |
| 7  | **No CI/CD Pipeline**         | No GitHub Actions, Docker, or automated deployment setup.                                                |
| 8  | **No Docker Support**         | Project does not include a `Dockerfile` or `docker-compose.yml` for containerized deployment.            |
| 9  | **No Permission Granularity** | Admin vs. regular user permissions are basic. No role-based access control (RBAC) system.                |
| 10 | **No Soft Deletes**           | Deleting a product or order permanently removes it from the database.                                    |
| 11 | **Dev Endpoint Exposed**      | The `/auth/users/` list endpoint is for development only and should be removed before production.        |
| 12 | **No API Versioning**         | Endpoints are not versioned (e.g., `/api/v1/`), which can complicate future breaking changes.            |

---

## 🔮 Future Work

Here's the roadmap for upcoming improvements:

- [ ] 🧪 **Add Comprehensive Tests** — Unit tests for services/selectors, integration tests for API endpoints using
  `pytest` and `factory_boy`
- [ ] 📧 **Email Verification & Password Reset** — Implement email confirmation on registration and "forgot password"
  flow
- [ ] 🐳 **Docker & Docker Compose** — Containerize the application with PostgreSQL, Redis, and the Django app
- [ ] ⚡ **Redis Caching** — Add caching for product listings, categories, and frequently accessed data
- [ ] 🚦 **Rate Limiting** — Implement throttling with DRF's built-in throttle classes or `django-ratelimit`
- [ ] 🔄 **API Versioning** — Introduce `/api/v1/` prefix for all endpoints
- [ ] 📦 **Product Variants** — Support for sizes, colors, and other product variations
- [ ] ⭐ **Reviews & Ratings** — Allow users to review and rate products
- [ ] 🔍 **Elasticsearch Integration** — Full-text search with relevance scoring
- [ ] 📊 **Admin Dashboard API** — Sales analytics, order statistics, revenue reports
- [ ] 🖼️ **Image Upload to S3/Cloudinary** — Replace URL-based images with actual file uploads
- [ ] 📱 **Push Notifications** — Order status change notifications

---

## 🤝 Contributing

Contributions are welcome! If you'd like to contribute:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

---

<p align="center">
  <b>Built with ❤️ using Django REST Framework</b>
  <br><br>
  <a href="./API_DOCUMENTATION.md">📄 API Docs</a> •
  <a href="#-getting-started">🚀 Get Started</a> •
  <a href="#-future-work">🔮 Roadmap</a>

</p>
