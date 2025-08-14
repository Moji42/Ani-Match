import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface RecommendationCardProps {
  anime: {
    Anime: string;
    Genres: string[];
    'Similarity Score'?: number;
    'Predicted Rating'?: number;
    'Combined_Score'?: string;
    Rating?: number;
    Method?: string;
    Content_Rating?: number;
    Similarity_Score?: number;
    Predicted_Rating?: number;
    Type?: string;
    Members?: number;
  };
  type: 'content' | 'collaborative' | 'hybrid' | 'random';
}

export const RecommendationCard = ({ anime, type }: RecommendationCardProps) => {
  const getScoreDisplay = () => {
    switch (type) {
      case 'content':
        return {
          label: 'Similarity',
          value: anime['Similarity Score'] || anime.Similarity_Score,
          format: (val: number) => `${(val * 100).toFixed(1)}%`
        };
      case 'collaborative':
        return {
          label: 'Predicted Rating',
          value: anime['Predicted Rating'] || anime.Predicted_Rating,
          format: (val: number) => `${val.toFixed(1)}/10`
        };
      case 'hybrid':
        return {
          label: 'Combined Score',
          value: parseFloat(anime.Combined_Score || '0'),
          format: (val: number) => `${(val * 100).toFixed(1)}%`
        };
      case 'random':
        return anime.Members ? {
          label: 'Members',
          value: anime.Members,
          format: (val: number) => val.toLocaleString()
        } : null;
      default:
        return null;
    }
  };

  const scoreInfo = getScoreDisplay();
  const genres = Array.isArray(anime.Genres) ? anime.Genres : [];

  return (
    <Card className="anime-card group cursor-pointer">
      <div className="space-y-4">
        <div className="space-y-2">
          <h3 className="text-lg font-bold text-foreground group-hover:gradient-text transition-all duration-300">
            {anime.Anime}
          </h3>
          
          {scoreInfo && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">{scoreInfo.label}</span>
              <span className="text-sm font-semibold text-primary">
                {scoreInfo.format(scoreInfo.value)}
              </span>
            </div>
          )}

          {anime.Method && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Method</span>
              <Badge 
                variant="outline" 
                className="text-xs capitalize border-primary/30 text-primary"
              >
                {anime.Method}
              </Badge>
            </div>
          )}

          {(anime.Rating || anime.Content_Rating) && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Rating</span>
              <span className="text-sm text-secondary">
                {(anime.Rating || anime.Content_Rating)?.toFixed(1)}/10
              </span>
            </div>
          )}
        </div>

        <div className="space-y-2">
          <span className="text-sm text-muted-foreground">Genres</span>
          <div className="flex flex-wrap gap-1">
            {genres.slice(0, 4).map((genre, index) => (
              <Badge 
                key={index} 
                variant="secondary" 
                className="text-xs bg-secondary/20 text-secondary-foreground border-secondary/30"
              >
                {genre}
              </Badge>
            ))}
            {genres.length > 4 && (
              <Badge 
                variant="outline" 
                className="text-xs border-muted-foreground/30 text-muted-foreground"
              >
                +{genres.length - 4}
              </Badge>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};