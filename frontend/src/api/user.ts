import { api } from "@/libs/api";
import { LoginUserData, RegisterUserData } from "@/types";

export async function registerUser(data: RegisterUserData) {
  const response = await api.post("/api/auth/register", data);
  return response.data;
}

export async function loginUser(data: LoginUserData) {
  const response = await api.post("/api/auth/login", data);
  return response.data;
}

export async function getUserJwt() {
  const response = await api.get("/api/user/jwt");
  return response.data;
}

export async function refreshToken() {
  const response = await api.post("/api/auth/refresh");
  return response.data
}

export async function logoutUser() {
  const response = await api.post("/api/auth/logout");
  return response.data;
}

export async function verifyEmail(data: { token: string }) {
  const response = await api.post("/api/auth/email-verification", data);
  return response.data;
}

export async function resendVerification(data: { email: string }) {
  const response = await api.post("/api/auth/resend-verification", data);
  return response.data;
}

export async function forgotPassword(data: { email: string }) {
  const response = await api.post("/api/auth/password-reset/request", data);
  return response.data;
}

export async function resetPassword(data: { token: string; new_password: string }) {
  const response = await api.post("/api/auth/password-reset/confirm", data);
  return response.data;
}
