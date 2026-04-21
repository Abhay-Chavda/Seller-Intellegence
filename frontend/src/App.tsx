import { FormEvent, ReactNode, useEffect, useState, useMemo } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';
import {
  AdminAgentUsage,
  AdminSubscriptionStat,
  AdminSummary,
  AdminUserUsage,
  Agent,
  AgentChatMessage,
  AgentCreatePayload,
  ApiError,
  api,
  DashboardOverview,
  DashboardRevenuePoint,
  Order,
  Product,
  User,
} from "./api";

const viteEnv = (import.meta as ImportMeta & {
  env?: Record<string, string | undefined>;
}).env || {};

type AuthMode = "login" | "signup";
type DashboardPage = "overview" | "inventory" | "orders" | "agents" | "admin";
type NoticeTone = "error" | "success";
type ThemeMode = "dark" | "light";
const AGENTS_ENABLED = viteEnv.VITE_ENABLE_AGENTS === "true" || Boolean(viteEnv.DEV);

const dashboardPages: Array<{ id: Exclude<DashboardPage, "admin">; label: string; icon: string }> = [
  { id: "overview", label: "Dashboard", icon: "📊" },
  { id: "inventory", label: "Inventory", icon: "📦" },
  { id: "orders", label: "Orders", icon: "🛍️" },
  { id: "agents", label: "Agents", icon: "🤖" },
];

const adminDashboardPage = { id: "admin" as const, label: "Admin", icon: "🛠️" };
const landingMetrics: Array<{ value: string; label: string; description: string }> = [
  {
    value: "Live",
    label: "seller dashboard",
    description: "See revenue, units sold, catalog size, and low-stock pressure as soon as you log in.",
  },
  {
    value: "Fast",
    label: "inventory actions",
    description: "Update listings, change pricing, and restock products without moving across multiple tools.",
  },
  {
    value: "Simple",
    label: "order flow",
    description: "Create orders, search records, and export seller data from one clean workspace.",
  },
];
const landingFeatures: Array<{ title: string; description: string }> = [
  {
    title: "Performance dashboard",
    description: "Follow revenue movement, order activity, and low-stock alerts without juggling spreadsheets or tabs.",
  },
  {
    title: "Inventory control",
    description: "Search products, update stock, edit pricing, and keep your catalog ready for daily seller operations.",
  },
  {
    title: "Order management",
    description: "Create new orders, filter activity by date, and keep marketplace sales records organized in one place.",
  },
  {
    title: "Seller assistant",
    description: "Use your connected AI assistant to help with seller workflows, product operations, and everyday questions.",
  },
];
const landingQuickFeatures = [
  "Dashboard visibility",
  "Product updates",
  "Low-stock tracking",
  "Order exports",
];

function formatCurrency(value: number): string {
  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(value);
}

function formatInteger(value: number): string {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(value);
}

function formatShortDate(value: string): string {
  if (!value) return "N/A";
  try {
    return new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric" }).format(new Date(value));
  } catch (e) {
    return "N/A";
  }
}

function downloadCSV(data: any[], filename: string) {
  if (data.length === 0) return;
  const headers = Object.keys(data[0]).join(",");
  const rows = data.map(obj => Object.values(obj).map(v => `"${v}"`).join(",")).join("\n");
  const csvContent = "data:text/csv;charset=utf-8," + headers + "\n" + rows;
  const encodedUri = encodeURI(csvContent);
  const link = document.createElement("a");
  link.setAttribute("href", encodedUri);
  link.setAttribute("download", filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

const COLORS = ['#6366f1', '#a855f7', '#ec4899', '#22d3ee', '#10b981', '#f59e0b'];
const LOW_STOCK_LIMIT = 10;
const QUICK_RESTOCK_UNITS = 10;
const DASHBOARD_RANGE_OPTIONS = [7, 14, 30, 90, 365] as const;

function getGeneratedOrderNumber(): string {
  return `ORD-${Date.now().toString().slice(-8)}`;
}

function getDashboardRangeLabel(days: number): string {
  return days >= 365 ? "1 year" : `${days} days`;
}

function formatChartDate(value: string, rangeDays: number): string {
  if (!value) return "N/A";
  try {
    return new Intl.DateTimeFormat(
      "en-US",
      rangeDays >= 365
        ? { month: "short" }
        : { month: "short", day: "numeric" }
    ).format(new Date(value));
  } catch (e) {
    return "N/A";
  }
}

function formatLongDate(value: string): string {
  if (!value) return "N/A";
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(new Date(value));
  } catch (e) {
    return "N/A";
  }
}

function renderInlineAgentText(text: string): ReactNode[] {
  return text.split(/(\*\*.*?\*\*)/g).filter(Boolean).map((part, index) => {
    if (part.startsWith("**") && part.endsWith("**") && part.length > 4) {
      return <strong key={`bold-${index}`}>{part.slice(2, -2)}</strong>;
    }
    return <span key={`text-${index}`}>{part}</span>;
  });
}

function renderAgentContent(content: string): ReactNode[] {
  const lines = content.split("\n");
  const blocks: ReactNode[] = [];
  let paragraphLines: string[] = [];
  let listItems: string[] = [];

  const flushParagraph = () => {
    if (paragraphLines.length === 0) return;
    blocks.push(
      <p key={`paragraph-${blocks.length}`}>
        {renderInlineAgentText(paragraphLines.join(" "))}
      </p>
    );
    paragraphLines = [];
  };

  const flushList = () => {
    if (listItems.length === 0) return;
    blocks.push(
      <ul key={`list-${blocks.length}`}>
        {listItems.map((item, index) => (
          <li key={`item-${index}`}>{renderInlineAgentText(item)}</li>
        ))}
      </ul>
    );
    listItems = [];
  };

  lines.forEach((rawLine) => {
    const line = rawLine.trim();

    if (!line) {
      flushParagraph();
      flushList();
      return;
    }

    const bulletMatch = line.match(/^[-*]\s+(.*)$/);
    if (bulletMatch) {
      flushParagraph();
      listItems.push(bulletMatch[1]);
      return;
    }

    flushList();
    paragraphLines.push(line);
  });

  flushParagraph();
  flushList();

  return blocks;
}

export default function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("token") || "");
  const [theme, setTheme] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem("theme");
    return saved === "light" ? "light" : "dark";
  });
  const [mode, setMode] = useState<AuthMode>("login");
  const [showLanding, setShowLanding] = useState<boolean>(() => !Boolean(localStorage.getItem("token")));
  const [page, setPage] = useState<DashboardPage>("overview");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [name, setName] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<NoticeTone>("success");
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [isAddingProduct, setIsAddingProduct] = useState(false);
  const [isAddingOrder, setIsAddingOrder] = useState(false);
  const [restockingProductId, setRestockingProductId] = useState<number | null>(null);
  const [dashboardDays, setDashboardDays] = useState(365);
  const [ordersFrom, setOrdersFrom] = useState("");
  const [ordersTo, setOrdersTo] = useState("");
  const [currentAgent, setCurrentAgent] = useState<Agent | null>(null);
  const [agentHistory, setAgentHistory] = useState<AgentChatMessage[]>([]);
  const [agentPrompt, setAgentPrompt] = useState("");
  const [agentBusy, setAgentBusy] = useState(false);
  const [agentChatBusy, setAgentChatBusy] = useState(false);
  const [adminLoading, setAdminLoading] = useState(false);
  const [adminSummary, setAdminSummary] = useState<AdminSummary | null>(null);
  const [adminUsers, setAdminUsers] = useState<AdminUserUsage[]>([]);
  const [adminSubscriptions, setAdminSubscriptions] = useState<AdminSubscriptionStat[]>([]);
  const [adminAgentUsage, setAdminAgentUsage] = useState<AdminAgentUsage[]>([]);
  const [agentForm, setAgentForm] = useState<AgentCreatePayload>({
    agent_name: "",
    instructions: "",
    existing_agent_id: "",
    project_endpoint: "",
    model_deployment_name: "",
  });
  const [newProduct, setNewProduct] = useState<Omit<Product, "id" | "seller_id">>({
    title: "",
    sku: "",
    sell_price: 0,
    stock: 0,
    marketplace: "Amazon",
  });
  const [newOrder, setNewOrder] = useState({
    order_number: "",
    marketplace: "Amazon",
    product_id: 0,
    quantity: 1,
    unit_price: 0,
  });

  function handleUnauthorizedError(err: unknown): boolean {
    if (
      err instanceof ApiError &&
      err.status === 401
    ) {
      handleLogout();
      setShowLanding(false);
      setMessage("Session expired. Please sign in again.");
      setMessageTone("error");
      return true;
    }
    return false;
  }

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  function toggleTheme() {
    setTheme(current => current === "dark" ? "light" : "dark");
  }

  function resetAuthForm() {
    setName("");
    setEmail("");
    setPassword("");
    setShowPassword(false);
  }

  function openAuth(nextMode: AuthMode) {
    setMode(nextMode);
    setShowLanding(false);
    resetAuthForm();
    setMessage("");
  }

  function handleBackToLanding() {
    setShowLanding(true);
    resetAuthForm();
    setMessage("");
  }

  function handleAuthModeSwitch() {
    setMode(current => current === "login" ? "signup" : "login");
    resetAuthForm();
    setMessage("");
  }

  function handleLogout() {
    localStorage.removeItem("token");
    setToken("");
    setUser(null);
    setOverview(null);
    setCurrentAgent(null);
    setAgentHistory([]);
    setAdminSummary(null);
    setAdminUsers([]);
    setAdminSubscriptions([]);
    setAdminAgentUsage([]);
    setMode("login");
    setShowLanding(true);
    resetAuthForm();
    setMessage("");
  }

  async function onCreateProduct(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createProduct(token, newProduct);
      setMessage("Listing created successfully.");
      setMessageTone("success");
      setIsAddingProduct(false);
      setNewProduct({ title: "", sku: "", sell_price: 0, stock: 0, marketplace: "Amazon" });
      await refreshData(token);
    } catch (err) {
      setMessage("Failed to create listing.");
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  async function onUpdateProduct(e: FormEvent) {
    e.preventDefault();
    if (!editingProduct) return;
    setLoading(true);
    try {
      await api.updateProduct(token, editingProduct.id, {
        title: editingProduct.title,
        sku: editingProduct.sku,
        stock: editingProduct.stock,
        sell_price: editingProduct.sell_price,
        marketplace: editingProduct.marketplace,
      });
      setMessage("Product updated successfully.");
      setMessageTone("success");
      setEditingProduct(null);
      await refreshData(token);
    } catch (err) {
      setMessage("Failed to update product.");
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  async function onDeleteProduct(id: number) {
    if (!confirm("Are you sure you want to delete this product?")) return;
    setLoading(true);
    try {
      await api.deleteProduct(token, id);
      setMessage("Product deleted.");
      setMessageTone("success");
      await refreshData(token);
    } catch (err) {
      setMessage("Failed to delete product.");
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  async function onQuickRestock(product: Product) {
    setRestockingProductId(product.id);
    try {
      await api.updateProduct(token, product.id, {
        stock: product.stock + QUICK_RESTOCK_UNITS,
      });
      setMessage(`Restocked ${product.sku} by +${QUICK_RESTOCK_UNITS} units.`);
      setMessageTone("success");
      await refreshData(token);
    } catch (err) {
      setMessage("Quick restock failed.");
      setMessageTone("error");
    } finally {
      setRestockingProductId(null);
    }
  }

  function onOpenCreateOrderModal() {
    if (products.length === 0) {
      setMessage("Please add a product before creating an order.");
      setMessageTone("error");
      return;
    }

    const firstProduct = products[0];
    setNewOrder({
      order_number: getGeneratedOrderNumber(),
      marketplace: firstProduct.marketplace || "Amazon",
      product_id: firstProduct.id,
      quantity: 1,
      unit_price: firstProduct.sell_price,
    });
    setIsAddingOrder(true);
  }

  function onOpenCreateProductModal() {
    setNewProduct({
      title: "",
      sku: "",
      sell_price: 0,
      stock: 0,
      marketplace: "Amazon",
    });
    setIsAddingProduct(true);
  }

  async function onCreateOrder(e: FormEvent) {
    e.preventDefault();
    if (!newOrder.product_id) {
      setMessage("Select a product first.");
      setMessageTone("error");
      return;
    }

    setLoading(true);
    try {
      await api.createOrder(token, {
        order_number: newOrder.order_number.trim() || getGeneratedOrderNumber(),
        marketplace: newOrder.marketplace,
        items: [
          {
            product_id: newOrder.product_id,
            quantity: newOrder.quantity,
            unit_price: newOrder.unit_price,
          },
        ],
      });
      setMessage("Order created successfully.");
      setMessageTone("success");
      setIsAddingOrder(false);
      await refreshData(token);
    } catch (err) {
      setMessage("Failed to create order.");
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!token) {
      localStorage.removeItem("token");
      setCurrentAgent(null);
      setAgentHistory([]);
      return;
    }
    localStorage.setItem("token", token);
    refreshData(token);
    if (AGENTS_ENABLED) {
      refreshAgentData(token, true);
    }
  }, [token]);

  useEffect(() => {
    if (AGENTS_ENABLED && token && page === "agents") {
      refreshAgentData(token, true);
    }
  }, [page, token]);

  useEffect(() => {
    if (!AGENTS_ENABLED && page === "agents") {
      setPage("overview");
      return;
    }
    if (user?.role !== "admin" && page === "admin") {
      setPage("overview");
    }
    if (user?.role === "admin" && page !== "admin") {
      setPage("admin");
    }
  }, [page, user?.role]);

  useEffect(() => {
    if (token && user?.role === "admin" && page === "admin") {
      refreshAdminData(token, true);
    }
  }, [page, token, user?.role]);

  async function refreshData(activeToken: string) {
    try {
      const me = await api.me(activeToken);
      const [ov, pr, ord] = await Promise.all([
        api.getOverview(activeToken),
        api.listProducts(activeToken),
        api.listOrders(activeToken)
      ]);
      setUser(me);
      setOverview(ov);
      setProducts(pr);
      setOrders(ord);
    } catch (err) {
      handleLogout();
    }
  }

  async function refreshAgentData(activeToken: string, silent = false) {
    try {
      const response = await api.getCurrentAgent(activeToken);
      setCurrentAgent(response.agent);
      if (response.agent) {
        setAgentForm(prev => ({
          ...prev,
          agent_name: response.agent?.agent_name || "",
          instructions: response.agent?.instructions || "",
          project_endpoint: response.agent?.project_endpoint || prev.project_endpoint || "",
        }));
      }
    } catch (err) {
      if (handleUnauthorizedError(err)) return;
      setCurrentAgent(null);
      if (!silent) {
        setMessage(err instanceof Error ? err.message : "Agent service is not available.");
        setMessageTone("error");
      }
    }
  }

  async function refreshAdminData(activeToken: string, silent = false) {
    setAdminLoading(true);
    try {
      const [summary, usersResponse, subscriptions, agentUsage] = await Promise.all([
        api.getAdminSummary(activeToken),
        api.getAdminUsers(activeToken),
        api.getAdminSubscriptions(activeToken),
        api.getAdminAgentUsage(activeToken),
      ]);
      setAdminSummary(summary);
      setAdminUsers(usersResponse);
      setAdminSubscriptions(subscriptions);
      setAdminAgentUsage(agentUsage);
    } catch (err) {
      if (handleUnauthorizedError(err)) return;
      if (!silent) {
        setMessage(err instanceof Error ? err.message : "Admin data is not available.");
        setMessageTone("error");
      }
    } finally {
      setAdminLoading(false);
    }
  }

  async function onAuth(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    try {
      if (mode === "signup") await api.signup(name, email, password);
      const auth = await api.login(email, password);
      setToken(auth.access_token);
      resetAuthForm();
    } catch (err) {
      setMessage("Authentication failed. Check your email or password.");
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
  }

  async function onCreateAgent(e: FormEvent) {
    e.preventDefault();
    setAgentBusy(true);
    try {
      const payload: AgentCreatePayload = {
        agent_name: agentForm.agent_name.trim(),
        instructions: agentForm.instructions?.trim() || undefined,
        existing_agent_id: agentForm.existing_agent_id?.trim() || undefined,
        project_endpoint: agentForm.project_endpoint?.trim() || undefined,
        model_deployment_name: agentForm.model_deployment_name?.trim() || undefined,
      };
      const response = await api.createAgent(token, payload);
      setCurrentAgent(response.agent);
      setAgentHistory([]);
      setMessage(response.created ? "Agent created successfully." : "Agent updated successfully.");
      setMessageTone("success");
    } catch (err) {
      if (handleUnauthorizedError(err)) return;
      setMessage(err instanceof Error ? err.message : "Failed to create agent.");
      setMessageTone("error");
    } finally {
      setAgentBusy(false);
    }
  }

  async function onDeleteAgent() {
    if (!currentAgent) return;
    if (!confirm(`Delete the saved agent "${currentAgent.agent_name}" from this app?`)) return;

    setAgentBusy(true);
    try {
      await api.deleteAgent(token);
      setCurrentAgent(null);
      setAgentHistory([]);
      setAgentPrompt("");
      setAgentForm(prev => ({
        ...prev,
        existing_agent_id: "",
        instructions: "",
      }));
      setMessage("Agent deleted from the app.");
      setMessageTone("success");
    } catch (err) {
      if (handleUnauthorizedError(err)) return;
      setMessage(err instanceof Error ? err.message : "Failed to delete agent.");
      setMessageTone("error");
    } finally {
      setAgentBusy(false);
    }
  }

  async function onResetAgentChat() {
    setAgentChatBusy(true);
    try {
      await api.resetAgentChat(token);
      setAgentHistory([]);
      setAgentPrompt("");
      setMessage("Agent chat cleared.");
      setMessageTone("success");
    } catch (err) {
      if (handleUnauthorizedError(err)) return;
      setMessage(err instanceof Error ? err.message : "Failed to clear agent chat.");
      setMessageTone("error");
    } finally {
      setAgentChatBusy(false);
    }
  }

  async function onSendAgentPrompt(e: FormEvent) {
    e.preventDefault();
    if (!currentAgent || !agentPrompt.trim()) return;

    setAgentChatBusy(true);
    try {
      const response = await api.chatWithAgent(token, {
        prompt: agentPrompt.trim(),
        history: agentHistory,
      });
      setAgentHistory(response.history);
      setAgentPrompt("");
    } catch (err) {
      if (handleUnauthorizedError(err)) return;
      setMessage(err instanceof Error ? err.message : "Agent chat failed.");
      setMessageTone("error");
    } finally {
      setAgentChatBusy(false);
    }
  }

  const lowStockProducts = useMemo(
    () => products.filter(p => p.stock < LOW_STOCK_LIMIT),
    [products]
  );

  const dashboardRevenueTrend = useMemo<DashboardRevenuePoint[]>(() => {
    if (!overview) return [];
    const cutoffDate = new Date();
    cutoffDate.setHours(0, 0, 0, 0);
    cutoffDate.setDate(cutoffDate.getDate() - dashboardDays + 1);

    return overview.revenue_trend.filter(point => {
      const currentDate = new Date(point.day);
      return !Number.isNaN(currentDate.getTime()) && currentDate >= cutoffDate;
    });
  }, [overview, dashboardDays]);

  const dashboardRevenueTotal = useMemo(
    () => dashboardRevenueTrend.reduce((total, point) => total + point.revenue, 0),
    [dashboardRevenueTrend]
  );

  const dashboardUnitsTotal = useMemo(
    () => dashboardRevenueTrend.reduce((total, point) => total + point.units, 0),
    [dashboardRevenueTrend]
  );
  const dashboardRangeLabel = getDashboardRangeLabel(dashboardDays);

  const filteredOrders = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    return orders.filter(o => {
      const matchesSearch =
        !query ||
        o.order_number.toLowerCase().includes(query) ||
        o.marketplace.toLowerCase().includes(query);

      const orderDate = new Date(o.created_at);
      if (Number.isNaN(orderDate.getTime())) return false;

      if (ordersFrom) {
        const fromDate = new Date(ordersFrom);
        fromDate.setHours(0, 0, 0, 0);
        if (orderDate < fromDate) return false;
      }

      if (ordersTo) {
        const toDate = new Date(ordersTo);
        toDate.setHours(23, 59, 59, 999);
        if (orderDate > toDate) return false;
      }

      return matchesSearch;
    });
  }, [orders, searchQuery, ordersFrom, ordersTo]);

  const filteredProducts = useMemo(() => {
    if (!searchQuery) return products;
    return products.filter(p => 
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      p.sku.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [products, searchQuery]);

  const visibleDashboardPages = useMemo(
    () =>
      user?.role === "admin"
        ? [adminDashboardPage]
        : dashboardPages.filter(pageItem => AGENTS_ENABLED || pageItem.id !== "agents"),
    [user?.role]
  );

  const filteredAdminUsers = useMemo(() => {
    if (!searchQuery) return adminUsers;
    const query = searchQuery.toLowerCase();
    return adminUsers.filter(entry =>
      entry.name.toLowerCase().includes(query) ||
      entry.email.toLowerCase().includes(query) ||
      entry.role.toLowerCase().includes(query) ||
      entry.subscription_type.toLowerCase().includes(query) ||
      (entry.agent_name || "").toLowerCase().includes(query)
    );
  }, [adminUsers, searchQuery]);

  const filteredAdminAgents = useMemo(() => {
    if (!searchQuery) return adminAgentUsage;
    const query = searchQuery.toLowerCase();
    return adminAgentUsage.filter(entry =>
      entry.seller_name.toLowerCase().includes(query) ||
      entry.seller_email.toLowerCase().includes(query) ||
      entry.agent_name.toLowerCase().includes(query) ||
      entry.subscription_type.toLowerCase().includes(query)
    );
  }, [adminAgentUsage, searchQuery]);

  const selectedOrderProduct = useMemo(
    () => products.find(p => p.id === newOrder.product_id) || null,
    [products, newOrder.product_id]
  );

  if (!token || !user || !overview) {
    return (
      <div className="auth-shell">
        <div className="landing-layout">
          <section className="landing-panel">
            <div className="landing-brand">
              <img src="/logo-mark.svg" alt="SellerIntel logo" className="landing-logo" />
              <div>
                <span className="landing-eyebrow">Seller Intelligence Platform</span>
                <h1>Run your seller operations from one clear, connected workspace.</h1>
              </div>
            </div>

            <p className="landing-copy">
              SellerIntel helps marketplace sellers track performance, manage inventory, organize orders,
              and coordinate AI-assisted workflows without bouncing between disconnected tools.
            </p>

            <div className="landing-metric-grid">
              {landingMetrics.map(metric => (
                <article key={metric.label} className="landing-metric-card">
                  <span className="landing-metric-value">{metric.value}</span>
                  <span className="landing-metric-label">{metric.label}</span>
                  <p>{metric.description}</p>
                </article>
              ))}
            </div>

            <div className="landing-section-head">
              <span className="landing-section-kicker">What you can do</span>
              <h2>Built for day-to-day seller execution</h2>
            </div>
            <div className="landing-feature-grid">
              {landingFeatures.map(feature => (
                <article key={feature.title} className="landing-feature-card">
                  <h3>{feature.title}</h3>
                  <p>{feature.description}</p>
                </article>
              ))}
            </div>
          </section>

          <div className={`auth-card landing-cta-card ${showLanding ? "landing-cta-card--home" : "landing-cta-card--auth"}`}>
            <div className="theme-toggle-row">
              <button type="button" className="theme-toggle-btn" onClick={toggleTheme}>
                <span>{theme === "dark" ? "☀️" : "🌙"}</span>
                <span>{theme === "dark" ? "Light Theme" : "Dark Theme"}</span>
              </button>
            </div>

            {showLanding ? (
              <>
                <span className="landing-badge">Start here</span>
                <h2>Access SellerIntel</h2>
                <p className="landing-cta-copy">
                  Sign in to continue with your seller workspace, or create a new account to start managing products,
                  orders, and insights from one dashboard.
                </p>

                <div className="landing-action-group">
                  <button type="button" className="auth-btn" onClick={() => openAuth("login")}>
                    Login
                  </button>
                  <button type="button" className="auth-btn auth-btn-secondary" onClick={() => openAuth("signup")}>
                    Sign Up
                  </button>
                </div>

                <div className="landing-quick-features">
                  <span className="landing-quick-features-label">Built for sellers</span>
                  <div className="landing-chip-row">
                    {landingQuickFeatures.map(feature => (
                      <span key={feature} className="landing-chip">
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <>
                <button type="button" className="landing-back-btn" onClick={handleBackToLanding}>
                  Back to home
                </button>
                <h1>{mode === "login" ? "Welcome Back" : "Get Started"}</h1>
                <p>
                  {mode === "login"
                    ? "Enter your credentials to access your intelligence dashboard."
                    : "Create your seller workspace and start managing operations in one place."}
                </p>

                <form onSubmit={onAuth} className="auth-form">
                  {mode === "signup" && (
                    <div className="input-group">
                      <span className="input-label">Full Name</span>
                      <input
                        className="auth-input"
                        placeholder="John Doe"
                        value={name}
                        onChange={e => setName(e.target.value)}
                        required
                      />
                    </div>
                  )}

                  <div className="input-group">
                    <span className="input-label">Email Address</span>
                    <input
                      className="auth-input"
                      placeholder="e.g. seller@willow.local"
                      type="email"
                      value={email}
                      onChange={e => setEmail(e.target.value)}
                      required
                    />
                  </div>

                  <div className="input-group">
                    <span className="input-label">Password</span>
                    <div className="auth-password-wrap">
                      <input
                        className="auth-input password-input"
                        placeholder="Enter your secure password"
                        type={showPassword ? "text" : "password"}
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        required
                      />
                      <button
                        type="button"
                        className="password-toggle-btn"
                        onClick={() => setShowPassword(current => !current)}
                      >
                        {showPassword ? "Hide" : "Show"}
                      </button>
                    </div>
                  </div>

                  <button className="auth-btn" disabled={loading}>
                    {loading ? "Processing..." : mode === "login" ? "Sign In" : "Create Account"}
                  </button>
                </form>

                <div className="auth-switch">
                  {mode === "login" ? "Don't have an account?" : "Already have an account?"}
                  <button type="button" className="auth-switch-btn" onClick={handleAuthModeSwitch}>
                    {mode === "login" ? "Sign Up" : "Back to Login"}
                  </button>
                </div>

                {message && (
                  <p className="auth-message" style={{ color: messageTone === "error" ? "var(--error)" : "var(--success)" }}>
                    {message}
                  </p>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="top-navbar">
        <div className="top-navbar-left">
          <div className="brand-lockup">
            <img src="/logo-mark.svg" alt="SellerIntel logo" className="brand-logo" />
            <h1 className="brand-title">SellerIntel</h1>
          </div>
          <nav className="top-nav-list">
            {visibleDashboardPages.map(p => (
              <button
                key={p.id}
                type="button"
                className={`nav-item ${page === p.id ? "active" : ""}`}
                onClick={() => setPage(p.id)}
              >
                <span style={{ fontSize: "1.2rem" }}>{p.icon}</span>
                <span style={{ fontWeight: 500 }}>{p.label}</span>
              </button>
            ))}
          </nav>
        </div>
        <div className="top-navbar-right">
          <button
            type="button"
            className="theme-toggle-btn"
            onClick={toggleTheme}
          >
            <span>{theme === "dark" ? "☀️" : "🌙"}</span>
            <span>{theme === "dark" ? "Light" : "Dark"}</span>
          </button>
          <div className="account-chip">
            <span className="account-label">User Account</span>
            <span className="account-email">{user.email}</span>
          </div>
          <button
            type="button"
            className="nav-item logout-btn"
            onClick={handleLogout}
          >
            <span>🚪</span>
            <span>Logout</span>
          </button>
        </div>
      </header>

      <main className="main-content">
        <header className="app-header">
          <div style={{ position: 'relative', flex: 1, maxWidth: '500px' }}>
            <span style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', opacity: 0.5 }}>🔍</span>
            <input 
              className="search-input" 
              style={{ paddingLeft: '2.5rem' }}
              placeholder={`Search ${page === 'inventory' ? 'products' : page === 'orders' ? 'orders' : page === 'agents' ? 'agent notes' : page === 'admin' ? 'users or agents' : 'anything'}...`} 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>
          {user.role !== "admin" && (
            <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
              <div className="stat-change up" style={{ fontSize: '0.85rem', background: 'rgba(16, 185, 129, 0.1)', padding: '6px 12px', borderRadius: '999px' }}>
                ● {overview.active_listings} Active Listings
              </div>
              <div style={{ fontSize: '0.85rem', background: 'rgba(245, 158, 11, 0.12)', color: 'var(--warning)', padding: '6px 12px', borderRadius: '999px', fontWeight: 600 }}>
                ⚠ {lowStockProducts.length} Low Stock
              </div>
            </div>
          )}
        </header>

        {message && (
          <div className={`notice-banner ${messageTone}`}>
            <span>{message}</span>
            <button
              type="button"
              className="notice-close-btn"
              onClick={() => setMessage("")}
            >
              ✕
            </button>
          </div>
        )}

        {page === "overview" && (
          <>
            <div className="filter-row">
              <span className="filter-label">Dashboard Range</span>
              <div className="filter-chip-group">
                {DASHBOARD_RANGE_OPTIONS.map(days => (
                  <button
                    key={days}
                    type="button"
                    className={`filter-chip ${dashboardDays === days ? "active" : ""}`}
                    onClick={() => setDashboardDays(days)}
                  >
                    {getDashboardRangeLabel(days)}
                  </button>
                ))}
              </div>
            </div>

            <div className="stats-grid">
              <div className="card stat-card">
                <span className="stat-label">Total Revenue</span>
                <span className="stat-value">{formatCurrency(dashboardRevenueTotal)}</span>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Last {dashboardRangeLabel}</div>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Units Sold</span>
                <span className="stat-value">{formatInteger(dashboardUnitsTotal)}</span>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Last {dashboardRangeLabel}</div>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Catalog Size</span>
                <span className="stat-value">{formatInteger(overview.total_listings)}</span>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Across 5 marketplaces</div>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Health Risk</span>
                <span className="stat-value" style={{ color: 'var(--error)' }}>{formatInteger(overview.low_stock_items)}</span>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Urgent restocking items</div>
              </div>
            </div>

            <div className="dashboard-panels">
              <div className="card revenue-flow-card">
                <div className="section-head" style={{ marginBottom: '1.5rem' }}>
                  <div>
                    <h3 style={{ fontFamily: 'Outfit', fontSize: '1.35rem' }}>Revenue Flow</h3>
                    <p className="section-copy">Daily revenue across the last {dashboardRangeLabel}.</p>
                  </div>
                </div>
                <div style={{ width: '100%', height: 360 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={dashboardRevenueTrend} margin={{ top: 12, right: 12, bottom: 0, left: 0 }}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 4" vertical={false} stroke="var(--chart-grid)" />
                      <XAxis
                        dataKey="day"
                        axisLine={false}
                        tickLine={false}
                        minTickGap={28}
                        tick={{fill: 'var(--text-muted)', fontSize: 10}}
                        tickFormatter={(value) => formatChartDate(value, dashboardDays)}
                      />
                      <YAxis axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 10}} tickFormatter={val => `$${val}`} />
                      <Tooltip
                        labelFormatter={(value) => formatLongDate(String(value))}
                        contentStyle={{background: 'var(--bg-accent)', border: '1px solid var(--glass-border)', borderRadius: '12px', backdropFilter: 'blur(10px)'}}
                      />
                      <Area type="monotone" dataKey="revenue" stroke="var(--primary)" fillOpacity={1} fill="url(#colorRevenue)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="secondary-panels-grid">
                <div className="card">
                  <h3 style={{ marginBottom: '1.5rem', fontFamily: 'Outfit', fontSize: '1.25rem' }}>Marketplace Distribution</h3>
                  <div style={{ width: '100%', height: 300 }}>
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={overview.marketplace_mix}
                          cx="50%"
                          cy="50%"
                          innerRadius={60}
                          outerRadius={80}
                          paddingAngle={5}
                          dataKey="listings"
                          nameKey="marketplace"
                        >
                          {overview.marketplace_mix.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                          ))}
                        </Pie>
                        <Tooltip 
                          contentStyle={{background: 'var(--bg-accent)', border: '1px solid var(--glass-border)', borderRadius: '12px'}} 
                          itemStyle={{color: 'var(--text-primary)'}}
                        />
                        <Legend iconType="circle" wrapperStyle={{fontSize: '10px', paddingTop: '10px'}} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                </div>
                <div className="card">
                  <h3 style={{ marginBottom: '1.5rem', fontFamily: 'Outfit', fontSize: '1.25rem' }}>Listing Mix</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                    {overview.marketplace_mix.map((m, idx) => (
                      <div key={m.marketplace}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                          <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{m.marketplace}</span>
                          <span style={{ fontWeight: '700', fontSize: '0.8rem' }}>{m.listings}</span>
                        </div>
                        <div style={{ height: '4px', background: 'var(--surface-soft)', borderRadius: '10px', overflow: 'hidden' }}>
                          <div style={{ height: '100%', background: COLORS[idx % COLORS.length], width: `${overview.total_listings ? (m.listings / overview.total_listings) * 100 : 0}%` }}></div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {page === "inventory" && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h3 style={{ fontFamily: 'Outfit', fontSize: '1.25rem' }}>Full Catalog Inventory</h3>
              <div style={{ display: 'flex', gap: '1rem' }}>
                <button 
                  type="button"
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.6rem 1.2rem', fontSize: '0.85rem', background: 'var(--surface-soft)', color: 'var(--text-primary)' }}
                  onClick={() => downloadCSV(products, "inventory_report.csv")}
                >
                  📥 Export CSV
                </button>
                <button 
                  type="button"
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.6rem 1.2rem', fontSize: '0.85rem' }}
                  onClick={onOpenCreateProductModal}
                >
                  ➕ List New Product
                </button>
              </div>
            </div>

            {lowStockProducts.length > 0 && (
              <div className="low-stock-alert">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
                  <strong style={{ color: 'var(--warning)' }}>⚠ {lowStockProducts.length} items need restock</strong>
                  <span style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Quick action adds +{QUICK_RESTOCK_UNITS} units</span>
                </div>
                <div style={{ display: 'flex', gap: '0.6rem', marginTop: '0.85rem', flexWrap: 'wrap' }}>
                  {lowStockProducts.slice(0, 4).map(p => (
                    <button
                      key={p.id}
                      type="button"
                      className="chip-btn"
                      onClick={() => onQuickRestock(p)}
                      disabled={restockingProductId === p.id}
                    >
                      {restockingProductId === p.id ? "Restocking..." : `${p.sku} (${p.stock}) +${QUICK_RESTOCK_UNITS}`}
                    </button>
                  ))}
                </div>
              </div>
            )}

            <table>
              <thead>
                <tr>
                  <th>Product Details</th><th>SKU</th><th>Marketplace</th><th>Price</th><th>Stock</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map(p => (
                  <tr key={p.id}>
                    <td>
                      <div style={{ fontWeight: '600' }}>{p.title}</div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>ID: #{p.id}</div>
                    </td>
                    <td><code style={{ background: 'var(--surface-soft)', padding: '4px 8px', borderRadius: '6px', fontSize: '0.8rem' }}>{p.sku}</code></td>
                    <td>{p.marketplace}</td>
                    <td style={{ fontWeight: '700' }}>{formatCurrency(p.sell_price)}</td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.45rem', flexWrap: 'wrap' }}>
                        <span style={{ 
                          padding: '4px 10px', 
                          borderRadius: '999px', 
                          fontSize: '0.75rem', 
                          background: p.stock < LOW_STOCK_LIMIT ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                          color: p.stock < LOW_STOCK_LIMIT ? 'var(--error)' : 'var(--success)',
                          fontWeight: '600'
                        }}>
                          {p.stock} Units
                        </span>
                        {p.stock < LOW_STOCK_LIMIT && <span className="low-badge">Low</span>}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button 
                          type="button"
                          onClick={() => setEditingProduct(p)} 
                          style={{ background: 'var(--surface-soft)', border: 'none', padding: '6px', borderRadius: '8px', cursor: 'pointer', color: 'var(--text-primary)' }}
                        >
                          ✏️
                        </button>
                        <button 
                          type="button"
                          onClick={() => onDeleteProduct(p.id)} 
                          style={{ background: 'rgba(239, 68, 68, 0.1)', border: 'none', padding: '6px', borderRadius: '8px', cursor: 'pointer' }}
                        >
                          🗑️
                        </button>
                        {p.stock < LOW_STOCK_LIMIT && (
                          <button
                            type="button"
                            onClick={() => onQuickRestock(p)}
                            style={{ background: 'rgba(245, 158, 11, 0.16)', border: '1px solid rgba(245, 158, 11, 0.3)', color: 'var(--warning)', padding: '6px 8px', borderRadius: '8px', cursor: 'pointer', fontSize: '0.75rem', fontWeight: 700 }}
                            disabled={restockingProductId === p.id}
                          >
                            {restockingProductId === p.id ? "..." : `+${QUICK_RESTOCK_UNITS}`}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {filteredProducts.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.25rem' }}>
                      No products found.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {page === "orders" && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
              <h3 style={{ fontFamily: 'Outfit', fontSize: '1.25rem' }}>Latest Transactions</h3>
              <div style={{ display: 'flex', gap: '0.65rem', flexWrap: 'wrap' }}>
                <input
                  type="date"
                  className="date-input"
                  value={ordersFrom}
                  onChange={e => setOrdersFrom(e.target.value)}
                  aria-label="Orders from date"
                />
                <input
                  type="date"
                  className="date-input"
                  value={ordersTo}
                  onChange={e => setOrdersTo(e.target.value)}
                  aria-label="Orders to date"
                />
                <button
                  type="button"
                  className="chip-btn"
                  onClick={() => {
                    setOrdersFrom("");
                    setOrdersTo("");
                  }}
                >
                  Clear Dates
                </button>
                <button 
                  type="button"
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.55rem 1rem', fontSize: '0.85rem' }}
                  onClick={onOpenCreateOrderModal}
                >
                  ➕ Create Order
                </button>
                <button 
                  type="button"
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.55rem 1rem', fontSize: '0.85rem', background: 'var(--surface-soft)', color: 'var(--text-primary)' }}
                  onClick={() => downloadCSV(filteredOrders, "order_history.csv")}
                >
                  📥 Download History
                </button>
              </div>
            </div>
            <div style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', marginBottom: '0.8rem' }}>
              Showing {filteredOrders.length} order(s)
            </div>
            <table>
              <thead>
                <tr>
                  <th>Reference #</th><th>Channel</th><th>Recorded On</th><th>Total Amount</th><th>Fulfillment</th>
                </tr>
              </thead>
              <tbody>
                {filteredOrders.map(o => (
                  <tr key={o.id}>
                    <td style={{ fontWeight: '700' }}>{o.order_number}</td>
                    <td>{o.marketplace}</td>
                    <td>{formatShortDate(o.created_at)}</td>
                    <td style={{ fontWeight: '700' }}>{formatCurrency(o.total_amount)}</td>
                    <td><span style={{ padding: '4px 10px', background: 'rgba(168, 85, 247, 0.1)', color: 'var(--secondary)', borderRadius: '999px', fontSize: '0.75rem', fontWeight: '600' }}>Completed</span></td>
                  </tr>
                ))}
                {filteredOrders.length === 0 && (
                  <tr>
                    <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.25rem' }}>
                      No orders found for current filters.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}

        {page === "agents" && (
          <div className="agent-grid">
            <section className="card">
              <div className="section-head">
                <div>
                  <h3 style={{ fontFamily: 'Outfit', fontSize: '1.25rem' }}>Your Agent</h3>
                  <p className="section-copy">Create a Foundry agent or link an existing one for your account.</p>
                </div>
                {currentAgent && (
                  <button
                    type="button"
                    className="danger-btn"
                    onClick={onDeleteAgent}
                    disabled={agentBusy}
                  >
                    {agentBusy ? "Removing..." : "Remove Current Agent"}
                  </button>
                )}
              </div>

              <p className="section-copy" style={{ marginTop: '1rem' }}>
                Each user can have only one agent.
              </p>

              <form onSubmit={onCreateAgent} className="auth-form" style={{ marginTop: '1.5rem' }}>
                <div className="input-group">
                  <span className="input-label">Agent Name</span>
                  <input
                    className="auth-input"
                    value={agentForm.agent_name}
                    onChange={e => setAgentForm({ ...agentForm, agent_name: e.target.value })}
                    placeholder="WillowAgent"
                    required
                  />
                </div>

                <div className="input-group">
                  <span className="input-label">Existing Agent ID (Optional)</span>
                  <input
                    className="auth-input"
                    value={agentForm.existing_agent_id || ""}
                    onChange={e => setAgentForm({ ...agentForm, existing_agent_id: e.target.value })}
                    placeholder="WillowAgent:1"
                  />
                </div>

                <div className="input-group">
                  <span className="input-label">Project Endpoint (Optional)</span>
                  <input
                    className="auth-input"
                    value={agentForm.project_endpoint || ""}
                    onChange={e => setAgentForm({ ...agentForm, project_endpoint: e.target.value })}
                    placeholder="https://.../api/projects/amar-0558"
                  />
                </div>

                <div className="input-group">
                  <span className="input-label">Model Deployment (Optional)</span>
                  <input
                    className="auth-input"
                    value={agentForm.model_deployment_name || ""}
                    onChange={e => setAgentForm({ ...agentForm, model_deployment_name: e.target.value })}
                    placeholder="gpt-5.2-chat"
                  />
                </div>

                <div className="input-group">
                  <span className="input-label">Instructions</span>
                  <textarea
                    className="agent-textarea"
                    value={agentForm.instructions || ""}
                    onChange={e => setAgentForm({ ...agentForm, instructions: e.target.value })}
                    placeholder="Help with dashboard, products, inventory, and orders."
                  />
                </div>

                <button type="submit" className="auth-btn" disabled={agentBusy}>
                  {agentBusy ? "Saving..." : currentAgent ? "Update Agent" : "Create Agent"}
                </button>
              </form>

              <div className="agent-status-card">
                <h4>Current Agent</h4>
                {currentAgent ? (
                  <div className="agent-meta-list">
                    <div><strong>Name:</strong> {currentAgent.agent_name}</div>
                    <div><strong>Version:</strong> {currentAgent.agent_version}</div>
                    <div><strong>Project:</strong> {currentAgent.project_endpoint || "Using API default"}</div>
                    <div><strong>Saved:</strong> {formatShortDate(currentAgent.updated_at)}</div>
                  </div>
                ) : (
                  <p className="section-copy" style={{ marginTop: '0.75rem' }}>
                    No agent saved for this user yet.
                  </p>
                )}
              </div>
            </section>

            <section className="card">
              <div className="section-head">
                <div>
                  <h3 style={{ fontFamily: 'Outfit', fontSize: '1.25rem' }}>Use Agent</h3>
                  <p className="section-copy">Chat with the current agent after it is created.</p>
                </div>
                <button
                  type="button"
                  className="chip-btn"
                  onClick={onResetAgentChat}
                  disabled={!currentAgent || agentChatBusy}
                >
                  Clear Chat
                </button>
              </div>

              {!currentAgent ? (
                <div className="empty-panel">
                  Create or link an agent first. Start the agent API with <code>./azure_tools_api/run_dev.sh</code>.
                </div>
              ) : (
                <>
                  <div className="agent-chat-log">
                    {agentHistory.length === 0 ? (
                      <div className="empty-panel">
                        No conversation yet. Ask something like <code>Show me my dashboard summary</code>.
                      </div>
                    ) : (
                      agentHistory.map((entry, index) => (
                        <div key={`${entry.role}-${index}`} className={`agent-message ${entry.role}`}>
                          <span className="agent-role">{entry.role === "user" ? "You" : currentAgent.agent_name}</span>
                          <div className="agent-message-content">{renderAgentContent(entry.content)}</div>
                        </div>
                      ))
                    )}
                  </div>

                  <form onSubmit={onSendAgentPrompt} className="auth-form" style={{ marginTop: '1rem' }}>
                    <div className="input-group">
                      <span className="input-label">Prompt</span>
                      <textarea
                        className="agent-textarea"
                        value={agentPrompt}
                        onChange={e => setAgentPrompt(e.target.value)}
                        placeholder="Ask the agent to summarize revenue, list low stock items, or create an order."
                      />
                    </div>
                    <button type="submit" className="auth-btn" disabled={agentChatBusy || !agentPrompt.trim()}>
                      {agentChatBusy ? "Sending..." : "Send to Agent"}
                    </button>
                  </form>
                </>
              )}
            </section>
          </div>
        )}

        {page === "admin" && user?.role === "admin" && (
          <>
            <div className="section-head" style={{ marginBottom: '1.5rem' }}>
              <div>
                <h3 style={{ fontFamily: 'Outfit', fontSize: '1.4rem' }}>Admin Control</h3>
                <p className="section-copy">Monitor users, subscription mix, and the agents they use.</p>
              </div>
              <button
                type="button"
                className="auth-btn"
                style={{ width: 'auto', padding: '0.75rem 1rem', fontSize: '0.9rem' }}
                onClick={() => refreshAdminData(token)}
                disabled={adminLoading}
              >
                {adminLoading ? "Refreshing..." : "Refresh Admin Data"}
              </button>
            </div>

            <div className="stats-grid">
              <div className="card stat-card">
                <span className="stat-label">Total Users</span>
                <span className="stat-value">{formatInteger(adminSummary?.total_users || 0)}</span>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Admin Accounts</span>
                <span className="stat-value">{formatInteger(adminSummary?.admin_users || 0)}</span>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Demo Plans</span>
                <span className="stat-value">{formatInteger(adminSummary?.demo_subscriptions || 0)}</span>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Users With Agents</span>
                <span className="stat-value">{formatInteger(adminSummary?.users_with_agents || 0)}</span>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Total Orders</span>
                <span className="stat-value">{formatInteger(adminSummary?.total_orders || 0)}</span>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Platform Sales</span>
                <span className="stat-value">{formatCurrency(adminSummary?.total_sales || 0)}</span>
              </div>
            </div>

            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <h3 style={{ marginBottom: '1rem', fontFamily: 'Outfit', fontSize: '1.1rem' }}>Subscriptions</h3>
              <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                {adminSubscriptions.map(subscription => (
                  <div key={subscription.subscription_type} className="account-chip">
                    <span className="account-label">{subscription.subscription_type}</span>
                    <span className="account-email">{subscription.users_count} user(s)</span>
                  </div>
                ))}
                {adminSubscriptions.length === 0 && (
                  <span className="section-copy">No subscription data yet.</span>
                )}
              </div>
            </div>

            <div className="card" style={{ marginBottom: '1.5rem' }}>
              <div className="section-head">
                <div>
                  <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem' }}>User Usage</h3>
                  <p className="section-copy">How much each user is using the website and which agent is attached.</p>
                </div>
                <span className="section-copy">Showing {filteredAdminUsers.length} user(s)</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Role</th>
                    <th>Subscription</th>
                    <th>Listings</th>
                    <th>Orders</th>
                    <th>Sales</th>
                    <th>Agent</th>
                    <th>Joined</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAdminUsers.map(entry => (
                    <tr key={entry.id}>
                      <td>
                        <div style={{ fontWeight: 700 }}>{entry.name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{entry.email}</div>
                      </td>
                      <td>{entry.role}</td>
                      <td>{entry.subscription_type}</td>
                      <td>{formatInteger(entry.products_count)}</td>
                      <td>{formatInteger(entry.orders_count)}</td>
                      <td>{formatCurrency(entry.total_sales)}</td>
                      <td>
                        {entry.agent_name ? (
                          <>
                            <div style={{ fontWeight: 700 }}>{entry.agent_name}</div>
                            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                              v{entry.agent_version} · {entry.agent_updated_at ? formatShortDate(entry.agent_updated_at) : "No recent update"}
                            </div>
                          </>
                        ) : (
                          <span style={{ color: 'var(--text-muted)' }}>No agent</span>
                        )}
                      </td>
                      <td>{formatShortDate(entry.created_at)}</td>
                    </tr>
                  ))}
                  {filteredAdminUsers.length === 0 && (
                    <tr>
                      <td colSpan={8} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.25rem' }}>
                        No users found for the current search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            <div className="card">
              <div className="section-head">
                <div>
                  <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem' }}>Agent Usage</h3>
                  <p className="section-copy">Current agent records and the usage footprint attached to them.</p>
                </div>
                <span className="section-copy">Showing {filteredAdminAgents.length} agent record(s)</span>
              </div>
              <table>
                <thead>
                  <tr>
                    <th>Seller</th>
                    <th>Subscription</th>
                    <th>Agent</th>
                    <th>Listings</th>
                    <th>Orders</th>
                    <th>Sales</th>
                    <th>Updated</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAdminAgents.map(entry => (
                    <tr key={`${entry.seller_id}-${entry.agent_name}-${entry.agent_version}`}>
                      <td>
                        <div style={{ fontWeight: 700 }}>{entry.seller_name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{entry.seller_email}</div>
                      </td>
                      <td>{entry.subscription_type}</td>
                      <td>
                        <div style={{ fontWeight: 700 }}>{entry.agent_name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>v{entry.agent_version}</div>
                      </td>
                      <td>{formatInteger(entry.products_count)}</td>
                      <td>{formatInteger(entry.orders_count)}</td>
                      <td>{formatCurrency(entry.total_sales)}</td>
                      <td>{formatShortDate(entry.agent_updated_at)}</td>
                    </tr>
                  ))}
                  {filteredAdminAgents.length === 0 && (
                    <tr>
                      <td colSpan={7} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.25rem' }}>
                        No agent usage data found for the current search.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </>
        )}

      </main>

      {editingProduct && (
        <div
          className="auth-shell"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            background: 'rgba(0,0,0,0.8)',
            padding: '1rem',
            overflowY: 'auto',
          }}
        >
          <div className="auth-card" style={{ width: '100%', maxWidth: '500px' }}>
            <h1>Edit Inventory</h1>
            <p>Modify stock and pricing for <strong>{editingProduct.title}</strong></p>
            
            <form onSubmit={onUpdateProduct} className="auth-form" style={{ marginTop: '2rem' }}>
              <div className="input-group">
                <span className="input-label">Product Title</span>
                <input 
                  className="auth-input" 
                  value={editingProduct.title} 
                  onChange={e => setEditingProduct({...editingProduct, title: e.target.value})} 
                  required 
                />
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                <div className="input-group">
                  <span className="input-label">Current Stock Level</span>
                  <input 
                    className="auth-input" 
                    type="number" 
                    value={editingProduct.stock} 
                    onChange={e => setEditingProduct({...editingProduct, stock: Number(e.target.value)})} 
                    required 
                    placeholder="e.g. 50"
                  />
                </div>
                <div className="input-group">
                  <span className="input-label">Sale Price ($)</span>
                  <input 
                    className="auth-input" 
                    type="number" 
                    step="0.01" 
                    value={editingProduct.sell_price} 
                    onChange={e => setEditingProduct({...editingProduct, sell_price: Number(e.target.value)})} 
                    required 
                    placeholder="e.g. 19.99"
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="auth-btn" style={{ flex: 1 }} disabled={loading}>
                  {loading ? "Saving..." : "Save Changes"}
                </button>
                <button 
                  type="button" 
                  className="auth-btn" 
                  style={{ flex: 1, background: 'var(--surface-soft)', color: 'var(--text-primary)' }} 
                  onClick={() => setEditingProduct(null)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isAddingOrder && (
        <div
          className="auth-shell"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            background: 'rgba(0,0,0,0.8)',
            padding: '1rem',
            overflowY: 'auto',
          }}
        >
          <div className="auth-card" style={{ width: '100%', maxWidth: '520px' }}>
            <h1>Create Order</h1>
            <p>Create a quick order using one product line item.</p>
            
            <form onSubmit={onCreateOrder} className="auth-form" style={{ marginTop: '2rem' }}>
              <div className="input-group">
                <span className="input-label">Order Number</span>
                <input
                  className="auth-input"
                  value={newOrder.order_number}
                  onChange={e => setNewOrder({ ...newOrder, order_number: e.target.value })}
                  placeholder="ORD-00012345"
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <span className="input-label">Marketplace</span>
                  <select
                    className="auth-input"
                    style={{ background: 'var(--surface-soft)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)' }}
                    value={newOrder.marketplace}
                    onChange={e => setNewOrder({ ...newOrder, marketplace: e.target.value })}
                  >
                    {["Amazon", "eBay", "Walmart", "Target", "Etsy", "Shopify"].map(m => (
                      <option key={m} value={m} style={{ background: 'var(--bg-accent)', color: 'var(--text-primary)' }}>{m}</option>
                    ))}
                  </select>
                </div>
                <div className="input-group">
                  <span className="input-label">Product</span>
                  <select
                    className="auth-input"
                    style={{ background: 'var(--surface-soft)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)' }}
                    value={newOrder.product_id}
                    onChange={e => {
                      const productId = Number(e.target.value);
                      const selected = products.find(p => p.id === productId);
                      setNewOrder({
                        ...newOrder,
                        product_id: productId,
                        unit_price: selected ? selected.sell_price : newOrder.unit_price,
                        marketplace: selected ? selected.marketplace : newOrder.marketplace,
                      });
                    }}
                  >
                    {products.map(p => (
                      <option key={p.id} value={p.id} style={{ background: 'var(--bg-accent)', color: 'var(--text-primary)' }}>
                        {p.sku} • {p.title}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                <div className="input-group">
                  <span className="input-label">Quantity</span>
                  <input
                    className="auth-input"
                    type="number"
                    min={1}
                    value={newOrder.quantity}
                    onChange={e => setNewOrder({ ...newOrder, quantity: Number(e.target.value) })}
                    required
                  />
                </div>
                <div className="input-group">
                  <span className="input-label">Unit Price ($)</span>
                  <input
                    className="auth-input"
                    type="number"
                    min={0}
                    step="0.01"
                    value={newOrder.unit_price}
                    onChange={e => setNewOrder({ ...newOrder, unit_price: Number(e.target.value) })}
                    required
                  />
                </div>
              </div>

              {selectedOrderProduct && (
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  Selected stock: <strong>{selectedOrderProduct.stock}</strong> units
                </div>
              )}

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="auth-btn" style={{ flex: 1 }} disabled={loading}>
                  {loading ? "Creating..." : "Create Order"}
                </button>
                <button 
                  type="button" 
                  className="auth-btn" 
                  style={{ flex: 1, background: 'var(--surface-soft)', color: 'var(--text-primary)' }} 
                  onClick={() => setIsAddingOrder(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isAddingProduct && (
        <div
          className="auth-shell"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 1000,
            background: 'rgba(0,0,0,0.8)',
            padding: '1rem',
            overflowY: 'auto',
          }}
        >
          <div className="auth-card" style={{ width: '100%', maxWidth: '500px' }}>
            <h1>List New Product</h1>
            <p>Create a new listing across your connected marketplaces.</p>
            
            <form onSubmit={onCreateProduct} className="auth-form" style={{ marginTop: '2rem' }}>
              <div className="input-group">
                <span className="input-label">Product Name</span>
                <input 
                  className="auth-input" 
                  placeholder="e.g. Wireless Noise Cancelling Headphones"
                  value={newProduct.title} 
                  onChange={e => setNewProduct({...newProduct, title: e.target.value})} 
                  required 
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="input-group">
                  <span className="input-label">SKU Identifier</span>
                  <input 
                    className="auth-input" 
                    placeholder="WNC-HEAD-001"
                    value={newProduct.sku} 
                    onChange={e => setNewProduct({...newProduct, sku: e.target.value})} 
                    required 
                  />
                </div>
                <div className="input-group">
                  <span className="input-label">Marketplace</span>
                  <select 
                    className="auth-input" 
                    style={{ background: 'var(--surface-soft)', color: 'var(--text-primary)', border: '1px solid var(--glass-border)' }}
                    value={newProduct.marketplace} 
                    onChange={e => setNewProduct({...newProduct, marketplace: e.target.value})} 
                  >
                    {["Amazon", "eBay", "Walmart", "Target", "Etsy", "Shopify"].map(m => (
                      <option key={m} value={m} style={{ background: 'var(--bg-accent)', color: 'var(--text-primary)' }}>{m}</option>
                    ))}
                  </select>
                </div>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.25rem' }}>
                <div className="input-group">
                  <span className="input-label">Initial Stock Level</span>
                  <input 
                    className="auth-input" 
                    type="number" 
                    value={newProduct.stock === 0 ? "" : newProduct.stock} 
                    onChange={e => setNewProduct({...newProduct, stock: Number(e.target.value)})} 
                    placeholder="e.g. 150"
                    required 
                  />
                </div>
                <div className="input-group">
                  <span className="input-label">MSRP Price ($)</span>
                  <input 
                    className="auth-input" 
                    type="number" 
                    step="0.01" 
                    value={newProduct.sell_price === 0 ? "" : newProduct.sell_price} 
                    onChange={e => setNewProduct({...newProduct, sell_price: Number(e.target.value)})} 
                    placeholder="e.g. 29.99"
                    required 
                  />
                </div>
              </div>

              <div style={{ display: 'flex', gap: '1rem', marginTop: '1rem' }}>
                <button type="submit" className="auth-btn" style={{ flex: 1 }} disabled={loading}>
                  {loading ? "Listing..." : "Create Listing"}
                </button>
                <button 
                  type="button" 
                  className="auth-btn" 
                  style={{ flex: 1, background: 'var(--surface-soft)', color: 'var(--text-primary)' }} 
                  onClick={() => setIsAddingProduct(false)}
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
