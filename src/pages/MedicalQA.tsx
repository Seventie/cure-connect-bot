import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Brain, Send, Loader2 } from "lucide-react";
import { askMedicalQuestion, QAResponse } from "@/services/api";
import { useToast } from "@/hooks/use-toast";

const MedicalQA = () => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<QAResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

  const handleAskQuestion = async () => {
    if (!question.trim()) {
      toast({
        title: "Please enter a question",
        variant: "destructive",
      });
      return;
    }

    setIsLoading(true);
    try {
      const response = await askMedicalQuestion(question);
      setAnswer(response);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to get answer. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background py-12">
      <div className="container max-w-4xl">
        <div className="text-center mb-8">
          <Brain className="h-16 w-16 text-primary mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-foreground mb-2">Medical Q&A Assistant</h1>
          <p className="text-muted-foreground">Ask any medical question and get AI-powered answers</p>
        </div>

        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Ask Your Question</CardTitle>
            <CardDescription>
              Powered by RAG-based model trained on MedQuAD dataset
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Textarea
              placeholder="E.g., What are the symptoms of diabetes?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={4}
              className="resize-none"
            />
            <Button 
              onClick={handleAskQuestion} 
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Send className="mr-2 h-4 w-4" />
                  Ask Question
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        {answer && (
          <Card className="bg-accent/5">
            <CardHeader>
              <CardTitle className="text-primary">Answer</CardTitle>
              <CardDescription>
                Confidence: {(answer.confidence * 100).toFixed(0)}%
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-foreground leading-relaxed">{answer.answer}</p>
              
              <div className="mt-6 p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">
                  <strong>Backend Integration:</strong> Connect your RAG model at <code className="text-primary">POST /api/qa/ask</code>
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {!answer && (
          <Card className="bg-muted/50">
            <CardContent className="py-8 text-center">
              <p className="text-muted-foreground">Your answer will appear here</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
};

export default MedicalQA;
