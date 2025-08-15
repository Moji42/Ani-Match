import { useState } from "react";
import { SearchForm } from "@/components/SearchForm";
import { ResultsDisplay } from "@/components/ResultsDisplay";
import { useAnimeRecommendations } from "@/hooks/useAnimeRecommendations";
import { Button } from "@/components/ui/button";
import { RotateCcw } from "lucide-react";
import heroBanner from "@/assets/hero-banner.jpg";
import { ErrorDisplay } from "../components/ErrorDisplay"; 

const Index = () => {
  const { results, error, isLoading, searchRecommendations, clearResults } = useAnimeRecommendations();
  const [searchType, setSearchType] = useState<'content' | 'collaborative' | 'hybrid' | 'random'>('content');

  const handleSearch = async (params: any) => {
    setSearchType(params.type);
    try {
      await searchRecommendations(params);
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat opacity-20"
          style={{ backgroundImage: `url(${heroBanner})` }}
        />
        <div className="relative container mx-auto px-4 py-12 text-center">
          <h1 className="text-5xl md:text-6xl font-bold mb-6 gradient-text">
            Anime Recommendations
          </h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-8 space-y-8">
        <div className="max-w-2xl mx-auto">
          <SearchForm 
            onSearch={handleSearch} 
            isLoading={isLoading} 
          />
        </div>

        {error && <ErrorDisplay error={error} onRetry={clearResults} />}

        {results && (
          <div className="space-y-6">
            <div className="flex justify-center">
              <Button 
                variant="outline" 
                onClick={clearResults}
                className="border-border/50 hover:border-primary/50"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                New Search
              </Button>
            </div>
            <ResultsDisplay 
              results={results} 
              searchType={searchType} 
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default Index;