"""Lightweight data models for the application."""

from dataclasses import dataclass


@dataclass(slots=True)
class Product:
    id: int
    name: str
    description: str
    price: float
    stock_quantity: int
    category: str
    created_at: str


@dataclass(slots=True)
class Customer:
    id: int
    name: str
    email: str
    phone: str
    created_at: str


@dataclass(slots=True)
class Order:
    id: int
    customer_id: int
    total_amount: float
    email_sent: int
    created_at: str


@dataclass(slots=True)
class OrderItem:
    id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: float
