import axios from "axios";
export const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000/api/v1" });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("admin_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export async function adminLogin(email: string, password: string, totp_code?: string) {
  const { data } = await api.post("/admin/auth/login", { email, password, totp_code });
  localStorage.setItem("admin_token", data.access_token);
}
export async function get<T>(path: string) { return (await api.get<T>(path)).data; }
export async function mutate<T>(method: "put" | "patch" | "post", path: string, body: unknown) {
  return (await api[method]<T>(path, body)).data;
}
