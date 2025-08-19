// Frontend/src/components/SearchSection.tsx
import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Shuffle, Sparkles, Filter } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface SearchSectionProps {
  onSearch: (title: string, userId: string, method: string, count: number, type: string) => void;
  onRandomSearch: (count: number, type: string) => void;
  loading: boolean;
}

interface AnimeType {
  value: string;
  label: string;
}

// Default anime types - will be replaced by API data when available
const defaultAnimeTypes: AnimeType[] = [
  { value: "all", label: "All Types" },
  { value: "tv", label: "TV Series" },
  { value: "movie", label: "Movie" },
  { value: "ova", label: "OVA" },
  { value: "ona", label: "ONA" },
  { value: "special", label: "Special" },
  { value: "music", label: "Music" },
];

export const SearchSection = ({ onSearch, onRandomSearch, loading }: SearchSectionProps) => {
  const [title, setTitle] = useState("");
  const [userId, setUserId] = useState("");
  const [method, setMethod] = useState("content");
  const [count, setCount] = useState(8);
  const [selectedType, setSelectedType] = useState("all");
  const [availableTypes, setAvailableTypes] = useState<AnimeType[]>(defaultAnimeTypes);
  const [typesLoading, setTypesLoading] = useState(false);
  const { toast } = useToast();

  const baseUrl = "http://127.0.0.1:5000";

  // Fetch available anime types from the API
  useEffect(() => {
    const fetchAvailableTypes = async () => {
      setTypesLoading(true);
      try {
        const response = await fetch(`${baseUrl}/api/types`);
        if (response.ok) {
          const data = await response.json();
          const formattedTypes: AnimeType[] = [
            { value: "all", label: "All Types" },
            ...data.types.map((type: string) => ({
              value: type.toLowerCase(),
              label: type
            }))
          ];
          setAvailableTypes(formattedTypes);
        } else {
          console.warn("Failed to fetch anime types, using defaults");
        }
      } catch (error) {
        console.warn("Error fetching anime types:", error);
        // Keep default types if API fails
      } finally {
        setTypesLoading(false);
      }
    };

    fetchAvailableTypes();
  }, [baseUrl]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() && method !== "collab") return;
    
    // Pass the type parameter along with other parameters
    onSearch(title, userId, method, count, selectedType);
  };

  const handleRandomSearch = () => {
    // Pass the type parameter to random search
    onRandomSearch(count, selectedType);
  };

  const handleMethodChange = (value: string) => {
    setMethod(value);
  };

  const handleCountChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = Math.min(20, Math.max(1, Number(e.target.value) || 8));
    setCount(value);
  };

  const handleTypeChange = (value: string) => {
    setSelectedType(value);
    
    // Show toast for type selection
    const selectedTypeLabel = availableTypes.find(t => t.value === value)?.label || value;
    if (value !== "all") {
      toast({
        title: "Filter Applied",
        description: `Filtering by ${selectedTypeLabel}`,
      });
    }
  };

  const getMethodDescription = (method: string) => {
    switch (method) {
      case "content":
        return "Find anime similar to your input based on genres, ratings, and characteristics";
      case "collab":
        return "Get recommendations based on users with similar taste to yours";
      case "hybrid":
        return "Combine both approaches for the most accurate recommendations";
      default:
        return "";
    }
  };

  return (
    <div className="bg-gradient-card backdrop-blur-sm border border-border rounded-xl p-10 shadow-elegant">
      <div className="flex items-center gap-4 mb-8">
        <div className="p-3 bg-gradient-primary rounded-lg">
          <Sparkles className="w-7 h-7 text-primary-foreground" />
        </div>
        <h2 className="text-3xl font-bold text-foreground">Discover Your Next Favorite Anime</h2>
      </div>

      <form onSubmit={handleSearch} className="space-y-8">
        <Tabs value={method} onValueChange={handleMethodChange} className="w-full">
          <TabsList className="grid w-full grid-cols-3 bg-secondary">
            <TabsTrigger value="content" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              Content-Based
            </TabsTrigger>
            <TabsTrigger value="collab" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              Collaborative
            </TabsTrigger>
            <TabsTrigger value="hybrid" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
              Hybrid
            </TabsTrigger>
          </TabsList>
          
          {/* Method description */}
          <div className="mt-4 p-4 bg-secondary/20 rounded-lg border border-secondary/30">
            <p className="text-sm text-muted-foreground">
              {getMethodDescription(method)}
            </p>
          </div>
        </Tabs>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="space-y-2">
            <Label htmlFor="anime-title" className="text-foreground font-medium">
              Anime Title {method !== "collab" && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id="anime-title"
              type="text"
              placeholder="e.g., Naruto, One Piece, Attack on Titan..."
              className="bg-input border-border text-foreground placeholder:text-muted-foreground"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required={method !== "collab"}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-id" className="text-foreground font-medium">
              User ID {method === "collab" && <span className="text-destructive">*</span>}
              {method === "hybrid" && <span className="text-destructive">*</span>}
            </Label>
            <Input
              id="user-id"
              type="number"
              placeholder="Enter user ID..."
              className="bg-input border-border text-foreground placeholder:text-muted-foreground"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              required={method === "collab" || method === "hybrid"}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="anime-type" className="text-foreground font-medium flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Anime Type
            </Label>
            <Select value={selectedType} onValueChange={handleTypeChange} disabled={typesLoading}>
              <SelectTrigger className="bg-input border-border text-foreground">
                <SelectValue placeholder={typesLoading ? "Loading types..." : "Select type"} />
              </SelectTrigger>
              <SelectContent className="bg-popover border-border">
                {availableTypes.map((type) => (
                  <SelectItem key={type.value} value={type.value} className="text-foreground hover:bg-accent">
                    {type.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Filter results by anime type (TV, Movie, OVA, etc.)
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="recommendation-count" className="text-foreground font-medium">
              Number of Recommendations
            </Label>
            <Input
              id="recommendation-count"
              type="number"
              min="1"
              max="20"
              value={count}
              onChange={handleCountChange}
              className="bg-input border-border text-foreground"
            />
            <p className="text-xs text-muted-foreground">
              Choose between 1-20 recommendations (default: 8)
            </p>
          </div>

          <div className="space-y-2">
            <Label className="text-foreground font-medium">Current Filters</Label>
            <div className="flex flex-wrap gap-2 p-3 bg-secondary/10 rounded-lg border border-secondary/30 min-h-[42px] items-center">
              {selectedType !== "all" && (
                <span className="inline-flex items-center gap-1 px-2 py-1 bg-primary/20 text-primary rounded-md text-xs">
                  <Filter className="w-3 h-3" />
                  {availableTypes.find(t => t.value === selectedType)?.label}
                </span>
              )}
              {selectedType === "all" && (
                <span className="text-xs text-muted-foreground">No filters applied</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex gap-6 flex-wrap">
          <Button
            type="submit"
            className="bg-gradient-primary hover:opacity-90 shadow-glow flex items-center gap-2 flex-1 md:flex-none"
            disabled={loading}
          >
            <Search className="w-4 h-4" />
            {loading ? "Searching..." : "Get Recommendations"}
          </Button>

          <Button
            type="button"
            variant="outline"
            onClick={handleRandomSearch}
            disabled={loading}
            className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
          >
            <Shuffle className="w-4 h-4" />
            Random Picks
            {selectedType !== "all" && (
              <span className="ml-1 px-2 py-0.5 bg-primary/20 text-primary rounded text-xs">
                {availableTypes.find(t => t.value === selectedType)?.label}
              </span>
            )}
          </Button>
        </div>

        {/* Filter Summary */}
        {selectedType !== "all" && (
          <div className="bg-accent/10 border border-accent/30 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <Filter className="w-4 h-4 text-accent" />
              <span className="text-sm font-medium text-accent">Active Filter</span>
            </div>
            <p className="text-sm text-muted-foreground">
              Showing only <strong>{availableTypes.find(t => t.value === selectedType)?.label}</strong> anime.
              Select "All Types" to remove this filter.
            </p>
          </div>
        )}
      </form>
    </div>
  );
};