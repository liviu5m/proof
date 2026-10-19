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
