import { useState, useEffect } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Brain, Network, Sparkles } from "lucide-react";
import {
  getNEREntities,
  getKnowledgeGraph,
  getEmbeddings,
  NEREntity,
  KnowledgeGraphData,
  EmbeddingPoint,
} from "@/services/api";

const Visualizations = () => {
  const [nerEntities, setNerEntities] = useState<NEREntity[]>([]);
  const [knowledgeGraph, setKnowledgeGraph] = useState<KnowledgeGraphData | null>(null);
  const [embeddings, setEmbeddings] = useState<EmbeddingPoint[]>([]);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadVisualizationData();
  }, []);

  const loadVisualizationData = async () => {
    setIsLoading(true);
    try {
      const [ner, kg, emb] = await Promise.all([
        getNEREntities(),
        getKnowledgeGraph(),
        getEmbeddings(),
      ]);
      setNerEntities(ner);
      setKnowledgeGraph(kg);
      setEmbeddings(emb);
    } catch (error) {
      console.error("Error loading visualization data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getNodeColor = (type: string) => {
    switch (type) {
      case "drug":
        return "bg-primary text-primary-foreground";
      case "condition":
        return "bg-accent text-accent-foreground";
      case "side_effect":
        return "bg-destructive/20 text-destructive";
      default:
        return "bg-muted text-muted-foreground";
    }
  };

  const getLabelColor = (label: string) => {
    switch (label) {
      case "DRUG":
        return "bg-primary";
      case "SYMPTOM":
        return "bg-accent";
      case "SIDE_EFFECT":
        return "bg-destructive/80";
      default:
        return "bg-muted";
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background py-12">
      <div className="container max-w-7xl">
        <div className="text-center mb-8">
          <Brain className="h-16 w-16 text-primary mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-foreground mb-2">Data Visualizations</h1>
          <p className="text-muted-foreground">
            Explore NER outputs, Knowledge Graphs, and semantic embeddings
          </p>
        </div>

        <Tabs defaultValue="ner" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="ner">Named Entity Recognition</TabsTrigger>
            <TabsTrigger value="kg">Knowledge Graph</TabsTrigger>
            <TabsTrigger value="embeddings">Embeddings</TabsTrigger>
          </TabsList>

          {/* NER Tab */}
          <TabsContent value="ner">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  Named Entity Recognition Results
                </CardTitle>
                <CardDescription>
                  Extracted medical entities from the MedQuAD dataset
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-muted-foreground text-center py-8">Loading NER data...</p>
                ) : (
                  <>
                    <div className="space-y-4">
                      {nerEntities.map((entity, idx) => (
                        <div
                          key={idx}
                          className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex-1">
                            <p className="font-medium text-foreground">{entity.text}</p>
                            <p className="text-sm text-muted-foreground">
                              Position: {entity.start} - {entity.end}
                            </p>
                          </div>
                          <Badge className={getLabelColor(entity.label)}>{entity.label}</Badge>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        <strong>Backend Integration:</strong> Connect your NER model output at{" "}
                        <code className="text-primary">GET /api/visualizations/ner</code>
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Knowledge Graph Tab */}
          <TabsContent value="kg">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Network className="h-5 w-5" />
                  Medical Knowledge Graph
                </CardTitle>
                <CardDescription>
                  Relationships between drugs, conditions, and side effects
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading || !knowledgeGraph ? (
                  <p className="text-muted-foreground text-center py-8">
                    Loading knowledge graph...
                  </p>
                ) : (
                  <>
                    <div className="grid md:grid-cols-2 gap-6">
                      {/* Nodes */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4 text-foreground">Entities</h3>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {knowledgeGraph.nodes.map((node) => (
                            <button
                              key={node.id}
                              onClick={() => setSelectedNode(node.id)}
                              className={`w-full text-left p-3 rounded-lg border transition-all ${
                                selectedNode === node.id
                                  ? "border-primary bg-primary/10"
                                  : "border-border hover:bg-muted/50"
                              }`}
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-foreground">{node.label}</span>
                                <Badge className={getNodeColor(node.type)} variant="secondary">
                                  {node.type}
                                </Badge>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Relationships */}
                      <div>
                        <h3 className="text-lg font-semibold mb-4 text-foreground">
                          Relationships
                        </h3>
                        <div className="space-y-2 max-h-96 overflow-y-auto">
                          {knowledgeGraph.edges
                            .filter(
                              (edge) =>
                                !selectedNode ||
                                edge.source === selectedNode ||
                                edge.target === selectedNode
                            )
                            .map((edge, idx) => {
                              const sourceNode = knowledgeGraph.nodes.find(
                                (n) => n.id === edge.source
                              );
                              const targetNode = knowledgeGraph.nodes.find(
                                (n) => n.id === edge.target
                              );
                              return (
                                <div
                                  key={idx}
                                  className="p-3 border rounded-lg bg-card hover:bg-muted/50 transition-colors"
                                >
                                  <div className="flex items-center gap-2 text-sm">
                                    <span className="font-medium text-foreground">
                                      {sourceNode?.label}
                                    </span>
                                    <Badge variant="outline" className="text-xs">
                                      {edge.relation}
                                    </Badge>
                                    <span className="font-medium text-foreground">
                                      {targetNode?.label}
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                        </div>
                      </div>
                    </div>

                    <div className="mt-6 p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        <strong>Backend Integration:</strong> Load your knowledge graph data at{" "}
                        <code className="text-primary">GET /api/visualizations/kg</code>
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Embeddings Tab */}
          <TabsContent value="embeddings">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Brain className="h-5 w-5" />
                  Semantic Embeddings Visualization
                </CardTitle>
                <CardDescription>
                  2D projection of medicine embeddings showing semantic similarity
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <p className="text-muted-foreground text-center py-8">
                    Loading embeddings data...
                  </p>
                ) : (
                  <>
                    {/* Simple scatter plot visualization */}
                    <div className="relative w-full h-96 border rounded-lg bg-muted/30 overflow-hidden">
                      <svg className="w-full h-full">
                        {/* Grid lines */}
                        <line
                          x1="0"
                          y1="50%"
                          x2="100%"
                          y2="50%"
                          stroke="currentColor"
                          strokeOpacity="0.1"
                        />
                        <line
                          x1="50%"
                          y1="0"
                          x2="50%"
                          y2="100%"
                          stroke="currentColor"
                          strokeOpacity="0.1"
                        />

                        {/* Data points */}
                        {embeddings.map((point) => (
                          <g key={point.id}>
                            <circle
                              cx={`${point.x}%`}
                              cy={`${point.y}%`}
                              r="6"
                              className="fill-primary hover:fill-primary/80 cursor-pointer transition-all"
                              strokeWidth="2"
                              stroke="currentColor"
                            />
                            <text
                              x={`${point.x}%`}
                              y={`${point.y}%`}
                              dy="-12"
                              textAnchor="middle"
                              className="text-xs fill-foreground pointer-events-none"
                            >
                              {point.name}
                            </text>
                          </g>
                        ))}
                      </svg>
                    </div>

                    {/* Legend */}
                    <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Array.from(new Set(embeddings.map((e) => e.category))).map((category) => (
                        <div key={category} className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full bg-primary" />
                          <span className="text-sm text-foreground">{category}</span>
                        </div>
                      ))}
                    </div>

                    <div className="mt-6 p-4 bg-muted rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        <strong>Backend Integration:</strong> Load your precomputed embeddings
                        (.npy files) at{" "}
                        <code className="text-primary">GET /api/visualizations/embeddings</code>
                      </p>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Technical Info Card */}
        <Card className="mt-6 bg-muted/50">
          <CardContent className="py-6">
            <h3 className="font-semibold text-foreground mb-2">Data Sources</h3>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>• NER: Extracted from MedQuAD processed dataset</li>
              <li>• Knowledge Graph: Built from drugs-side-effects dataset relationships</li>
              <li>• Embeddings: Precomputed using sentence transformers (encoded_docs.npy)</li>
              <li>• FAISS Index: Available for similarity search (faiss.index)</li>
            </ul>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Visualizations;
