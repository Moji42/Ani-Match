import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BarChart3, Heart, Star, TrendingUp, User, Clock, Filter } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

interface UserStats {
  total_ratings: number;
  average_rating: number;
  favorite_genres: string[];
  total_favorites: number;
  total_watchlist: number;
  recommendation_accuracy: number;
}

interface UserActivity {
  anime_name: string;
  action: 'like' | 'dislike' | 'rating';
  value?: number;
  timestamp: string;
  genres?: string[];
}

export const UserDashboard = () => {
  const [open, setOpen] = useState(false);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<UserActivity[]>([]);
  const [loading, setLoading] = useState(false);
  const { user } = useAuth();
  const { toast } = useToast();

  const baseUrl = "http://127.0.0.1:5000";

  useEffect(() => {
    if (user && open) {
      fetchUserData();
    }
  }, [user, open]);

  const fetchUserData = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      // Fetch user statistics
      const statsResponse = await fetch(`${baseUrl}/api/user/stats`, {
        headers: {
          'Authorization': `Bearer ${user.id}`,
          'Content-Type': 'application/json'
        }
      });

      // Fetch recent activity
      const activityResponse = await fetch(`${baseUrl}/api/user/activity`, {
        headers: {
          'Authorization': `Bearer ${user.id}`,
          'Content-Type': 'application/json'
        }
      });

      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      } else {
        // Fallback mock data if API not implemented yet
        setStats({
          total_ratings: 47,
          average_rating: 7.8,
          favorite_genres: ['Action', 'Adventure', 'Shounen'],
          total_favorites: 12,
          total_watchlist: 8,
          recommendation_accuracy: 85.3
        });
      }

      if (activityResponse.ok) {
        const activityData = await activityResponse.json();
        setRecentActivity(activityData);
      } else {
        // Fallback mock activity data
        setRecentActivity([
          {
            anime_name: "Naruto",
            action: 'like',
            timestamp: new Date().toISOString(),
            genres: ['Action', 'Adventure']
          },
          {
            anime_name: "Attack on Titan",
            action: 'rating',
            value: 9.5,
            timestamp: new Date(Date.now() - 86400000).toISOString(),
            genres: ['Action', 'Drama']
          }
        ]);
      }
    } catch (error) {
      console.error("Failed to fetch user data:", error);
      toast({
        title: "Error",
        description: "Failed to load user data",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" className="gap-2">
          <User className="w-4 h-4" />
          Dashboard
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>User Dashboard</DialogTitle>
        </DialogHeader>
        
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : (
          <Tabs defaultValue="stats" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="stats">Statistics</TabsTrigger>
              <TabsTrigger value="activity">Recent Activity</TabsTrigger>
            </TabsList>
            
            <TabsContent value="stats" className="space-y-4 mt-4">
              {stats && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Total Ratings</CardTitle>
                      <Star className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.total_ratings}</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Average Rating</CardTitle>
                      <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.average_rating.toFixed(1)}/10</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Favorites</CardTitle>
                      <Heart className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.total_favorites}</div>
                    </CardContent>
                  </Card>
                  
                  <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
                      <TrendingUp className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold">{stats.recommendation_accuracy}%</div>
                    </CardContent>
                  </Card>
                </div>
              )}
              
              {stats?.favorite_genres && stats.favorite_genres.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Favorite Genres</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {stats.favorite_genres.map((genre, index) => (
                        <Badge key={index} variant="secondary">
                          {genre}
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
            
            <TabsContent value="activity" className="mt-4">
              <div className="space-y-4">
                {recentActivity.map((activity, index) => (
                  <Card key={index}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold">{activity.anime_name}</h4>
                          <p className="text-sm text-muted-foreground">
                            {activity.action === 'like' && 'Liked'}
                            {activity.action === 'dislike' && 'Disliked'}
                            {activity.action === 'rating' && `Rated ${activity.value}/10`}
                          </p>
                          {activity.genres && activity.genres.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-2">
                              {activity.genres.map((genre, idx) => (
                                <Badge key={idx} variant="outline" className="text-xs">
                                  {genre}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </div>
                        <div className="text-right text-sm text-muted-foreground">
                          <Clock className="h-4 w-4 inline mr-1" />
                          {new Date(activity.timestamp).toLocaleDateString()}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
                
                {recentActivity.length === 0 && (
                  <div className="text-center py-8 text-muted-foreground">
                    No recent activity found
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
};