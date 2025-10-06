import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Activity, Brain, Pill, Search } from "lucide-react";
import { Link } from "react-router-dom";

const Home = () => {
  const features = [
    {
      icon: Brain,
      title: "Medical Q&A Bot",
      description: "Ask medical questions and get answers powered by RAG-based AI model trained on MedQuAD dataset",
      link: "/medical-qa",
    },
    {
      icon: Search,
      title: "Medicine Search",
      description: "Search and filter medicines based on conditions, causes, and side effects",
      link: "/medicine-search",
    },
    {
      icon: Pill,
      title: "Medicine Recommendations",
      description: "Get personalized medicine recommendations based on your symptoms",
      link: "/recommendations",
    },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background">
      <div className="container mx-auto px-4 py-16">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <div className="flex justify-center mb-6">
            <Activity className="h-20 w-20 text-primary" />
          </div>
          <h1 className="text-5xl font-bold text-foreground mb-4">
            Medical AI Assistant
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
            Advanced NLP-powered medical information system with RAG-based Q&A and intelligent medicine recommendations
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {features.map((feature, idx) => {
            const Icon = feature.icon;
            return (
              <Card key={idx} className="hover:shadow-xl transition-all hover:-translate-y-1">
                <CardHeader>
                  <Icon className="h-12 w-12 text-primary mb-4" />
                  <CardTitle>{feature.title}</CardTitle>
                  <CardDescription>{feature.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Link to={feature.link}>
                    <Button className="w-full">Explore</Button>
                  </Link>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* About Section */}
        <Card className="bg-card/80 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-2xl">About This Project</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Datasets Used</h3>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li><strong>MedQuAD:</strong> Medical Question Answering Dataset for RAG-based Q&A system</li>
                <li><strong>Drugs Side Effects Dataset:</strong> Comprehensive medicine information for search and recommendations</li>
              </ul>
            </div>
            
            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">AI Models</h3>
              <ul className="list-disc list-inside space-y-1 text-muted-foreground">
                <li><strong>RAG Medical QA Model:</strong> Retrieval-Augmented Generation for accurate medical answers</li>
                <li><strong>Medicine Recommendation System:</strong> ML-based recommendation engine for personalized suggestions</li>
              </ul>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-foreground mb-2">Technical Stack</h3>
              <div className="flex flex-wrap gap-2">
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">React</span>
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">TypeScript</span>
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">NLP</span>
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">RAG</span>
                <span className="px-3 py-1 bg-primary/10 text-primary rounded-full text-sm">Machine Learning</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Home;
