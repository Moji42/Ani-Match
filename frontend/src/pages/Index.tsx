import { useState } from "react";
import { Toaster } from "@/components/ui/toaster";
import { useToast } from "@/hooks/use-toast";
import { SearchSection } from "@/components/SearchSection";
import { AnimeCard } from "@/components/AnimeCard";
import { AuthModal } from "@/components/AuthModal";
import { MLExplanation } from "@/components/MLExplanation";
import { Loader2, Star } from "lucide-react";

interface AnimeRecommendation {
  Anime: string;
  "Similarity Score"?: number;
  "Predicted Rating"?: number;
  Rating?: number;
  Genres: string[] | string;
  Method?: string;
  Content_Rating?: number;
  Combined_Score?: number;
}

const Index = () => {
  const [recommendations, setRecommendations] = useState<AnimeRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentMethod, setCurrentMethod] = useState<string>("");
  const { toast } = useToast();

  const baseUrl = "http://127.0.0.1:5000"; // Flask backend URL matching your logs

  const handleSearch = async (title: string, userId: string, method: string) => {
    setLoading(true);
    setCurrentMethod(method);
    
    try {
      let url = `${baseUrl}/recommend/${method}?n=8`;
      
      if (method === "content") {
        url += `&title=${encodeURIComponent(title)}`;
      } else if (method === "collab") {
        url += `&user_id=${userId}`;
      } else if (method === "hybrid") {
        url += `&title=${encodeURIComponent(title)}&user_id=${userId}`;
      }

      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (method === "hybrid") {
        setRecommendations(data.hybrid || []);
      } else {
        setRecommendations(Array.isArray(data) ? data : []);
      }
      
      toast({
        title: "Recommendations loaded!",
        description: `Found ${Array.isArray(data) ? data.length : data.hybrid?.length || 0} anime recommendations using ${method} method.`,
      });
    } catch (error) {
      console.error("Search error:", error);
      toast({
        title: "Search failed",
        description: "Please make sure your Flask backend is running on localhost:5000",
        variant: "destructive",
      });
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRandomSearch = async () => {
    setLoading(true);
    setCurrentMethod("random");
    
    try {
      const response = await fetch(`${baseUrl}/recommend/random?n=8`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setRecommendations(data);
      
      toast({
        title: "Random picks loaded!",
        description: `Discovered ${data.length} random anime for you to explore.`,
      });
    } catch (error) {
      console.error("Random search error:", error);
      toast({
        title: "Random search failed",
        description: "Please make sure your Flask backend is running on localhost:5000",
        variant: "destructive",
      });
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = (anime: AnimeRecommendation) => {
    toast({
      title: "Liked!",
      description: `Added "${anime.Anime}" to your favorites.`,
    });
  };

  const handleDislike = (anime: AnimeRecommendation) => {
    toast({
      title: "Noted",
      description: `We'll avoid recommending similar anime in the future.`,
    });
  };

  const handleDetails = (anime: AnimeRecommendation) => {
    toast({
      title: "Details",
      description: `More details for "${anime.Anime}" coming soon!`,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/50">
      {/* Hero Header */}
      <div className="relative overflow-hidden mb-12">
        <div className="absolute inset-0 bg-gradient-hero opacity-30" />
        <div className="relative container mx-auto px-6 py-16">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
            <div className="text-center lg:text-left">
              <div className="flex items-center gap-4 justify-center lg:justify-start mb-6">
                <div className="p-4 bg-gradient-primary rounded-xl shadow-glow">
                  <Star className="w-10 h-10 text-primary-foreground" />
                </div>
                <h1 className="text-5xl lg:text-7xl font-bold text-foreground animate-fade-in">
                  Anime Geist
                </h1>
              </div>
              <p className="text-xl lg:text-2xl text-muted-foreground max-w-2xl animate-slide-up leading-relaxed">
                Discover your next favorite anime with AI-powered recommendations. 
                Get personalized suggestions based on your preferences and viewing history.
              </p>
            </div>
            
            <div className="flex items-center">
              <AuthModal />
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-6 pb-24">
        <div className="max-w-6xl mx-auto space-y-16">
          <SearchSection
            onSearch={handleSearch}
            onRandomSearch={handleRandomSearch}
            loading={loading}
          />

          {/* Loading State */}
          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="flex items-center gap-4 text-muted-foreground">
                <Loader2 className="w-8 h-8 animate-spin" />
                <span className="text-xl">Finding perfect anime for you...</span>
              </div>
            </div>
          )}

          {/* Results Section */}
          {!loading && recommendations.length > 0 && (
            <div className="space-y-10">
              <div className="flex items-center gap-4">
                <h3 className="text-3xl font-bold text-foreground">
                  Recommendations
                </h3>
                {currentMethod && (
                  <span className="text-sm text-muted-foreground capitalize bg-secondary px-4 py-2 rounded-full">
                    {currentMethod} method
                  </span>
                )}
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {recommendations.map((anime, index) => (
                  <AnimeCard
                    key={`${anime.Anime}-${index}`}
                    anime={anime}
                    onLike={() => handleLike(anime)}
                    onDislike={() => handleDislike(anime)}
                    onDetails={() => handleDetails(anime)}
                  />
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!loading && recommendations.length === 0 && (
            <div className="text-center py-24">
              <div className="max-w-lg mx-auto">
                <div className="w-32 h-32 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-8 opacity-50">
                  <Star className="w-16 h-16 text-primary-foreground" />
                </div>
                <h3 className="text-2xl font-semibold text-foreground mb-4">
                  Ready to Discover Amazing Anime?
                </h3>
                <p className="text-lg text-muted-foreground">
                  Search for an anime you love or try our random recommendations to get started.
                </p>
              </div>
            </div>
          )}

          {/* ML Explanation Section */}
          <div className="mt-20">
            <MLExplanation />
          </div>
        </div>
      </div>
      
      <Toaster />
    </div>
  );
};

export default Index;
