import { useState } from "react";
import { SearchForm, SearchParams } from "@/components/SearchForm";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { useAnimeRecommendations } from "@/hooks/useAnimeRecommendations";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { AlertCircle, RotateCcw } from "lucide-react";
import heroBanner from "@/assets/hero-banner.jpg";

const Index = () => {
  const { results, error, isLoading, searchRecommendations, clearResults } = useAnimeRecommendations();
  const [searchType, setSearchType] = useState<'content' | 'collaborative' | 'hybrid' | 'random'>('content');

  const handleSearch = async (params: SearchParams) => {
    setSearchType(params.type);
    await searchRecommendations(params);
  };

  const handleClearResults = () => {
    clearResults();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20"
          style={{ backgroundImage: `url(${heroBanner})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-background/50 to-background" />
        
        <div className="relative container mx-auto px-4 py-12 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 gradient-text">
            Anime Recommendations
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto mb-8">
            Discover your next favorite anime with our advanced recommendation system. 
            Choose from content-based, collaborative, or hybrid filtering to find the perfect match.
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Search Form */}
        <div className="max-w-2xl mx-auto">
          <SearchForm onSearch={handleSearch} isLoading={isLoading} />
        </div>

        {/* Error Display */}
        {error && (
          <div className="max-w-2xl mx-auto">
            <Alert variant="destructive" className="border-destructive/50 bg-destructive/10">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription className="flex items-center justify-between">
                <span>{error}</span>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  onClick={handleClearResults}
                  className="ml-2 h-auto p-1"
                >
                  <RotateCcw className="h-3 w-3" />
                </Button>
              </AlertDescription>
            </Alert>
          </div>
        )}

        {/* Results Display */}
        {results && !error && (
          <div className="space-y-6">
            <div className="flex justify-center">
              <Button 
                variant="outline" 
                onClick={handleClearResults}
                className="border-border/50 hover:border-primary/50"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                New Search
              </Button>
            </div>
            <ResultsDisplay results={results} searchType={searchType} />
          </div>
        )}

        {/* Footer */}
        <footer className="text-center py-8 text-muted-foreground">
          <p>Powered by advanced machine learning algorithms for anime discovery</p>
        </footer>
      </div>
    </div>
  );
};

export default Index;