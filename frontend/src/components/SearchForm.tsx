import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Sparkles, Users, Zap } from "lucide-react";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
  isLoading: boolean;
}

export interface SearchParams {
  type: 'content' | 'collaborative' | 'hybrid';
  title?: string;
  userId?: string;
  count: string;
}

export const SearchForm = ({ onSearch, isLoading }: SearchFormProps) => {
  const [formData, setFormData] = useState<SearchParams>({
    type: 'content',
    title: '',
    userId: '',
    count: '5'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validation
    if (formData.type === 'content' && !formData.title?.trim()) {
      return;
    }
    if (formData.type === 'collaborative' && !formData.userId?.trim()) {
      return;
    }
    if (formData.type === 'hybrid' && (!formData.title?.trim() || !formData.userId?.trim())) {
      return;
    }

    onSearch(formData);
  };

  const getTabIcon = (type: string) => {
    switch (type) {
      case 'content': return <Sparkles className="w-4 h-4" />;
      case 'collaborative': return <Users className="w-4 h-4" />;
      case 'hybrid': return <Zap className="w-4 h-4" />;
      default: return null;
    }
  };

  return (
    <Card className="anime-card">
      <div className="space-y-6">
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold gradient-text">Find Your Next Anime</h2>
          <p className="text-muted-foreground">
            Choose your recommendation type and discover amazing anime
          </p>
        </div>

        <Tabs 
          value={formData.type} 
          onValueChange={(value) => setFormData(prev => ({ 
            ...prev, 
            type: value as SearchParams['type'] 
          }))}
        >
          <TabsList className="grid w-full grid-cols-3 bg-muted/20">
            <TabsTrigger value="content" className="flex items-center gap-2">
              {getTabIcon('content')}
              Content
            </TabsTrigger>
            <TabsTrigger value="collaborative" className="flex items-center gap-2">
              {getTabIcon('collaborative')}
              Collaborative
            </TabsTrigger>
            <TabsTrigger value="hybrid" className="flex items-center gap-2">
              {getTabIcon('hybrid')}
              Hybrid
            </TabsTrigger>
          </TabsList>

          <form onSubmit={handleSubmit} className="space-y-4">
            <TabsContent value="content" className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="title">Anime Title</Label>
                <Input
                  id="title"
                  placeholder="e.g., Naruto, One Piece, Attack on Titan..."
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="anime-input"
                  required
                />
              </div>
            </TabsContent>

            <TabsContent value="collaborative" className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="userId">User ID</Label>
                <Input
                  id="userId"
                  type="number"
                  placeholder="Enter your user ID..."
                  value={formData.userId}
                  onChange={(e) => setFormData(prev => ({ ...prev, userId: e.target.value }))}
                  className="anime-input"
                  required
                />
              </div>
            </TabsContent>

            <TabsContent value="hybrid" className="space-y-4 mt-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="hybrid-title">Anime Title</Label>
                  <Input
                    id="hybrid-title"
                    placeholder="e.g., Naruto..."
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    className="anime-input"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="hybrid-userId">User ID</Label>
                  <Input
                    id="hybrid-userId"
                    type="number"
                    placeholder="Your user ID..."
                    value={formData.userId}
                    onChange={(e) => setFormData(prev => ({ ...prev, userId: e.target.value }))}
                    className="anime-input"
                    required
                  />
                </div>
              </div>
            </TabsContent>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="count">Number of Recommendations</Label>
                <Input
                  id="count"
                  type="number"
                  min="1"
                  max="20"
                  value={formData.count}
                  onChange={(e) => setFormData(prev => ({ ...prev, count: e.target.value }))}
                  className="anime-input"
                />
              </div>
              <div className="flex items-end">
                <Button 
                  type="submit" 
                  className="w-full gradient-button" 
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <LoadingSpinner size="sm" className="mr-2" />
                  ) : (
                    <Search className="w-4 h-4 mr-2" />
                  )}
                  {isLoading ? 'Searching...' : 'Get Recommendations'}
                </Button>
              </div>
            </div>
          </form>
        </Tabs>
      </div>
    </Card>
  );
};