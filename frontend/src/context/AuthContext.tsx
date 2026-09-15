import React, { createContext, useContext, useState, useEffect } from 'react';
import { jwtDecode } from 'jwt-decode';

interface User {
  username: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string, role: string, username: string) => void;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function getUserFromToken(t: string | null): User | null {
  if (!t) return null;
  try {
    const decoded = jwtDecode(t) as any;
    if (decoded && decoded.exp && decoded.exp * 1000 > Date.now()) {
      return { username: decoded.sub, role: decoded.role };
    }
  } catch {
    // invalid token
  }
  return null;
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<User | null>(() => getUserFromToken(token));

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const login = (newToken: string, role: string, username: string) => {
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser({ username, role });
  };

  useEffect(() => {
    const validUser = getUserFromToken(token);
    if (token && !validUser) {
      logout();
    }
  }, [token]);

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
