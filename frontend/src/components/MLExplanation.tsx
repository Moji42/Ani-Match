import { Brain, Users, GitMerge, Shuffle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export const MLExplanation = () => {
  const methods = [
    {
      icon: Brain,
      title: "Content-Based Filtering",
      description: "Analyzes anime characteristics like genres, ratings, and popularity to find similar titles",
      details: "Uses cosine similarity on genre vectors, normalized ratings, and member counts with weighted features (50% genre, 30% rating, 20% popularity)"
    },
    {
      icon: Users,
      title: "Collaborative Filtering",
      description: "Leverages user behavior patterns to recommend anime liked by similar users",
      details: "Employs SVD matrix factorization with 50 factors, learning rate 0.003, and regularization 0.05 to predict your ratings"
    },
    {
      icon: GitMerge,
      title: "Hybrid Approach",
      description: "Combines both methods using smart weighting and genre similarity bonuses",
      details: "Merges content (60%) and collaborative (40%) scores with percentile normalization and ensures diverse recommendations"
    },
    {
      icon: Shuffle,
      title: "Random Discovery",
      description: "Explores the full database for serendipitous discoveries",
      details: "Samples from 12,000+ anime without replacement to help you discover hidden gems outside your usual preferences"
    }
  ];

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h2 className="text-3xl font-bold text-foreground">How Our AI Recommendation Engine Works</h2>
        <p className="text-lg text-muted-foreground max-w-3xl mx-auto">
          Our system uses advanced machine learning algorithms to analyze anime characteristics, user preferences, 
          and viewing patterns to deliver personalized recommendations tailored just for you.
        </p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {methods.map((method, index) => (
          <Card key={index} className="bg-gradient-card border-border hover:shadow-glow transition-all duration-300 group">
            <CardHeader className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-gradient-primary rounded-xl shadow-glow group-hover:scale-110 transition-transform duration-300">
                  <method.icon className="w-6 h-6 text-primary-foreground" />
                </div>
                <CardTitle className="text-xl text-foreground group-hover:text-primary-glow transition-colors duration-300">
                  {method.title}
                </CardTitle>
              </div>
              <CardDescription className="text-muted-foreground leading-relaxed">
                {method.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-muted/30 rounded-lg border border-border">
                <p className="text-sm text-foreground/80 leading-relaxed">
                  <span className="font-medium text-accent">Technical Details:</span> {method.details}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
      
      <div className="bg-gradient-secondary rounded-xl p-8 border border-border">
        <div className="text-center space-y-4">
          <h3 className="text-xl font-semibold text-foreground">Dataset & Performance</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">12,232</div>
              <div className="text-sm text-muted-foreground">Anime Titles</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">SVD</div>
              <div className="text-sm text-muted-foreground">Matrix Factorization</div>
            </div>
            <div className="space-y-2">
              <div className="text-2xl font-bold text-primary">300ms</div>
              <div className="text-sm text-muted-foreground">Avg Response Time</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};