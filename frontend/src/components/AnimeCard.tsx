// Frontend/src/components/AnimeCard.tsx
import { useState } from "react";
import { Star, Tv, Film, Music, PlayCircle, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AnimeDetailsPopup } from "@/components/AnimeDetailsPopup";
import { useToast } from "@/hooks/use-toast";

interface AnimeCardProps {
  anime: {
    Anime: string;
    "Similarity Score"?: number;
    "Predicted Rating"?: number;
    Rating?: number;
    Genres: string[] | string;
    Type?: string;
    Method?: string; 
    Content_Rating?: number;
    Combined_Score?: number;
  };
  onLike?: () => void;
  onDislike?: () => void;
  onDetails?: () => void;
  user?: any;
  onReplace?: (newAnime: any, index: number) => void;
  searchParams?: {
    title: string;
    userId: string;
    method: string;
    type: string;
  };
  index: number;
}

export const AnimeCard = ({
  anime,
  onLike,
  onDislike,
  onDetails,
  onReplace,
  searchParams,
  index
}: AnimeCardProps) => {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [isReplacing, setIsReplacing] = useState(false);
  const { toast } = useToast();

  const rating = anime["Predicted Rating"] || anime.Rating || anime.Content_Rating || 0;
  const score = anime["Similarity Score"] || anime.Combined_Score || 0;
  const genres = Array.isArray(anime.Genres) ? anime.Genres : anime.Genres?.split(',') || [];
  const method = anime.Method || 'content';
  const type = anime.Type || 'Unknown';

  const getAuthHeaders = () => {
    const token = localStorage.getItem('access_token');
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };
  };

  const handleReplace = async () => {
    if (!onReplace || !searchParams) return;
    setIsReplacing(true);
    try {
      const baseUrl = "http://127.0.0.1:5000";
      const params = new URLSearchParams({
        title: searchParams.title || '',
        user_id: searchParams.userId || '',
        method: searchParams.method,
        type: searchParams.type || 'all'
      });
      params.append('excluded', anime.Anime);

      const response = await fetch(`${baseUrl}/recommend/replacement?${params}`, {
        headers: getAuthHeaders()
      });

      if (!response.ok) throw new Error('Failed to get replacement');

      const newAnime = await response.json();
      onReplace(newAnime, index);

      toast({ title: "Recommendation replaced", description: `Found a new anime for you!` });
    } catch (error) {
      console.error("Replace error:", error);
      toast({ title: "Replacement failed", description: "Could not get a new recommendation", variant: "destructive" });
    } finally {
      setIsReplacing(false);
    }
  };

  const getMethodBadgeVariant = (method: string) => {
    switch (method) {
      case 'hybrid': return 'default';
      case 'collab': return 'secondary';
      case 'content': return 'outline';
      default: return 'outline';
    }
  };

  const getTypeIcon = (type: string) => {
    const lowerType = type.toLowerCase();
    switch (lowerType) {
      case 'tv': return <Tv className="w-4 h-4" />;
      case 'movie': return <Film className="w-4 h-4" />;
      case 'music': return <Music className="w-4 h-4" />;
      case 'ova':
      case 'ona':
      case 'special':
        return <PlayCircle className="w-4 h-4" />;
      default: return <PlayCircle className="w-4 h-4" />;
    }
  };

  const getTypeBadgeColor = (type: string) => {
    const lowerType = type.toLowerCase();
    switch (lowerType) {
      case 'tv': return 'bg-blue-500/20 text-blue-400 border-blue-500/30';
      case 'movie': return 'bg-purple-500/20 text-purple-400 border-purple-500/30';
      case 'ova': return 'bg-green-500/20 text-green-400 border-green-500/30';
      case 'ona': return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30';
      case 'special': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30';
      case 'music': return 'bg-pink-500/20 text-pink-400 border-pink-500/30';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/30';
    }
  };

  const handleDetailsClick = () => {
    setDetailsOpen(true);
    if (onDetails) onDetails();
  };

  return (
    <>
      <div className="bg-gradient-card backdrop-blur-sm border border-border rounded-lg p-8 shadow-card hover:shadow-glow transition-all duration-300 group animate-fade-in relative">
        {onReplace && (
          <button
            onClick={handleReplace}
            disabled={isReplacing}
            className="absolute top-3 right-3 p-1 rounded-full bg-destructive/10 hover:bg-destructive/20 text-destructive transition-colors duration-200 disabled:opacity-50"
            aria-label="Replace recommendation"
          >
            <X className="w-4 h-4" />
          </button>
        )}

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
              {score > 0 && <div className="text-xs text-muted-foreground">Match: {(score * 100).toFixed(0)}%</div>}
            </div>
          </div>

          <div className="flex flex-col gap-2">
            <Badge variant={getMethodBadgeVariant(method)} className="capitalize text-xs">{method}</Badge>
            {type && type !== 'Unknown' && (
              <Badge variant="outline" className={`text-xs capitalize flex items-center gap-1 ${getTypeBadgeColor(type)}`}>
                {getTypeIcon(type)} {type}
              </Badge>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {genres.slice(0, 3).map((genre, idx) => <Badge key={idx} variant="outline" className="text-xs">{genre.trim()}</Badge>)}
          {genres.length > 3 && <Badge variant="outline" className="text-xs">+{genres.length - 3}</Badge>}
        </div>

        <div className="flex justify-between items-center gap-4">
          <Button variant="outline" size="sm" onClick={handleDetailsClick} className="hover:bg-primary hover:text-primary-foreground">
            Details & Watch
          </Button>
          <div className="flex gap-3">
            <Button variant="ghost" size="sm" onClick={onLike} className="hover:bg-green-500/20 hover:text-green-400">👍</Button>
            <Button variant="ghost" size="sm" onClick={onDislike} className="hover:bg-red-500/20 hover:text-red-400">👎</Button>
          </div>
        </div>

        {type && type !== 'Unknown' && (
          <div className="mt-4 pt-4 border-t border-border">
            <div className="text-xs text-muted-foreground">
              <span className="font-medium">Format:</span> {type.toUpperCase()}
              {type.toLowerCase() === 'tv' && ' Series'}
              {type.toLowerCase() === 'ova' && ' (Original Video Animation)'}
              {type.toLowerCase() === 'ona' && ' (Original Net Animation)'}
            </div>
          </div>
        )}
      </div>

      <AnimeDetailsPopup
        anime={{ Anime: anime.Anime, Rating: rating, Genres: genres, type }}
        open={detailsOpen}
        onOpenChange={setDetailsOpen}
      />
    </>
  );
};
