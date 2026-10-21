import { api } from "@/libs/api";

export async function createDataset(formData: FormData) {
  const repsonse = await api.post("/api/dataset", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return repsonse.data;
}
