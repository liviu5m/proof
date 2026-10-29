"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { formatDate } from "@/libs/utils";
import { Upload, Search, Filter, Eye, Download, Trash } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useMutation, useQuery } from "@tanstack/react-query";
import { getUserJwt } from "@/api/user";
import {
  createDataset,
  getDatasets,
  downloadDataset,
  deleteDataset,
} from "@/api/datasets";
import { useState } from "react";
import { Dataset } from "@/types";
import Loader from "@/components/Loader";
import { useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import Swal from "sweetalert2";

export default function DatasetsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [showUpload, setShowUpload] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState("");
  const [viewingDataset, setViewingDataset] = useState<Dataset | null>(null);
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { data: user } = useQuery({
    queryKey: ["userJwt"],
    queryFn: () => getUserJwt(),
  });

  const { mutate: uploadDataset, isPending: isUploading } = useMutation({
    mutationKey: ["uploadDataset"],
    mutationFn: (formData: FormData) => createDataset(formData),
    onSuccess: () => {
      toast.success("Dataset uploaded successfully!");
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
      setShowUpload(false);
      setSelectedFile(null);
      setDatasetName("");
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.error || "Failed to upload dataset");
    },
  });

  const { mutate: removeDataset } = useMutation({
    mutationFn: (id: number) => deleteDataset(id),
    onSuccess: () => {
      toast.success("Dataset deleted successfully");
      queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (error: any) => {
      toast.error(error?.response?.data?.error || "Failed to delete dataset");
    },
  });

  const handleDownload = async (id: number) => {
    try {
      const res = await downloadDataset(id);
      if (res.url) {
        window.open(res.url, "_blank");
      } else {
        toast.error("Could not retrieve download URL");
      }
    } catch (e: any) {
      toast.error(e?.response?.data?.error || "Download failed");
    }
  };

  const { data: datasets, isLoading } = useQuery({
    queryKey: ["datasets", searchQuery],
    queryFn: () => getDatasets(searchQuery),
  });

  return isLoading ? (
    <Loader />
  ) : (
    <div className="space-y-6 animate-in fade-in-50 duration-500">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white">
            Datasets
          </h1>
          <p className="text-slate-400 mt-1">
            Manage your evaluation datasets. Upload CSV files to create new
            datasets.
          </p>
        </div>
        <Button
          onClick={() => setShowUpload(true)}
          className="gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold shadow-lg shadow-lime-500/20 cursor-pointer transition-all"
        >
          <Upload className="h-4 w-4" /> Upload CSV
        </Button>
      </div>
      <Card className="bg-slate-900/80 border-slate-800/30 backdrop-blur-xl shadow-2xl shadow-black/40 rounded-2xl overflow-hidden">
        <CardHeader className="px-6 py-5 border-b border-slate-800/30">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="text-lg font-semibold text-white">
              Datasets ({datasets.length})
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search datasets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-full sm:w-64 bg-slate-950/60 border-slate-800/50 text-white placeholder-slate-500 focus-visible:border-lime-500 focus-visible:ring-lime-500/20"
                />
              </div>
              <Button
                variant="outline"
                size="icon"
                className="bg-slate-800/50 border-slate-800/60 text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer"
              >
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {(!datasets || datasets.length === 0) ? (
            <div className="flex flex-col items-center justify-center py-16 px-4 text-center">
              <div className="bg-slate-800/50 p-4 rounded-full mb-4 text-slate-400">
                <Upload className="h-8 w-8" />
              </div>
              <h3 className="text-lg font-semibold text-white">No datasets found</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-sm">
                {searchQuery ? "No datasets match your search query." : "Get started by uploading your first evaluation CSV dataset."}
              </p>
              <Button
                onClick={() => setShowUpload(true)}
                className="mt-6 gap-2 bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold cursor-pointer"
              >
                <Upload className="h-4 w-4" /> Upload Dataset
              </Button>
            </div>
          ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-slate-950/40">
                <TableRow className="border-slate-800/30 hover:bg-transparent">
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider pl-6">
                    ID
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Name
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Items
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Hash (8)
                  </TableHead>
                  <TableHead className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    Created
                  </TableHead>
                  <TableHead className="text-right text-xs font-semibold text-slate-400 uppercase tracking-wider pr-6">
                    Actions
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {datasets.map((dataset: Dataset) => (
                  <TableRow
                    key={dataset.id}
                    className="border-slate-800/20 hover:bg-slate-800/40 transition-colors"
                  >
                    <TableCell className="font-mono text-sm text-slate-300 pl-6">
                      {dataset.id}
                    </TableCell>
                    <TableCell className="font-medium text-white truncate max-w-[220px]">
                      {dataset.name}
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant="secondary"
                        className="bg-slate-800 text-slate-300 border-slate-700"
                      >
                        {dataset.item_count} items
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm text-slate-400">
                      {dataset.hash.slice(0, 8)}
                    </TableCell>
                    <TableCell className="text-sm text-slate-400">
                      {formatDate(dataset.createdAt)}
                    </TableCell>
                    <TableCell className="text-right pr-6">
                      <div className="flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => setViewingDataset(dataset)}
                          className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDownload(dataset.id)}
                          className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={async () => {
                            const result = await Swal.fire({
                              title: "Are you sure?",
                              text: `Delete dataset "${dataset.name}"? This cannot be undone.`,
                              icon: "warning",
                              showCancelButton: true,
                              confirmButtonColor: "#ef4444",
                              cancelButtonColor: "#334155",
                              confirmButtonText: "Yes, delete it!",
                              background: "#0f172a",
                              color: "#f8fafc",
                            });
                            if (result.isConfirmed) {
                              removeDataset(dataset.id);
                            }
                          }}
                          className="h-8 w-8 text-slate-400 hover:text-red-400 hover:bg-slate-800 cursor-pointer"
                          title="Delete"
                        >
                          <Trash className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          )}
        </CardContent>
      </Card>

      {viewingDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in-0 duration-200">
          <Card className="w-full max-w-lg mx-4 bg-slate-900 border-slate-800 shadow-2xl">
            <CardHeader>
              <CardTitle className="text-xl font-semibold text-white">
                Dataset Details: {viewingDataset.name}
              </CardTitle>
              <CardDescription className="text-slate-400">
                ID: {viewingDataset.id} • Created:{" "}
                {formatDate(viewingDataset.createdAt)}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 text-sm text-slate-300">
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Total Items:</span>
                  <span className="font-semibold text-white">
                    {viewingDataset.item_count}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">File Hash (SHA256):</span>
                  <span className="font-mono text-xs text-lime-400">
                    {viewingDataset.hash}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-800">
                  <span className="text-slate-400">Storage Path:</span>
                  <span className="font-mono text-xs text-slate-300 truncate max-w-[260px]">
                    {viewingDataset.source_path}
                  </span>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <Button
                  onClick={() => handleDownload(viewingDataset.id)}
                  className="bg-indigo-600 hover:bg-indigo-500 text-white gap-2 cursor-pointer"
                >
                  <Download className="h-4 w-4" /> Download CSV
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setViewingDataset(null)}
                  className="bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700 hover:text-white cursor-pointer"
                >
                  Close
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm animate-in fade-in-0 duration-200">
          <Card className="w-full max-w-md mx-4 bg-slate-900 border-slate-800 shadow-2xl">
            <CardHeader className="space-y-1">
              <CardTitle className="text-xl font-semibold text-white">
                Upload CSV Dataset
              </CardTitle>
              <CardDescription className="text-slate-400">
                Drag and drop or click to select a CSV file
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  if (!selectedFile) return;
                  const formData = new FormData();
                  formData.append("file", selectedFile);
                  formData.append("name", datasetName);
                  uploadDataset(formData);
                }}
              >
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-lime-500 transition-colors bg-slate-950/40 cursor-pointer"
                >
                  <Upload className="h-10 w-10 mx-auto text-slate-400 mb-3" />
                  <p className="text-sm font-medium text-white">
                    {selectedFile ? selectedFile.name : "Drop CSV file here"}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    or click to browse from your device
                  </p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    className="hidden"
                    onChange={(e) => {
                      if (e.target.files?.[0]) {
                        setSelectedFile(e.target.files[0]);
                        if (!datasetName)
                          setDatasetName(
                            e.target.files[0].name.replace(/\.[^/.]+$/, ""),
                          );
                      }
                    }}
                  />
                  <Button
                    type="button"
                    variant="outline"
                    className="mt-4 bg-slate-800 border-slate-700 text-white hover:bg-slate-700 cursor-pointer"
                  >
                    Choose File
                  </Button>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="dataset-name" className="text-slate-300">
                    Dataset Name
                  </Label>
                  <Input
                    id="dataset-name"
                    placeholder="My Evaluation Dataset"
                    className="bg-slate-950/60 border-slate-800 text-white placeholder-slate-500"
                    value={datasetName}
                    onChange={(e) => setDatasetName(e.target.value)}
                  />
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => setShowUpload(false)}
                    className="bg-transparent border-slate-700 text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer"
                  >
                    Cancel
                  </Button>
                  <Button
                    className="bg-lime-500 hover:bg-lime-400 text-slate-950 font-semibold cursor-pointer"
                    type="submit"
                  >
                    Upload Dataset
                  </Button>
                </div>
              </form>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
