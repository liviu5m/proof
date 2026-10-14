"use client"

import * as React from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import { formatDate, truncate } from "@/lib/utils"
import {
  Upload,
  Search,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  Download,
  AlertTriangle,
  WifiOff,
} from "lucide-react"
import { mockDatasets } from "@/lib/mock-data"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const columns = [
  { key: "id", header: "ID" },
  { key: "name", header: "NAME" },
  { key: "item_count", header: "ITEMS" },
  { key: "hash", header: "HASH (8)" },
  { key: "createdAt", header: "CREATED" },
]

export default function DatasetsPage() {
  const [searchQuery, setSearchQuery] = React.useState("")
  const [showUpload, setShowUpload] = React.useState(false)

  const filteredDatasets = mockDatasets.filter(
    (dataset) =>
      dataset.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      dataset.hash.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Datasets</h1>
          <p className="text-muted-foreground mt-1">
            Manage your evaluation datasets. Upload CSV files to create new datasets.
          </p>
        </div>
        <Button
          onClick={() => setShowUpload(true)}
          className="gap-2 bg-lime-500 hover:bg-lime-600 text-slate-900"
        >
          <Upload className="h-4 w-4" />
          Upload CSV
        </Button>
      </div>

      <Alert className="border-amber-500/50 bg-amber-500/10 text-amber-900 dark:text-amber-100">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Backend Offline</AlertTitle>
        <AlertDescription>
          Backend API at <code>http://localhost:8000/api</code> is offline. Showing demo data.
        </AlertDescription>
      </Alert>

      <Card>
        <CardHeader>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <CardTitle>Datasets ({filteredDatasets.length})</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search datasets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
                />
              </div>
              <Button variant="outline" size="icon">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="rounded-md border">
            <Table>
              <TableHeader>
                <TableRow>
                  {columns.map((col) => (
                    <TableHead key={col.key} className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                      {col.header}
                    </TableHead>
                  ))}
                  <TableHead className="text-right">ACTIONS</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredDatasets.map((dataset) => (
                  <TableRow key={dataset.id}>
                    <TableCell className="font-mono text-sm">{dataset.id}</TableCell>
                    <TableCell className="font-medium truncate max-w-[200px]">{dataset.name}</TableCell>
                    <TableCell>
                      <Badge variant="secondary">{dataset.item_count} items</Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm text-muted-foreground">
                      {dataset.hash.slice(0, 8)}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {formatDate(dataset.createdAt)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-1">
                        <Button variant="ghost" size="icon" className="h-8 w-8" title="View">
                          <Eye className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" title="Download">
                          <Download className="h-4 w-4" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-8 w-8" title="More">
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