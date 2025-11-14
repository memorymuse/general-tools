// Sample TypeScript file for testing
import { EventEmitter } from 'events';
import type { User, Product } from '@/types';
import './global.css';

// Interface (will be ignored by regex parser)
interface CartItem {
  productId: string;
  quantity: number;
  price: number;
}

// Type alias (will be ignored)
type PaymentStatus = 'pending' | 'completed' | 'failed';

// Service class
export class CartService extends EventEmitter {
  private items: Map<string, CartItem>;

  constructor(private userId: string) {
    super();
    this.items = new Map();
  }

  async addItem(product: Product, quantity: number): Promise<void> {
    const item: CartItem = {
      productId: product.id,
      quantity,
      price: product.price
    };
    this.items.set(product.id, item);
    this.emit('itemAdded', item);
  }

  getTotal(): number {
    let total = 0;
    for (const item of this.items.values()) {
      total += item.price * item.quantity;
    }
    return total;
  }

  static async processPayment(amount: number): Promise<PaymentStatus> {
    // Simulate payment processing
    return 'completed';
  }
}

// Generic function
export function findItem<T extends CartItem>(
  items: T[],
  predicate: (item: T) => boolean
): T | undefined {
  return items.find(predicate);
}

// Async arrow function with type annotations
const fetchProducts = async (categoryId: string): Promise<Product[]> => {
  const response = await fetch(`/api/products/${categoryId}`);
  return response.json();
};
