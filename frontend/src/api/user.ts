import { api } from "@/libs/api";
import { LoginUserData, RegisterUserData } from "@/types";

export async function registerUser(data: RegisterUserData) {
  const response = await api.post("/auth/register", data);
  return response.data;
}

export async function loginUser(data: LoginUserData) {
  const response = await api.post("/auth/login", data);
  return response.data;
}

export async function getUserJwt() {
  const response = await api.get("/user/jwt");
  return response.data;
}
