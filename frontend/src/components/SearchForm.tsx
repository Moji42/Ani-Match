import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, Sparkles, Users, Zap, Shuffle } from "lucide-react";
import { LoadingSpinner } from "@/components/ui/loading-spinner";


interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
  isLoading: boolean;
  error?: string | null;
}

export interface SearchParams {
  type: 'content' | 'collaborative' | 'hybrid' | 'random';
  title?: string;
  userId?: string;
  count: string;
}

export const SearchForm = ({ onSearch, isLoading, error }: SearchFormProps) => {
  const [formData, setFormData] = useState<SearchParams>({
    type: 'content',
    title: '',
    userId: '',
    count: '5'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (formData.type === 'collaborative' && !formData.userId) {
      return;
    }

    onSearch(formData);
  };

  const handleRandomClick = () => {
    onSearch({ type: 'random', count: formData.count });
  };

  return (
    <Card className="p-6 space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold">Find Your Next Anime</h2>
        <p className="text-muted-foreground">
          Choose your recommendation type and discover amazing anime
        </p>
      </div>

      <div className="text-center space-y-4 p-4 rounded-lg bg-secondary/10">
        <Button 
          onClick={handleRandomClick}
          disabled={isLoading}
          size="lg"
        >
          {isLoading ? <LoadingSpinner className="mr-2" /> : <Shuffle className="mr-2" />}
          Get Random Anime
        </Button>
      </div>

      <Tabs 
        value={formData.type} 
        onValueChange={(type) => setFormData(prev => ({ ...prev, type: type as SearchParams['type'] }))}
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="content">
            <Sparkles className="w-4 h-4 mr-2" />
            Content
          </TabsTrigger>
          <TabsTrigger value="collaborative">
            <Users className="w-4 h-4 mr-2" />
            Collaborative
          </TabsTrigger>
          <TabsTrigger value="hybrid">
            <Zap className="w-4 h-4 mr-2" />
            Hybrid
          </TabsTrigger>
        </TabsList>

        <form onSubmit={handleSubmit} className="space-y-4 mt-4">
          <TabsContent value="content" className="space-y-4">
            <div className="space-y-2">
              <Label>Anime Title</Label>
              <Input
                placeholder="e.g., Naruto"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                required
              />
            </div>
          </TabsContent>

          <TabsContent value="collaborative" className="space-y-4">
            <div className="space-y-2">
              <Label>User ID</Label>
              <Input
                type="number"
                min="1"
                placeholder="Enter user ID (1, 2, or 3)"
                value={formData.userId}
                onChange={(e) => setFormData(prev => ({ ...prev, userId: e.target.value }))}
                required
              />
            </div>
          </TabsContent>

          <TabsContent value="hybrid" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label>Anime Title</Label>
                <Input
                  placeholder="e.g., Naruto"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label>User ID</Label>
                <Input
                  type="number"
                  min="1"
                  placeholder="Enter user ID"
                  value={formData.userId}
                  onChange={(e) => setFormData(prev => ({ ...prev, userId: e.target.value }))}
                  required
                />
              </div>
            </div>
          </TabsContent>

          <div className="grid gap-4 grid-cols-2">
            <div className="space-y-2">
              <Label>Number of Recommendations</Label>
              <Input
                type="number"
                min="1"
                max="20"
                value={formData.count}
                onChange={(e) => setFormData(prev => ({ ...prev, count: e.target.value }))}
              />
            </div>
            <div className="flex items-end">
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? <LoadingSpinner className="mr-2" /> : <Search className="mr-2" />}
                Get Recommendations
              </Button>
            </div>
          </div>
        </form>
      </Tabs>

      {error && (
        <div className="text-red-500 text-sm mt-2">
          {error}
        </div>
      )}
    </Card>
  );
};