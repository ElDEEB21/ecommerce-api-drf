# 🛒 E-Commerce API Documentation

> **Version:** 1.0.0
> **Base URL:** `https://your-domain.com/`
> **Last Updated:** March 5, 2026

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Pagination](#pagination)
4. [Error Handling](#error-handling)
5. [API Endpoints](#api-endpoints)
    - [Auth / Accounts](#1-auth--accounts)
    - [Products](#2-products)
    - [Categories](#3-categories)
    - [Cart](#4-cart)
    - [Orders](#5-orders)
    - [Payments](#6-payments)
6. [Enums & Status Values](#enums--status-values)
7. [Interactive API Docs](#interactive-api-docs)
8. [Cross-App Synchronization](#cross-app-synchronization)
9. [Payment Flow (Step by Step)](#payment-flow-step-by-step)
10. [Quick Reference Table](#quick-reference-table)

---

## Overview

This is a RESTful E-Commerce API built with Django REST Framework. It supports user authentication (JWT), product
browsing, cart management, order placement, and Stripe-based payments.

**Content Type:** All requests and responses use `application/json` unless otherwise noted.

---

## Authentication

The API uses **JWT (JSON Web Tokens)** via `djangorestframework-simplejwt`.

### Token Delivery

Tokens can be delivered in two ways:

1. **JSON Response (default):** Tokens are returned in the response body.
2. **HTTP-Only Cookies:** Append `?use_cookies=true` to login/register requests. Tokens are set as secure HTTP-only
   cookies.

### Using Tokens

| Method               | How to Send                                   |
|----------------------|-----------------------------------------------|
| **Header (default)** | `Authorization: Bearer <access_token>`        |
| **Cookie**           | Cookies are sent automatically by the browser |

### Token Lifetimes

| Token         | Lifetime  |
|---------------|-----------|
| Access Token  | 5 minutes |
| Refresh Token | 7 days    |

> ⚠️ Refresh tokens are **rotated** on each refresh and the old token is **blacklisted**.

---

## Pagination

All list endpoints use **PageNumberPagination** with a default page size of **10**.

### Query Parameters

| Parameter | Type    | Description               |
|-----------|---------|---------------------------|
| `page`    | integer | Page number (starts at 1) |

### Response Format

```json
{
  "count": 50,
  "next": "https://your-domain.com/products/?page=2",
  "previous": null,
  "results": [ ... ]
}
```

---

## Error Handling

All errors return a consistent JSON format:

```json
{
  "error": "Description of the error"
}
```

or

```json
{
  "detail": "Description of the error"
}
```

### Common HTTP Status Codes

| Code  | Meaning                              |
|-------|--------------------------------------|
| `200` | Success                              |
| `201` | Created                              |
| `400` | Bad Request (validation error)       |
| `401` | Unauthorized (missing/invalid token) |
| `403` | Forbidden (insufficient permissions) |
| `404` | Not Found                            |
| `500` | Internal Server Error                |

---

## API Endpoints

---

### 1. Auth / Accounts

Base path: `/auth/`

---

#### 1.1 Register

Create a new user account.

|                  |                                                                       |
|------------------|-----------------------------------------------------------------------|
| **URL**          | `POST /auth/register/`                                                |
| **Auth**         | ❌ Not required                                                        |
| **Query Params** | `use_cookies` (optional, `true`/`false`) — deliver tokens via cookies |

**Request Body:**

| Field        | Type           | Required | Description                                             |
|--------------|----------------|----------|---------------------------------------------------------|
| `email`      | string (email) | ✅        | User's email address (must be unique)                   |
| `first_name` | string         | ✅        | User's first name                                       |
| `last_name`  | string         | ✅        | User's last name                                        |
| `password`   | string         | ✅        | Password (validated against Django password validators) |
| `password2`  | string         | ✅        | Password confirmation (must match `password`)           |

**Success Response:** `201 Created`

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_staff": false,
    "date_joined": "2026-03-04T12:00:00Z"
  },
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

> If `?use_cookies=true`, the `tokens` field is omitted and tokens are set as HTTP-only cookies.

---

#### 1.2 Login

Authenticate a user and receive JWT tokens.

|                  |                                          |
|------------------|------------------------------------------|
| **URL**          | `POST /auth/login/`                      |
| **Auth**         | ❌ Not required                           |
| **Query Params** | `use_cookies` (optional, `true`/`false`) |

**Request Body:**

| Field      | Type           | Required | Description     |
|------------|----------------|----------|-----------------|
| `email`    | string (email) | ✅        | User's email    |
| `password` | string         | ✅        | User's password |

**Success Response:** `200 OK`

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "is_staff": false,
    "date_joined": "2026-03-04T12:00:00Z"
  },
  "tokens": {
    "access": "eyJ...",
    "refresh": "eyJ..."
  }
}
```

**Error Responses:**

| Status | Reason              |
|--------|---------------------|
| `401`  | Invalid credentials |
| `403`  | Account is disabled |

---

#### 1.3 Logout

Blacklist the refresh token and delete auth cookies.

|          |                      |
|----------|----------------------|
| **URL**  | `POST /auth/logout/` |
| **Auth** | ✅ Required           |

**Request Body:**

| Field     | Type   | Required | Description                                   |
|-----------|--------|----------|-----------------------------------------------|
| `refresh` | string | ✅*       | Refresh token (can also be read from cookies) |

> *If using cookie-based auth, the refresh token is read from the cookie automatically.

**Success Response:** `200 OK`

```json
{
  "detail": "Logged out successfully",
  "security_info": {
    "refresh_token": "blacklisted and cannot be reused",
    "access_token": "will expire naturally in ~5 minutes",
    "cookies": "deleted (if cookie-based auth was used)"
  }
}
```

---

#### 1.4 Refresh Token

Get a new access token using a valid refresh token.

|                  |                                          |
|------------------|------------------------------------------|
| **URL**          | `POST /auth/token/refresh/`              |
| **Auth**         | ❌ Not required                           |
| **Query Params** | `use_cookies` (optional, `true`/`false`) |

**Request Body:**

| Field     | Type   | Required | Description       |
|-----------|--------|----------|-------------------|
| `refresh` | string | ✅*       | The refresh token |

> *If using cookie-based auth, the refresh token is read from the cookie automatically.

**Success Response (JSON mode):** `200 OK`

```json
{
  "access": "eyJ...",
  "refresh": "eyJ..."
}
```

**Success Response (Cookie mode):** `200 OK`

```json
{
  "detail": "Token refreshed successfully"
}
```

> The old refresh token is blacklisted and a new one is issued (rotation).

---

#### 1.5 Change Password

Change the current user's password.

|          |                               |
|----------|-------------------------------|
| **URL**  | `POST /auth/change-password/` |
| **Auth** | ✅ Required                    |

**Request Body:**

| Field           | Type   | Required | Description                                        |
|-----------------|--------|----------|----------------------------------------------------|
| `old_password`  | string | ✅        | Current password                                   |
| `new_password`  | string | ✅        | New password (validated against Django validators) |
| `new_password2` | string | ✅        | New password confirmation                          |

**Success Response:** `200 OK`

```json
{
  "detail": "Password changed successfully"
}
```

---

#### 1.6 Get Current User

Retrieve the authenticated user's profile.

|          |                 |
|----------|-----------------|
| **URL**  | `GET /auth/me/` |
| **Auth** | ✅ Required      |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_active": true,
  "is_staff": false,
  "date_joined": "2026-03-04T12:00:00Z"
}
```

---

#### 1.7 Update Current User

Update the authenticated user's profile (partial update).

|          |                   |
|----------|-------------------|
| **URL**  | `PATCH /auth/me/` |
| **Auth** | ✅ Required        |

**Request Body (all fields optional):**

| Field        | Type           | Description        |
|--------------|----------------|--------------------|
| `first_name` | string         | Updated first name |
| `last_name`  | string         | Updated last name  |
| `email`      | string (email) | Updated email      |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "email": "updated@example.com",
  "first_name": "Jane",
  "last_name": "Doe",
  "is_active": true,
  "is_staff": false,
  "date_joined": "2026-03-04T12:00:00Z"
}
```

---

#### 1.8 List / Create Users ⚠️ (Dev Only)

> ⚠️ **This endpoint is for development purposes only and should be removed in production.**

|          |                    |
|----------|--------------------|
| **URL**  | `GET /auth/users/` |
| **Auth** | ❌ Not required     |

Returns a list of all users.

|          |                     |
|----------|---------------------|
| **URL**  | `POST /auth/users/` |
| **Auth** | ❌ Not required      |

Creates a new user (admin-level creation).

---

### 2. Products

Base path: `/products/`

---

#### 2.1 List Products

Get a paginated list of all active products.

|          |                  |
|----------|------------------|
| **URL**  | `GET /products/` |
| **Auth** | ❌ Not required   |

**Query Parameters:**

| Parameter        | Type    | Description                                                               |
|------------------|---------|---------------------------------------------------------------------------|
| `page`           | integer | Page number                                                               |
| `category`       | integer | Filter by category ID                                                     |
| `category__slug` | string  | Filter by category slug                                                   |
| `is_active`      | boolean | Filter by active status (`true`/`false`)                                  |
| `search`         | string  | Search in product `name` and `description`                                |
| `ordering`       | string  | Order by: `price`, `-price`, `created_at`, `-created_at`, `name`, `-name` |

**Success Response:** `200 OK`

```json
{
  "count": 25,
  "next": "http://your-domain.com/products/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "slug": "wireless-headphones",
      "description": "High-quality wireless headphones...",
      "price": "99.99",
      "stock_quantity": 50,
      "is_active": true,
      "category": {
        "id": 1,
        "name": "Electronics",
        "slug": "electronics"
      },
      "images": [
        {
          "id": 1,
          "product": 1,
          "image_url": "https://example.com/image.jpg",
          "is_primary": true
        }
      ]
    }
  ]
}
```

---

#### 2.2 Create Product 🔒

Create a new product.

|          |                         |
|----------|-------------------------|
| **URL**  | `POST /products/`       |
| **Auth** | ✅ Required (Admin only) |

**Request Body:**

| Field            | Type    | Required | Description                                     |
|------------------|---------|----------|-------------------------------------------------|
| `name`           | string  | ✅        | Product name                                    |
| `slug`           | string  | ✅        | URL-friendly slug (must be unique)              |
| `description`    | string  | ✅        | Product description                             |
| `price`          | decimal | ✅        | Product price (e.g. `"99.99"`)                  |
| `stock_quantity` | integer | ✅        | Available stock                                 |
| `is_active`      | boolean | ❌        | Whether the product is active (default: `true`) |
| `category_id`    | integer | ✅        | ID of the category                              |

**Success Response:** `201 Created`

Returns the created product object (same format as list item above).

---

#### 2.3 Get Product Detail

Get a single product by its slug.

|          |                         |
|----------|-------------------------|
| **URL**  | `GET /products/{slug}/` |
| **Auth** | ❌ Not required          |

**URL Parameters:**

| Parameter | Type   | Description  |
|-----------|--------|--------------|
| `slug`    | string | Product slug |

**Success Response:** `200 OK`

Returns a single product object.

---

#### 2.4 Update Product 🔒

Update a product (full or partial update).

|          |                                                      |
|----------|------------------------------------------------------|
| **URL**  | `PUT /products/{slug}/` or `PATCH /products/{slug}/` |
| **Auth** | ✅ Required (Admin only)                              |

**Request Body:** Same fields as [Create Product](#22-create-product-) (all optional for `PATCH`).

**Success Response:** `200 OK`

---

#### 2.5 Delete Product 🔒

Delete a product.

|          |                            |
|----------|----------------------------|
| **URL**  | `DELETE /products/{slug}/` |
| **Auth** | ✅ Required (Admin only)    |

**Success Response:** `204 No Content`

---

#### 2.6 Upload Product Image 🔒

Add an image to a product.

|          |                                 |
|----------|---------------------------------|
| **URL**  | `POST /products/{slug}/images/` |
| **Auth** | ✅ Required (Admin only)         |

**URL Parameters:**

| Parameter | Type   | Description  |
|-----------|--------|--------------|
| `slug`    | string | Product slug |

**Request Body:**

| Field       | Type         | Required | Description              |
|-------------|--------------|----------|--------------------------|
| `image_url` | string (URL) | ✅        | URL of the product image |

**Success Response:** `201 Created`

Returns the full product object with the new image included.

---

#### 2.7 Get Product Image

Get a single product image by ID.

|          |                              |
|----------|------------------------------|
| **URL**  | `GET /products/images/{id}/` |
| **Auth** | ❌ Not required               |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "product": 1,
  "image_url": "https://example.com/image.jpg",
  "is_primary": true
}
```

---

#### 2.8 Update Product Image 🔒

|          |                                                                |
|----------|----------------------------------------------------------------|
| **URL**  | `PUT /products/images/{id}/` or `PATCH /products/images/{id}/` |
| **Auth** | ✅ Required (Admin only)                                        |

**Request Body:**

| Field        | Type         | Required | Description                       |
|--------------|--------------|----------|-----------------------------------|
| `product`    | integer      | ✅ (PUT)  | Product ID                        |
| `image_url`  | string (URL) | ✅ (PUT)  | Image URL                         |
| `is_primary` | boolean      | ❌        | Whether this is the primary image |

---

#### 2.9 Delete Product Image 🔒

|          |                                 |
|----------|---------------------------------|
| **URL**  | `DELETE /products/images/{id}/` |
| **Auth** | ✅ Required (Admin only)         |

**Success Response:** `204 No Content`

---

### 3. Categories

Base path: `/products/categories/`

---

#### 3.1 List Categories

Get all product categories.

|          |                             |
|----------|-----------------------------|
| **URL**  | `GET /products/categories/` |
| **Auth** | ❌ Not required              |

**Success Response:** `200 OK`

```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Electronics",
      "slug": "electronics"
    }
  ]
}
```

---

#### 3.2 Create Category 🔒

|          |                              |
|----------|------------------------------|
| **URL**  | `POST /products/categories/` |
| **Auth** | ✅ Required (Admin only)      |

**Request Body:**

| Field  | Type   | Required | Description                        |
|--------|--------|----------|------------------------------------|
| `name` | string | ✅        | Category name                      |
| `slug` | string | ✅        | URL-friendly slug (must be unique) |

**Success Response:** `201 Created`

---

#### 3.3 Get Category Detail

Get a category with its products.

|          |                                    |
|----------|------------------------------------|
| **URL**  | `GET /products/categories/{slug}/` |
| **Auth** | ❌ Not required                     |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "name": "Electronics",
  "slug": "electronics",
  "products": [
    {
      "id": 1,
      "name": "Wireless Headphones",
      "slug": "wireless-headphones",
      "price": "99.99"
    }
  ]
}
```

---

#### 3.4 Update Category 🔒

|          |                                                                            |
|----------|----------------------------------------------------------------------------|
| **URL**  | `PUT /products/categories/{slug}/` or `PATCH /products/categories/{slug}/` |
| **Auth** | ✅ Required (Admin only)                                                    |

---

#### 3.5 Delete Category 🔒

|          |                                       |
|----------|---------------------------------------|
| **URL**  | `DELETE /products/categories/{slug}/` |
| **Auth** | ✅ Required (Admin only)               |

**Success Response:** `204 No Content`

---

### 4. Cart

Base path: `/cart/`

> All cart endpoints require authentication. Each user has their own cart.

---

#### 4.1 Get Cart

Retrieve the current user's cart with all items.

|          |              |
|----------|--------------|
| **URL**  | `GET /cart/` |
| **Auth** | ✅ Required   |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "user": 1,
  "created_at": "2026-03-04T12:00:00Z",
  "updated_at": "2026-03-04T12:30:00Z",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Wireless Headphones",
        "slug": "wireless-headphones",
        "price": "99.99",
        "stock_quantity": 50,
        "is_active": true
      },
      "quantity": 2,
      "price_snapshot": "99.99",
      "item_total": "199.98",
      "created_at": "2026-03-04T12:15:00Z"
    }
  ],
  "total_items": 2,
  "cart_total": "199.98"
}
```

---

#### 4.2 Add Item to Cart

Add a product to the cart.

|          |                     |
|----------|---------------------|
| **URL**  | `POST /cart/items/` |
| **Auth** | ✅ Required          |

**Request Body:**

| Field        | Type    | Required | Description                    |
|--------------|---------|----------|--------------------------------|
| `product_id` | integer | ✅        | ID of the product to add       |
| `quantity`   | integer | ❌        | Quantity to add (default: `1`) |

**Success Response:** `200 OK`

Returns the full cart object (same format as [Get Cart](#41-get-cart)).

> If the product already exists in the cart, the quantity is updated.

---

#### 4.3 Update Cart Item

Update the quantity of a cart item.

|          |                                                                |
|----------|----------------------------------------------------------------|
| **URL**  | `PUT /cart/items/{item_id}/` or `PATCH /cart/items/{item_id}/` |
| **Auth** | ✅ Required                                                     |

**URL Parameters:**

| Parameter | Type    | Description  |
|-----------|---------|--------------|
| `item_id` | integer | Cart item ID |

**Request Body:**

| Field      | Type    | Required | Description                                  |
|------------|---------|----------|----------------------------------------------|
| `quantity` | integer | ✅        | New quantity (set to `0` to remove the item) |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "product": {
    "id": 1,
    "name": "Wireless Headphones",
    "slug": "wireless-headphones",
    "price": "99.99",
    "stock_quantity": 50,
    "is_active": true
  },
  "quantity": 3,
  "price_snapshot": "99.99",
  "item_total": "299.97",
  "created_at": "2026-03-04T12:15:00Z"
}
```

> If `quantity` is set to `0`, the item is removed and you get:
> ```json
> { "message": "Cart item removed successfully" }
> ```

---

#### 4.4 Remove Cart Item

Remove a specific item from the cart.

|          |                                 |
|----------|---------------------------------|
| **URL**  | `DELETE /cart/items/{item_id}/` |
| **Auth** | ✅ Required                      |

**Success Response:** `200 OK`

```json
{
  "message": "Cart item removed successfully"
}
```

---

#### 4.5 Clear Cart

Remove all items from the cart.

|          |                     |
|----------|---------------------|
| **URL**  | `POST /cart/clear/` |
| **Auth** | ✅ Required          |

**Success Response:** `200 OK`

```json
{
  "message": "Cart cleared successfully"
}
```

---

### 5. Orders

Base path: `/orders/`

---

#### 5.1 Checkout

Create an order from the current cart contents. The entire operation (order creation, stock deduction, cart clearing,
and status transition) runs inside a **single atomic transaction** — if any step fails, everything is rolled back.

|          |                          |
|----------|--------------------------|
| **URL**  | `POST /orders/checkout/` |
| **Auth** | ✅ Required               |

**Request Body:**

| Field              | Type   | Required | Description                    |
|--------------------|--------|----------|--------------------------------|
| `shipping_address` | string | ❌        | Shipping address for the order |

**What happens on checkout:**

1. All cart items are validated for stock availability and active status **before** any changes.
2. Order `total_amount` and `price_snapshot` are taken from the **cart's `price_snapshot`** (the price at the time the
   item was added to cart).
3. Product stock is deducted atomically.
4. Cart items are cleared.
5. Order status is set to `processing`.

**Success Response:** `201 Created`

```json
{
  "id": 1,
  "user": 1,
  "status": "processing",
  "created_at": "2026-03-04T12:30:00Z",
  "updated_at": "2026-03-04T12:30:00Z",
  "items": [
    {
      "id": 1,
      "product": {
        "id": 1,
        "name": "Wireless Headphones",
        "slug": "wireless-headphones",
        "price": "99.99",
        "stock_quantity": 48,
        "is_active": true
      },
      "quantity": 2,
      "price_snapshot": "99.99",
      "item_total": "199.98",
      "created_at": "2026-03-04T12:30:00Z"
    }
  ],
  "total_price": "199.98"
}
```

**Error Responses:**

| Status | Reason                                    |
|--------|-------------------------------------------|
| `400`  | Cart not found / Cart is empty            |
| `400`  | Product is no longer available (inactive) |
| `400`  | Not enough stock for a product            |

> ⚠️ If checkout fails at any point, no order is created, no stock is deducted, and the cart remains unchanged.

---

#### 5.2 List My Orders

Get all orders for the authenticated user.

|          |                |
|----------|----------------|
| **URL**  | `GET /orders/` |
| **Auth** | ✅ Required     |

**Success Response:** `200 OK`

Returns a paginated list of order objects (same format as checkout response).

---

#### 5.3 Get Order Detail

Get details of a specific order.

|          |                                                          |
|----------|----------------------------------------------------------|
| **URL**  | `GET /orders/{order_id}/`                                |
| **Auth** | ✅ Required (order must belong to the authenticated user) |

**URL Parameters:**

| Parameter  | Type    | Description |
|------------|---------|-------------|
| `order_id` | integer | Order ID    |

**Success Response:** `200 OK`

Returns a single order object.

---

#### 5.4 Cancel Order

Cancel a pending or processing order. Only orders in `pending` or `processing` status can be cancelled.

|          |                                                          |
|----------|----------------------------------------------------------|
| **URL**  | `POST /orders/{order_id}/cancel/`                        |
| **Auth** | ✅ Required (order must belong to the authenticated user) |

**URL Parameters:**

| Parameter  | Type    | Description |
|------------|---------|-------------|
| `order_id` | integer | Order ID    |

**What happens on cancellation:**

1. If there is an active (pending/processing) Stripe PaymentIntent for this order, it is **cancelled on Stripe** and the
   payment record is set to `cancelled`.
2. The order status is set to `cancelled`.
3. Product stock is **restored** for all items in the order.

**Success Response:** `200 OK`

```json
{
  "message": "Order cancelled successfully"
}
```

**Error Responses:**

| Status | Reason                                                          |
|--------|-----------------------------------------------------------------|
| `400`  | Order cannot be cancelled (already shipped/delivered/cancelled) |
| `404`  | Order not found or does not belong to user                      |

---

#### 5.5 List All Orders 🔒 (Admin)

Get all orders in the system.

|          |                               |
|----------|-------------------------------|
| **URL**  | `GET /orders/admin/`          |
| **Auth** | ✅ Required (Admin/Staff only) |

**Success Response:** `200 OK`

Returns a paginated list of all order objects. Returns empty list for non-staff users.

---

#### 5.6 Update Order Status 🔒 (Admin)

Update the status of any order. Only valid transitions are allowed (see [Order Statuses](#order-statuses)).

|          |                                         |
|----------|-----------------------------------------|
| **URL**  | `POST /orders/admin/{order_id}/status/` |
| **Auth** | ✅ Required (Admin/Staff only)           |

**URL Parameters:**

| Parameter  | Type    | Description |
|------------|---------|-------------|
| `order_id` | integer | Order ID    |

**Request Body:**

| Field    | Type   | Required | Description                                              |
|----------|--------|----------|----------------------------------------------------------|
| `status` | string | ✅        | New order status (see [Order Statuses](#order-statuses)) |

**Success Response:** `200 OK`

```json
{
  "message": "Order status updated successfully"
}
```

**Error Responses:**

| Status | Reason                                         |
|--------|------------------------------------------------|
| `400`  | Invalid status value or transition not allowed |
| `403`  | User is not staff                              |
| `404`  | Order not found                                |

---

### 6. Payments

Base path: `/payments/`

> This module integrates with **Stripe** for payment processing.

---

#### 6.1 Get Stripe Publishable Key

Retrieve the Stripe publishable key for initializing Stripe.js on the frontend.

|          |                         |
|----------|-------------------------|
| **URL**  | `GET /payments/config/` |
| **Auth** | ✅ Required              |

**Success Response:** `200 OK`

```json
{
  "publishable_key": "pk_test_..."
}
```

---

#### 6.2 Create Payment Intent

Create a Stripe PaymentIntent for an order. This is the first step in the payment flow.

|          |                                 |
|----------|---------------------------------|
| **URL**  | `POST /payments/create-intent/` |
| **Auth** | ✅ Required                      |

> ℹ️ The order must be in `pending` or `processing` status. After checkout, the order status is set to `processing`,
> which is valid for payment creation.

**Request Body:**

| Field             | Type    | Required | Description                                   |
|-------------------|---------|----------|-----------------------------------------------|
| `order_id`        | integer | ✅        | ID of the order to pay for                    |
| `currency`        | string  | ❌        | 3-letter ISO currency code (default: `"usd"`) |
| `idempotency_key` | string  | ❌        | Unique key to prevent duplicate payments      |

**Success Response:** `201 Created`

```json
{
  "payment": {
    "id": 1,
    "order": {
      "id": 1,
      "status": "processing",
      "total_amount": "199.98",
      "created_at": "2026-03-04T12:30:00Z"
    },
    "stripe_payment_intent_id": "pi_1234567890",
    "status": "pending",
    "status_display": "Pending",
    "amount": "199.98",
    "currency": "usd",
    "failure_message": null,
    "is_successful": false,
    "is_pending": true,
    "is_failed": false,
    "can_be_refunded": false,
    "created_at": "2026-03-04T12:35:00Z",
    "updated_at": "2026-03-04T12:35:00Z"
  },
  "client_secret": "pi_1234567890_secret_abc",
  "publishable_key": "pk_test_..."
}
```

> **Frontend Flow:** Use `client_secret` with Stripe.js `confirmCardPayment()` to complete the payment.

---

#### 6.3 List My Payments

Get all payments for the authenticated user.

|          |                  |
|----------|------------------|
| **URL**  | `GET /payments/` |
| **Auth** | ✅ Required       |

**Query Parameters:**

| Parameter | Type   | Description                                                          |
|-----------|--------|----------------------------------------------------------------------|
| `status`  | string | Filter by payment status (see [Payment Statuses](#payment-statuses)) |

**Success Response:** `200 OK`

Returns an array of payment objects.

```json
[
  {
    "id": 1,
    "order": { "id": 1, "status": "processing", "total_amount": "199.98", "created_at": "..." },
    "stripe_payment_intent_id": "pi_1234567890",
    "status": "succeeded",
    "status_display": "Succeeded",
    "amount": "199.98",
    "currency": "usd",
    "failure_message": null,
    "is_successful": true,
    "is_pending": false,
    "is_failed": false,
    "can_be_refunded": true,
    "created_at": "2026-03-04T12:35:00Z",
    "updated_at": "2026-03-04T12:36:00Z"
  }
]
```

---

#### 6.4 Get Payment Detail

Get details of a specific payment.

|          |                               |
|----------|-------------------------------|
| **URL**  | `GET /payments/{payment_id}/` |
| **Auth** | ✅ Required (owner or admin)   |

**URL Parameters:**

| Parameter    | Type    | Description |
|--------------|---------|-------------|
| `payment_id` | integer | Payment ID  |

**Success Response:** `200 OK`

Returns a single payment object.

---

#### 6.5 Get Payment Status

Get a lightweight status check for a payment.

|          |                                      |
|----------|--------------------------------------|
| **URL**  | `GET /payments/{payment_id}/status/` |
| **Auth** | ✅ Required (owner or admin)          |

**Success Response:** `200 OK`

```json
{
  "id": 1,
  "order_id": 1,
  "status": "succeeded",
  "status_display": "Succeeded",
  "is_successful": true
}
```

---

#### 6.6 Get Payment by Order

Get the payment associated with a specific order.

|          |                                   |
|----------|-----------------------------------|
| **URL**  | `GET /payments/order/{order_id}/` |
| **Auth** | ✅ Required (owner or admin)       |

**URL Parameters:**

| Parameter  | Type    | Description |
|------------|---------|-------------|
| `order_id` | integer | Order ID    |

**Success Response:** `200 OK`

Returns a single payment object.

---

#### 6.7 Cancel Payment

Cancel a pending or processing payment and its associated Stripe PaymentIntent. This also cancels the associated order
and restores product stock.

|          |                          |
|----------|--------------------------|
| **URL**  | `POST /payments/cancel/` |
| **Auth** | ✅ Required               |

**Request Body:**

| Field        | Type    | Required | Description                 |
|--------------|---------|----------|-----------------------------|
| `payment_id` | integer | ✅        | ID of the payment to cancel |

**What happens on cancellation:**

1. The Stripe PaymentIntent is cancelled.
2. The payment record status is set to `cancelled`.
3. The associated order is set to `cancelled`.
4. Product stock is **restored** for all items in the order.

**Success Response:** `200 OK`

```json
{
  "message": "Payment cancelled successfully.",
  "payment": { ... }
}
```

**Error Responses:**

| Status | Reason                                             |
|--------|----------------------------------------------------|
| `400`  | Payment is not in `pending` or `processing` status |
| `400`  | Stripe could not cancel the PaymentIntent          |
| `403`  | Not authorized (payment belongs to another user)   |

---

#### 6.8 Refund Payment

Refund a successful payment (full or partial). This also cancels the associated order and restores product stock.

|          |                             |
|----------|-----------------------------|
| **URL**  | `POST /payments/refund/`    |
| **Auth** | ✅ Required (owner or admin) |

**Request Body:**

| Field        | Type    | Required | Description                                                                |
|--------------|---------|----------|----------------------------------------------------------------------------|
| `payment_id` | integer | ✅        | ID of the payment to refund                                                |
| `amount`     | decimal | ❌        | Partial refund amount (omit for full refund, min: `0.01`)                  |
| `reason`     | string  | ❌        | Refund reason: `"duplicate"`, `"fraudulent"`, or `"requested_by_customer"` |

**What happens on refund:**

1. A Stripe Refund is created for the PaymentIntent.
2. The payment record status is set to `refunded`.
3. If the order is still in `pending` or `processing` status, it is set to `cancelled`.
4. Product stock is **restored** for all items in the order.

**Success Response:** `200 OK`

```json
{
  "message": "Payment refunded successfully.",
  "payment": { ... }
}
```

**Error Responses:**

| Status | Reason                                                                  |
|--------|-------------------------------------------------------------------------|
| `400`  | Payment cannot be refunded (not in `succeeded` status)                  |
| `400`  | Refund amount exceeds payment amount                                    |
| `403`  | Not authorized (non-staff user trying to refund another user's payment) |

---

#### 6.9 Sync Payment Status

Manually sync a payment's status with Stripe (useful if webhooks are delayed).

|          |                               |
|----------|-------------------------------|
| **URL**  | `POST /payments/sync-status/` |
| **Auth** | ✅ Required (owner or admin)   |

**Request Body:**

| Field               | Type   | Required | Description                                 |
|---------------------|--------|----------|---------------------------------------------|
| `payment_intent_id` | string | ✅        | Stripe PaymentIntent ID (starts with `pi_`) |

**Success Response:** `200 OK`

```json
{
  "message": "Payment status synced.",
  "payment": { ... }
}
```

---

#### 6.10 Payment Statistics

Get payment statistics for the authenticated user.

|          |                             |
|----------|-----------------------------|
| **URL**  | `GET /payments/statistics/` |
| **Auth** | ✅ Required                  |

**Success Response:** `200 OK`

```json
{
  "total_payments": 10,
  "total_spent": "1599.90",
  "pending_count": 1,
  "processing_count": 0,
  "succeeded_count": 7,
  "failed_count": 1,
  "cancelled_count": 0,
  "refunded_count": 1
}
```

---

#### 6.11 Stripe Webhook

Endpoint for Stripe to send webhook events. **This is NOT called by the frontend.**

|          |                                                |
|----------|------------------------------------------------|
| **URL**  | `POST /payments/webhook/`                      |
| **Auth** | ❌ Not required (verified via Stripe signature) |

> This endpoint is called by Stripe servers to notify about payment events. The frontend does **not** need to interact
> with this endpoint.

**Handled Events:**

| Stripe Event                    | Effect                                                                                                                                |
|---------------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| `payment_intent.succeeded`      | Payment → `succeeded`. Order stays `processing` (or advances from `pending` → `processing`). Idempotent — skips if already succeeded. |
| `payment_intent.payment_failed` | Payment → `failed`. Failure message is recorded. Order is unchanged.                                                                  |
| `payment_intent.canceled`       | Payment → `cancelled`. Order → `cancelled`. Product stock is **restored**.                                                            |
| `charge.refunded`               | Payment → `refunded` (if fully refunded).                                                                                             |

---

## Enums & Status Values

### Order Statuses

| Value        | Display    | Description                                          |
|--------------|------------|------------------------------------------------------|
| `pending`    | Pending    | Order has been created, awaiting checkout processing |
| `processing` | Processing | Order has been checked out, awaiting payment         |
| `shipped`    | Shipped    | Order has been shipped                               |
| `delivered`  | Delivered  | Order has been delivered                             |
| `cancelled`  | Cancelled  | Order has been cancelled                             |

**Allowed Status Transitions:**

| From         | Allowed To                |
|--------------|---------------------------|
| `pending`    | `processing`, `cancelled` |
| `processing` | `shipped`, `cancelled`    |
| `shipped`    | `delivered`               |
| `delivered`  | *(none — terminal state)* |
| `cancelled`  | *(none — terminal state)* |

> ℹ️ Checkout automatically transitions the order from `pending` → `processing`. The frontend never sees `pending`
> orders.

### Payment Statuses

| Value        | Display    | Description                              |
|--------------|------------|------------------------------------------|
| `pending`    | Pending    | Payment intent created, awaiting payment |
| `processing` | Processing | Payment is being processed by Stripe     |
| `succeeded`  | Succeeded  | Payment completed successfully           |
| `failed`     | Failed     | Payment failed                           |
| `cancelled`  | Cancelled  | Payment was cancelled                    |
| `refunded`   | Refunded   | Payment was refunded                     |

### Refund Reasons

| Value                   | Display          |
|-------------------------|------------------|
| `duplicate`             | Duplicate        |
| `fraudulent`            | Fraudulent       |
| `requested_by_customer` | Customer request |

---

## Interactive API Docs

The API also provides auto-generated interactive documentation:

| URL                | Description                           |
|--------------------|---------------------------------------|
| `GET /api/docs/`   | Swagger UI (interactive API explorer) |
| `GET /api/schema/` | OpenAPI 3.0 schema (JSON/YAML)        |

---

## Cross-App Synchronization

The **Cart**, **Orders**, and **Payments** apps are tightly synchronized. Every action that affects one app
automatically propagates to the others. Here is a summary of all side effects:

| Action                                                      | Order Effect                                     | Payment Effect                         | Stock Effect  |
|-------------------------------------------------------------|--------------------------------------------------|----------------------------------------|---------------|
| **Checkout** (`POST /orders/checkout/`)                     | Created → `processing`                           | *(none yet)*                           | **Deducted**  |
| **Cancel Order** (`POST /orders/{id}/cancel/`)              | → `cancelled`                                    | Active payment **cancelled on Stripe** | **Restored**  |
| **Create Payment Intent** (`POST /payments/create-intent/`) | *(no change)*                                    | Payment record created (`pending`)     | *(no change)* |
| **Cancel Payment** (`POST /payments/cancel/`)               | → `cancelled`                                    | → `cancelled` on Stripe                | **Restored**  |
| **Refund Payment** (`POST /payments/refund/`)               | → `cancelled` (if pending/processing)            | → `refunded` on Stripe                 | **Restored**  |
| **Webhook: `payment_intent.succeeded`**                     | Stays `processing` (or `pending` → `processing`) | → `succeeded`                          | *(no change)* |
| **Webhook: `payment_intent.canceled`**                      | → `cancelled`                                    | → `cancelled`                          | **Restored**  |
| **Webhook: `payment_intent.payment_failed`**                | *(no change)*                                    | → `failed`                             | *(no change)* |
| **Webhook: `charge.refunded`**                              | *(no change)*                                    | → `refunded`                           | *(no change)* |

### Key Guarantees

- **Atomic transactions**: Checkout, order cancellation, payment cancellation, and refund all run inside
  `transaction.atomic()`. If any step fails, everything rolls back.
- **No orphaned orders**: Cancelling or refunding a payment always cancels the associated order and restores stock.
- **No orphaned payments**: Cancelling an order always cancels any active Stripe PaymentIntent.
- **No double-deduction**: Stock is validated **before** any changes during checkout. Stock updates use database-level
  `F()` expressions for atomicity.
- **Idempotent webhooks**: The `payment_intent.succeeded` webhook skips if the payment is already marked as succeeded.
  Order status transitions are only attempted when valid.
- **Price consistency**: The order total and item prices are taken from the cart's `price_snapshot` (the price at the
  time items were added to cart), not the current product price.

---

## Payment Flow (Step by Step)

Here's the recommended frontend flow for processing a payment:

```
1. User adds items to cart
   POST /cart/items/  (repeat for each product)
   → price_snapshot is saved at this point

2. User proceeds to checkout
   POST /orders/checkout/  →  returns order with status "processing"
   → Stock is deducted, cart is cleared (atomic)
   → Order total uses cart price_snapshot

3. Frontend fetches Stripe publishable key (can be cached)
   GET /payments/config/  →  returns publishable_key

4. Frontend creates a payment intent
   POST /payments/create-intent/  { order_id }  →  returns client_secret
   → If a pending/failed PaymentIntent already exists, it is reused

5. Frontend uses Stripe.js to confirm payment
   stripe.confirmCardPayment(client_secret, { payment_method: { card } })

6. Stripe sends webhook to backend (automatic)
   POST /payments/webhook/
   → payment_intent.succeeded  → Payment = succeeded, Order stays processing
   → payment_intent.payment_failed → Payment = failed (user can retry step 4)

7. Frontend checks payment status (poll or after Stripe.js callback)
   GET /payments/{payment_id}/status/  →  poll until succeeded/failed

8. (Optional) If user wants to cancel before paying:
   POST /payments/cancel/  { payment_id }
   → Payment cancelled on Stripe, order cancelled, stock restored

9. (Optional) Admin ships the order:
   POST /orders/admin/{order_id}/status/  { status: "shipped" }
```

---

## Quick Reference Table

| Method      | Endpoint                           | Auth     | Description                                         |
|-------------|------------------------------------|----------|-----------------------------------------------------|
| `POST`      | `/auth/register/`                  | ❌        | Register new user                                   |
| `POST`      | `/auth/login/`                     | ❌        | Login                                               |
| `POST`      | `/auth/logout/`                    | ✅        | Logout (blacklist token)                            |
| `POST`      | `/auth/token/refresh/`             | ❌        | Refresh access token                                |
| `POST`      | `/auth/change-password/`           | ✅        | Change password                                     |
| `GET`       | `/auth/me/`                        | ✅        | Get current user profile                            |
| `PATCH`     | `/auth/me/`                        | ✅        | Update current user profile                         |
|             |                                    |          |                                                     |
| `GET`       | `/products/`                       | ❌        | List products (filterable, searchable)              |
| `POST`      | `/products/`                       | 🔒 Admin | Create product                                      |
| `GET`       | `/products/{slug}/`                | ❌        | Get product detail                                  |
| `PUT/PATCH` | `/products/{slug}/`                | 🔒 Admin | Update product                                      |
| `DELETE`    | `/products/{slug}/`                | 🔒 Admin | Delete product                                      |
| `POST`      | `/products/{slug}/images/`         | 🔒 Admin | Upload product image                                |
| `GET`       | `/products/images/{id}/`           | ❌        | Get product image                                   |
| `PUT/PATCH` | `/products/images/{id}/`           | 🔒 Admin | Update product image                                |
| `DELETE`    | `/products/images/{id}/`           | 🔒 Admin | Delete product image                                |
| `GET`       | `/products/categories/`            | ❌        | List categories                                     |
| `POST`      | `/products/categories/`            | 🔒 Admin | Create category                                     |
| `GET`       | `/products/categories/{slug}/`     | ❌        | Get category with products                          |
| `PUT/PATCH` | `/products/categories/{slug}/`     | 🔒 Admin | Update category                                     |
| `DELETE`    | `/products/categories/{slug}/`     | 🔒 Admin | Delete category                                     |
|             |                                    |          |                                                     |
| `GET`       | `/cart/`                           | ✅        | Get user's cart                                     |
| `POST`      | `/cart/items/`                     | ✅        | Add item to cart                                    |
| `PUT/PATCH` | `/cart/items/{item_id}/`           | ✅        | Update cart item quantity                           |
| `DELETE`    | `/cart/items/{item_id}/`           | ✅        | Remove cart item                                    |
| `POST`      | `/cart/clear/`                     | ✅        | Clear entire cart                                   |
|             |                                    |          |                                                     |
| `GET`       | `/orders/`                         | ✅        | List user's orders                                  |
| `POST`      | `/orders/checkout/`                | ✅        | Create order from cart (deducts stock, clears cart) |
| `GET`       | `/orders/{order_id}/`              | ✅        | Get order detail                                    |
| `POST`      | `/orders/{order_id}/cancel/`       | ✅        | Cancel order (cancels payment, restores stock)      |
| `GET`       | `/orders/admin/`                   | 🔒 Staff | List all orders                                     |
| `POST`      | `/orders/admin/{order_id}/status/` | 🔒 Staff | Update order status                                 |
|             |                                    |          |                                                     |
| `GET`       | `/payments/`                       | ✅        | List user's payments                                |
| `GET`       | `/payments/config/`                | ✅        | Get Stripe publishable key                          |
| `POST`      | `/payments/create-intent/`         | ✅        | Create Stripe PaymentIntent                         |
| `GET`       | `/payments/{payment_id}/`          | ✅        | Get payment detail                                  |
| `GET`       | `/payments/{payment_id}/status/`   | ✅        | Get payment status                                  |
| `GET`       | `/payments/order/{order_id}/`      | ✅        | Get payment by order                                |
| `POST`      | `/payments/cancel/`                | ✅        | Cancel payment (cancels order, restores stock)      |
| `POST`      | `/payments/refund/`                | ✅        | Refund payment (cancels order, restores stock)      |
| `POST`      | `/payments/sync-status/`           | ✅        | Sync payment status with Stripe                     |
| `GET`       | `/payments/statistics/`            | ✅        | Get payment statistics                              |
| `POST`      | `/payments/webhook/`               | ❌        | Stripe webhook (server-to-server)                   |
