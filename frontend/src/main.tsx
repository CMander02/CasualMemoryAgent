import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import "./index.css"
import { Layout } from "@/components/Layout"
import { ChatPage } from "@/pages/ChatPage"
import { MemoryPage } from "@/pages/MemoryPage"
import { EventsPage } from "@/pages/EventsPage"
import { GraphPage } from "@/pages/GraphPage"

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<ChatPage />} />
          <Route path="memory" element={<MemoryPage />} />
          <Route path="events" element={<EventsPage />} />
          <Route path="graph" element={<GraphPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>
)
