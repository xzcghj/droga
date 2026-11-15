import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ToastProvider } from "./components/ui/Toast";
import { ListPage } from "./pages/ListPage";
import { MeetupPage } from "./pages/MeetupPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<ListPage />} />
            <Route path="/meetups/:id" element={<MeetupPage />} />
            <Route path="*" element={<ListPage />} />
          </Routes>
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
}
