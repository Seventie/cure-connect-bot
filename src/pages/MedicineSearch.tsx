import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search } from "lucide-react";
import { searchMedicines, Medicine } from "@/services/api";
import MedicineCard from "@/components/MedicineCard";

const MedicineSearch = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [medicines, setMedicines] = useState<Medicine[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    loadMedicines();
  }, []);

  const loadMedicines = async (query?: string) => {
    setIsLoading(true);
    try {
      const results = await searchMedicines(query || "");
      setMedicines(results);
    } catch (error) {
      console.error("Error loading medicines:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    setSearchQuery(value);
    loadMedicines(value);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-secondary/20 to-background py-12">
      <div className="container">
        <div className="text-center mb-8">
          <Search className="h-16 w-16 text-primary mx-auto mb-4" />
          <h1 className="text-4xl font-bold text-foreground mb-2">Medicine Search</h1>
          <p className="text-muted-foreground">Search medicines by name, condition, or side effects</p>
        </div>

        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Search Database</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground h-4 w-4" />
              <Input
                placeholder="Search by medicine name or condition..."
                value={searchQuery}
                onChange={(e) => handleSearch(e.target.value)}
                className="pl-10"
              />
            </div>
          </CardContent>
        </Card>

        {isLoading ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground">Loading medicines...</p>
          </div>
        ) : (
          <>
            <div className="mb-4">
              <p className="text-sm text-muted-foreground">
                Found {medicines.length} medicine(s)
              </p>
            </div>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {medicines.map((medicine) => (
                <MedicineCard key={medicine.id} medicine={medicine} />
              ))}
            </div>

            {medicines.length === 0 && (
              <Card className="bg-muted/50">
                <CardContent className="py-12 text-center">
                  <p className="text-muted-foreground">No medicines found. Try a different search.</p>
                </CardContent>
              </Card>
            )}
          </>
        )}

        <Card className="mt-8 bg-muted/50">
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">
              <strong>Backend Integration:</strong> Connect your drugs dataset at <code className="text-primary">GET /api/medicines/search</code>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default MedicineSearch;
