import React, { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Star, Play, Heart, Clock, Calendar, Users, Award, ExternalLink, Tv, Globe, BookOpen } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface StreamingSource {
  name: string;
  url: string;
  type: 'legal' | 'subscription' | 'free';
  region?: string;
  logo?: string;
}

interface AnimeDetails {
  Anime: string;
  Rating?: number;
  Genres: string[] | string;
  synopsis?: string;
  episodes?: number;
  status?: string;
  year?: number;
  studio?: string;
  duration?: string;
  score?: number;
  ranked?: number;
  popularity?: number;
  members?: number;
  source?: string;
  type?: string;
}

interface AnimeDetailsPopupProps {
  anime: AnimeDetails;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

// Enhanced streaming sources with more platforms
const getStreamingSources = (animeName: string): StreamingSource[] => {
  const allSources: StreamingSource[] = [
    { 
      name: "Crunchyroll", 
      url: `https://www.crunchyroll.com/search?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "Global" 
    },
    { 
      name: "Funimation", 
      url: `https://www.funimation.com/search/?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "US/CA/UK" 
    },
    { 
      name: "Netflix", 
      url: `https://www.netflix.com/search?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "Global" 
    },
    { 
      name: "Hulu", 
      url: `https://www.hulu.com/search?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "US" 
    },
    { 
      name: "Amazon Prime Video", 
      url: `https://www.amazon.com/s?k=${encodeURIComponent(animeName)}&i=instant-video`, 
      type: "subscription", 
      region: "Global" 
    },
    { 
      name: "VRV", 
      url: `https://vrv.co/search?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "US" 
    },
    { 
      name: "AnimeLab", 
      url: `https://www.animelab.com/search?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "AU/NZ" 
    },
    { 
      name: "Wakanim", 
      url: `https://www.wakanim.tv/sc/v2/search?q=${encodeURIComponent(animeName)}`, 
      type: "subscription", 
      region: "EU" 
    },
    { 
      name: "Tubi", 
      url: `https://tubitv.com/search/${encodeURIComponent(animeName)}`, 
      type: "free", 
      region: "US/CA/AU" 
    },
    { 
      name: "YouTube", 
      url: `https://www.youtube.com/results?search_query=${encodeURIComponent(animeName + ' anime')}`, 
      type: "free", 
      region: "Global" 
    }
  ];
  
  // Randomly select 3-6 sources for demo (in production, filter based on actual availability)
  const shuffled = allSources.sort(() => 0.5 - Math.random());
  const selectedCount = Math.floor(Math.random() * 4) + 3; // 3-6 sources
  return shuffled.slice(0, selectedCount);
};

// Enhanced mock function for anime details with more realistic data
const getAnimeDetails = (animeName: string): Partial<AnimeDetails> => {
  const animeTypes = ["TV", "Movie", "OVA", "Special", "ONA"];
  const statuses = ["Completed", "Ongoing", "Upcoming", "On Hiatus"];
  const sources = ["Manga", "Light Novel", "Original", "Game", "Visual Novel", "Novel"];
  const studios = [
    "Mappa", "Wit Studio", "Toei Animation", "Madhouse", "Bones", "Studio Pierrot",
    "Production I.G", "A-1 Pictures", "Sunrise", "Trigger", "Kyoto Animation",
    "White Fox", "David Production", "Shaft", "Cloverworks"
  ];

  // Create synopsis based on anime name for more realistic content
  const createSynopsis = (name: string): string => {
    const templates = [
      `${name} follows the journey of extraordinary characters as they navigate a world filled with challenges, mysteries, and unexpected alliances. With stunning animation and compelling storytelling, this series explores themes of friendship, courage, and personal growth.`,
      `In the world of ${name}, our protagonists face incredible odds as they fight to protect what they hold dear. This gripping tale combines intense action sequences with deep character development and emotional storytelling.`,
      `${name} presents a unique and captivating story that has captured the hearts of fans worldwide. Through its compelling narrative and memorable characters, the series delivers both entertainment and meaningful life lessons.`
    ];
    return templates[Math.floor(Math.random() * templates.length)];
  };

  return {
    synopsis: createSynopsis(animeName),
    episodes: Math.floor(Math.random() * 300) + 12, // 12-312 episodes
    status: statuses[Math.floor(Math.random() * statuses.length)],
    year: 2015 + Math.floor(Math.random() * 9), // 2015-2023
    studio: studios[Math.floor(Math.random() * studios.length)],
    duration: Math.random() > 0.8 ? "24 min" : Math.random() > 0.5 ? "23 min" : "22 min",
    ranked: Math.floor(Math.random() * 2000) + 1,
    popularity: Math.floor(Math.random() * 10000) + 100,
    members: Math.floor(Math.random() * 2000000) + 10000,
    source: sources[Math.floor(Math.random() * sources.length)],
    type: animeTypes[Math.floor(Math.random() * animeTypes.length)]
  };
};

export const AnimeDetailsPopup: React.FC<AnimeDetailsPopupProps> = ({
  anime,
  open,
  onOpenChange,
}) => {
  const [streamingSources] = useState<StreamingSource[]>(() => getStreamingSources(anime.Anime));
  const [additionalDetails] = useState<Partial<AnimeDetails>>(() => getAnimeDetails(anime.Anime));
  const [isInFavorites, setIsInFavorites] = useState(false);
  const [isInWatchlist, setIsInWatchlist] = useState(false);
  const { toast } = useToast();
  
  const genres = Array.isArray(anime.Genres) ? anime.Genres : anime.Genres?.split(',') || [];
  const rating = anime.Rating || additionalDetails.score || 0;

  const getSourceTypeColor = (type: StreamingSource['type']) => {
    switch (type) {
      case 'legal': return 'bg-green-500';
      case 'subscription': return 'bg-blue-500';
      case 'free': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  const getSourceTypeLabel = (type: StreamingSource['type']) => {
    switch (type) {
      case 'legal': return 'Official';
      case 'subscription': return 'Premium';
      case 'free': return 'Free';
      default: return 'Unknown';
    }
  };

  const handleStreamingClick = (source: StreamingSource) => {
    window.open(source.url, '_blank', 'noopener,noreferrer');
    toast({
      title: `Opening ${source.name}`,
      description: `Searching for "${anime.Anime}" on ${source.name}`,
    });
  };

  const handleAddToFavorites = () => {
    setIsInFavorites(!isInFavorites);
    toast({
      title: isInFavorites ? "Removed from Favorites" : "Added to Favorites",
      description: `"${anime.Anime}" ${isInFavorites ? 'removed from' : 'added to'} your favorites list.`,
    });
  };

  const handleAddToWatchlist = () => {
    setIsInWatchlist(!isInWatchlist);
    toast({
      title: isInWatchlist ? "Removed from Watchlist" : "Added to Watchlist",
      description: `"${anime.Anime}" ${isInWatchlist ? 'removed from' : 'added to'} your watch list.`,
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-background via-background to-background/80 border border-border">
        <DialogHeader className="pb-4">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-3xl font-bold text-foreground mb-2">
                {anime.Anime}
              </DialogTitle>
              <div className="flex items-center gap-4 mb-3">
                {rating > 0 && (
                  <div className="flex items-center gap-1 text-yellow-500">
                    <Star className="w-5 h-5 fill-current" />
                    <span className="font-semibold">{rating.toFixed(1)}</span>
                    <span className="text-sm text-muted-foreground">/10</span>
                  </div>
                )}
                {additionalDetails.year && (
                  <div className="flex items-center gap-1 text-muted-foreground">
                    <Calendar className="w-4 h-4" />
                    <span>{additionalDetails.year}</span>
                  </div>
                )}
                {additionalDetails.type && (
                  <Badge variant="outline">{additionalDetails.type}</Badge>
                )}
                {additionalDetails.status && (
                  <Badge 
                    variant={additionalDetails.status === "Completed" ? "default" : "secondary"}
                    className={additionalDetails.status === "Ongoing" ? "bg-green-500/20 text-green-400 border-green-500/30" : ""}
                  >
                    {additionalDetails.status}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </DialogHeader>

        <div className="space-y-6">
          {/* Synopsis */}
          {additionalDetails.synopsis && (
            <div className="space-y-3">
              <h3 className="text-xl font-semibold text-foreground flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                Synopsis
              </h3>
              <div className="bg-secondary/10 rounded-lg p-4 border border-border">
                <p className="text-muted-foreground leading-relaxed">
                  {additionalDetails.synopsis}
                </p>
              </div>
            </div>
          )}

          {/* Genres */}
          <div className="space-y-3">
            <h3 className="text-xl font-semibold text-foreground">Genres</h3>
            <div className="flex flex-wrap gap-2">
              {genres.map((genre, index) => (
                <Badge 
                  key={index} 
                  variant="secondary" 
                  className="bg-gradient-to-r from-secondary/20 to-secondary/30 hover:from-secondary/30 hover:to-secondary/40 transition-colors cursor-pointer"
                >
                  {genre.trim()}
                </Badge>
              ))}
            </div>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {additionalDetails.episodes && (
              <Card className="bg-secondary/10 border-border hover:bg-secondary/20 transition-colors">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Tv className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Episodes</p>
                    <p className="text-muted-foreground">{additionalDetails.episodes}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {additionalDetails.duration && (
              <Card className="bg-secondary/10 border-border hover:bg-secondary/20 transition-colors">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Clock className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Duration</p>
                    <p className="text-muted-foreground">{additionalDetails.duration} per episode</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {additionalDetails.studio && (
              <Card className="bg-secondary/10 border-border hover:bg-secondary/20 transition-colors">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Award className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Studio</p>
                    <p className="text-muted-foreground">{additionalDetails.studio}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {additionalDetails.source && (
              <Card className="bg-secondary/10 border-border hover:bg-secondary/20 transition-colors">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Globe className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Source</p>
                    <p className="text-muted-foreground">{additionalDetails.source}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {additionalDetails.members && (
              <Card className="bg-secondary/10 border-border hover:bg-secondary/20 transition-colors">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Users className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Members</p>
                    <p className="text-muted-foreground">{additionalDetails.members?.toLocaleString()}</p>
                  </div>
                </CardContent>
              </Card>
            )}

            {additionalDetails.ranked && (
              <Card className="bg-secondary/10 border-border hover:bg-secondary/20 transition-colors">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 bg-primary/20 rounded-lg">
                    <Award className="w-5 h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-foreground">Ranked</p>
                    <p className="text-muted-foreground">#{additionalDetails.ranked}</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          <Separator className="my-6" />

          {/* Where to Watch */}
          <div className="space-y-4">
            <h3 className="text-xl font-semibold text-foreground flex items-center gap-2">
              <Play className="w-5 h-5" />
              Where to Watch
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {streamingSources.map((source, index) => (
                <Card 
                  key={index} 
                  className="cursor-pointer hover:shadow-lg transition-all duration-200 bg-gradient-to-r from-secondary/5 to-secondary/10 border-border hover:border-primary/50 hover:scale-[1.02]"
                  onClick={() => handleStreamingClick(source)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getSourceTypeColor(source.type)} shadow-sm`} />
                        <div>
                          <p className="font-medium text-foreground">{source.name}</p>
                          {source.region && (
                            <p className="text-xs text-muted-foreground">{source.region}</p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge 
                          variant="outline" 
                          className="text-xs capitalize border-primary/30"
                          style={{ 
                            backgroundColor: `${getSourceTypeColor(source.type)}20`,
                            borderColor: `${getSourceTypeColor(source.type)}50`
                          }}
                        >
                          {getSourceTypeLabel(source.type)}
                        </Badge>
                        <ExternalLink className="w-4 h-4 text-muted-foreground" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            <div className="bg-muted/20 rounded-lg p-3 border border-muted">
              <p className="text-xs text-muted-foreground flex items-center gap-2">
                <Globe className="w-3 h-3" />
                Availability may vary by region. Click to search on each platform. Links will open in a new tab.
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 pt-4">
            <Button 
              className={`flex-1 transition-all duration-200 ${
                isInFavorites 
                  ? 'bg-red-500 hover:bg-red-600 text-white' 
                  : 'bg-gradient-to-r from-pink-500 to-red-500 hover:from-pink-600 hover:to-red-600'
              }`}
              onClick={handleAddToFavorites}
            >
              <Heart className={`w-4 h-4 mr-2 ${isInFavorites ? 'fill-current' : ''}`} />
              {isInFavorites ? 'Remove from Favorites' : 'Add to Favorites'}
            </Button>
            
            <Button 
              variant={isInWatchlist ? "default" : "outline"}
              className={`flex-1 transition-all duration-200 ${
                isInWatchlist 
                  ? 'bg-blue-500 hover:bg-blue-600 text-white' 
                  : 'hover:bg-blue-500 hover:text-white'
              }`}
              onClick={handleAddToWatchlist}
            >
              <Clock className="w-4 h-4 mr-2" />
              {isInWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
            </Button>
          </div>

          {/* Additional Info Footer */}
          <div className="pt-4 border-t border-border">
            <div className="flex flex-wrap justify-between items-center gap-4 text-sm text-muted-foreground">
              <div className="flex items-center gap-4">
                {additionalDetails.popularity && (
                  <span>Popularity: #{additionalDetails.popularity}</span>
                )}
                {additionalDetails.year && additionalDetails.studio && (
                  <span>{additionalDetails.year} • {additionalDetails.studio}</span>
                )}
              </div>
              <div className="text-xs">
                Data provided by community databases
              </div>
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};