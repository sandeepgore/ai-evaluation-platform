import { useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert, Avatar, Box, Button, Chip, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, Divider, FormControl, InputLabel, MenuItem, Paper,
  Select, Stack, TextField, Typography,
} from "@mui/material";
import PersonAddAlt1Outlined from "@mui/icons-material/PersonAddAlt1Outlined";
import AdminPanelSettingsOutlined from "@mui/icons-material/AdminPanelSettingsOutlined";
import CodeOutlined from "@mui/icons-material/CodeOutlined";
import VisibilityOutlined from "@mui/icons-material/VisibilityOutlined";
import SearchOutlined from "@mui/icons-material/SearchOutlined";
import { apiClient } from "../../services/api/client";
import { useAuthStore, type AppRole, type AuthUser } from "../../store/authStore";

const roleInfo: Record<AppRole, { label: string; description: string; access: string; icon: ReactNode }> = {
  admin: {
    label: "Administrator",
    description: "Full platform access, including user and organization management.",
    access: "Manage users and roles · Manage organizations · Create and update platform data",
    icon: <AdminPanelSettingsOutlined />,
  },
  dev: {
    label: "Developer",
    description: "Build and maintain platform data and evaluation workflows.",
    access: "Create and update projects, datasets, models, evaluations, and experiments",
    icon: <CodeOutlined />,
  },
  user: {
    label: "User",
    description: "View platform data and results without making changes.",
    access: "Read-only access across the platform",
    icon: <VisibilityOutlined />,
  },
};

const roleOrder: AppRole[] = ["admin", "dev", "user"];

function displayName(user: AuthUser) {
  return user.full_name?.trim() || user.email;
}

function initials(user: AuthUser) {
  const name = displayName(user);
  return name.split(/[\s@._-]+/).filter(Boolean).slice(0, 2).map((part) => part[0]?.toUpperCase()).join("") || "U";
}

function getErrorMessage(error: unknown, fallback: string) {
  const detail = (error as { response?: { data?: { detail?: unknown } } } | null)?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  return error instanceof Error ? error.message : fallback;
}

export function UserAccessPage() {
  const currentUser = useAuthStore((state) => state.user);
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [createOpen, setCreateOpen] = useState(false);
  const [newUser, setNewUser] = useState({ full_name: "", email: "", password: "", role: "user" as AppRole });
  const users = useQuery({
    queryKey: ["admin-users"],
    queryFn: async () => (await apiClient.get<AuthUser[]>("/api/v1/auth/users")).data,
  });
  const changeRole = useMutation({
    mutationFn: async ({ id, role }: { id: string; role: AppRole }) =>
      (await apiClient.patch<AuthUser>(`/api/v1/auth/users/${id}/role`, { role })).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-users"] }),
  });
  const createUser = useMutation({
    mutationFn: async (payload: typeof newUser) =>
      (await apiClient.post<AuthUser>("/api/v1/auth/users", payload)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin-users"] });
      setCreateOpen(false);
      setNewUser({ full_name: "", email: "", password: "", role: "user" });
    },
  });

  const filteredUsers = useMemo(() => {
    const needle = search.trim().toLowerCase();
    return (users.data ?? []).filter((user) =>
      !needle || `${user.full_name ?? ""} ${user.email} ${user.role}`.toLowerCase().includes(needle),
    );
  }, [users.data, search]);

  const counts = useMemo(() => roleOrder.reduce((result, role) => {
    result[role] = (users.data ?? []).filter((user) => user.role === role).length;
    return result;
  }, { admin: 0, dev: 0, user: 0 } as Record<AppRole, number>), [users.data]);

  return (
    <Box sx={{ p: { xs: 2, md: 3 }, maxWidth: 1120, mx: "auto", width: "100%" }}>
      <Stack spacing={3}>
        <Box>
          <Typography variant="h4" fontWeight={700}>Users & roles</Typography>
          <Typography color="text.secondary" sx={{ mt: 0.5 }}>
            See who has access and assign the right level of platform responsibility.
          </Typography>
        </Box>

        <Box sx={{ display: "grid", gridTemplateColumns: { xs: "1fr", md: "repeat(3, minmax(0, 1fr))" }, gap: 2 }}>
          {roleOrder.map((role) => {
            const info = roleInfo[role];
            return (
              <Paper key={role} variant="outlined" sx={{ p: 2.25, height: "100%" }}>
                <Stack spacing={1.5}>
                  <Stack direction="row" spacing={1.25} alignItems="center">
                    <Avatar sx={{ width: 36, height: 36, bgcolor: "action.selected", color: "text.primary" }}>{info.icon}</Avatar>
                    <Box sx={{ flex: 1 }}>
                      <Typography fontWeight={700}>{info.label}</Typography>
                      <Typography variant="caption" color="text.secondary">{counts[role]} {counts[role] === 1 ? "account" : "accounts"}</Typography>
                    </Box>
                  </Stack>
                  <Typography variant="body2" color="text.secondary">{info.description}</Typography>
                  <Divider />
                  <Typography variant="caption" color="text.secondary" sx={{ lineHeight: 1.6 }}>{info.access}</Typography>
                </Stack>
              </Paper>
            );
          })}
        </Box>

        <Paper variant="outlined" sx={{ overflow: "hidden" }}>
          <Stack spacing={2} sx={{ p: { xs: 2, md: 2.5 } }}>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={1.5} justifyContent="space-between" alignItems={{ sm: "center" }}>
              <Box>
                <Typography variant="h6" fontWeight={700}>Platform accounts</Typography>
                <Typography variant="body2" color="text.secondary">Role changes take effect on the account’s next request.</Typography>
              </Box>
              <Stack direction={{ xs: "column-reverse", sm: "row" }} spacing={1}>
                <TextField
                  size="small"
                  placeholder="Search name, email, or role"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  inputProps={{ "aria-label": "Search platform accounts" }}
                  InputProps={{ startAdornment: <SearchOutlined fontSize="small" sx={{ mr: 1, color: "text.secondary" }} /> }}
                  sx={{ width: { xs: "100%", sm: 260 } }}
                />
                <Button
                  variant="contained"
                  startIcon={<PersonAddAlt1Outlined />}
                  onClick={() => { createUser.reset(); setCreateOpen(true); }}
                  sx={{ whiteSpace: "nowrap" }}
                >
                  Add user
                </Button>
              </Stack>
            </Stack>

            {users.isError && <Alert severity="error">{users.error instanceof Error ? users.error.message : "Could not load accounts."}</Alert>}
            {changeRole.isError && <Alert severity="error">{changeRole.error instanceof Error ? changeRole.error.message : "Could not update this role."}</Alert>}
            {changeRole.isSuccess && <Alert severity="success" onClose={() => changeRole.reset()}>Role updated successfully.</Alert>}
            {createUser.isError && !createOpen && <Alert severity="error">{getErrorMessage(createUser.error, "Could not create the account.")}</Alert>}
            {createUser.isSuccess && !createOpen && <Alert severity="success" onClose={() => createUser.reset()}>Account created. The user can now sign in with the provided email and password.</Alert>}
            {users.isLoading ? (
              <Box sx={{ minHeight: 180, display: "grid", placeItems: "center" }}><CircularProgress size={28} /></Box>
            ) : filteredUsers.length === 0 ? (
              <Box sx={{ py: 5, textAlign: "center" }}>
                <Typography fontWeight={600}>{search ? "No matching accounts" : "No accounts found"}</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>{search ? "Try a different name, email, or role." : "Registered accounts will appear here."}</Typography>
              </Box>
            ) : (
              <Stack divider={<Divider flexItem />}>
                {filteredUsers.map((user) => {
                  const isSelf = currentUser?.id === user.id;
                  const role = roleInfo[user.role];
                  return (
                    <Stack key={user.id} direction={{ xs: "column", sm: "row" }} spacing={2} alignItems={{ sm: "center" }} sx={{ py: 1.75 }}>
                      <Stack direction="row" spacing={1.5} alignItems="center" sx={{ flex: 1, minWidth: 0 }}>
                        <Avatar sx={{ width: 38, height: 38, bgcolor: "action.selected", color: "text.primary", fontSize: 14, fontWeight: 700 }}>{initials(user)}</Avatar>
                        <Box sx={{ minWidth: 0 }}>
                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <Typography fontWeight={600} noWrap>{displayName(user)}</Typography>
                            {isSelf && <Chip size="small" label="You" variant="outlined" />}
                          </Stack>
                          <Typography variant="body2" color="text.secondary" noWrap>{user.email}</Typography>
                        </Box>
                      </Stack>
                      <Chip
                        size="small"
                        label={user.is_active === false ? "Inactive" : "Active"}
                        color={user.is_active === false ? "default" : "success"}
                        variant="outlined"
                        sx={{ alignSelf: { xs: "flex-start", sm: "center" } }}
                      />
                      <FormControl size="small" sx={{ minWidth: { xs: "100%", sm: 190 } }}>
                        <InputLabel id={`role-label-${user.id}`}>Role</InputLabel>
                        <Select
                          labelId={`role-label-${user.id}`}
                          value={user.role}
                          label="Role"
                          disabled={changeRole.isPending || isSelf}
                          onChange={(event) => {
                            changeRole.reset();
                            changeRole.mutate({ id: user.id, role: event.target.value as AppRole });
                          }}
                        >
                          {roleOrder.map((option) => <MenuItem key={option} value={option}>{roleInfo[option].label}</MenuItem>)}
                        </Select>
                      </FormControl>
                      <Typography variant="caption" color="text.secondary" sx={{ width: { sm: 190 }, flexShrink: 0 }}>
                        {role.access.split(" · ")[0]}{isSelf ? " · Your role is protected" : ""}
                      </Typography>
                    </Stack>
                  );
                })}
              </Stack>
            )}
          </Stack>
        </Paper>
      </Stack>

      <Dialog
        open={createOpen}
        onClose={() => { if (!createUser.isPending) setCreateOpen(false); }}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle sx={{ pb: 0.5 }}>Add platform user</DialogTitle>
        <DialogContent>
          <Stack
            component="form"
            id="create-platform-user-form"
            spacing={2}
            sx={{ pt: 1.5 }}
            onSubmit={(event) => {
              event.preventDefault();
              createUser.mutate(newUser);
            }}
          >
            <Typography variant="body2" color="text.secondary">
              Create an account and choose the access level. Share the initial password securely so the user can sign in.
            </Typography>
            {createUser.isError && (
              <Alert severity="error">{getErrorMessage(createUser.error, "Could not create the account.")}</Alert>
            )}
            <TextField
              label="Full name"
              required
              autoComplete="name"
              value={newUser.full_name}
              onChange={(event) => setNewUser({ ...newUser, full_name: event.target.value })}
            />
            <TextField
              label="Email address"
              type="email"
              required
              autoComplete="email"
              value={newUser.email}
              onChange={(event) => setNewUser({ ...newUser, email: event.target.value })}
            />
            <TextField
              label="Initial password"
              type="password"
              required
              autoComplete="new-password"
              value={newUser.password}
              onChange={(event) => setNewUser({ ...newUser, password: event.target.value })}
              inputProps={{ minLength: 8, maxLength: 128 }}
              helperText="Use 8–128 characters."
            />
            <FormControl fullWidth>
              <InputLabel id="new-user-role-label">Role</InputLabel>
              <Select
                labelId="new-user-role-label"
                label="Role"
                value={newUser.role}
                onChange={(event) => setNewUser({ ...newUser, role: event.target.value as AppRole })}
              >
                {roleOrder.map((role) => <MenuItem key={role} value={role}>{roleInfo[role].label}</MenuItem>)}
              </Select>
            </FormControl>
            <Typography variant="caption" color="text.secondary">{roleInfo[newUser.role].description}</Typography>
          </Stack>
        </DialogContent>
        <DialogActions sx={{ px: 3, pb: 2.5 }}>
          <Button onClick={() => setCreateOpen(false)} disabled={createUser.isPending}>Cancel</Button>
          <Button
            variant="contained"
            type="submit"
            form="create-platform-user-form"
            disabled={createUser.isPending || !newUser.full_name.trim() || !newUser.email.trim() || newUser.password.length < 8}
          >
            {createUser.isPending ? "Creating…" : "Create account"}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
