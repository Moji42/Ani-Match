import { Star, Heart, ThumbsDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface AnimeCardProps {
  anime: {
    Anime: string;
    "Similarity Score"?: number;
    "Predicted Rating"?: number;
    Rating?: number;
    Genres: string[] | string;
    Method?: string;
    Content_Rating?: number;
    Combined_Score?: number;
  };
  onLike?: () => void;
  onDislike?: () => void;
  onDetails?: () => void;
}

export const AnimeCard = ({ anime, onLike, onDislike, onDetails }: AnimeCardProps) => {
  const rating = anime["Predicted Rating"] || anime.Rating || anime.Content_Rating || 0;
  const score = anime["Similarity Score"] || anime.Combined_Score || 0;
  const genres = Array.isArray(anime.Genres) ? anime.Genres : anime.Genres?.split(',') || [];
  const method = anime.Method || 'content';

  const getMethodBadgeVariant = (method: string) => {
    switch (method) {
      case 'hybrid': return 'default';
      case 'collab': return 'secondary';
      case 'content': return 'outline';
      default: return 'outline';
    }
  };

  return (
    <div className="bg-gradient-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-card hover:shadow-glow transition-all duration-300 group animate-fade-in">
      <div className="flex justify-between items-start mb-6">
        <div className="flex-1">
          <h3 className="text-xl font-semibold text-foreground group-hover:text-primary-glow transition-colors duration-300 mb-3">
            {anime.Anime}
          </h3>
          <div className="flex items-center gap-3 mb-3">
            <div className="flex items-center gap-1 text-accent">
              <Star className="w-4 h-4 fill-current" />
              <span className="text-sm font-medium">{rating.toFixed(1)}</span>
            </div>
            {score > 0 && (
              <div className="text-xs text-muted-foreground">
                Match: {(score * 100).toFixed(0)}%
              </div>
            )}
          </div>
        </div>
        <Badge variant={getMethodBadgeVariant(method)} className="capitalize">
          {method}
        </Badge>
      </div>

      <div className="flex flex-wrap gap-2 mb-6">
        {genres.slice(0, 3).map((genre, index) => (
          <Badge key={index} variant="outline" className="text-xs">
            {genre.trim()}
          </Badge>
        ))}
        {genres.length > 3 && (
          <Badge variant="outline" className="text-xs">
            +{genres.length - 3}
          </Badge>
        )}
      </div>

      <div className="flex justify-between items-center gap-4">
        <Button
          variant="outline"
          size="sm"
          onClick={onDetails}
          className="hover:bg-primary hover:text-primary-foreground"
        >
          Details
        </Button>
        <div className="flex gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={onLike}
            className="hover:bg-green-500/20 hover:text-green-400"
          >
            👍
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDislike}
            className="hover:bg-red-500/20 hover:text-red-400"
          >
            👎
          </Button>
        </div>
      </div>
    </div>
  );
};