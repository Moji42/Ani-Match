// Frontend/src/App.tsx
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import NotFound from "./pages/NotFound";
import { useToast } from "@/hooks/use-toast";
import { useEffect } from "react";

const queryClient = new QueryClient();

function AppContent() {
  const { toast } = useToast();

  // Global OAuth message listener
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'OAUTH_SUCCESS') {
        const { access_token, user_id, email, provider } = event.data.data;

        localStorage.setItem('access_token', access_token);
        localStorage.setItem('user_id', user_id);
        localStorage.setItem('user_email', email);
        localStorage.setItem('auth_provider', provider);

        toast({
          title: `Signed in with ${provider}!`,
          description: `Welcome, ${email}!`,
        });

        // Force a re-render to update auth state
        window.dispatchEvent(new Event('storage'));
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [toast]);

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Index />} />
        {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <AppContent />
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;