import { RecommendationCard } from "./RecommendationCard";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, Users, Zap, Shuffle } from "lucide-react";

interface ResultsDisplayProps {
  results: any;
  searchType: 'content' | 'collaborative' | 'hybrid' | 'random';
}

export const ResultsDisplay = ({ results, searchType }: ResultsDisplayProps) => {
  if (!results) return null;

  const getRecommendations = () => {
    if (searchType === 'hybrid' && results.hybrid) {
      return results.hybrid;
    }
    return Array.isArray(results) ? results : [];
  };

  const recommendations = getRecommendations();

  if (recommendations.length === 0) {
    return (
      <Card className="text-center p-8">
        <p>No recommendations found</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold flex items-center justify-center gap-2">
          {searchType === 'content' ? (
            <Sparkles className="w-5 h-5" />
          ) : searchType === 'collaborative' ? (
            <Users className="w-5 h-5" />
          ) : searchType === 'random' ? (
            <Shuffle className="w-5 h-5" />
          ) : (
            <Zap className="w-5 h-5" />
          )}
          {searchType.charAt(0).toUpperCase() + searchType.slice(1)} Recommendations
        </h2>
        <Badge variant="outline">
          {recommendations.length} results
        </Badge>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {recommendations.map((anime: any, index: number) => (
          <RecommendationCard 
            key={`${anime.Anime}-${index}`}
            anime={anime}
            type={searchType}
          />
        ))}
      </div>
    </div>
  );
};