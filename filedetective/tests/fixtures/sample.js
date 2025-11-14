// Sample JavaScript file for testing
import React from 'react';
import { useState, useEffect } from 'react';
import './styles.css';
const axios = require('axios');

// Utility function
export function calculateTotal(items) {
  return items.reduce((sum, item) => sum + item.price, 0);
}

// Arrow function
const formatCurrency = (amount) => {
  return `$${amount.toFixed(2)}`;
};

// Async arrow function
const fetchData = async (url) => {
  const response = await axios.get(url);
  return response.data;
};

// Main class
export class ShoppingCart {
  constructor(userId) {
    this.userId = userId;
    this.items = [];
  }

  addItem(item) {
    this.items.push(item);
  }

  async checkout() {
    const total = calculateTotal(this.items);
    await this.processPayment(total);
    this.clear();
  }

  static async processPayment(amount) {
    // Payment processing logic
    return true;
  }

  clear() {
    this.items = [];
  }
}

// Async function
async function loadUserCart(userId) {
  const cart = await fetchData(`/api/cart/${userId}`);
  return new ShoppingCart(cart.userId);
}
