import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { apiClient, type StudentProfile } from '../lib/api';

interface AuthState {
  studentId: string | null;
  profile: StudentProfile | null;
  isAdmin: boolean;
}

interface AuthContextValue extends AuthState {
  loginStudent: (studentId: string) => Promise<void>;
  logoutStudent: () => void;
  loginAdmin: (password: string) => Promise<void>;
  logoutAdmin: () => void;
  refreshProfile: () => Promise<void>;
}

const STORAGE_KEY = 'edubot.auth.v1';

const AuthContext = createContext<AuthContextValue | null>(null);

function loadInitial(): AuthState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return { studentId: null, profile: null, isAdmin: false };
    const parsed = JSON.parse(raw) as Partial<AuthState>;
    return {
      studentId: parsed.studentId ?? null,
      profile: parsed.profile ?? null,
      isAdmin: !!parsed.isAdmin,
    };
  } catch {
    return { studentId: null, profile: null, isAdmin: false };
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(loadInitial);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }, [state]);

  const refreshProfile = useCallback(async () => {
    if (!state.studentId) return;
    try {
      const profile = await apiClient.getStudent(state.studentId);
      setState((s) => ({ ...s, profile }));
    } catch {
      // profile may have been deleted server-side
      setState((s) => ({ ...s, profile: null }));
    }
  }, [state.studentId]);

  const loginStudent = useCallback(async (studentId: string) => {
    const profile = await apiClient.getStudent(studentId);
    setState((s) => ({ ...s, studentId, profile }));
  }, []);

  const logoutStudent = useCallback(() => {
    setState((s) => ({ ...s, studentId: null, profile: null }));
  }, []);

  const loginAdmin = useCallback(async (password: string) => {
    await apiClient.adminLogin(password);
    setState((s) => ({ ...s, isAdmin: true }));
  }, []);

  const logoutAdmin = useCallback(() => {
    setState((s) => ({ ...s, isAdmin: false }));
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      loginStudent,
      logoutStudent,
      loginAdmin,
      logoutAdmin,
      refreshProfile,
    }),
    [state, loginStudent, logoutStudent, loginAdmin, logoutAdmin, refreshProfile]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
