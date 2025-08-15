import { RecommendationCard } from "./RecommendationCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sparkles, Users, Zap } from "lucide-react";

type RecommendationType = 'content' | 'collaborative' | 'hybrid' | 'random';

interface AnimeRecommendation {
  Anime: string;
  Genres: string[];
  'Similarity Score'?: number;
  'Predicted Rating'?: number;
  'Combined_Score'?: string;
  Rating?: number;
  Members?: number;
  Method?: RecommendationType;
  Content_Score?: number;
  Collab_Score?: number;
}

interface HybridResults {
  content_based: AnimeRecommendation[];
  collaborative: AnimeRecommendation[];
  hybrid: AnimeRecommendation[];
}

interface ResultsDisplayProps {
  results: AnimeRecommendation[] | HybridResults | null;
  searchType: RecommendationType;
}

export const ResultsDisplay = ({ results, searchType }: ResultsDisplayProps) => {
  if (!results) return null;

  const renderRecommendationCard = (anime: AnimeRecommendation, index: number) => {
    // Ensure the type is always one of the allowed values
    const cardType: RecommendationType = anime.Method || searchType;
    
    return (
      <RecommendationCard 
        key={`${anime.Anime}-${index}`}
        anime={anime}
        type={cardType}
      />
    );
  };

  if (searchType === 'hybrid' && 'hybrid' in results) {
    const hybridResults = results as HybridResults;
    return (
      <Tabs defaultValue="hybrid" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="hybrid">
            <Zap className="w-4 h-4 mr-2" /> Hybrid
          </TabsTrigger>
          <TabsTrigger value="content">
            <Sparkles className="w-4 h-4 mr-2" /> Content
          </TabsTrigger>
          <TabsTrigger value="collaborative">
            <Users className="w-4 h-4 mr-2" /> Collaborative
          </TabsTrigger>
        </TabsList>

        <TabsContent value="hybrid">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hybridResults.hybrid.map(renderRecommendationCard)}
          </div>
        </TabsContent>

        <TabsContent value="content">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hybridResults.content_based.map(renderRecommendationCard)}
          </div>
        </TabsContent>

        <TabsContent value="collaborative">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {hybridResults.collaborative.map(renderRecommendationCard)}
          </div>
        </TabsContent>
      </Tabs>
    );
  }

  const items = Array.isArray(results) ? results : [];
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map(renderRecommendationCard)}
    </div>
  );
};