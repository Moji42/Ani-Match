// components/OAuthButtons.tsx
import { Button } from "@/components/ui/button";
import { Github, Chrome, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";

interface OAuthButtonsProps {
  variant?: "default" | "outline" | "ghost";
  size?: "default" | "sm" | "lg";
  className?: string;
}

export const OAuthButtons = ({ variant = "outline", size = "default", className = "" }: OAuthButtonsProps) => {
  const [oauthLoading, setOauthLoading] = useState<string | null>(null);
  const { toast } = useToast();
  const baseUrl = "http://127.0.0.1:5000";

  const handleOAuthLogin = (provider: 'google' | 'github') => {
    setOauthLoading(provider);
    
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
      setOauthLoading(null);
      return;
    }
    
    const checkPopup = setInterval(() => {
      if (popup.closed) {
        clearInterval(checkPopup);
        setOauthLoading(null);
      }
    }, 500);
  };

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      <Button
        type="button"
        variant={variant}
        size={size}
        className="w-full gap-2"
        onClick={() => handleOAuthLogin('google')}
        disabled={!!oauthLoading}
      >
        {oauthLoading === 'google' ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Chrome className="w-4 h-4" />
        )}
        Continue with Google
      </Button>
      
      <Button
        type="button"
        variant={variant}
        size={size}
        className="w-full gap-2"
        onClick={() => handleOAuthLogin('github')}
        disabled={!!oauthLoading}
      >
        {oauthLoading === 'github' ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Github className="w-4 h-4" />
        )}
        Continue with GitHub
      </Button>
    </div>
  );
};