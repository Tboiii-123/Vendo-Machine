---

# Mini Vending API

A RESTful API built with **Django REST Framework** for a vending system. It supports user registration, authentication, product management, deposits, purchases, and session handling. Swagger documentation is included for API exploration.

---

## Features

* User authentication (register, login, logout)
* Buyer deposit and reset
* Product management for sellers (create, update, delete, list)
* Product purchase with automatic change calculation
* Session management to prevent concurrent logins
* Swagger documentation

---

## Installation

1. **Clone the repository**

```bash
git clone <your-repo-url>
cd <repo-folder>
```

2. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. **Install dependencies**

```bash
pip install -r requirements.txt
```

4. **Apply migrations**

```bash
python manage.py migrate
```

5. **Run the development server**

```bash
python manage.py runserver
```

6. **Access Swagger UI**

```
http://127.0.0.1:8000/swagger/
```

---

## API Endpoints

### Auth

| Endpoint                | Method | Description              |
| ----------------------- | ------ | ------------------------ |
| `/api/auth/register/`   | POST   | Register a new user      |
| `/api/auth/login/`      | POST   | Login and get JWT tokens |
| `/api/auth/logout_all/` | POST   | Logout all sessions      |
| `/api/auth/user/`       | GET    | Get current user info    |

### Deposit

| Endpoint              | Method | Description                      |
| --------------------- | ------ | -------------------------------- |
| `/api/deposit/`       | POST   | Deposit coins (buyers only)      |
| `/api/deposit/reset/` | POST   | Reset deposit to 0 (buyers only) |

### Products

| Endpoint                | Method           | Description                               |
| ----------------------- | ---------------- | ----------------------------------------- |
| `/api/products/`        | GET              | List all products                         |
| `/api/products/create/` | POST             | Create a product (sellers only)           |
| `/api/products/<id>/`   | PUT/PATCH/DELETE | Update or delete a product (sellers only) |

### Purchase

| Endpoint    | Method | Description               |
| ----------- | ------ | ------------------------- |
| `/api/buy/` | POST   | Buy product (buyers only) |

---

## User Roles

* **Buyer**

  * Can deposit coins
  * Can buy products
  * Can reset deposit
* **Seller**

  * Can create, update, and delete products

---

## Data Models

* **User**

  * `user_name`, `email`, `password`, `role`, `deposit`
* **Product**

  * `product_name`, `cost`, `amount_available`, `seller`
* **UserSession**

  * Tracks active sessions to prevent multiple logins

---

## Notes

* Only predefined coin values are accepted for deposits: `COINS = [5, 10, 20, 50, 100]`.
* JWT authentication is used. Include `Authorization: Bearer <token>` for protected endpoints.
* Swagger UI provides interactive documentation and testing.

---

## License

This project is licensed under the MIT License.

---


