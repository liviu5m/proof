"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/libs/utils";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { LogOut, User, Settings, Bell, Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";
import { getUserJwt, logoutUser } from "@/api/user";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { AxiosError } from "axios";

export function Header() {
  const pathname = usePathname();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);
  const router = useRouter();

  React.useEffect(() => {
    setMounted(true);
  }, []);

  const title = React.useMemo(() => {
    if (pathname.includes("/datasets")) return "Datasets";
    if (pathname.includes("/runs")) return "Runs";
    if (pathname.includes("/evaluate")) return "New Evaluation";
    if (pathname.includes("/compare")) return "Compare Runs";
    return "Dashboard";
  }, [pathname]);

  const { data: user, isLoading } = useQuery({
    queryKey: ["userJwt"],
    queryFn: () => getUserJwt(),
  });

  const { mutate: logout, isPending: isLoggingOut } = useMutation({
    mutationKey: ["logoutUser"],
    mutationFn: () => logoutUser(),
    onSuccess: () => {
      toast.success("Logged out successfully");
      router.push("/auth/login");
    },
    onError: (error: AxiosError) => {
      const errorMessage =
        (error?.response?.data as any)?.detail ||
        error?.message ||
        "Failed to logout";
      toast.error(errorMessage);
    },
  });

  const userInitials = user?.name
    ? user.name
        .split(" ")
        .map((n: string) => n[0])
        .join("")
        .toUpperCase()
        .slice(0, 2)
    : "U";

  return (
    <header className="sticky top-0 z-30 h-16 bg-slate-900/95 backdrop-blur supports-[backdrop-filter]:bg-slate-900/60 border-b border-slate-800">
      <div className="flex h-full items-center justify-between px-4 md:px-6">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold text-white truncate max-w-[300px]">
            {title}
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="relative h-9 w-9 rounded-full ring-offset-slate-900 focus-visible:ring-2 focus-visible:ring-lime-500 focus-visible:ring-offset-2 cursor-pointer"
              >
                <Avatar className="h-9 w-9 border border-slate-700">
                  <AvatarFallback className="bg-slate-800 text-lime-400 font-semibold text-xs">
                    {userInitials}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56 bg-slate-900 border-slate-800 text-slate-200" align="end" forceMount>
              <div className="flex items-center gap-2 px-3 py-2">
                <div className="flex flex-col space-y-0.5">
                  <p className="text-sm font-medium text-white truncate">
                    {user?.name || "User"}
                  </p>
                  <p className="text-xs text-slate-400 truncate">
                    {user?.email || "user@example.com"}
                  </p>
                </div>
              </div>
              <DropdownMenuSeparator className="bg-slate-800" />
              <DropdownMenuItem
                asChild
                className="hover:bg-slate-800 focus:bg-slate-800 cursor-pointer text-slate-200"
              >
                <Link
                  href="/dashboard/settings"
                  className="flex items-center gap-2 w-full"
                >
                  <User className="h-4 w-4 text-slate-400" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem
                asChild
                className="hover:bg-slate-800 focus:bg-slate-800 cursor-pointer text-slate-200"
              >
                <Link
                  href="/dashboard/settings"
                  className="flex items-center gap-2 w-full"
                >
                  <Settings className="h-4 w-4 text-slate-400" />
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator className="bg-slate-800" />
              <DropdownMenuItem
                className="text-red-400 hover:text-red-300 focus:text-red-300 hover:bg-slate-800 focus:bg-slate-800 cursor-pointer"
                onClick={() => logout()}
                disabled={isLoggingOut}
              >
                <LogOut className="h-4 w-4 mr-2" />
                {isLoggingOut ? "Signing out..." : "Sign out"}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
}
