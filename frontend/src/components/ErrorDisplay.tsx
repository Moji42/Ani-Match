import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, RotateCcw } from "lucide-react";

export const ErrorDisplay = ({ error, onRetry }: { error: string; onRetry: () => void }) => (
  <div className="max-w-2xl mx-auto">
    <Alert variant="destructive" className="border-destructive/50 bg-destructive/10">
      <AlertCircle className="h-4 w-4" />
      <AlertDescription className="flex items-center justify-between">
        <span>{error}</span>
        <Button 
          variant="ghost" 
          size="sm" 
          onClick={onRetry}
          className="ml-2 h-auto p-1"
        >
          <RotateCcw className="h-3 w-3" />
        </Button>
      </AlertDescription>
    </Alert>
  </div>
);