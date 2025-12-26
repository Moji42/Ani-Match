// hooks/useOAuth.ts
import { useState } from 'react';
import { useToast } from '@/hooks/use-toast';

export const useOAuth = () => {
  const [loading, setLoading] = useState<string | null>(null);
  const { toast } = useToast();
  const baseUrl = "http://127.0.0.1:5000";

  const startOAuthFlow = (provider: 'google' | 'github') => {
    setLoading(provider);
    
    const width = 600;
    const height = 700;
    const left = (window.innerWidth - width) / 2;
    const top = (window.innerHeight - height) / 2;
    
    const popup = window.open(
      `${baseUrl}/auth/${provider}?redirect_to=${encodeURIComponent(window.location.href)}`,
      `${provider}OAuth`,
      `width=${width},height=${height},top=${top},left=${left}`
    );
    
    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
      toast({
        title: "Popup blocked",
        description: "Please allow popups for this site to continue with OAuth login",
        variant: "destructive",
      });
      setLoading(null);
      return;
    }

    // Check for popup closure
    const checkPopup = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkPopup);
        setLoading(null);
      }
    }, 500);

    return popup;
  };

  return { startOAuthFlow, loading };
};