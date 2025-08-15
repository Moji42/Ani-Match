import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface RecommendationCardProps {
  anime: {
    Anime: string;
    Genres: string[] | string;
    'Predicted Rating'?: number;
    'Similarity Score'?: number;
    Rating?: number;
    Members?: number;
    Type?: string;
  };
  type: 'content' | 'collaborative' | 'hybrid' | 'random';
}

export const RecommendationCard = ({ anime, type }: RecommendationCardProps) => {
  const genres = Array.isArray(anime.Genres) 
    ? anime.Genres 
    : typeof anime.Genres === 'string' 
      ? anime.Genres.split(',') 
      : [];

  const getScore = () => {
    switch (type) {
      case 'content':
        return anime['Similarity Score'] ? `${(anime['Similarity Score'] * 100).toFixed(1)}%` : null;
      case 'collaborative':
        return anime['Predicted Rating'] ? `${anime['Predicted Rating'].toFixed(1)}/10` : null;
      case 'random':
        return anime.Members ? `${anime.Members.toLocaleString()} members` : null;
      default:
        return null;
    }
  };

  return (
    <Card className="p-4 space-y-3 hover:shadow-md transition-shadow">
      <h3 className="font-bold text-lg">{anime.Anime}</h3>
      
      {getScore() && (
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">
            {type === 'content' ? 'Similarity' : 
             type === 'collaborative' ? 'Predicted Rating' : 'Members'}
          </span>
          <span className="font-medium">{getScore()}</span>
        </div>
      )}

      {anime.Rating && (
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Rating</span>
          <span className="text-muted-foreground">{anime.Rating.toFixed(1)}/10</span>
        </div>
      )}

      <div className="flex flex-wrap gap-1">
        {genres.slice(0, 4).map((genre, i) => (
          <Badge key={i} variant="secondary" className="text-xs">
            {genre.trim()}
          </Badge>
        ))}
        {genres.length > 4 && (
          <Badge variant="outline" className="text-xs">
            +{genres.length - 4}
          </Badge>
        )}
      </div>
    </Card>
  );
};