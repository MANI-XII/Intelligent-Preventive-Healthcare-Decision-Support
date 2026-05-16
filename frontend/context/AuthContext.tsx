import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { clearStoredToken, getStoredToken, login as loginRequest, me, setStoredToken, signup as signupRequest } from "../services/auth";

type AuthContextValue = {
  userId: string | null;
  token: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (userId: string, password: string) => Promise<void>;
  signup: (userId: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [userId, setUserId] = useState<string | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const hydrate = async () => {
      const existingToken = getStoredToken();
      if (!existingToken) {
        setIsLoading(false);
        return;
      }

      try {
        const profile = await me(existingToken);
        setToken(existingToken);
        setUserId(profile.user_id);
      } catch {
        clearStoredToken();
        setToken(null);
        setUserId(null);
      } finally {
        setIsLoading(false);
      }
    };

    hydrate();
  }, []);

  const handleLogin = async (id: string, password: string) => {
    const res = await loginRequest(id, password);
    setStoredToken(res.access_token);
    setToken(res.access_token);
    setUserId(res.user_id);
  };

  const handleSignup = async (id: string, password: string) => {
    const res = await signupRequest(id, password);
    setStoredToken(res.access_token);
    setToken(res.access_token);
    setUserId(res.user_id);
  };

  const handleLogout = () => {
    if (userId) {
      try {
        window.localStorage.removeItem(`predictPageState-${userId}`);
        window.localStorage.removeItem(`simulatePageState-${userId}`);
        window.localStorage.removeItem(`userHealthInput-${userId}`);
        window.localStorage.removeItem(`latestPrediction-${userId}`);
      } catch {
        // ignore localStorage cleanup failures
      }
    }
    clearStoredToken();
    setToken(null);
    setUserId(null);
  };

  const value = useMemo<AuthContextValue>(
    () => ({
      userId,
      token,
      isLoading,
      isAuthenticated: Boolean(userId && token),
      login: handleLogin,
      signup: handleSignup,
      logout: handleLogout,
    }),
    [isLoading, token, userId]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
