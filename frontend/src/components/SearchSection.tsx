import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Shuffle, Sparkles } from "lucide-react";

interface SearchSectionProps {
  onSearch: (title: string, userId: string, method: string) => void;
  onRandomSearch: () => void;
  loading: boolean;
}

export const SearchSection = ({ onSearch, onRandomSearch, loading }: SearchSectionProps) => {
  const [title, setTitle] = useState("");
  const [userId, setUserId] = useState("");
  const [method, setMethod] = useState("content");

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() && method !== "collab") return;
    onSearch(title, userId, method);
  };

  const handleMethodChange = (value: string) => {
    setMethod(value);
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
        </Tabs>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
            onClick={onRandomSearch}
            disabled={loading}
            className="flex items-center gap-2 hover:bg-accent hover:text-accent-foreground"
          >
            <Shuffle className="w-4 h-4" />
            Random Picks
          </Button>
        </div>
      </form>
    </div>
  );
};