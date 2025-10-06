import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Pill, Sparkles, Loader2 } from "lucide-react";
import { getRecommendations, RecommendationResponse } from "@/services/api";
import { useToast } from "@/hooks/use-toast";
import MedicineCard from "@/components/MedicineCard";

const MedicineRecommendation = () => {
  const [symptoms, setSymptoms] = useState("");
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleGetRecommendations = async () => {
    if (!symptoms.trim()) {
      toast({
        title: "Please enter your symptoms",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await getRecommendations(symptoms);
      setRecommendations(response);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get recommendations. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background py-12">
      <div className="container max-w-6xl">
        <div className="text-center mb-8">
          <Pill className="h-16 w-16 text-primary mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-foreground mb-2">Medicine Recommendations</h1>
          <p className="text-muted-foreground">Get personalized medicine suggestions based on your symptoms</p>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Describe Your Symptoms</CardTitle>
            <CardDescription>
              Our AI will analyze and recommend suitable medicines
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="E.g., I have a headache, fever, and body aches..."
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <Button 
              onClick={handleGetRecommendations} 
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Get Recommendations
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {recommendations && (
          <>
            <Card className="mb-6 bg-accent/5">
              <CardHeader>
                <CardTitle className="text-primary">AI Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-foreground leading-relaxed">{recommendations.reasoning}</p>
                
                <div className="mt-4 p-4 bg-muted rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    <strong>Backend Integration:</strong> Connect your recommendation model at <code className="text-primary">POST /api/recommendations/suggest</code>
                  </p>
                </div>
              </CardContent>
            </Card>

            <div className="mb-4">
              <h2 className="text-2xl font-bold text-foreground">Recommended Medicines</h2>
              <p className="text-sm text-muted-foreground mt-1">
                Based on your symptoms analysis
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {recommendations.medicines.map((medicine) => (
                <MedicineCard key={medicine.id} medicine={medicine} />
              ))}
            </div>
          </>
        )}

        {!recommendations && (
          <Card className="bg-muted/50">
            <CardContent className="py-12 text-center">
              <p className="text-muted-foreground">Enter your symptoms to get personalized recommendations</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MedicineRecommendation;
