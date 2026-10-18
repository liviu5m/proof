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
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { formatDate } from "@/libs/utils";
import {
  Upload,
  Search,
  Filter,
  MoreHorizontal,
  Eye,
  Download,
  AlertTriangle,
} from "lucide-react";
import { mockDatasets } from "@/libs/mock-data";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useQuery } from "@tanstack/react-query";
import { getUserJwt } from "@/api/user";

export default function DatasetsPage() {
  const [searchQuery, setSearchQuery] = React.useState("");
  const [showUpload, setShowUpload] = React.useState(false);
  const filteredDatasets = mockDatasets.filter(
    (d) =>
      d.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.hash.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  const { data: user } = useQuery({
    queryKey: ["userJwt"],
    queryFn: () => getUserJwt(),
  });

  console.log(user);
  

  return (
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

      <Alert className="border-amber-500/30 bg-amber-500/10 text-amber-200">
        <AlertTriangle className="h-4 w-4 text-amber-400" />
        <AlertTitle className="font-semibold">Backend Offline</AlertTitle>
        <AlertDescription className="text-amber-300/80">
          Backend API at{" "}
          <code className="bg-amber-500/20 px-1.5 py-0.5 rounded">
            http://localhost:8000/api
          </code>{" "}
          is offline. Showing demo data.
        </AlertDescription>
      </Alert>

      <Card className="bg-slate-900/80 border-slate-800/80 backdrop-blur-xl shadow-2xl shadow-black/40 rounded-2xl overflow-hidden">
        <CardHeader className="px-6 py-5 border-b border-slate-800/80">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle className="text-lg font-semibold text-white">
              Datasets ({filteredDatasets.length})
            </CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search datasets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-full sm:w-64 bg-slate-950/60 border-slate-800 text-white placeholder-slate-500 focus-visible:border-lime-500 focus-visible:ring-lime-500/20"
                />
              </div>
              <Button
                variant="outline"
                size="icon"
                className="bg-slate-800/50 border-slate-700/80 text-slate-300 hover:bg-slate-800 hover:text-white cursor-pointer"
              >
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader className="bg-slate-950/40">
                <TableRow className="border-slate-800 hover:bg-transparent">
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
                {filteredDatasets.map((dataset) => (
                  <TableRow
                    key={dataset.id}
                    className="border-slate-800/80 hover:bg-slate-800/40 transition-colors"
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
                          className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="View"
                        >
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="Download"
                        >
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-400 hover:text-white hover:bg-slate-800 cursor-pointer"
                          title="More"
                        >
                          <MoreHorizontal className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

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
              <div className="border-2 border-dashed border-slate-700 rounded-xl p-8 text-center hover:border-lime-500 transition-colors bg-slate-950/40">
                <Upload className="h-10 w-10 mx-auto text-slate-400 mb-3" />
                <p className="text-sm font-medium text-white">
                  Drop CSV file here
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  or click to browse from your device
                </p>
                <input
                  type="file"
                  accept=".csv"
                  className="hidden"
                  id="csv-upload"
                />
                <label htmlFor="csv-upload" className="mt-4 inline-block">
                  <Button
                    variant="outline"
                    className="bg-slate-800 border-slate-700 text-white hover:bg-slate-700 cursor-pointer"
                  >
                    Choose File
                  </Button>
                </label>
              </div>
              <div className="space-y-2">
                <Label htmlFor="dataset-name" className="text-slate-300">
                  Dataset Name
                </Label>
                <Input
                  id="dataset-name"
                  placeholder="My Evaluation Dataset"
                  className="bg-slate-950/60 border-slate-800 text-white placeholder-slate-500"
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
                  onClick={() => setShowUpload(false)}
                >
                  Upload Dataset
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
