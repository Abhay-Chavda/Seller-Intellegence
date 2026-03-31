import { FormEvent, useEffect, useState } from "react";
import { api, BuyboxInput, BuyboxPrediction, DashboardSummary, Order, Product, User } from "./api";

type AuthMode = "login" | "signup";

type ProductForm = {
  title: string;
  sku: string;
  sell_price: number;
  stock: number;
  marketplace: string;
};

const initialProductForm: ProductForm = {
  title: "",
  sku: "",
  sell_price: 0,
  stock: 0,
  marketplace: "Amazon",
};

export default function App() {
  const [token, setToken] = useState<string>(() => localStorage.getItem("token") || "");
  const [mode, setMode] = useState<AuthMode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [user, setUser] = useState<User | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [form, setForm] = useState<ProductForm>(initialProductForm);
  const [orderNumber, setOrderNumber] = useState("");
  const [orderMarketplace, setOrderMarketplace] = useState("Amazon");
  const [orderProductId, setOrderProductId] = useState<number>(0);
  const [orderQty, setOrderQty] = useState(1);
  const [orderPrice, setOrderPrice] = useState(0);
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
  const [prediction, setPrediction] = useState<BuyboxPrediction | null>(null);
  const [agentPrompt, setAgentPrompt] = useState("");
  const [agentReply, setAgentReply] = useState("");
  const [message, setMessage] = useState<string>("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!token) {
      return;
    }

    localStorage.setItem("token", token);
    refreshDashboard(token).catch((err: Error) => setMessage(err.message));
  }, [token]);

  async function refreshDashboard(activeToken: string) {
    const [me, dashboard, items] = await Promise.all([
      api.me(activeToken),
      api.getSummary(activeToken),
      api.listProducts(activeToken),
    ]);
    const orderList = await api.listOrders(activeToken);
    setUser(me);
    setSummary(dashboard);
    setProducts(items);
    setOrders(orderList);
    if (items.length && orderProductId === 0) {
      setOrderProductId(items[0].id);
      setBuyboxInput((prev) => ({ ...prev, sku: items[0].sku, SellPrice: items[0].sell_price }));
    }
  }

  async function onAuthSubmit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      if (mode === "signup") {
        await api.signup(name, email, password);
        setMessage("Signup successful. Please login.");
        setMode("login");
      } else {
        const auth = await api.login(email, password);
        setToken(auth.access_token);
        setMessage("Login successful.");
      }
    } catch (err) {
      setMessage((err as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function onCreateProduct(event: FormEvent) {
    event.preventDefault();
    if (!token) return;

    try {
      await api.createProduct(token, form);
      setForm(initialProductForm);
      await refreshDashboard(token);
      setMessage("Product added.");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function onCreateOrder(event: FormEvent) {
    event.preventDefault();
    if (!token || !orderProductId) return;
    try {
      await api.createOrder(token, {
        order_number: orderNumber,
        marketplace: orderMarketplace,
        items: [{ product_id: orderProductId, quantity: orderQty, unit_price: orderPrice }],
      });
      setOrderNumber("");
      await refreshDashboard(token);
      setMessage("Order created.");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function onPredictBuybox(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    try {
      const result = await api.predictBuybox(token, buyboxInput);
      setPrediction(result);
      setMessage("Buybox prediction generated.");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  async function onAgentSubmit(event: FormEvent) {
    event.preventDefault();
    if (!token || !agentPrompt.trim()) return;
    try {
      const reply = await api.agentChat(token, agentPrompt);
      setAgentReply(`[${reply.action}] ${reply.result}`);
      setAgentPrompt("");
    } catch (err) {
      setMessage((err as Error).message);
    }
  }

  function logout() {
    setToken("");
    setUser(null);
    setSummary(null);
    setProducts([]);
    localStorage.removeItem("token");
  }

  if (!token || !user) {
    return (
      <div className="container">
        <h1>Seller Intelligence Platform</h1>
        <p>Track listings, sales data, and buybox insights (Phase 1 foundation).</p>

        <form onSubmit={onAuthSubmit} className="card">
          <h2>{mode === "login" ? "Login" : "Create Account"}</h2>
          {mode === "signup" && (
            <input
              placeholder="Full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          )}
          <input
            placeholder="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <input
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <button disabled={loading}>{loading ? "Please wait..." : "Submit"}</button>
          <button
            type="button"
            className="secondary"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
          >
            Switch to {mode === "login" ? "Signup" : "Login"}
          </button>
          {message && <p className="message">{message}</p>}
        </form>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header-row">
        <h1>Welcome, {user.name}</h1>
        <button className="secondary" onClick={logout}>
          Logout
        </button>
      </div>

      <div className="stats-grid">
        <div className="card">
          <h3>Total Products</h3>
          <strong>{summary?.total_products ?? 0}</strong>
        </div>
        <div className="card">
          <h3>Low Stock Items</h3>
          <strong>{summary?.low_stock_items ?? 0}</strong>
        </div>
        <div className="card">
          <h3>Average Sell Price</h3>
          <strong>${summary?.average_price ?? 0}</strong>
        </div>
        <div className="card">
          <h3>Total Orders</h3>
          <strong>{summary?.total_orders ?? 0}</strong>
        </div>
        <div className="card">
          <h3>Total Sales</h3>
          <strong>${summary?.total_sales ?? 0}</strong>
        </div>
        <div className="card">
          <h3>Units Sold</h3>
          <strong>{summary?.total_units_sold ?? 0}</strong>
        </div>
      </div>

      <form onSubmit={onCreateProduct} className="card">
        <h2>Add Product</h2>
        <div className="form-grid">
          <input
            placeholder="Title"
            value={form.title}
            onChange={(e) => setForm({ ...form, title: e.target.value })}
            required
          />
          <input
            placeholder="SKU"
            value={form.sku}
            onChange={(e) => setForm({ ...form, sku: e.target.value })}
            required
          />
          <input
            placeholder="Sell Price"
            type="number"
            value={form.sell_price}
            onChange={(e) => setForm({ ...form, sell_price: Number(e.target.value) })}
            required
          />
          <input
            placeholder="Stock"
            type="number"
            value={form.stock}
            onChange={(e) => setForm({ ...form, stock: Number(e.target.value) })}
            required
          />
          <input
            placeholder="Marketplace"
            value={form.marketplace}
            onChange={(e) => setForm({ ...form, marketplace: e.target.value })}
            required
          />
        </div>
        <button>Add Product</button>
      </form>

      <div className="card">
        <h2>Your Products</h2>
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>SKU</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Marketplace</th>
            </tr>
          </thead>
          <tbody>
            {products.map((product) => (
              <tr key={product.id}>
                <td>{product.title}</td>
                <td>{product.sku}</td>
                <td>${product.sell_price}</td>
                <td>{product.stock}</td>
                <td>{product.marketplace}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form onSubmit={onCreateOrder} className="card">
        <h2>Create Order</h2>
        <div className="form-grid">
          <input
            placeholder="Order Number"
            value={orderNumber}
            onChange={(e) => setOrderNumber(e.target.value)}
            required
          />
          <input
            placeholder="Marketplace"
            value={orderMarketplace}
            onChange={(e) => setOrderMarketplace(e.target.value)}
            required
          />
          <select
            value={orderProductId}
            onChange={(e) => setOrderProductId(Number(e.target.value))}
            required
          >
            <option value={0}>Select Product</option>
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.sku} - {product.title}
              </option>
            ))}
          </select>
          <input
            placeholder="Quantity"
            type="number"
            value={orderQty}
            onChange={(e) => setOrderQty(Number(e.target.value))}
            required
          />
          <input
            placeholder="Unit Price"
            type="number"
            value={orderPrice}
            onChange={(e) => setOrderPrice(Number(e.target.value))}
            required
          />
        </div>
        <button>Create Order</button>
      </form>

      <div className="card">
        <h2>Recent Orders</h2>
        <table>
          <thead>
            <tr>
              <th>Order #</th>
              <th>Marketplace</th>
              <th>Total</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={order.id}>
                <td>{order.order_number}</td>
                <td>{order.marketplace}</td>
                <td>${order.total_amount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <form onSubmit={onPredictBuybox} className="card">
        <h2>Buybox Predictor</h2>
        <div className="form-grid">
          <input
            placeholder="SKU"
            value={buyboxInput.sku}
            onChange={(e) => setBuyboxInput({ ...buyboxInput, sku: e.target.value })}
            required
          />
          <input
            placeholder="SellPrice"
            type="number"
            value={buyboxInput.SellPrice}
            onChange={(e) =>
              setBuyboxInput({ ...buyboxInput, SellPrice: Number(e.target.value) })
            }
            required
          />
          <input
            placeholder="ShippingPrice"
            type="number"
            value={buyboxInput.ShippingPrice}
            onChange={(e) =>
              setBuyboxInput({ ...buyboxInput, ShippingPrice: Number(e.target.value) })
            }
            required
          />
          <input
            placeholder="MinCompetitorPrice"
            type="number"
            value={buyboxInput.MinCompetitorPrice}
            onChange={(e) =>
              setBuyboxInput({ ...buyboxInput, MinCompetitorPrice: Number(e.target.value) })
            }
            required
          />
          <input
            placeholder="PositiveFeedbackPercent"
            type="number"
            value={buyboxInput.PositiveFeedbackPercent}
            onChange={(e) =>
              setBuyboxInput({
                ...buyboxInput,
                PositiveFeedbackPercent: Number(e.target.value),
              })
            }
            required
          />
          <input
            placeholder="IsFBA (0/1)"
            type="number"
            value={buyboxInput.IsFBA}
            onChange={(e) => setBuyboxInput({ ...buyboxInput, IsFBA: Number(e.target.value) })}
            required
          />
        </div>
        <button>Predict Buybox</button>
        {prediction && (
          <p className="message ok">
            Recommended Price: ${prediction.recommended_price} | Confidence: {prediction.confidence}{" "}
            | Model: {prediction.model_name}
          </p>
        )}
      </form>

      <form onSubmit={onAgentSubmit} className="card">
        <h2>Agent Chat</h2>
        <input
          placeholder="Try: show total sales OR predict buybox"
          value={agentPrompt}
          onChange={(e) => setAgentPrompt(e.target.value)}
          required
        />
        <button>Run Agent Task</button>
        {agentReply && <p className="message ok">{agentReply}</p>}
      </form>
      {message && <p className="message">{message}</p>}
    </div>
  );
}
