import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, useNavigate, useParams, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { 
  Plus, 
  Radar, 
  ArrowLeft, 
  ExternalLink, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  MessageSquare,
  Trash2,
  AlertCircle,
  Loader2,
  Zap,
  ThumbsUp,
  ThumbsDown,
  Hash,
  Target,
  ChevronDown,
  Bug,
  Info,
  Database,
  LogOut,
  User,
  Mail,
  Lock,
  Edit,
  Save,
  X,
  Link2,
  MessageCircle,
  Settings,
  Shield,
  History,
  BarChart3,
  ChevronRight,
  AlertTriangle
} from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios
axios.defaults.withCredentials = true;

// Add interceptor to include Authorization header from localStorage
axios.interceptors.request.use((config) => {
  const token = localStorage.getItem('session_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ============== AUTH CONTEXT ==============
const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(false);

  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('session_token');
    if (!token) {
      return null;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
      return response.data;
    } catch (e) {
      localStorage.removeItem('session_token');
      setUser(null);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (e) {
      console.error("Logout error:", e);
    } finally {
      localStorage.removeItem('session_token');
      setUser(null);
    }
  }, []);

  return { user, setUser, loading, checkAuth, logout };
};

// ============== LOGIN PAGE ==============
const LoginPage = ({ setUser }) => {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState("login");
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: ""
  });

  // Check if already logged in
  useEffect(() => {
    const checkExisting = async () => {
      const token = localStorage.getItem('session_token');
      if (!token) return;
      
      try {
        const response = await axios.get(`${API}/auth/me`);
        if (response.data) {
          setUser(response.data);
          navigate("/dashboard");
        }
      } catch (e) {
        // Not logged in or invalid token
        localStorage.removeItem('session_token');
      }
    };
    checkExisting();
  }, [navigate, setUser]);

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });
      // Store token in localStorage
      if (response.data.session_token) {
        localStorage.setItem('session_token', response.data.session_token);
      }
      setUser(response.data);
      toast.success(`Welcome back, ${response.data.name}!`);
      navigate("/dashboard");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  const handleEmailSignup = async (e) => {
    e.preventDefault();
    if (!formData.name) {
      toast.error("Name is required");
      return;
    }
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/signup`, {
        email: formData.email,
        password: formData.password,
        name: formData.name
      });
      // Store token in localStorage
      if (response.data.session_token) {
        localStorage.setItem('session_token', response.data.session_token);
      }
      setUser(response.data);
      toast.success(`Welcome, ${response.data.name}!`);
      navigate("/dashboard");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b] flex items-center justify-center p-6">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Radar className="w-10 h-10 text-[#D3F34B]" />
          </div>
          <h1 className="font-heading text-4xl font-black tracking-tighter uppercase text-white">
            SENTIENT TRACKER
          </h1>
          <p className="text-zinc-500 mt-2">Game Community Pulse</p>
        </div>

        {/* Auth Card */}
        <div className="card-glass p-8">
            {/* Email Login Form */}

          {/* Email Auth Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="w-full bg-black/30 mb-6">
              <TabsTrigger value="login" className="flex-1 data-[state=active]:bg-[#D3F34B] data-[state=active]:text-black">
                Sign In
              </TabsTrigger>
              <TabsTrigger value="signup" className="flex-1 data-[state=active]:bg-[#D3F34B] data-[state=active]:text-black">
                Sign Up
              </TabsTrigger>
            </TabsList>

            <TabsContent value="login">
              <form onSubmit={handleEmailLogin} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm text-zinc-400">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <Input
                      type="email"
                      data-testid="email-input"
                      placeholder="you@example.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="pl-10 bg-black/50 border-white/10"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-zinc-400">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <Input
                      type="password"
                      data-testid="password-input"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="pl-10 bg-black/50 border-white/10"
                      required
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  data-testid="login-submit-btn"
                  className="w-full bg-[#D3F34B] text-black hover:bg-[#D3F34B]/90 font-bold"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Sign In"}
                </Button>
              </form>
            </TabsContent>

            <TabsContent value="signup">
              <form onSubmit={handleEmailSignup} className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-sm text-zinc-400">Name</Label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <Input
                      type="text"
                      data-testid="name-input"
                      placeholder="Your name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="pl-10 bg-black/50 border-white/10"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-zinc-400">Email</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <Input
                      type="email"
                      data-testid="signup-email-input"
                      placeholder="you@example.com"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="pl-10 bg-black/50 border-white/10"
                      required
                    />
                  </div>
                </div>
                <div className="space-y-2">
                  <Label className="text-sm text-zinc-400">Password</Label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-500" />
                    <Input
                      type="password"
                      data-testid="signup-password-input"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="pl-10 bg-black/50 border-white/10"
                      required
                      minLength={6}
                    />
                  </div>
                </div>
                <Button
                  type="submit"
                  disabled={loading}
                  data-testid="signup-submit-btn"
                  className="w-full bg-[#D3F34B] text-black hover:bg-[#D3F34B]/90 font-bold"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Create Account"}
                </Button>
              </form>
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
};

// ============== PROTECTED ROUTE ==============
const ProtectedRoute = ({ children, user, checkAuth }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAuthenticated, setIsAuthenticated] = useState(null);
  const [checkedAuth, setCheckedAuth] = useState(false);

  useEffect(() => {
    // If we already have a user from parent, we're authenticated
    if (user) {
      setIsAuthenticated(true);
      return;
    }

    // If passed user via location state (from login), we're authenticated
    if (location.state?.user) {
      setIsAuthenticated(true);
      return;
    }

    // Check localStorage for token
    const token = localStorage.getItem('session_token');
    if (!token) {
      setIsAuthenticated(false);
      navigate("/login");
      return;
    }

    // Verify token is valid
    if (!checkedAuth) {
      setCheckedAuth(true);
      checkAuth().then(userData => {
        if (userData) {
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          navigate("/login");
        }
      });
    }
  }, [checkAuth, navigate, location.state, user, checkedAuth]);

  if (isAuthenticated === null) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[#D3F34B] animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return children;
};

// ============== DASHBOARD PAGE ==============
const Dashboard = ({ user, logout }) => {
  const [games, setGames] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newGame, setNewGame] = useState({ name: "", subreddit: "", keywords: "" });
  const [creating, setCreating] = useState(false);
  const navigate = useNavigate();

  const fetchGames = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/games`);
      setGames(response.data);
    } catch (e) {
      console.error("Error fetching games:", e);
      if (e.response?.status === 401) {
        navigate("/login");
      } else {
        toast.error("Failed to load tracked games");
      }
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  useEffect(() => {
    fetchGames();
  }, [fetchGames]);

  const handleCreateGame = async (e) => {
    e.preventDefault();
    if (!newGame.name || !newGame.subreddit) {
      toast.error("Game name and subreddit are required");
      return;
    }
    setCreating(true);
    try {
      const response = await axios.post(`${API}/games`, {
        name: newGame.name,
        subreddit: newGame.subreddit,
        keywords: newGame.keywords
      });
      setGames([...games, response.data]);
      setNewGame({ name: "", subreddit: "", keywords: "" });
      setDialogOpen(false);
      toast.success("Game added successfully");
    } catch (e) {
      toast.error("Failed to add game");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteGame = async (gameId, e) => {
    e.stopPropagation();
    try {
      await axios.delete(`${API}/games/${gameId}`);
      setGames(games.filter(g => g.id !== gameId));
      toast.success("Game removed");
    } catch (e) {
      toast.error("Failed to delete game");
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Header with User Info */}
      <div className="border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 md:px-12 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Radar className="w-6 h-6 text-[#D3F34B]" />
            <span className="font-heading font-bold text-white">SENTIENT TRACKER</span>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} className="w-8 h-8 rounded-full" />
              ) : (
                <div className="w-8 h-8 bg-[#D3F34B]/20 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-[#D3F34B]" />
                </div>
              )}
              <span className="text-sm text-zinc-400 hidden sm:block">{user?.name}</span>
            </div>
            <button
              onClick={() => navigate("/account")}
              className="p-2 text-zinc-500 hover:text-[#D3F34B] transition-colors"
              data-testid="account-btn"
              title="Account Settings"
            >
              <Settings className="w-5 h-5" />
            </button>
            <button
              onClick={handleLogout}
              className="p-2 text-zinc-500 hover:text-white transition-colors"
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="hero-glow">
        <div className="max-w-7xl mx-auto px-6 md:px-12 pt-12 pb-8">
          <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-6">
            <div>
              <h1 className="font-heading text-4xl md:text-5xl font-black tracking-tighter uppercase leading-none text-white" data-testid="dashboard-title">
                YOUR GAMES
              </h1>
              <p className="mt-4 text-base text-zinc-400 max-w-xl">
                Track community sentiment across your favorite games.
              </p>
            </div>
            
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <button className="btn-primary px-8 py-4 flex items-center gap-3" data-testid="add-game-btn">
                  <span className="flex items-center gap-2">
                    <Plus className="w-5 h-5" />
                    ADD GAME
                  </span>
                </button>
              </DialogTrigger>
              <DialogContent className="bg-[#121214] border-white/10 max-w-md">
                <DialogHeader>
                  <DialogTitle className="font-heading text-2xl font-bold tracking-tight text-white">
                    Track New Game
                  </DialogTitle>
                  <DialogDescription className="text-zinc-400">
                    Enter the game details and subreddit to start tracking.
                  </DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateGame} className="space-y-6 mt-4">
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-zinc-300">Game Name</Label>
                    <Input
                      data-testid="game-name-input"
                      placeholder="e.g. Elden Ring"
                      value={newGame.name}
                      onChange={(e) => setNewGame({ ...newGame, name: e.target.value })}
                      className="bg-black/50 border-white/10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-zinc-300">Subreddit</Label>
                    <Input
                      data-testid="subreddit-input"
                      placeholder="e.g. Eldenring or r/Eldenring"
                      value={newGame.subreddit}
                      onChange={(e) => setNewGame({ ...newGame, subreddit: e.target.value })}
                      className="bg-black/50 border-white/10"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-sm font-medium text-zinc-300">Keywords (optional)</Label>
                    <Input
                      data-testid="keywords-input"
                      placeholder="e.g. DLC, bugs, performance"
                      value={newGame.keywords}
                      onChange={(e) => setNewGame({ ...newGame, keywords: e.target.value })}
                      className="bg-black/50 border-white/10"
                    />
                  </div>
                  <Button
                    type="submit"
                    disabled={creating}
                    data-testid="submit-game-btn"
                    className="w-full bg-[#D3F34B] text-black hover:bg-[#D3F34B]/90 font-bold"
                  >
                    {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : "Start Tracking"}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </div>

      {/* Games Grid */}
      <div className="max-w-7xl mx-auto px-6 md:px-12 pb-16">
        <div className="flex items-center gap-3 mb-8">
          <Target className="w-5 h-5 text-[#D3F34B]" />
          <h2 className="font-heading text-xl font-bold tracking-tight uppercase text-white">
            Tracked Games
          </h2>
          <span className="font-mono text-sm text-zinc-500">({games.length})</span>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="card-glass p-6 animate-pulse">
                <div className="h-6 bg-white/5 rounded mb-4 w-3/4" />
                <div className="h-4 bg-white/5 rounded mb-2 w-1/2" />
              </div>
            ))}
          </div>
        ) : games.length === 0 ? (
          <div className="card-glass p-12 text-center">
            <Radar className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
            <h3 className="font-heading text-xl font-bold text-white mb-2">No Games Tracked</h3>
            <p className="text-zinc-400 mb-6">Add your first game to start monitoring.</p>
            <button onClick={() => setDialogOpen(true)} className="btn-primary px-6 py-3" data-testid="empty-add-game-btn">
              <span className="flex items-center gap-2">
                <Plus className="w-4 h-4" />
                ADD YOUR FIRST GAME
              </span>
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="games-grid">
            {games.map((game) => (
              <div
                key={game.id}
                onClick={() => navigate(`/game/${game.id}`)}
                className="card-glass card-hover p-6 cursor-pointer group relative"
                data-testid={`game-card-${game.id}`}
              >
                <button
                  onClick={(e) => handleDeleteGame(game.id, e)}
                  className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                  data-testid={`delete-game-${game.id}`}
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <div className="flex items-start gap-4">
                  <div className="w-12 h-12 bg-[#D3F34B]/10 flex items-center justify-center">
                    <Zap className="w-6 h-6 text-[#D3F34B]" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-heading text-lg font-bold text-white truncate">{game.name}</h3>
                    <p className="font-mono text-sm text-zinc-500 mt-1">r/{game.subreddit}</p>
                    {game.keywords && (
                      <div className="flex items-center gap-2 mt-3">
                        <Hash className="w-3 h-3 text-zinc-600" />
                        <span className="text-xs text-zinc-500 truncate">{game.keywords}</span>
                      </div>
                    )}
                  </div>
                </div>
                <div className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-xs text-zinc-600 font-mono">
                    Added {new Date(game.created_at).toLocaleDateString()}
                  </span>
                  <span className="text-xs text-[#D3F34B] font-mono group-hover:translate-x-1 transition-transform">
                    VIEW →
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// ============== DEBUG INFO COMPONENT ==============
const DebugInfoPanel = ({ debugInfo, cached }) => {
  const [isOpen, setIsOpen] = useState(false);

  if (!debugInfo) return null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className="mt-4">
      <CollapsibleTrigger className="flex items-center gap-2 text-zinc-500 hover:text-zinc-300 transition-colors text-sm">
        <Bug className="w-4 h-4" />
        <span className="font-mono">Debug Info</span>
        <ChevronDown className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </CollapsibleTrigger>
      <CollapsibleContent className="mt-3">
        <div className="bg-black/50 border border-white/5 p-4 font-mono text-xs space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-zinc-500">Subreddit:</span>
            <span className="text-[#00E5FF]">{debugInfo.subreddit_normalized || 'N/A'}</span>
          </div>
          {debugInfo.window_used && (
            <div className="flex items-center gap-2">
              <span className="text-zinc-500">Time Window:</span>
              <span className="text-[#D3F34B]">{debugInfo.window_used}</span>
            </div>
          )}
          {debugInfo.posts_url && (
            <div>
              <span className="text-zinc-500">API URL:</span>
              <div className="text-zinc-400 break-all mt-1 text-[10px]">{debugInfo.posts_url}</div>
              {debugInfo.posts_status && (
                <span className={`${debugInfo.posts_status === 200 ? 'text-[#00FF94]' : 'text-[#FF003C]'}`}>
                  (HTTP {debugInfo.posts_status})
                </span>
              )}
            </div>
          )}
          <div className="flex flex-wrap gap-4 pt-2 border-t border-white/5">
            <div>
              <span className="text-zinc-500">Raw Posts:</span>
              <span className="text-white ml-2">{debugInfo.raw_post_count || 0}</span>
            </div>
            <div>
              <span className="text-zinc-500">After Filter:</span>
              <span className="text-white ml-2">{debugInfo.after_quality_filter || 0}</span>
            </div>
            <div>
              <span className="text-zinc-500">Final:</span>
              <span className="text-white ml-2">{debugInfo.final_post_count || 0}</span>
            </div>
          </div>
          {(debugInfo.comments_fetched_for > 0 || debugInfo.total_comments > 0) && (
            <div className="flex flex-wrap gap-4 pt-2 border-t border-white/5">
              <div>
                <span className="text-zinc-500">Posts w/ Comments:</span>
                <span className="text-white ml-2">{debugInfo.comments_fetched_for || 0}</span>
              </div>
              <div>
                <span className="text-zinc-500">Total Comments:</span>
                <span className="text-white ml-2">{debugInfo.total_comments || 0}</span>
              </div>
            </div>
          )}
          {cached && (
            <div className="flex items-center gap-2 text-[#FCEE0A]">
              <Database className="w-3 h-3" />
              <span>Results from cache</span>
            </div>
          )}
          {debugInfo.error_details && (
            <div className="text-zinc-400 pt-2 border-t border-white/5">
              <span className="text-zinc-500">Note:</span> {debugInfo.error_details}
            </div>
          )}
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
};

// ============== GAME DETAIL PAGE ==============
const GameDetail = ({ user }) => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [game, setGame] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({ name: "", subreddit: "", keywords: "" });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [gameRes, resultRes] = await Promise.all([
          axios.get(`${API}/games/${id}`),
          axios.get(`${API}/games/${id}/latest-result`)
        ]);
        setGame(gameRes.data);
        setResult(resultRes.data);
        setEditForm({
          name: gameRes.data.name,
          subreddit: gameRes.data.subreddit,
          keywords: gameRes.data.keywords || ""
        });
      } catch (e) {
        console.error("Error fetching game:", e);
        if (e.response?.status === 404 || e.response?.status === 401) {
          toast.error(e.response?.status === 401 ? "Please login" : "Game not found");
          navigate(e.response?.status === 401 ? "/login" : "/dashboard");
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id, navigate]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const response = await axios.post(`${API}/games/${id}/scan`);
      setResult(response.data);
      if (response.data.error) {
        toast.error(response.data.error);
      } else {
        toast.success(response.data.cached ? "Scan completed (from cache)" : "Scan completed");
      }
    } catch (e) {
      toast.error("Failed to run scan");
    } finally {
      setScanning(false);
    }
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      const response = await axios.put(`${API}/games/${id}`, editForm);
      setGame(response.data);
      setEditing(false);
      toast.success("Game updated");
    } catch (e) {
      toast.error("Failed to update game");
    } finally {
      setSaving(false);
    }
  };

  const getSentimentColor = (label) => {
    switch (label?.toLowerCase()) {
      case "positive": return "text-[#00FF94] border-[#00FF94]";
      case "negative": return "text-[#FF003C] border-[#FF003C]";
      case "mixed": return "text-[#FCEE0A] border-[#FCEE0A]";
      default: return "text-zinc-400 border-zinc-400";
    }
  };

  const getSentimentIcon = (label) => {
    switch (label?.toLowerCase()) {
      case "positive": return <TrendingUp className="w-5 h-5" />;
      case "negative": return <TrendingDown className="w-5 h-5" />;
      default: return <AlertCircle className="w-5 h-5" />;
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "Never";
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[#D3F34B] animate-spin" />
      </div>
    );
  }

  if (!game) return null;

  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Header */}
      <div className="border-b border-white/5">
        <div className="max-w-7xl mx-auto px-6 md:px-12 py-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors mb-6"
            data-testid="back-btn"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-mono text-sm">Back to Dashboard</span>
          </button>
          
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="flex-1">
              {editing ? (
                <div className="space-y-4 max-w-md">
                  <div>
                    <Label className="text-sm text-zinc-400">Game Name</Label>
                    <Input
                      value={editForm.name}
                      onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                      className="bg-black/50 border-white/10 mt-1"
                      data-testid="edit-name-input"
                    />
                  </div>
                  <div>
                    <Label className="text-sm text-zinc-400">Subreddit</Label>
                    <Input
                      value={editForm.subreddit}
                      onChange={(e) => setEditForm({ ...editForm, subreddit: e.target.value })}
                      className="bg-black/50 border-white/10 mt-1"
                      data-testid="edit-subreddit-input"
                    />
                  </div>
                  <div>
                    <Label className="text-sm text-zinc-400">Keywords</Label>
                    <Input
                      value={editForm.keywords}
                      onChange={(e) => setEditForm({ ...editForm, keywords: e.target.value })}
                      className="bg-black/50 border-white/10 mt-1"
                      data-testid="edit-keywords-input"
                    />
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={handleSaveEdit}
                      disabled={saving}
                      className="bg-[#D3F34B] text-black hover:bg-[#D3F34B]/90"
                      data-testid="save-edit-btn"
                    >
                      {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <><Save className="w-4 h-4 mr-2" /> Save</>}
                    </Button>
                    <Button
                      onClick={() => setEditing(false)}
                      variant="outline"
                      className="border-white/10"
                      data-testid="cancel-edit-btn"
                    >
                      <X className="w-4 h-4 mr-2" /> Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center gap-3 mb-2">
                    <Zap className="w-6 h-6 text-[#D3F34B]" />
                    <span className="font-mono text-sm text-zinc-500">r/{game.subreddit}</span>
                    <button
                      onClick={() => setEditing(true)}
                      className="p-1 text-zinc-500 hover:text-[#D3F34B] transition-colors"
                      data-testid="edit-game-btn"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                  </div>
                  <h1 className="font-heading text-4xl md:text-5xl font-black tracking-tighter uppercase text-white" data-testid="game-title">
                    {game.name}
                  </h1>
                  {game.keywords && (
                    <div className="flex items-center gap-2 mt-3">
                      <Hash className="w-4 h-4 text-zinc-600" />
                      <span className="text-sm text-zinc-500">{game.keywords}</span>
                    </div>
                  )}
                </>
              )}
            </div>
            
            {!editing && (
              <div className="flex flex-col items-end gap-2">
                <button
                  onClick={handleScan}
                  disabled={scanning}
                  className="btn-primary px-8 py-4 flex items-center gap-3 disabled:opacity-50"
                  data-testid="run-scan-btn"
                >
                  <span className="flex items-center gap-2">
                    {scanning ? (
                      <><Loader2 className="w-5 h-5 animate-spin" /> SCANNING...</>
                    ) : (
                      <><Radar className="w-5 h-5" /> RUN SCAN</>
                    )}
                  </span>
                </button>
                <div className="flex items-center gap-2 text-zinc-600 text-xs" data-testid="mvp-note">
                  <Info className="w-3 h-3" />
                  <span className="font-mono">MVP mode: uses Arctic Shift (Reddit data mirror)</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 md:px-12 py-8">
        {scanning && (
          <div className="card-glass p-8 mb-8 relative overflow-hidden scan-animation">
            <div className="flex items-center gap-4">
              <Loader2 className="w-8 h-8 text-[#D3F34B] animate-spin" />
              <div>
                <h3 className="font-heading text-xl font-bold text-white">Scanning Reddit...</h3>
                <p className="text-zinc-400 text-sm mt-1">Fetching posts and running AI analysis</p>
              </div>
            </div>
          </div>
        )}

        {result?.error && (
          <div className="card-glass p-6 mb-8 border-l-2 border-l-[#FF003C]" data-testid="scan-error">
            <div className="flex items-start gap-4">
              <AlertCircle className="w-6 h-6 text-[#FF003C] flex-shrink-0 mt-1" />
              <div className="flex-1">
                <h3 className="font-heading text-lg font-bold text-white">Scan Error</h3>
                <p className="text-zinc-400 mt-1">{result.error}</p>
                <DebugInfoPanel debugInfo={result.debug_info} cached={result.cached} />
              </div>
            </div>
          </div>
        )}

        {!result && !scanning && (
          <div className="card-glass p-12 text-center" data-testid="no-results">
            <Radar className="w-12 h-12 text-zinc-600 mx-auto mb-4" />
            <h3 className="font-heading text-xl font-bold text-white mb-2">No Scans Yet</h3>
            <p className="text-zinc-400 mb-6">Run your first scan to see community sentiment.</p>
            <button onClick={handleScan} className="btn-primary px-6 py-3" data-testid="first-scan-btn">
              <span className="flex items-center gap-2">
                <Radar className="w-4 h-4" /> RUN FIRST SCAN
              </span>
            </button>
          </div>
        )}

        {result && !result.error && (
          <div className="space-y-8" data-testid="scan-results">
            {result.cached && (
              <div className="flex items-center gap-2 text-[#FCEE0A] text-sm font-mono">
                <Database className="w-4 h-4" />
                <span>Results from cache (data less than 10 min old)</span>
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="card-glass p-6">
                <div className="font-mono text-sm text-zinc-500 uppercase tracking-wider mb-2">Posts Analysed</div>
                <div className="font-heading text-3xl font-black text-white" data-testid="post-count">{result.post_count}</div>
              </div>
              <div className="card-glass p-6">
                <div className="font-mono text-sm text-zinc-500 uppercase tracking-wider mb-2">Last 7 Days</div>
                <div className="font-heading text-3xl font-black text-white" data-testid="posts-7-days">{result.posts_last_7_days}</div>
              </div>
              <div className="card-glass p-6">
                <div className="font-mono text-sm text-zinc-500 uppercase tracking-wider mb-2">Comments</div>
                <div className="font-heading text-3xl font-black text-white" data-testid="comments-sampled">{result.comments_sampled || 0}</div>
              </div>
              <div className="card-glass p-6">
                <div className="font-mono text-sm text-zinc-500 uppercase tracking-wider mb-2">Sentiment</div>
                <div className={`font-heading text-2xl font-black ${getSentimentColor(result.sentiment_label)}`} data-testid="sentiment-label">
                  {result.sentiment_label}
                </div>
              </div>
              <div className="card-glass p-6">
                <div className="font-mono text-sm text-zinc-500 uppercase tracking-wider mb-2">Last Scanned</div>
                <div className="flex items-center gap-2 text-white">
                  <Clock className="w-4 h-4 text-zinc-500" />
                  <span className="font-mono text-sm" data-testid="last-scan">{formatDate(result.created_at)}</span>
                </div>
              </div>
            </div>

            <div className="card-glass p-6 active-border" data-testid="sentiment-summary">
              <div className="flex items-center gap-3 mb-4">
                <div className={`p-2 ${getSentimentColor(result.sentiment_label)} bg-current/10`}>
                  {getSentimentIcon(result.sentiment_label)}
                </div>
                <h3 className="font-heading text-xl font-bold text-white">Sentiment Analysis</h3>
              </div>
              <p className="text-zinc-300 leading-relaxed">{result.sentiment_summary || "No summary available"}</p>
              <DebugInfoPanel debugInfo={result.debug_info} cached={result.cached} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="card-glass p-6" data-testid="themes-section">
                <div className="flex items-center gap-3 mb-4">
                  <MessageSquare className="w-5 h-5 text-[#00E5FF]" />
                  <h3 className="font-heading text-lg font-bold text-white">Top Themes</h3>
                </div>
                {result.themes?.length > 0 ? (
                  <ul className="space-y-3">
                    {result.themes.map((theme, i) => (
                      <li key={i} className="flex items-start gap-3">
                        <span className="font-mono text-xs text-[#00E5FF] mt-1">{String(i + 1).padStart(2, '0')}</span>
                        <span className="text-zinc-300 text-sm">{theme}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-zinc-500 text-sm">No themes identified</p>
                )}
              </div>

              <div className="card-glass p-6" data-testid="pain-points-section">
                <div className="flex items-center gap-3 mb-4">
                  <ThumbsDown className="w-5 h-5 text-[#FF003C]" />
                  <h3 className="font-heading text-lg font-bold text-white">Pain Points</h3>
                </div>
                {result.pain_points?.length > 0 ? (
                  <ul className="space-y-4">
                    {result.pain_points.map((point, i) => {
                      const text = typeof point === 'string' ? point : point?.text || '';
                      const evidence = typeof point === 'object' ? point?.evidence || [] : [];
                      return (
                        <li key={i} className="space-y-1">
                          <div className="flex items-start gap-3">
                            <span className="font-mono text-xs text-[#FF003C] mt-1">{String(i + 1).padStart(2, '0')}</span>
                            <span className="text-zinc-300 text-sm">{text}</span>
                          </div>
                          {evidence.length > 0 && (
                            <div className="flex items-center gap-2 ml-7">
                              <Link2 className="w-3 h-3 text-zinc-600" />
                              {evidence.map((link, j) => (
                                <a
                                  key={j}
                                  href={link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-zinc-500 hover:text-[#FF003C] transition-colors font-mono"
                                  data-testid={`pain-point-${i}-evidence-${j}`}
                                >
                                  [source {j + 1}]
                                </a>
                              ))}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="text-zinc-500 text-sm">No pain points identified</p>
                )}
              </div>

              <div className="card-glass p-6" data-testid="wins-section">
                <div className="flex items-center gap-3 mb-4">
                  <ThumbsUp className="w-5 h-5 text-[#00FF94]" />
                  <h3 className="font-heading text-lg font-bold text-white">Community Wins</h3>
                </div>
                {result.wins?.length > 0 ? (
                  <ul className="space-y-4">
                    {result.wins.map((win, i) => {
                      const text = typeof win === 'string' ? win : win?.text || '';
                      const evidence = typeof win === 'object' ? win?.evidence || [] : [];
                      return (
                        <li key={i} className="space-y-1">
                          <div className="flex items-start gap-3">
                            <span className="font-mono text-xs text-[#00FF94] mt-1">{String(i + 1).padStart(2, '0')}</span>
                            <span className="text-zinc-300 text-sm">{text}</span>
                          </div>
                          {evidence.length > 0 && (
                            <div className="flex items-center gap-2 ml-7">
                              <Link2 className="w-3 h-3 text-zinc-600" />
                              {evidence.map((link, j) => (
                                <a
                                  key={j}
                                  href={link}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-xs text-zinc-500 hover:text-[#00FF94] transition-colors font-mono"
                                  data-testid={`win-${i}-evidence-${j}`}
                                >
                                  [source {j + 1}]
                                </a>
                              ))}
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p className="text-zinc-500 text-sm">No wins identified</p>
                )}
              </div>
            </div>

            <div className="card-glass p-6" data-testid="source-posts-section">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <ExternalLink className="w-5 h-5 text-[#D3F34B]" />
                  <h3 className="font-heading text-lg font-bold text-white">Source Posts</h3>
                </div>
                <span className="font-mono text-sm text-zinc-500">{result.source_posts?.length || 0} posts</span>
              </div>
              
              <ScrollArea className="h-[400px]">
                <div className="space-y-2">
                  {result.source_posts?.map((post, i) => (
                    <a
                      key={post.id || i}
                      href={post.permalink}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block p-4 bg-black/30 hover:bg-black/50 border border-white/5 hover:border-white/10 transition-all group"
                      data-testid={`source-post-${i}`}
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <h4 className="text-white text-sm font-medium group-hover:text-[#D3F34B] transition-colors line-clamp-2">
                            {post.title}
                          </h4>
                          <div className="flex items-center gap-4 mt-2">
                            <span className="font-mono text-xs text-zinc-500">{post.score} pts</span>
                            <span className="font-mono text-xs text-zinc-500">{post.num_comments} comments</span>
                            <span className="font-mono text-xs text-zinc-600">
                              {new Date(post.created_utc * 1000).toLocaleDateString()}
                            </span>
                          </div>
                        </div>
                        <ExternalLink className="w-4 h-4 text-zinc-600 group-hover:text-[#D3F34B] flex-shrink-0" />
                      </div>
                    </a>
                  ))}
                </div>
              </ScrollArea>
            </div>

            {/* Sentiment Trend Chart */}
            <SentimentTrendChart gameId={id} />

            {/* Scan History List */}
            <ScanHistoryList gameId={id} />
          </div>
        )}
      </div>
    </div>
  );
};

// ============== SENTIMENT TREND CHART ==============
const SentimentTrendChart = ({ gameId }) => {
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await axios.get(`${API}/games/${gameId}/history?limit=20`);
        setHistoryData(response.data);
      } catch (e) {
        console.error("Error fetching history:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [gameId]);

  if (loading) {
    return (
      <div className="card-glass p-6 flex items-center justify-center h-[200px]">
        <Loader2 className="w-6 h-6 text-[#D3F34B] animate-spin" />
      </div>
    );
  }

  if (!historyData || historyData.trend_data.length < 2) {
    return (
      <div className="card-glass p-6" data-testid="sentiment-trend-empty">
        <div className="flex items-center gap-3 mb-4">
          <BarChart3 className="w-5 h-5 text-[#D3F34B]" />
          <h3 className="font-heading text-lg font-bold text-white">Sentiment Trend</h3>
        </div>
        <p className="text-zinc-500 text-sm">Run more scans to see sentiment trends over time.</p>
      </div>
    );
  }

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-[#121214] border border-white/10 p-3 font-mono text-xs">
          <p className="text-zinc-400">{new Date(data.created_at).toLocaleDateString()}</p>
          <p className={`font-bold ${
            data.sentiment_label === "Positive" ? "text-[#00FF94]" :
            data.sentiment_label === "Negative" ? "text-[#FF003C]" : "text-[#FCEE0A]"
          }`}>{data.sentiment_label}</p>
          <p className="text-zinc-500">{data.post_count} posts</p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="card-glass p-6" data-testid="sentiment-trend-chart">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <BarChart3 className="w-5 h-5 text-[#D3F34B]" />
          <h3 className="font-heading text-lg font-bold text-white">Sentiment Trend</h3>
        </div>
        <span className="font-mono text-xs text-zinc-500">{historyData.total_scans} scans</span>
      </div>
      <div className="h-[180px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={historyData.trend_data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <XAxis 
              dataKey="created_at" 
              tickFormatter={(val) => new Date(val).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              stroke="#3f3f46"
              tick={{ fill: '#71717a', fontSize: 10 }}
            />
            <YAxis 
              domain={[-1.5, 1.5]} 
              ticks={[-1, 0, 1]}
              tickFormatter={(val) => val === 1 ? '😊' : val === -1 ? '😞' : '😐'}
              stroke="#3f3f46"
              tick={{ fill: '#71717a', fontSize: 12 }}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="#3f3f46" strokeDasharray="3 3" />
            <Line 
              type="monotone" 
              dataKey="sentiment_value" 
              stroke="#D3F34B" 
              strokeWidth={2}
              dot={{ fill: '#D3F34B', strokeWidth: 0, r: 4 }}
              activeDot={{ fill: '#D3F34B', strokeWidth: 0, r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="flex justify-center gap-6 mt-3 text-xs font-mono">
        <span className="text-[#00FF94]">↑ Positive</span>
        <span className="text-[#FCEE0A]">― Mixed</span>
        <span className="text-[#FF003C]">↓ Negative</span>
      </div>
    </div>
  );
};

// ============== SCAN HISTORY LIST ==============
const ScanHistoryList = ({ gameId }) => {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await axios.get(`${API}/games/${gameId}/results?limit=20`);
        setResults(response.data);
      } catch (e) {
        console.error("Error fetching results:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [gameId]);

  if (loading) {
    return (
      <div className="card-glass p-6 flex items-center justify-center h-[200px]">
        <Loader2 className="w-6 h-6 text-[#D3F34B] animate-spin" />
      </div>
    );
  }

  if (results.length === 0) {
    return null;
  }

  const getSentimentColor = (label) => {
    switch (label?.toLowerCase()) {
      case "positive": return "text-[#00FF94]";
      case "negative": return "text-[#FF003C]";
      case "mixed": return "text-[#FCEE0A]";
      default: return "text-zinc-400";
    }
  };

  return (
    <div className="card-glass p-6" data-testid="scan-history-list">
      <div className="flex items-center gap-3 mb-4">
        <History className="w-5 h-5 text-[#00E5FF]" />
        <h3 className="font-heading text-lg font-bold text-white">Scan History</h3>
      </div>
      <div className="space-y-2">
        {results.map((result, index) => (
          <div key={result.id} className="border border-white/5 bg-black/30">
            <button
              onClick={() => setExpandedId(expandedId === result.id ? null : result.id)}
              className="w-full p-4 flex items-center justify-between hover:bg-black/50 transition-colors"
              data-testid={`history-item-${index}`}
            >
              <div className="flex items-center gap-4">
                <span className="font-mono text-xs text-zinc-600">
                  {new Date(result.created_at).toLocaleDateString()}
                </span>
                <span className={`font-bold text-sm ${getSentimentColor(result.sentiment_label)}`}>
                  {result.sentiment_label}
                </span>
                <span className="font-mono text-xs text-zinc-500">
                  {result.post_count} posts
                </span>
                {result.comments_sampled > 0 && (
                  <span className="font-mono text-xs text-zinc-600">
                    {result.comments_sampled} comments
                  </span>
                )}
              </div>
              <ChevronRight className={`w-4 h-4 text-zinc-500 transition-transform ${expandedId === result.id ? 'rotate-90' : ''}`} />
            </button>
            {expandedId === result.id && (
              <div className="px-4 pb-4 border-t border-white/5 space-y-3">
                <p className="text-zinc-400 text-sm mt-3">{result.sentiment_summary}</p>
                {result.themes?.length > 0 && (
                  <div>
                    <span className="text-xs text-zinc-500 font-mono">Themes:</span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {result.themes.slice(0, 5).map((theme, i) => (
                        <span key={i} className="text-xs bg-white/5 px-2 py-1 text-zinc-400">{theme}</span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

// ============== ACCOUNT PAGE ==============
const AccountPage = ({ user, setUser, logout }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [editingName, setEditingName] = useState(false);
  const [newName, setNewName] = useState(user?.name || "");
  const [passwordForm, setPasswordForm] = useState({ current: "", new: "", confirm: "" });
  const [changingPassword, setChangingPassword] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmText, setDeleteConfirmText] = useState("");

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await axios.get(`${API}/account/stats`);
        setStats(response.data);
      } catch (e) {
        console.error("Error fetching stats:", e);
      }
    };
    fetchStats();
  }, []);

  const handleUpdateName = async () => {
    if (!newName.trim()) {
      toast.error("Name cannot be empty");
      return;
    }
    setLoading(true);
    try {
      const response = await axios.put(`${API}/account/profile`, { name: newName });
      setUser({ ...user, name: response.data.name });
      setEditingName(false);
      toast.success("Name updated");
    } catch (e) {
      toast.error("Failed to update name");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    if (passwordForm.new !== passwordForm.confirm) {
      toast.error("Passwords don't match");
      return;
    }
    if (passwordForm.new.length < 6) {
      toast.error("Password must be at least 6 characters");
      return;
    }
    setChangingPassword(true);
    try {
      await axios.post(`${API}/account/change-password`, {
        current_password: passwordForm.current,
        new_password: passwordForm.new
      });
      setPasswordForm({ current: "", new: "", confirm: "" });
      toast.success("Password changed successfully");
    } catch (e) {
      toast.error(e.response?.data?.detail || "Failed to change password");
    } finally {
      setChangingPassword(false);
    }
  };

  const handleRevokeOtherSessions = async () => {
    try {
      const response = await axios.delete(`${API}/account/sessions`);
      toast.success(response.data.message);
    } catch (e) {
      toast.error("Failed to revoke sessions");
    }
  };

  const handleDeleteAccount = async () => {
    if (deleteConfirmText !== "DELETE") {
      toast.error("Please type DELETE to confirm");
      return;
    }
    try {
      await axios.delete(`${API}/account`);
      toast.success("Account deleted");
      logout();
      navigate("/login");
    } catch (e) {
      toast.error("Failed to delete account");
    }
  };

  return (
    <div className="min-h-screen bg-[#09090b]">
      {/* Header */}
      <div className="border-b border-white/5">
        <div className="max-w-3xl mx-auto px-6 py-6">
          <button
            onClick={() => navigate("/dashboard")}
            className="flex items-center gap-2 text-zinc-400 hover:text-white transition-colors mb-6"
            data-testid="back-to-dashboard"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="font-mono text-sm">Back to Dashboard</span>
          </button>
          
          <div className="flex items-center gap-4">
            {user?.picture ? (
              <img src={user.picture} alt={user.name} className="w-16 h-16 rounded-full" />
            ) : (
              <div className="w-16 h-16 bg-[#D3F34B]/20 rounded-full flex items-center justify-center">
                <User className="w-8 h-8 text-[#D3F34B]" />
              </div>
            )}
            <div>
              <h1 className="font-heading text-3xl font-black text-white">Account Settings</h1>
              <p className="text-zinc-500 font-mono text-sm">{user?.email}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
        {/* Stats */}
        {stats && (
          <div className="grid grid-cols-2 gap-4">
            <div className="card-glass p-4">
              <div className="font-mono text-xs text-zinc-500 uppercase">Games Tracked</div>
              <div className="font-heading text-2xl font-black text-white">{stats.games_count}</div>
            </div>
            <div className="card-glass p-4">
              <div className="font-mono text-xs text-zinc-500 uppercase">Total Scans</div>
              <div className="font-heading text-2xl font-black text-white">{stats.scans_count}</div>
            </div>
          </div>
        )}

        {/* Profile Section */}
        <div className="card-glass p-6">
          <div className="flex items-center gap-3 mb-4">
            <User className="w-5 h-5 text-[#D3F34B]" />
            <h2 className="font-heading text-lg font-bold text-white">Profile</h2>
          </div>
          
          <div className="space-y-4">
            <div>
              <Label className="text-sm text-zinc-400">Name</Label>
              {editingName ? (
                <div className="flex gap-2 mt-1">
                  <Input
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    className="bg-black/50 border-white/10"
                    data-testid="edit-name-input"
                  />
                  <Button onClick={handleUpdateName} disabled={loading} className="bg-[#D3F34B] text-black">
                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                  </Button>
                  <Button onClick={() => { setEditingName(false); setNewName(user?.name || ""); }} variant="outline" className="border-white/10">
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-white">{user?.name}</span>
                  <button onClick={() => setEditingName(true)} className="text-zinc-500 hover:text-[#D3F34B]" data-testid="edit-name-btn">
                    <Edit className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
            
            <div>
              <Label className="text-sm text-zinc-400">Email</Label>
              <p className="text-white mt-1">{user?.email}</p>
            </div>
            
            <div>
              <Label className="text-sm text-zinc-400">Auth Provider</Label>
              <p className="text-white mt-1 capitalize">{user?.auth_provider}</p>
            </div>
          </div>
        </div>

        {/* Password Section (only for email auth) */}
        {user?.auth_provider === "email" && (
          <div className="card-glass p-6">
            <div className="flex items-center gap-3 mb-4">
              <Lock className="w-5 h-5 text-[#00E5FF]" />
              <h2 className="font-heading text-lg font-bold text-white">Change Password</h2>
            </div>
            
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div>
                <Label className="text-sm text-zinc-400">Current Password</Label>
                <Input
                  type="password"
                  value={passwordForm.current}
                  onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                  className="bg-black/50 border-white/10 mt-1"
                  required
                  data-testid="current-password-input"
                />
              </div>
              <div>
                <Label className="text-sm text-zinc-400">New Password</Label>
                <Input
                  type="password"
                  value={passwordForm.new}
                  onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                  className="bg-black/50 border-white/10 mt-1"
                  required
                  minLength={6}
                  data-testid="new-password-input"
                />
              </div>
              <div>
                <Label className="text-sm text-zinc-400">Confirm New Password</Label>
                <Input
                  type="password"
                  value={passwordForm.confirm}
                  onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                  className="bg-black/50 border-white/10 mt-1"
                  required
                  data-testid="confirm-password-input"
                />
              </div>
              <Button type="submit" disabled={changingPassword} className="bg-[#00E5FF] text-black hover:bg-[#00E5FF]/90">
                {changingPassword ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Lock className="w-4 h-4 mr-2" />}
                Change Password
              </Button>
            </form>
          </div>
        )}

        {/* Security Section */}
        <div className="card-glass p-6">
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-5 h-5 text-[#FCEE0A]" />
            <h2 className="font-heading text-lg font-bold text-white">Security</h2>
          </div>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm">Active Sessions</p>
                <p className="text-zinc-500 text-xs">Sign out from all other devices</p>
              </div>
              <Button onClick={handleRevokeOtherSessions} variant="outline" className="border-white/10" data-testid="revoke-sessions-btn">
                Revoke Other Sessions
              </Button>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="card-glass p-6 border-l-2 border-l-[#FF003C]">
          <div className="flex items-center gap-3 mb-4">
            <AlertTriangle className="w-5 h-5 text-[#FF003C]" />
            <h2 className="font-heading text-lg font-bold text-white">Danger Zone</h2>
          </div>
          
          {!showDeleteConfirm ? (
            <div className="flex items-center justify-between">
              <div>
                <p className="text-white text-sm">Delete Account</p>
                <p className="text-zinc-500 text-xs">Permanently delete your account and all data</p>
              </div>
              <Button onClick={() => setShowDeleteConfirm(true)} variant="outline" className="border-[#FF003C] text-[#FF003C] hover:bg-[#FF003C]/10" data-testid="delete-account-btn">
                Delete Account
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <p className="text-[#FF003C] text-sm">This action cannot be undone. All your games and scan history will be permanently deleted.</p>
              <div>
                <Label className="text-sm text-zinc-400">Type "DELETE" to confirm</Label>
                <Input
                  value={deleteConfirmText}
                  onChange={(e) => setDeleteConfirmText(e.target.value)}
                  className="bg-black/50 border-[#FF003C]/50 mt-1"
                  placeholder="DELETE"
                  data-testid="delete-confirm-input"
                />
              </div>
              <div className="flex gap-2">
                <Button onClick={handleDeleteAccount} className="bg-[#FF003C] text-white hover:bg-[#FF003C]/90" data-testid="confirm-delete-btn">
                  Permanently Delete Account
                </Button>
                <Button onClick={() => { setShowDeleteConfirm(false); setDeleteConfirmText(""); }} variant="outline" className="border-white/10">
                  Cancel
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ============== MAIN APP ==============
function AppRouter() {
  const location = useLocation();
  const { user, setUser, loading, checkAuth, logout } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#09090b] flex items-center justify-center">
        <Loader2 className="w-8 h-8 text-[#D3F34B] animate-spin" />
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/login" element={<LoginPage setUser={setUser} />} />
      <Route path="/" element={<LoginPage setUser={setUser} />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute user={user} checkAuth={checkAuth}>
            <Dashboard user={user} logout={logout} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/game/:id"
        element={
          <ProtectedRoute user={user} checkAuth={checkAuth}>
            <GameDetail user={user} />
          </ProtectedRoute>
        }
      />
      <Route
        path="/account"
        element={
          <ProtectedRoute user={user} checkAuth={checkAuth}>
            <AccountPage user={user} setUser={setUser} logout={logout} />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <Toaster 
        position="top-right" 
        toastOptions={{
          style: {
            background: '#121214',
            color: '#fff',
            border: '1px solid rgba(255,255,255,0.1)',
          },
        }}
      />
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
    </div>
  );
}

export default App;
