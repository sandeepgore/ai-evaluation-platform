import { useState, type FormEvent } from "react";
import { Alert, Box, Button, Container, Paper, Stack, TextField, Typography } from "@mui/material";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { apiClient } from "../../services/api/client";
import { useAuthStore, type AuthUser } from "../../store/authStore";

interface SessionResponse { access_token: string; user: AuthUser }

export function LoginPage() {
  const [registering, setRegistering] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const token = useAuthStore((state) => state.token);
  const setSession = useAuthStore((state) => state.setSession);
  const navigate = useNavigate();
  const location = useLocation();
  if (token) return <Navigate to="/" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      const response = await apiClient.post<SessionResponse>(`/api/v1/auth/${registering ? "register" : "login"}`, { email, password, ...(registering ? { full_name: fullName } : {}) });
      setSession(response.data.access_token, response.data.user);
      navigate((location.state as { from?: string } | null)?.from ?? "/", { replace: true });
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Unable to sign in"); }
    finally { setBusy(false); }
  }

  return <Container maxWidth="sm" sx={{ py: 10 }}><Paper elevation={3} sx={{ p: 4 }}>
    <Stack component="form" spacing={2.5} onSubmit={submit}>
      <Box><Typography variant="h4" fontWeight={700}>{registering ? "Create account" : "Sign in"}</Typography><Typography color="text.secondary">AI Evaluation Platform</Typography></Box>
      {error && <Alert severity="error">{error}</Alert>}
      {registering && <TextField label="Full name" value={fullName} onChange={(e) => setFullName(e.target.value)} inputProps={{ maxLength: 150 }} />}
      <TextField label="Email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      <TextField label="Password" type="password" required value={password} onChange={(e) => setPassword(e.target.value)} inputProps={{ minLength: 8, maxLength: 128 }} helperText={registering ? "Use at least 8 characters." : undefined} />
      <Button type="submit" variant="contained" size="large" disabled={busy}>{busy ? "Please wait…" : registering ? "Create account" : "Sign in"}</Button>
      <Button onClick={() => { setRegistering(!registering); setError(""); }} disabled={busy}>{registering ? "Already have an account? Sign in" : "New here? Create an account"}</Button>
    </Stack>
  </Paper></Container>;
}
