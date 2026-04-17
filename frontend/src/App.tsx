import { FormEvent, useEffect, useState, useMemo } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';
import {
  api,
  DashboardOverview,
  DashboardRevenuePoint,
  Order,
  Product,
  User,
} from "./api";

type AuthMode = "login" | "signup";
type DashboardPage = "overview" | "inventory" | "orders";
type NoticeTone = "error" | "success";

const dashboardPages: Array<{ id: DashboardPage; label: string; icon: string }> = [
  { id: "overview", label: "Dashboard", icon: "📊" },
  { id: "inventory", label: "Inventory", icon: "📦" },
  { id: "orders", label: "Orders", icon: "🛍️" },
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

function getGeneratedOrderNumber(): string {
  return `ORD-${Date.now().toString().slice(-8)}`;
}

export default function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("token") || "");
  const [mode, setMode] = useState<AuthMode>("login");
  const [page, setPage] = useState<DashboardPage>("overview");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
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
  const [dashboardDays, setDashboardDays] = useState(14);
  const [ordersFrom, setOrdersFrom] = useState("");
  const [ordersTo, setOrdersTo] = useState("");
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

  async function onCreateProduct(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createProduct(token, newProduct);
      setMessage("Listing created successfully.");
      setMessageTone("success");
      setIsAddingProduct(false);
      setNewProduct({ title: "", sku: "", sell_price: 0, stock: 0, marketplace: "Amazon" });
      refreshData(token);
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
      refreshData(token);
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
      refreshData(token);
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
      refreshData(token);
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
      refreshData(token);
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
      return;
    }
    localStorage.setItem("token", token);
    refreshData(token);
  }, [token]);

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
      setToken("");
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
    } catch (err) {
      setMessage("Authentication failed. Check your email or password.");
      setMessageTone("error");
    } finally {
      setLoading(false);
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

  const selectedOrderProduct = useMemo(
    () => products.find(p => p.id === newOrder.product_id) || null,
    [products, newOrder.product_id]
  );

  if (!token || !user || !overview) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <h1>{mode === "login" ? "Welcome Back" : "Get Started"}</h1>
          <p>
            {mode === "login" 
              ? "Enter your credentials to access your intelligence dashboard." 
              : "Launch your premium seller workspace today."}
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
              <input 
                className="auth-input" 
                placeholder="Enter your secure password" 
                type="password" 
                value={password} 
                onChange={e => setPassword(e.target.value)} 
                required 
              />
            </div>
            
            <button className="auth-btn" disabled={loading}>
              {loading ? "Processing..." : mode === "login" ? "Sign In" : "Create Account"}
            </button>
          </form>
          
          <div className="auth-switch">
            {mode === "login" ? "Don't have an account?" : "Already have an account?"}
            <button className="auth-switch-btn" onClick={() => setMode(mode === "login" ? "signup" : "login")}>
              {mode === "login" ? "Sign Up" : "Back to Login"}
            </button>
          </div>
          
          {message && (
            <p style={{ color: messageTone === "error" ? 'var(--error)' : 'var(--success)', marginTop: '1.5rem', fontWeight: '500' }}>
              {message}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="top-navbar">
        <div className="top-navbar-left">
          <h1 className="brand-title">SellerIntel</h1>
          <nav className="top-nav-list">
            {dashboardPages.map(p => (
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
          <div className="account-chip">
            <span className="account-label">User Account</span>
            <span className="account-email">{user.email}</span>
          </div>
          <button
            type="button"
            className="nav-item logout-btn"
            onClick={() => setToken("")}
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
              placeholder={`Search ${page === 'inventory' ? 'products' : page === 'orders' ? 'orders' : 'anything'}...`} 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
            />
          </div>
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            <div className="stat-change up" style={{ fontSize: '0.85rem', background: 'rgba(16, 185, 129, 0.1)', padding: '6px 12px', borderRadius: '999px' }}>
              ● {overview.active_listings} Active Listings
            </div>
            <div style={{ fontSize: '0.85rem', background: 'rgba(245, 158, 11, 0.12)', color: 'var(--warning)', padding: '6px 12px', borderRadius: '999px', fontWeight: 600 }}>
              ⚠ {lowStockProducts.length} Low Stock
            </div>
          </div>
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
                {[7, 14, 30, 90].map(days => (
                  <button
                    key={days}
                    type="button"
                    className={`filter-chip ${dashboardDays === days ? "active" : ""}`}
                    onClick={() => setDashboardDays(days)}
                  >
                    {days} days
                  </button>
                ))}
              </div>
            </div>

            <div className="stats-grid">
              <div className="card stat-card">
                <span className="stat-label">Total Revenue</span>
                <span className="stat-value">{formatCurrency(dashboardRevenueTotal)}</span>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Last {dashboardDays} days</div>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Units Sold</span>
                <span className="stat-value">{formatInteger(dashboardUnitsTotal)}</span>
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '0.25rem' }}>Last {dashboardDays} days</div>
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

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1.5rem' }}>
              <div className="card">
                <h3 style={{ marginBottom: '1.5rem', fontFamily: 'Outfit', fontSize: '1.25rem' }}>Revenue Flow ({dashboardDays}d)</h3>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={[...dashboardRevenueTrend].reverse()}>
                      <defs>
                        <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="var(--primary)" stopOpacity={0.3}/>
                          <stop offset="95%" stopColor="var(--primary)" stopOpacity={0}/>
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 4" vertical={false} stroke="rgba(255,255,255,0.03)" />
                      <XAxis dataKey="day" axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 10}} tickFormatter={formatShortDate} />
                      <YAxis axisLine={false} tickLine={false} tick={{fill: 'var(--text-muted)', fontSize: 10}} tickFormatter={val => `$${val}`} />
                      <Tooltip contentStyle={{background: 'var(--bg-accent)', border: '1px solid var(--glass-border)', borderRadius: '12px', backdropFilter: 'blur(10px)'}} />
                      <Area type="monotone" dataKey="revenue" stroke="var(--primary)" fillOpacity={1} fill="url(#colorRevenue)" strokeWidth={3} />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>
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
                        itemStyle={{color: '#fff'}}
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
                      <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: '10px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', background: COLORS[idx % COLORS.length], width: `${overview.total_listings ? (m.listings / overview.total_listings) * 100 : 0}%` }}></div>
                      </div>
                    </div>
                  ))}
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
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.6rem 1.2rem', fontSize: '0.85rem', background: 'rgba(255,255,255,0.05)', color: '#fff' }}
                  onClick={() => downloadCSV(products, "inventory_report.csv")}
                >
                  📥 Export CSV
                </button>
                <button 
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.6rem 1.2rem', fontSize: '0.85rem' }}
                  onClick={() => setIsAddingProduct(true)}
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
                    <td><code style={{ background: 'rgba(255,255,255,0.05)', padding: '4px 8px', borderRadius: '6px', fontSize: '0.8rem' }}>{p.sku}</code></td>
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
                          onClick={() => setEditingProduct(p)} 
                          style={{ background: 'rgba(255,255,255,0.05)', border: 'none', padding: '6px', borderRadius: '8px', cursor: 'pointer' }}
                        >
                          ✏️
                        </button>
                        <button 
                          onClick={() => onDeleteProduct(p.id)} 
                          style={{ background: 'rgba(239, 68, 68, 0.1)', border: 'none', padding: '6px', borderRadius: '8px', cursor: 'pointer' }}
                        >
                          🗑️
                        </button>
                        {p.stock < LOW_STOCK_LIMIT && (
                          <button
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
                  className="auth-btn"
                  style={{ width: 'auto', padding: '0.55rem 1rem', fontSize: '0.85rem' }}
                  onClick={onOpenCreateOrderModal}
                >
                  ➕ Create Order
                </button>
                <button 
                  className="auth-btn" 
                  style={{ width: 'auto', padding: '0.55rem 1rem', fontSize: '0.85rem', background: 'rgba(255,255,255,0.05)', color: '#fff' }}
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

      </main>

      {editingProduct && (
        <div className="auth-shell" style={{ position: 'fixed', zIndex: 1000, background: 'rgba(0,0,0,0.8)' }}>
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
                  style={{ flex: 1, background: 'rgba(255,255,255,0.05)', color: '#fff' }} 
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
        <div className="auth-shell" style={{ position: 'fixed', zIndex: 1000, background: 'rgba(0,0,0,0.8)' }}>
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
                    style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--glass-border)' }}
                    value={newOrder.marketplace}
                    onChange={e => setNewOrder({ ...newOrder, marketplace: e.target.value })}
                  >
                    {["Amazon", "eBay", "Walmart", "Target", "Etsy", "Shopify"].map(m => (
                      <option key={m} value={m} style={{ background: '#111' }}>{m}</option>
                    ))}
                  </select>
                </div>
                <div className="input-group">
                  <span className="input-label">Product</span>
                  <select
                    className="auth-input"
                    style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--glass-border)' }}
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
                      <option key={p.id} value={p.id} style={{ background: '#111' }}>
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
                  style={{ flex: 1, background: 'rgba(255,255,255,0.05)', color: '#fff' }} 
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
        <div className="auth-shell" style={{ position: 'fixed', zIndex: 1000, background: 'rgba(0,0,0,0.8)' }}>
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
                    style={{ background: 'rgba(255,255,255,0.05)', color: '#fff', border: '1px solid var(--glass-border)' }}
                    value={newProduct.marketplace} 
                    onChange={e => setNewProduct({...newProduct, marketplace: e.target.value})} 
                  >
                    {["Amazon", "eBay", "Walmart", "Target", "Etsy", "Shopify"].map(m => (
                      <option key={m} value={m} style={{ background: '#111' }}>{m}</option>
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
                  style={{ flex: 1, background: 'rgba(255,255,255,0.05)', color: '#fff' }} 
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
