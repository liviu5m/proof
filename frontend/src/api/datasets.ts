import { api } from "@/libs/api";

export async function createDataset(formData: FormData) {
  const repsonse = await api.post("/api/dataset", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return repsonse.data;
}

export async function getDatasets(searchQuery: string) {
  const repsonse = await api.get("/api/dataset", {
    params: {
      searchQuery,
    },
  });
  return repsonse.data;
}

export async function downloadDataset(id: number) {
  const response = await api.get(`/api/dataset/${id}/download`);
  return response.data;
}

export async function deleteDataset(id: number) {
  const response = await api.delete(`/api/dataset/${id}`);
  return response.data;
}
