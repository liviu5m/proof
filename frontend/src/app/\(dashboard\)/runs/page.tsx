"use client"

import * as React from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { formatDate } from "@/lib/utils"
import { Search, Filter, Eye, AlertTriangle, PlayCircle } from "lucide-react"
import { mockRuns } from "@/lib/mock-data"
import { Input } from "@/components/ui/input"
import Link from "next/link"

export default function RunsPage() {
  const [searchQuery, setSearchQuery] = React.useState("")

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Runs</h1>
          <p className="text-muted-foreground mt-1">
            View and manage your evaluation runs.
          </p>
        </div>
        <Link href="/dashboard/evaluate">
          <Button className="gap-2 bg-lime-500 hover:bg-lime-600 text-slate-900">
            <PlayCircle className="h-4 w-4" />
            New Run
          </Button>
        </Link>
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
            <CardTitle>Evaluation Runs ({mockRuns.length})</CardTitle>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search runs..."
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
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">ID</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">DATASET</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">MODEL</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">AVG SCORE</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">TOTAL</TableHead>
                  <TableHead className="text-xs font-medium text-muted-foreground uppercase tracking-wider">CREATED</TableHead>
                  <TableHead className="text-right text-xs font-medium text-muted-foreground uppercase tracking-wider">ACTIONS</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockRuns.map((run) => (
                  <TableRow key={run.id}>
                    <TableCell className="font-mono text-sm">#{run.id}</TableCell>
                    <TableCell>Dataset #{run.dataset_id}</TableCell>
                    <TableCell className="font-mono text-sm">{run.model}</TableCell>
                    <TableCell>
                      <Badge variant={run.avg_score && run.avg_score >= 4 ? "success" : run.avg_score && run.avg_score >= 3 ? "warning" : "destructive"}>
                        {run.avg_score ? run.avg_score.toFixed(1) : "—"}/5
                      </Badge>
                    </TableCell>
                    <TableCell className="font-mono text-sm">{run.total}</TableCell>
                    <TableCell className="text-sm text-muted-foreground">{formatDate(run.created_at)}</TableCell>
                    <TableCell className="text-right">
                      <Link href={`/dashboard/runs/${run.id}`}>
                        <Button variant="ghost" size="icon" className="h-8 w-8" title="View">
                          <Eye className="h-4 w-4" />
                        </Button>
                      </Link>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}