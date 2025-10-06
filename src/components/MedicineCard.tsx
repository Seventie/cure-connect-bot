import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Medicine } from "@/services/api";

interface MedicineCardProps {
  medicine: Medicine;
}

const MedicineCard = ({ medicine }: MedicineCardProps) => {
  return (
    <Card className="hover:shadow-lg transition-shadow">
      <CardHeader>
        <CardTitle className="text-primary">{medicine.name}</CardTitle>
        <CardDescription>{medicine.condition}</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-1">Usage</h4>
          <p className="text-sm text-muted-foreground">{medicine.usage}</p>
        </div>
        
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-1">Dosage</h4>
          <p className="text-sm text-muted-foreground">{medicine.dosage}</p>
        </div>
        
        <div>
          <h4 className="text-sm font-semibold text-foreground mb-2">Side Effects</h4>
          <div className="flex flex-wrap gap-2">
            {medicine.sideEffects.map((effect, idx) => (
              <Badge key={idx} variant="secondary" className="text-xs">
                {effect}
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MedicineCard;
