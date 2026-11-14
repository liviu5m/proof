import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api",
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true,
});

let isRefreshing = false;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (!isRefreshing) {
        isRefreshing = true;
        try {
          await api.post("/api/auth/refresh");
        } catch {
        } finally {
          isRefreshing = false;
        }
      }

      await new Promise((r) => setTimeout(r, 300));
      originalRequest._retry = true;
      return api(originalRequest);
    }

    return Promise.reject(error);
  },
);
