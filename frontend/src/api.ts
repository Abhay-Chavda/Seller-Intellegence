const viteEnv = (import.meta as ImportMeta & {
  env?: Record<string, string | undefined>;
}).env || {};

const API_BASE_URL =
  viteEnv.VITE_API_BASE_URL || (viteEnv.DEV ? "http://127.0.0.1:8000" : "/api");
const AGENT_API_BASE_URL =
  viteEnv.VITE_AGENT_API_BASE_URL || (viteEnv.DEV ? "http://127.0.0.1:8001" : "/agent-api");

export type AuthToken = {
  access_token: string;
  token_type: string;
};

export type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  subscription_type: string;
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

export type DashboardCategoryCount = {
  label: string;
  value: number;
};

export type DashboardMarketplaceMix = {
  marketplace: string;
  listings: number;
  avg_price: number;
};

export type DashboardRevenuePoint = {
  day: string;
  revenue: number;
  units: number;
};

export type DashboardTopListing = {
  sku: string;
  title: string;
  marketplace: string;
  status: string;
  quantity: number;
  price: number;
  competitor_low_price: number | null;
  revenue: number;
  units_sold: number;
};

export type DashboardRecentSale = {
  sale_date: string;
  sku: string;
  title: string;
  units_sold: number;
  revenue: number;
};

export type DashboardOverview = {
  source: string;
  seller_display_name: string;
  company_name: string | null;
  total_listings: number;
  active_listings: number;
  low_stock_items: number;
  total_sales: number;
  total_units_sold: number;
  average_listing_price: number;
  prime_listings: number;
  marketplace_mix: DashboardMarketplaceMix[];
  revenue_trend: DashboardRevenuePoint[];
  top_listings: DashboardTopListing[];
  recent_sales: DashboardRecentSale[];
  listing_status: DashboardCategoryCount[];
  inventory_bands: DashboardCategoryCount[];
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
  created_at: string;
  items: Array<{
    id: number;
    product_id: number;
    quantity: number;
    unit_price: number;
  }>;
};

export type Agent = {
  id: number;
  seller_id: number;
  agent_id: string;
  agent_name: string;
  agent_version: string;
  project_endpoint: string | null;
  instructions: string;
  created_at: string;
  updated_at: string;
};

export type AgentChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type AgentCreatePayload = {
  agent_name: string;
  instructions?: string;
  existing_agent_id?: string;
  project_endpoint?: string;
  model_deployment_name?: string;
};

export type AdminSummary = {
  total_users: number;
  admin_users: number;
  demo_subscriptions: number;
  users_with_agents: number;
  total_orders: number;
  total_products: number;
  total_sales: number;
};

export type AdminSubscriptionStat = {
  subscription_type: string;
  users_count: number;
};

export type AdminUserUsage = {
  id: number;
  name: string;
  email: string;
  role: string;
  subscription_type: string;
  created_at: string;
  products_count: number;
  orders_count: number;
  total_sales: number;
  last_order_at: string | null;
  last_product_update_at: string | null;
  agent_name: string | null;
  agent_version: string | null;
  project_endpoint: string | null;
  agent_updated_at: string | null;
};

export type AdminAgentUsage = {
  seller_id: number;
  seller_name: string;
  seller_email: string;
  subscription_type: string;
  agent_name: string;
  agent_version: string;
  project_endpoint: string | null;
  agent_updated_at: string;
  orders_count: number;
  products_count: number;
  total_sales: number;
};

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
  baseUrl = API_BASE_URL
): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    // If the backend returns Pydantic validation errors, it will be an object with
    // a `detail` array. Include that in the thrown error so the UI can display it.
    let errMsg = "Request failed";
    if (body) {
      if (body.detail) {
        try {
          errMsg = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
        } catch (e) {
          errMsg = String(body.detail);
        }
      } else {
        try {
          errMsg = JSON.stringify(body);
        } catch (e) {
          errMsg = String(body);
        }
      }
    }
    throw new ApiError(response.status, errMsg);
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
  getOverview(token: string) {
    return request<DashboardOverview>("/dashboard/overview", { method: "GET" }, token);
  },
  getSummary(token: string) {
    return request<DashboardSummary>("/dashboard/summary", { method: "GET" }, token);
  },
  getAdminSummary(token: string) {
    return request<AdminSummary>("/admin/summary", { method: "GET" }, token);
  },
  getAdminUsers(token: string) {
    return request<AdminUserUsage[]>("/admin/users", { method: "GET" }, token);
  },
  getAdminSubscriptions(token: string) {
    return request<AdminSubscriptionStat[]>("/admin/subscriptions", { method: "GET" }, token);
  },
  getAdminAgentUsage(token: string) {
    return request<AdminAgentUsage[]>("/admin/agents/usage", { method: "GET" }, token);
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
  updateProduct(
    token: string,
    id: number,
    payload: Partial<Omit<Product, "id" | "seller_id">>
  ) {
    return request<Product>(
      `/products/${id}`,
      {
        method: "PUT",
        body: JSON.stringify(payload),
      },
      token
    );
  },
  deleteProduct(token: string, id: number) {
    return request<void>(`/products/${id}`, { method: "DELETE" }, token);
  },
  listOrders(token: string, search?: string) {
    const url = search ? `/orders?search=${encodeURIComponent(search)}` : "/orders";
    return request<Order[]>(url, { method: "GET" }, token);
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
  getCurrentAgent(token: string) {
    return request<{ agent: Agent | null }>("/agent/current", { method: "GET" }, token, AGENT_API_BASE_URL);
  },
  createAgent(token: string, payload: AgentCreatePayload) {
    return request<{ created: boolean; agent: Agent }>(
      "/agent/create",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token,
      AGENT_API_BASE_URL
    );
  },
  deleteAgent(token: string) {
    return request<{ deleted: boolean }>("/agent/current", { method: "DELETE" }, token, AGENT_API_BASE_URL);
  },
  resetAgentChat(token: string) {
    return request<{ ok: boolean }>("/agent/chat/reset", { method: "POST" }, token, AGENT_API_BASE_URL);
  },
  chatWithAgent(
    token: string,
    payload: { prompt: string; history?: AgentChatMessage[]; reset_history?: boolean }
  ) {
    return request<{ reply: string; history: AgentChatMessage[] }>(
      "/agent/chat",
      {
        method: "POST",
        body: JSON.stringify(payload),
      },
      token,
      AGENT_API_BASE_URL
    );
  },
};
