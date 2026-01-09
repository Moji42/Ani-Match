// components/AuthModal.tsx
import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { User, Mail, Lock, Loader2, Github, Chrome } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useOAuth } from "@/hooks/useOAuth";

interface AuthResponse {
  message: string;
  user_id: string;
  email: string;
  access_token: string;
}

export const AuthModal = () => {
  const [open, setOpen] = useState(false);
  const [libraryOpen, setLibraryOpen] = useState(false);
  const [favorites, setFavorites] = useState<any[]>([]);
  const [watchlist, setWatchlist] = useState<any[]>([]);
  const [likes, setLikes] = useState<any[]>([]);
  const [dislikes, setDislikes] = useState<any[]>([]);
  const [libraryLoading, setLibraryLoading] = useState(false);
  const [loginData, setLoginData] = useState({ email: "", password: "" });
  const [signupData, setSignupData] = useState({ email: "", password: "", confirmPassword: "" });
  const [loading, setLoading] = useState(false);
  const { startOAuthFlow, loading: oauthLoading } = useOAuth();
  const { toast } = useToast();

  const baseUrl = "http://127.0.0.1:5000";

  // Listen for OAuth success messages from the popup
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'OAUTH_SUCCESS') {
        const { access_token, user_id, email, provider } = event.data.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user_id', user_id);
        localStorage.setItem('user_email', email);
        localStorage.setItem('auth_provider', provider);

        toast({
          title: `Signed in with ${provider}!`,
          description: `Welcome, ${email}!`,
        });

        setOpen(false);
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [toast]);

  // Load library items when library dialog opens
  useEffect(() => {
    const loadLibrary = async () => {
      const token = localStorage.getItem('access_token');
      if (!token) return;
      setLibraryLoading(true);
      try {
        const base = 'http://127.0.0.1:5000';
        const [favRes, watchRes, likeRes, dislikeRes] = await Promise.all([
          fetch(`${base}/user/favorites`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${base}/user/watchlist`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${base}/user/preferences?action=like`, { headers: { Authorization: `Bearer ${token}` } }),
          fetch(`${base}/user/preferences?action=dislike`, { headers: { Authorization: `Bearer ${token}` } })
        ]);

        if (favRes.ok) setFavorites(await favRes.json());
        if (watchRes.ok) setWatchlist(await watchRes.json());
        if (likeRes.ok) setLikes(await likeRes.json());
        if (dislikeRes.ok) setDislikes(await dislikeRes.json());
      } catch (e) {
        console.error('Failed to load library', e);
      } finally {
        setLibraryLoading(false);
      }
    };

    if (libraryOpen) void loadLibrary();
  }, [libraryOpen]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch(`${baseUrl}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(loginData),
      });

      const data = await response.json();

      if (response.ok) {
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user_id', data.user_id);
        localStorage.setItem('user_email', data.email);

        toast({
          title: "Login successful!",
          description: `Welcome back, ${data.email}!`,
        });
        setOpen(false);
      } else {
        toast({
          title: "Login failed",
          description: data.error || "Invalid credentials",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Login error",
        description: "Could not connect to server",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();

    if (signupData.password !== signupData.confirmPassword) {
      toast({
        title: "Passwords don't match",
        description: "Please make sure your passwords match",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);

    try {
      const response = await fetch(`${baseUrl}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: signupData.email,
          password: signupData.password,
        }),
      });

      if (response.ok) {
        const data: AuthResponse = await response.json();
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('user_id', data.user_id);
        localStorage.setItem('user_email', data.email);

        toast({
          title: "Account created!",
          description: `Welcome, ${data.email}!`,
        });
        setOpen(false);
      } else {
        const errorData = await response.json();
        toast({
          title: "Signup failed",
          description: errorData.error || "Could not create account",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Signup error",
        description: "Could not connect to server",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    const provider = localStorage.getItem('auth_provider');
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_id');
    localStorage.removeItem('user_email');
    localStorage.removeItem('auth_provider');

    toast({
      title: "Logged out",
      description: `You have been logged out from ${provider || 'your account'}`,
    });
  };

  const isLoggedIn = () => {
    return !!localStorage.getItem('access_token');
  };

  const getUserEmail = () => {
    return localStorage.getItem('user_email');
  };

  const getAuthProvider = () => {
    return localStorage.getItem('auth_provider') || 'email';
  };

  if (isLoggedIn()) {
    return (
      <div className="flex items-center gap-4">
        <span className="text-sm text-muted-foreground">
          Welcome, {getUserEmail()}
        </span>
        <Dialog open={libraryOpen} onOpenChange={setLibraryOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="gap-2">
              My Library
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-lg">
            <DialogHeader>
              <DialogTitle>My Library</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {libraryLoading ? (
                <div>Loading...</div>
              ) : (
                <>
                  <div>
                    <h4 className="font-medium">Favorites</h4>
                    <div className="mt-2 flex flex-col gap-2">
                      {favorites.length ? favorites.map((f, i) => <div key={i}>{f.anime}</div>) : <div className="text-sm text-muted-foreground">No favorites</div>}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium">Watchlist</h4>
                    <div className="mt-2 flex flex-col gap-2">
                      {watchlist.length ? watchlist.map((w, i) => <div key={i}>{w.anime}</div>) : <div className="text-sm text-muted-foreground">No items</div>}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium">Likes</h4>
                    <div className="mt-2 flex flex-col gap-2">
                      {likes.length ? likes.map((l, i) => <div key={i}>{l.anime}</div>) : <div className="text-sm text-muted-foreground">No likes</div>}
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium">Dislikes</h4>
                    <div className="mt-2 flex flex-col gap-2">
                      {dislikes.length ? dislikes.map((d, i) => <div key={i}>{d.anime}</div>) : <div className="text-sm text-muted-foreground">No dislikes</div>}
                    </div>
                  </div>
                </>
              )}
            </div>
          </DialogContent>
        </Dialog>

        <Button
          variant="outline"
          onClick={handleLogout}
          className="gap-2"
        >
          <User className="w-4 h-4" />
          Logout ({getAuthProvider()})
        </Button>
      </div>
    );
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <User className="w-4 h-4" />
          Sign In
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-gradient-card border-border sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-foreground text-center">Welcome to Ani-Match</DialogTitle>
        </DialogHeader>

        {/* OAuth Buttons */}
        <div className="space-y-3">
          <Button
            type="button"
            variant="outline"
            className="w-full gap-2"
            onClick={() => startOAuthFlow('google')}
            disabled={!!loading || !!oauthLoading}
          >
            {oauthLoading === 'google' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Chrome className="w-4 h-4" />
            )}
            Continue with Google
          </Button>

          <Button
            type="button"
            variant="outline"
            className="w-full gap-2"
            onClick={() => startOAuthFlow('github')}
            disabled={!!loading || !!oauthLoading}
          >
            {oauthLoading === 'github' ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Github className="w-4 h-4" />
            )}
            Continue with GitHub
          </Button>
        </div>

        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <span className="w-full border-t" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-background px-2 text-muted-foreground">
              Or continue with email
            </span>
          </div>
        </div>

        <Tabs defaultValue="login" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-secondary">
            <TabsTrigger value="login">Login</TabsTrigger>
            <TabsTrigger value="signup">Sign Up</TabsTrigger>
          </TabsList>

          <TabsContent value="login" className="space-y-4">
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="login-email" className="text-foreground">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="login-email"
                    type="email"
                    placeholder="your@email.com"
                    className="pl-10 bg-input border-border text-foreground"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    required
                    disabled={loading || !!oauthLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="login-password" className="text-foreground">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="login-password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10 bg-input border-border text-foreground"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    required
                    disabled={loading || !!oauthLoading}
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full bg-gradient-primary hover:opacity-90"
                disabled={loading || !!oauthLoading}
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                Login
              </Button>
            </form>
          </TabsContent>

          <TabsContent value="signup" className="space-y-4">
            <form onSubmit={handleSignup} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="signup-email" className="text-foreground">Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="signup-email"
                    type="email"
                    placeholder="your@email.com"
                    className="pl-10 bg-input border-border text-foreground"
                    value={signupData.email}
                    onChange={(e) => setSignupData({ ...signupData, email: e.target.value })}
                    required
                    disabled={loading || !!oauthLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="signup-password" className="text-foreground">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="signup-password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10 bg-input border-border text-foreground"
                    value={signupData.password}
                    onChange={(e) => setSignupData({ ...signupData, password: e.target.value })}
                    required
                    disabled={loading || !!oauthLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirm-password" className="text-foreground">Confirm Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    id="confirm-password"
                    type="password"
                    placeholder="••••••••"
                    className="pl-10 bg-input border-border text-foreground"
                    value={signupData.confirmPassword}
                    onChange={(e) => setSignupData({ ...signupData, confirmPassword: e.target.value })}
                    required
                    disabled={loading || !!oauthLoading}
                  />
                </div>
              </div>

              <Button
                type="submit"
                className="w-full bg-gradient-primary hover:opacity-90"
                disabled={loading || !!oauthLoading}
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : null}
                Create Account
              </Button>
            </form>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
};