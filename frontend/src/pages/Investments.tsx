import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { TrendingUp, ExternalLink, Lightbulb } from "lucide-react";

const Investments = () => {
  const suggestions = [
    {
      section: "80C",
      title: "Maximize Tax-Saving Investments",
      amount: "₹1,50,000",
      saving: "₹45,000",
      description: "Invest in ELSS mutual funds, PPF, or NPS to claim maximum deduction",
      recommendations: [
        "ELSS Mutual Funds: ₹75,000 (Lock-in: 3 years, High returns)",
        "Public Provident Fund: ₹50,000 (Lock-in: 15 years, Safe)",
        "Life Insurance Premium: ₹25,000"
      ],
      priority: "high"
    },
    {
      section: "80D",
      title: "Health Insurance Premium",
      amount: "₹50,000",
      saving: "₹15,000",
      description: "Purchase health insurance for self and parents to maximize deduction",
      recommendations: [
        "Self & Family: ₹25,000 (under 60 years)",
        "Parents: ₹25,000 (under 60) or ₹50,000 (above 60)",
        "Preventive health check-up: ₹5,000 (included in limit)"
      ],
      priority: "high"
    },
    {
      section: "80CCD(1B)",
      title: "Additional NPS Contribution",
      amount: "₹50,000",
      saving: "₹15,000",
      description: "Extra deduction over and above ₹1.5L under 80C",
      recommendations: [
        "National Pension System Tier I account",
        "Long-term retirement planning benefit",
        "Partial withdrawal after 3 years"
      ],
      priority: "medium"
    },
    {
      section: "HRA",
      title: "House Rent Allowance",
      amount: "Optimize",
      saving: "Variable",
      description: "Claim HRA exemption if living in a rented accommodation",
      recommendations: [
        "Keep rent receipts and rental agreement",
        "HRA exemption is least of: Actual HRA, 50% of salary (metro) or 40% (non-metro), Rent paid minus 10% of salary",
        "Cannot claim both HRA and home loan deduction for same property"
      ],
      priority: "medium"
    },
    {
      section: "24(b)",
      title: "Home Loan Interest",
      amount: "₹2,00,000",
      saving: "₹60,000",
      description: "Deduction on interest paid for self-occupied property",
      recommendations: [
        "Maximum deduction: ₹2 lakh per year",
        "Keep home loan interest certificate from bank",
        "Additional ₹1.5 lakh for first-time home buyers under 80EEA"
      ],
      priority: "low"
    },
    {
      section: "80E",
      title: "Education Loan Interest",
      amount: "No Limit",
      saving: "Variable",
      description: "Interest on education loan is fully deductible",
      recommendations: [
        "Loan must be for higher education",
        "Deduction available for 8 years or until interest is paid, whichever is earlier",
        "No upper limit on deduction amount"
      ],
      priority: "low"
    }
  ];

  const getPriorityColor = (priority: string) => {
    switch(priority) {
      case "high": return "bg-destructive/10 text-destructive border-destructive/20";
      case "medium": return "bg-warning/10 text-warning border-warning/20";
      case "low": return "bg-primary/10 text-primary border-primary/20";
      default: return "bg-muted";
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in pb-20 lg:pb-6">
        <div>
          <h1 className="font-['Poppins'] font-bold text-3xl mb-2">Investment Suggestions</h1>
          <p className="text-muted-foreground">
            AI-powered recommendations to maximize your tax savings for FY 2024-25
          </p>
        </div>

        {/* Summary Card */}
        <Card className="bg-gradient-success text-success-foreground shadow-lg">
          <CardContent className="py-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-lg mb-2 opacity-90">Potential Additional Savings</p>
                <p className="text-4xl font-bold mb-2">₹1,35,000</p>
                <p className="text-sm opacity-90">
                  By implementing all high-priority recommendations
                </p>
              </div>
              <TrendingUp className="h-16 w-16 opacity-50" />
            </div>
          </CardContent>
        </Card>

        {/* Investment Cards */}
        <div className="space-y-4">
          {suggestions.map((suggestion, index) => (
            <Card 
              key={index} 
              className="animate-scale-in hover:shadow-lg transition-all"
              style={{ animationDelay: `${index * 0.05}s` }}
            >
              <CardHeader>
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <Badge variant="outline" className="font-mono">
                        Section {suggestion.section}
                      </Badge>
                      <Badge className={getPriorityColor(suggestion.priority)}>
                        {suggestion.priority.toUpperCase()} Priority
                      </Badge>
                    </div>
                    <CardTitle className="font-['Poppins'] text-xl mb-1">
                      {suggestion.title}
                    </CardTitle>
                    <CardDescription>{suggestion.description}</CardDescription>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-sm text-muted-foreground mb-1">Investment</p>
                    <p className="text-2xl font-bold text-primary">{suggestion.amount}</p>
                    {suggestion.saving !== "Variable" && (
                      <>
                        <p className="text-xs text-muted-foreground mt-2">Tax Saving</p>
                        <p className="text-lg font-semibold text-success">{suggestion.saving}</p>
                      </>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 mb-4">
                  <div className="flex items-start gap-2">
                    <Lightbulb className="h-5 w-5 text-warning shrink-0 mt-0.5" />
                    <div className="space-y-1">
                      {suggestion.recommendations.map((rec, i) => (
                        <p key={i} className="text-sm text-muted-foreground">• {rec}</p>
                      ))}
                    </div>
                  </div>
                </div>
                <Button variant="outline" className="w-full sm:w-auto">
                  Learn More <ExternalLink className="h-4 w-4 ml-2" />
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Disclaimer */}
        <Card className="bg-muted/50">
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">
              <strong>Note:</strong> These are AI-generated suggestions based on your current financial data. 
              Please consult with a certified financial advisor before making investment decisions. 
              Tax laws are subject to change.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Investments;
