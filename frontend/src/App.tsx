import { FormEvent, useEffect, useState, useMemo } from "react";
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid, PieChart, Pie, Cell, Legend } from 'recharts';
import {
  api,
  BuyboxInput,
  BuyboxPrediction,
  DashboardCategoryCount,
  DashboardOverview,
  DashboardRevenuePoint,
  Order,
  Product,
  User,
} from "./api";

type AuthMode = "login" | "signup";
type DashboardPage = "overview" | "inventory" | "orders" | "ai";
type NoticeTone = "error" | "success";

const dashboardPages: Array<{ id: DashboardPage; label: string; icon: string }> = [
  { id: "overview", label: "Dashboard", icon: "📊" },
  { id: "inventory", label: "Inventory", icon: "📦" },
  { id: "orders", label: "Orders", icon: "🛍️" },
  { id: "ai", label: "AI Insights", icon: "🤖" },
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
  const [thinkingLog, setThinkingLog] = useState<string[]>([]);
  const [newProduct, setNewProduct] = useState<Omit<Product, "id" | "seller_id">>({
    title: "",
    sku: "",
    sell_price: 0,
    stock: 0,
    marketplace: "Amazon",
  });
  const [prediction, setPrediction] = useState<BuyboxPrediction | null>(null);
  const [buyboxInput, setBuyboxInput] = useState<BuyboxInput>({
    sku: "",
    SellPrice: 0,
    ShippingPrice: 0,
    TotalPrice: 0,
    MinCompetitorPrice: 0,
    MinTotalPriceInSnapshot: 0,
    PriceGap: 0,
    TotalPriceGap: 0,
    PriceGapPercent: 0,
    PriceRank: 0,
    PriceRankNormalized: 0,
    TotalCompetitorsInSnapshot: 1,
    PositiveFeedbackPercent: 95,
    MaxFeedbackInSnapshot: 99,
    FeedbackGapFromMax: 4,
    IsMinSellPrice: 0,
    IsMinTotalPrice: 0,
    IsFBA: 1,
  });

  async function onPredictBuybox(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      const result = await api.predictBuybox(token, buyboxInput);
      setPrediction(result);
    } catch (err) {
      setMessage("Prediction failed. Try again.");
      setMessageTone("error");
    } finally {
      setLoading(false);
    }
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

  useEffect(() => {
    const messages = [
      "Neural agent initialized...",
      "Analyzing marketplace saturation...",
      "Scanning Walmart competitor nodes...",
      "Cross-referencing SKU-984 across Shopify...",
      "Calculating real-time market price rank...",
      "Engineering 18-point feature vector...",
      "Analyzing feedback gap vs market leader...",
      "Recalculating price elasticity for high-demand items...",
      "Agent: Buying signal detected for Amazon electronics.",
      "Optimizing buybox win-rate for SKU-001...",
      "Neural weights updated for Q2 seasonality...",
    ];
    let i = 0;
    const interval = setInterval(() => {
      setThinkingLog(prev => [messages[i % messages.length], ...prev].slice(0, 8));
      i++;
    }, 4500);
    return () => clearInterval(interval);
  }, []);

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

  const filteredOrders = useMemo(() => {
    if (!searchQuery) return orders;
    return orders.filter(o => 
      o.order_number.toLowerCase().includes(searchQuery.toLowerCase()) || 
      o.marketplace.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [orders, searchQuery]);

  const filteredProducts = useMemo(() => {
    if (!searchQuery) return products;
    return products.filter(p => 
      p.title.toLowerCase().includes(searchQuery.toLowerCase()) || 
      p.sku.toLowerCase().includes(searchQuery.toLowerCase())
    );
  }, [products, searchQuery]);

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
      <aside className="sidebar">
        <div className="brand">
          <h1 style={{ background: 'none', WebkitTextFillColor: 'initial', color: '#fff', fontSize: '1.5rem' }}>SellerIntel</h1>
        </div>
        <nav className="nav-list">
          {dashboardPages.map(p => (
            <li key={p.id} className={`nav-item ${page === p.id ? 'active' : ''}`} onClick={() => setPage(p.id)}>
              <span style={{ fontSize: '1.2rem' }}>{p.icon}</span>
              <span style={{ fontWeight: '500' }}>{p.label}</span>
            </li>
          ))}
        </nav>
        <div style={{ marginTop: 'auto' }}>
          <div className="card" style={{ padding: '1rem', background: 'rgba(255,255,255,0.03)' }}>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>User Account</p>
            <p style={{ fontWeight: '600', fontSize: '0.85rem', marginTop: '0.25rem' }}>{user.email}</p>
          </div>
          <button 
            className="nav-item" 
            style={{ background: 'none', border: 'none', width: '100%', marginTop: '1rem', color: 'var(--error)' }}
            onClick={() => setToken("")}
          >
            <span>🚪</span> <span>Logout</span>
          </button>
        </div>
      </aside>

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
            <div className="stat-change up" style={{ fontSize: '0.85rem', background: 'rgba(16, 185, 129, 0.1)', padding: '6px 12px', borderRadius: 'full' }}>
              ● {overview.active_listings} Active Listings
            </div>
          </div>
        </header>

        {page === "overview" && (
          <>
            <div className="stats-grid">
              <div className="card stat-card">
                <span className="stat-label">Total Revenue</span>
                <span className="stat-value">{formatCurrency(overview.total_sales)}</span>
                <div className="stat-change up" style={{ marginTop: '0.25rem' }}>↑ 12.5% vs last month</div>
              </div>
              <div className="card stat-card">
                <span className="stat-label">Units Sold</span>
                <span className="stat-value">{formatInteger(overview.total_units_sold)}</span>
                <div className="stat-change up" style={{ marginTop: '0.25rem' }}>↑ 8.2% vs last month</div>
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

            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr 1fr', gap: '1.5rem' }}>
              <div className="card">
                <h3 style={{ marginBottom: '1.5rem', fontFamily: 'Outfit', fontSize: '1.25rem' }}>Revenue Flow (14d)</h3>
                <div style={{ width: '100%', height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={[...overview.revenue_trend].reverse()}>
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
                        <div style={{ height: '100%', background: COLORS[idx % COLORS.length], width: `${(m.listings / overview.total_listings) * 100}%` }}></div>
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
                      <span style={{ 
                        padding: '4px 10px', 
                        borderRadius: 'full', 
                        fontSize: '0.75rem', 
                        background: p.stock < 10 ? 'rgba(239, 68, 68, 0.1)' : 'rgba(16, 185, 129, 0.1)',
                        color: p.stock < 10 ? 'var(--error)' : 'var(--success)',
                        fontWeight: '600'
                      }}>
                        {p.stock} Units
                      </span>
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
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {page === "orders" && (
          <div className="card">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
              <h3 style={{ fontFamily: 'Outfit', fontSize: '1.25rem' }}>Latest Transactions</h3>
              <button 
                className="auth-btn" 
                style={{ width: 'auto', padding: '0.6rem 1.2rem', fontSize: '0.85rem', background: 'rgba(255,255,255,0.05)', color: '#fff' }}
                onClick={() => downloadCSV(orders, "order_history.csv")}
              >
                📥 Download History
              </button>
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
                    <td><span style={{ padding: '4px 10px', background: 'rgba(168, 85, 247, 0.1)', color: 'var(--secondary)', borderRadius: 'full', fontSize: '0.75rem', fontWeight: '600' }}>Completed</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {page === "ai" && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '1.5rem' }}>
            <div className="card">
              <h3 style={{ marginBottom: '1.5rem', fontFamily: 'Outfit', fontSize: '1.2rem' }}>Buybox Predictor</h3>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>Dynamic pricing signals powered by historical training data.</p>
              
              <form onSubmit={onPredictBuybox} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem 1.25rem' }}>
                  <div className="input-group">
                    <span className="input-label">SKU Identifier</span>
                    <input className="auth-input" placeholder="e.g. EB-008-2" value={buyboxInput.sku} onChange={e => setBuyboxInput({...buyboxInput, sku: e.target.value})} required />
                  </div>
                  <div className="input-group">
                    <span className="input-label">Proposed Sell Price</span>
                    <input className="auth-input" placeholder="e.g. 49.99" type="number" step="0.01" value={buyboxInput.SellPrice} onChange={e => setBuyboxInput({...buyboxInput, SellPrice: Number(e.target.value)})} required />
                  </div>
                  <div className="input-group">
                    <span className="input-label">Min Competitor Price</span>
                    <input className="auth-input" placeholder="e.g. 45.00" type="number" step="0.01" value={buyboxInput.MinCompetitorPrice} onChange={e => setBuyboxInput({...buyboxInput, MinCompetitorPrice: Number(e.target.value)})} required />
                  </div>
                  <div className="input-group">
                    <span className="input-label">Fulfillment Model</span>
                    <select 
                      className="auth-input" 
                      style={{ background: 'rgba(255,255,255,0.03)', color: '#fff', border: '1px solid var(--glass-border)' }}
                      value={buyboxInput.IsFBA} 
                      onChange={e => setBuyboxInput({...buyboxInput, IsFBA: Number(e.target.value)})}
                    >
                      <option value="1" style={{ background: '#111' }}>FBA (Fulfilled by Amazon)</option>
                      <option value="0" style={{ background: '#111' }}>FBM (Merchant Fulfilled)</option>
                    </select>
                  </div>
                </div>
                <button type="submit" className="auth-btn" style={{ marginTop: '0.5rem' }}>Generate Intelligence Signal</button>
              </form>

              {prediction && (
                <div style={{ 
                  marginTop: '1.5rem', 
                  padding: '1.5rem', 
                  background: 'rgba(34, 211, 238, 0.05)', 
                  borderRadius: '16px', 
                  border: '1px solid rgba(34, 211, 238, 0.2)',
                  boxShadow: '0 0 20px rgba(34, 211, 238, 0.1)'
                }}>
                   <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                     <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: '700', textTransform: 'uppercase', letterSpacing: '0.05em' }}>AI Recommendation</span>
                     <span style={{ 
                       padding: '4px 8px', 
                       background: prediction.confidence > 0.7 ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)', 
                       color: prediction.confidence > 0.7 ? 'var(--success)' : 'var(--warning)',
                       borderRadius: '6px',
                       fontSize: '0.7rem',
                       fontWeight: '700'
                     }}>
                       {(prediction.confidence * 100).toFixed(0)}% Confidence
                     </span>
                   </div>
                   <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                     <div style={{ fontSize: '2rem', fontWeight: '800', color: '#fff' }}>{formatCurrency(prediction.recommended_price)}</div>
                     <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Target Price</div>
                   </div>
                   <div style={{ marginTop: '1rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                     Signal Source: <code style={{ color: 'var(--accent)' }}>{prediction.model_name}</code>
                   </div>
                </div>
              )}
            </div>

            <div className="card" style={{ border: '1px solid var(--primary)', boxShadow: '0 0 20px rgba(99, 102, 241, 0.1)' }}>
              <h3 style={{ marginBottom: '1.5rem', fontFamily: 'Outfit', fontSize: '1.25rem' }}>🤖 Neural Agent Pulse</h3>
              <div style={{ 
                background: 'rgba(0,0,0,0.3)', 
                padding: '1rem', 
                borderRadius: '12px', 
                fontFamily: 'monospace', 
                fontSize: '0.8rem', 
                height: '400px', 
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.6rem'
              }}>
                {thinkingLog.map((log, idx) => (
                  <div key={idx} style={{ 
                    color: idx === 0 ? 'var(--primary)' : 'var(--text-muted)',
                    opacity: 1 - (idx * 0.12),
                    transition: 'all 0.5s ease',
                    display: 'flex',
                    gap: '0.75rem'
                  }}>
                    <span style={{ color: 'var(--success)', fontWeight: '700' }}>[OK]</span>
                    <span>{log}</span>
                  </div>
                ))}
                {thinkingLog.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Waiting for telemetry...</div>}
              </div>
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(255,255,255,0.02)', borderRadius: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Agent System Load</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--success)' }}>Nominal</span>
                </div>
                <div style={{ height: '4px', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '10px', width: '100%' }}>
                  <div style={{ height: '100%', background: 'var(--success)', width: '24%', borderRadius: '10px' }}></div>
                </div>
              </div>
            </div>
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
