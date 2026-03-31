const API_BASE_URL = "http://localhost:8000";

export type AuthToken = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: number;
  name: string;
  email: string;
};

export type Product = {
  id: number;
  seller_id: number;
  title: string;
  sku: string;
  sell_price: number;
  stock: number;
  marketplace: string;
};

export type DashboardSummary = {
  total_products: number;
  low_stock_items: number;
  average_price: number;
  total_orders: number;
  total_sales: number;
  total_units_sold: number;
};

export type OrderItemInput = {
  product_id: number;
  quantity: number;
  unit_price: number;
};

export type Order = {
  id: number;
  seller_id: number;
  order_number: string;
  marketplace: string;
  total_amount: number;
  items: Array<{
    id: number;
    product_id: number;
    quantity: number;
    unit_price: number;
  }>;
};

export type BuyboxInput = {
  sku: string;
  SellPrice: number;
  ShippingPrice: number;
  TotalPrice: number;
  MinCompetitorPrice: number;
  MinTotalPriceInSnapshot: number;
  PriceGap: number;
  TotalPriceGap: number;
  PriceGapPercent: number;
  PriceRank: number;
  PriceRankNormalized: number;
  TotalCompetitorsInSnapshot: number;
  PositiveFeedbackPercent: number;
  MaxFeedbackInSnapshot: number;
  FeedbackGapFromMax: number;
  IsMinSellPrice: number;
  IsMinTotalPrice: number;
  IsFBA: number;
};

export type BuyboxPrediction = {
  recommended_price: number;
  confidence: number;
  model_name: string;
};

export type AgentResponse = {
  action: string;
  result: string;
};

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || "Request failed");
  }

  if (response.status === 204) {
    return {} as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  signup(name: string, email: string, password: string) {
    return request<User>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
  },
  login(email: string, password: string) {
    return request<AuthToken>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  },
  me(token: string) {
    return request<User>("/auth/me", { method: "GET" }, token);
  },
  getSummary(token: string) {
    return request<DashboardSummary>("/dashboard/summary", { method: "GET" }, token);
  },
  listProducts(token: string) {
    return request<Product[]>("/products", { method: "GET" }, token);
  },
  createProduct(
    token: string,
    payload: Omit<Product, "id" | "seller_id">
  ) {
    return request<Product>(
      "/products",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token
    );
  },
  listOrders(token: string) {
    return request<Order[]>("/orders", { method: "GET" }, token);
  },
  createOrder(
    token: string,
    payload: { order_number: string; marketplace: string; items: OrderItemInput[] }
  ) {
    return request<Order>(
      "/orders",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token
    );
  },
  predictBuybox(token: string, payload: BuyboxInput) {
    return request<BuyboxPrediction>(
      "/predict/buybox",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token
    );
  },
  agentChat(token: string, prompt: string) {
    return request<AgentResponse>(
      "/agent/chat",
      {
        method: "POST",
        body: JSON.stringify({ prompt }),
      },
      token
    );
  },
};
