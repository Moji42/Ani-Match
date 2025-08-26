import { useState, useEffect } from "react";
import { Toaster } from "@/components/ui/toaster";
import { useToast } from "@/hooks/use-toast";
import { SearchSection } from "@/components/SearchSection";
import { AnimeCard } from "@/components/AnimeCard";
import { AuthModal } from "@/components/AuthModal";
import { MLExplanation } from "@/components/MLExplanation";
import { Loader2, Star, Filter } from "lucide-react";
import { Badge } from "@/components/ui/badge";

interface AnimeRecommendation {
  Anime: string;
  "Similarity Score"?: number;
  "Predicted Rating"?: number;
  Rating?: number;
  Genres: string[] | string;
  Type?: string;
  Method?: string;
  Content_Rating?: number;
  Combined_Score?: number;
}

const Index = () => {
  const [recommendations, setRecommendations] = useState<AnimeRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [currentMethod, setCurrentMethod] = useState<string>("");
  const [currentFilter, setCurrentFilter] = useState<string>("all");
  const [currentSearchParams, setCurrentSearchParams] = useState<{
    title: string;
    userId: string;
    method: string;
    type: string;
  }>({ title: "", userId: "", method: "content", type: "all" });

  const { toast } = useToast();
  const baseUrl = "http://127.0.0.1:5000";

  const getAuthHeaders = () => {
    const token = localStorage.getItem("access_token");
    return {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    };
  };

  const handleSearch = async (
    title: string,
    userId: string,
    method: string,
    count: number,
    type: string
  ) => {
    setLoading(true);
    setCurrentMethod(method);
    setCurrentFilter(type);
    setCurrentSearchParams({ title, userId, method, type });

    try {
      let url = `${baseUrl}/recommend/${method}?n=${count}`;
      if (type && type !== "all") url += `&type=${encodeURIComponent(type)}`;

      if (method === "content") url += `&title=${encodeURIComponent(title)}`;
      else if (method === "collab") url += `&user_id=${userId}`;
      else if (method === "hybrid") url += `&title=${encodeURIComponent(title)}&user_id=${userId}`;

      const response = await fetch(url, { headers: getAuthHeaders() });
      if (!response.ok) {
        if (response.status === 401) throw new Error("Authentication required. Please sign in.");
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (method === "hybrid") setRecommendations(data.hybrid || []);
      else setRecommendations(Array.isArray(data) ? data : []);

      const resultCount = method === "hybrid" ? (data.hybrid?.length || 0) : (Array.isArray(data) ? data.length : 0);
      const filterText = type && type !== "all" ? ` (${type} only)` : "";

      toast({ title: "Recommendations loaded!", description: `Found ${resultCount} anime recommendations using ${method} method${filterText}.` });
    } catch (error) {
      console.error("Search error:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";

      toast({
        title: "Search failed",
        description:
          errorMessage.includes("Authentication")
            ? "Please sign in to get recommendations"
            : errorMessage.includes("No recommendations found")
            ? `No ${type !== "all" ? type + " " : ""}anime found matching your criteria.`
            : "Please make sure your Flask backend is running on localhost:5000",
        variant: "destructive",
      });
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRandomSearch = async (count: number, type: string) => {
    setLoading(true);
    setCurrentMethod("random");
    setCurrentFilter(type);
    setCurrentSearchParams({ title: "", userId: "", method: "random", type });

    try {
      let url = `${baseUrl}/recommend/random?n=${count}`;
      if (type && type !== "all") url += `&type=${encodeURIComponent(type)}`;

      const response = await fetch(url, { headers: getAuthHeaders() });
      if (!response.ok) {
        if (response.status === 401) throw new Error("Authentication required. Please sign in.");
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setRecommendations(data);

      const filterText = type && type !== "all" ? ` ${type}` : "";
      toast({ title: "Random picks loaded!", description: `Discovered ${data.length}${filterText} anime for you to explore.` });
    } catch (error) {
      console.error("Random search error:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error occurred";

      toast({
        title: "Random search failed",
        description:
          errorMessage.includes("Authentication")
            ? "Please sign in to get recommendations"
            : errorMessage.includes("No anime found")
            ? `No ${type !== "all" ? type + " " : ""}anime available.`
            : "Please make sure your Flask backend is running on localhost:5000",
        variant: "destructive",
      });
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleLike = (anime: AnimeRecommendation) => {
    toast({ title: "Liked!", description: `Added "${anime.Anime}" to your favorites.` });
  };

  const handleDislike = (anime: AnimeRecommendation) => {
    toast({ title: "Noted", description: `We'll avoid recommending similar anime in the future.` });
  };

  const handleReplaceRecommendation = (newAnime: any, index: number) => {
    setRecommendations((prev) => {
      const newRecs = [...prev];
      newRecs[index] = newAnime;
      return newRecs;
    });
  };

  const getTypeStatistics = () => {
    if (!recommendations.length) return null;
    const typeCounts: Record<string, number> = {};
    recommendations.forEach((anime) => {
      const type = anime.Type || "Unknown";
      typeCounts[type] = (typeCounts[type] || 0) + 1;
    });
    return Object.entries(typeCounts).sort(([, a], [, b]) => b - a).slice(0, 5);
  };

  const typeStats = getTypeStatistics();

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-background/50">
      <div className="relative overflow-hidden mb-12">
        <div className="absolute inset-0 bg-gradient-hero opacity-30" />
        <div className="relative container mx-auto px-6 py-16">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-12">
            <div className="text-center lg:text-left">
              <div className="flex items-center gap-4 justify-center lg:justify-start mb-6">
                <div className="p-4 bg-gradient-primary rounded-xl shadow-glow">
                  <Star className="w-10 h-10 text-primary-foreground" />
                </div>
                <h1 className="text-5xl lg:text-7xl font-bold text-foreground animate-fade-in">Ani-Match</h1>
              </div>
              <p className="text-xl lg:text-2xl text-muted-foreground max-w-2xl animate-slide-up leading-relaxed">
                Discover your next favorite anime with AI-powered recommendations. Get personalized suggestions based on your preferences and viewing history.
              </p>
            </div>
            <div className="flex items-center">
              <AuthModal />
            </div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 pb-24">
        <div className="max-w-6xl mx-auto space-y-16">
          <SearchSection onSearch={handleSearch} onRandomSearch={handleRandomSearch} loading={loading} />

          {loading && (
            <div className="flex items-center justify-center py-20">
              <div className="flex items-center gap-4 text-muted-foreground">
                <Loader2 className="w-8 h-8 animate-spin" />
                <span className="text-xl">Finding perfect anime for you...</span>
              </div>
            </div>
          )}

          {!loading && recommendations.length > 0 && (
            <div className="space-y-10">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex items-center gap-4">
                  <h3 className="text-3xl font-bold text-foreground">Recommendations ({recommendations.length})</h3>
                  {currentMethod && (
                    <Badge variant="outline" className="capitalize bg-secondary/20 text-secondary-foreground border-secondary/30">
                      {currentMethod} method
                    </Badge>
                  )}
                </div>

                <div className="flex flex-wrap items-center gap-3">
                  {currentFilter && currentFilter !== "all" && (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-accent/10 border border-accent/30 rounded-lg">
                      <Filter className="w-4 h-4 text-accent" />
                      <span className="text-sm font-medium text-accent capitalize">{currentFilter}</span>
                    </div>
                  )}

                  {typeStats && typeStats.length > 0 && (
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">Types:</span>
                      {typeStats.map(([type, count]) => (
                        <Badge key={type} variant="outline" className="text-xs">
                          {type} ({count})
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
                {recommendations.map((anime, index) => (
                  <AnimeCard
                    key={`${anime.Anime}-${index}`}
                    anime={anime}
                    onLike={() => handleLike(anime)}
                    onDislike={() => handleDislike(anime)}
                    onReplace={handleReplaceRecommendation}
                    searchParams={currentSearchParams}
                    index={index}
                  />
                ))}
              </div>
            </div>
          )}

          {!loading && recommendations.length === 0 && (
            <div className="text-center py-24">
              <div className="max-w-lg mx-auto">
                <div className="w-32 h-32 bg-gradient-primary rounded-full flex items-center justify-center mx-auto mb-8 opacity-50">
                  <Star className="w-16 h-16 text-primary-foreground" />
                </div>
                <h3 className="text-2xl font-semibold text-foreground mb-4">Ready to Discover Amazing Anime?</h3>
                <p className="text-lg text-muted-foreground mb-6">
                  Search for an anime you love, apply filters by type, or try our random recommendations to get started.
                </p>
                <div className="flex flex-wrap justify-center gap-2 mb-4">
                  <Badge variant="outline" className="bg-secondary/10">TV Series</Badge>
                  <Badge variant="outline" className="bg-secondary/10">Movies</Badge>
                  <Badge variant="outline" className="bg-secondary/10">OVA</Badge>
                  <Badge variant="outline" className="bg-secondary/10">Specials</Badge>
                  <Badge variant="outline" className="bg-secondary/10">ONA</Badge>
                </div>
                <p className="text-sm text-muted-foreground">Filter by any anime type to find exactly what you're looking for</p>
              </div>
            </div>
          )}

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
