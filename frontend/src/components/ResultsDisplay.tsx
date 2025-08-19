// Frontend/src/components/ResultsDisplay.tsx

import { RecommendationCard } from "./RecommendationCard";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Sparkles, Users, Zap, TrendingUp } from "lucide-react";

interface ResultsDisplayProps {
  results: any;
  searchType: 'content' | 'collaborative' | 'hybrid';
}

export const ResultsDisplay = ({ results, searchType }: ResultsDisplayProps) => {
  if (!results) return null;

  const getResultIcon = (type: string) => {
    switch (type) {
      case 'content': return <Sparkles className="w-4 h-4" />;
      case 'collaborative': return <Users className="w-4 h-4" />;
      case 'hybrid': return <Zap className="w-4 h-4" />;
      default: return <TrendingUp className="w-4 h-4" />;
    }
  };

  const renderResults = (data: any[], type: 'content' | 'collaborative' | 'hybrid') => {
    if (!data || data.length === 0) {
      return (
        <Card className="anime-card text-center py-8">
          <p className="text-muted-foreground">No recommendations found</p>
        </Card>
      );
    }

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {data.map((anime, index) => (
          <RecommendationCard 
            key={`${anime.Anime}-${index}`} 
            anime={anime} 
            type={type} 
          />
        ))}
      </div>
    );
  };

  // Handle hybrid results (multiple result types)
  if (searchType === 'hybrid' && results.hybrid) {
    return (
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold gradient-text flex items-center justify-center gap-2">
            {getResultIcon('hybrid')}
            Hybrid Recommendations
          </h2>
          <p className="text-muted-foreground">
            Best of both content-based and collaborative filtering
          </p>
        </div>

        <Tabs defaultValue="hybrid" className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-muted/20">
            <TabsTrigger value="hybrid" className="flex items-center gap-2">
              <Zap className="w-4 h-4" />
              Hybrid
              <Badge variant="outline" className="ml-1 text-xs">
                {results.hybrid?.length || 0}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="content" className="flex items-center gap-2">
              <Sparkles className="w-4 h-4" />
              Content
              <Badge variant="outline" className="ml-1 text-xs">
                {results.content_based?.length || 0}
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="collaborative" className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Collaborative
              <Badge variant="outline" className="ml-1 text-xs">
                {results.collaborative?.length || 0}
              </Badge>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="hybrid" className="mt-6">
            {renderResults(results.hybrid, 'hybrid')}
          </TabsContent>

          <TabsContent value="content" className="mt-6">
            {renderResults(results.content_based, 'content')}
          </TabsContent>

          <TabsContent value="collaborative" className="mt-6">
            {renderResults(results.collaborative, 'collaborative')}
          </TabsContent>
        </Tabs>
      </div>
    );
  }

  // Handle single result type (content or collaborative)
  const resultData = Array.isArray(results) ? results : [];
  
  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold gradient-text flex items-center justify-center gap-2">
          {getResultIcon(searchType)}
          {searchType === 'content' ? 'Content-Based' : 'Collaborative'} Recommendations
        </h2>
        <div className="flex items-center justify-center gap-2">
          <p className="text-muted-foreground">
            Found {resultData.length} recommendations
          </p>
          <Badge variant="outline" className="text-primary border-primary/30">
            {searchType}
          </Badge>
        </div>
      </div>

      {renderResults(resultData, searchType)}
    </div>
  );
};