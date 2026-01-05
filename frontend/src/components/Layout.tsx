import { useState, useEffect } from "react"
import { NavLink, Outlet, useLocation } from "react-router-dom"
import {
  MessageSquare,
  Brain,
  CalendarCheck,
  Share2,
  PanelLeftClose,
  PanelLeft,
  Moon,
  Sun,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

const navItems = [
  { path: "/", icon: MessageSquare, label: "Chat" },
  { path: "/memory", icon: Brain, label: "Memory" },
  { path: "/events", icon: CalendarCheck, label: "Events" },
  { path: "/graph", icon: Share2, label: "Graph" },
]

export function Layout() {
  const [collapsed, setCollapsed] = useState(false)
  const [isDark, setIsDark] = useState(true)
  const location = useLocation()

  useEffect(() => {
    // Default to dark mode
    document.documentElement.classList.add("dark")
  }, [])

  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle("dark")
  }

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Sidebar */}
      <aside
        className={cn(
          "flex flex-col border-r border-sidebar-border bg-sidebar transition-sidebar",
          collapsed ? "w-16" : "w-56"
        )}
      >
        {/* Logo area */}
        <div className="flex h-14 items-center border-b border-sidebar-border px-4">
          <div className="flex items-center gap-2 overflow-hidden">
            <div className="relative flex h-8 w-8 shrink-0 items-center justify-center">
              <div className="absolute inset-0 rounded-lg bg-primary/10" />
              <Brain className="h-5 w-5 text-primary" />
            </div>
            <span
              className={cn(
                "font-mono text-sm font-semibold tracking-tight text-sidebar-foreground transition-opacity duration-200",
                collapsed ? "opacity-0" : "opacity-100"
              )}
            >
              Memory Agent
            </span>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => {
            const isActive = location.pathname === item.path
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={cn(
                  "group flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150",
                  "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground glow-accent"
                    : "text-sidebar-foreground/70"
                )}
              >
                <item.icon
                  className={cn(
                    "h-5 w-5 shrink-0 transition-colors",
                    isActive ? "text-primary" : "text-sidebar-foreground/50 group-hover:text-sidebar-foreground/70"
                  )}
                />
                <span
                  className={cn(
                    "truncate transition-opacity duration-200",
                    collapsed ? "opacity-0 w-0" : "opacity-100"
                  )}
                >
                  {item.label}
                </span>
                {isActive && (
                  <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary animate-pulse-node" />
                )}
              </NavLink>
            )
          })}
        </nav>

        {/* Sidebar footer */}
        <div className="border-t border-sidebar-border p-2">
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleTheme}
              className="h-9 w-9 shrink-0 text-sidebar-foreground/50 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            >
              {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setCollapsed(!collapsed)}
              className="h-9 w-9 shrink-0 text-sidebar-foreground/50 hover:text-sidebar-foreground hover:bg-sidebar-accent"
            >
              {collapsed ? (
                <PanelLeft className="h-4 w-4" />
              ) : (
                <PanelLeftClose className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto bg-background bg-grid-pattern scrollbar-thin">
        <Outlet />
      </main>
    </div>
  )
}
