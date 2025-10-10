import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Download } from "lucide-react";
import { toast } from "sonner";

const TaxComputation = () => {
  const oldRegime = {
    grossIncome: 1250000,
    deductions: 250000,
    taxableIncome: 1000000,
    taxPayable: 115000,
    effectiveRate: 9.2
  };

  const newRegime = {
    grossIncome: 1250000,
    deductions: 50000,
    taxableIncome: 1200000,
    taxPayable: 160000,
    effectiveRate: 12.8
  };

  const incomeBreakdown = [
    { source: "Salary Income", amount: 1050000 },
    { source: "Interest Income", amount: 150000 },
    { source: "Other Sources", amount: 50000 }
  ];

  const deductionsOld = [
    { section: "80C", description: "ELSS, PPF, LIC", amount: 150000, limit: 150000 },
    { section: "80D", description: "Health Insurance", amount: 25000, limit: 25000 },
    { section: "HRA", description: "House Rent Allowance", amount: 50000, limit: null },
    { section: "80CCD(1B)", description: "NPS", amount: 25000, limit: 50000 }
  ];

  const handleGeneratePDF = () => {
    toast.success("PDF report generation started");
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in pb-20 lg:pb-6">
        <div>
          <h1 className="font-['Poppins'] font-bold text-3xl mb-2">Tax Computation</h1>
          <p className="text-muted-foreground">FY 2024-25 • Compare old and new tax regimes</p>
        </div>

        {/* Regime Comparison */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Old Regime */}
          <Card className="border-success/50 shadow-lg animate-scale-in">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="font-['Poppins'] text-2xl">Old Tax Regime</CardTitle>
                  <CardDescription>With all deductions</CardDescription>
                </div>
                <Badge className="bg-success/10 text-success border-success/20">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Recommended
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-muted-foreground">Gross Income</span>
                  <span className="font-semibold">₹{oldRegime.grossIncome.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-muted-foreground">Total Deductions</span>
                  <span className="font-semibold text-success">-₹{oldRegime.deductions.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-muted-foreground">Taxable Income</span>
                  <span className="font-semibold">₹{oldRegime.taxableIncome.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-3 bg-success/10 rounded-lg px-3 mt-4">
                  <span className="font-medium">Tax Payable</span>
                  <span className="font-bold text-xl text-success">₹{oldRegime.taxPayable.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm pt-2">
                  <span className="text-muted-foreground">Effective Tax Rate</span>
                  <span className="font-medium">{oldRegime.effectiveRate}%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* New Regime */}
          <Card className="animate-scale-in" style={{ animationDelay: "0.1s" }}>
            <CardHeader>
              <CardTitle className="font-['Poppins'] text-2xl">New Tax Regime</CardTitle>
              <CardDescription>Lower rates, fewer deductions</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-3">
                <div className="flex justify-between py-2 border-b">
                  <span className="text-muted-foreground">Gross Income</span>
                  <span className="font-semibold">₹{newRegime.grossIncome.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-muted-foreground">Total Deductions</span>
                  <span className="font-semibold">-₹{newRegime.deductions.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-2 border-b">
                  <span className="text-muted-foreground">Taxable Income</span>
                  <span className="font-semibold">₹{newRegime.taxableIncome.toLocaleString()}</span>
                </div>
                <div className="flex justify-between py-3 bg-muted rounded-lg px-3 mt-4">
                  <span className="font-medium">Tax Payable</span>
                  <span className="font-bold text-xl">₹{newRegime.taxPayable.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm pt-2">
                  <span className="text-muted-foreground">Effective Tax Rate</span>
                  <span className="font-medium">{newRegime.effectiveRate}%</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Savings Highlight */}
        <Card className="bg-gradient-success text-success-foreground shadow-lg">
          <CardContent className="py-6">
            <div className="text-center">
              <p className="text-lg mb-2">You Save with Old Regime</p>
              <p className="text-4xl font-bold mb-2">
                ₹{(newRegime.taxPayable - oldRegime.taxPayable).toLocaleString()}
              </p>
              <p className="text-sm opacity-90">
                That's {((newRegime.taxPayable - oldRegime.taxPayable) / newRegime.taxPayable * 100).toFixed(1)}% less tax compared to new regime
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Income Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Poppins']">Income Breakdown</CardTitle>
            <CardDescription>Your income sources for FY 2024-25</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {incomeBreakdown.map((income, index) => (
                <div key={index} className="flex justify-between items-center p-3 rounded-lg border">
                  <span className="font-medium">{income.source}</span>
                  <span className="text-lg font-semibold">₹{income.amount.toLocaleString()}</span>
                </div>
              ))}
              <div className="flex justify-between items-center p-3 rounded-lg bg-primary/10 border-primary/20 border-2 mt-4">
                <span className="font-bold">Total Gross Income</span>
                <span className="text-xl font-bold text-primary">
                  ₹{incomeBreakdown.reduce((sum, item) => sum + item.amount, 0).toLocaleString()}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Deductions (Old Regime) */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Poppins']">Deductions (Old Regime)</CardTitle>
            <CardDescription>Your claimed deductions under various sections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {deductionsOld.map((deduction, index) => (
                <div key={index} className="p-4 rounded-lg border hover:bg-muted/50 transition-colors">
                  <div className="flex justify-between items-start mb-2">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline">{deduction.section}</Badge>
                        {deduction.limit && deduction.amount >= deduction.limit && (
                          <Badge className="bg-success/10 text-success border-success/20">
                            <CheckCircle2 className="h-3 w-3 mr-1" />
                            Maxed
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground">{deduction.description}</p>
                    </div>
                    <span className="text-lg font-semibold whitespace-nowrap ml-4">
                      ₹{deduction.amount.toLocaleString()}
                    </span>
                  </div>
                  {deduction.limit && (
                    <div className="text-xs text-muted-foreground">
                      Limit: ₹{deduction.limit.toLocaleString()} 
                      {deduction.amount < deduction.limit && 
                        ` • ₹${(deduction.limit - deduction.amount).toLocaleString()} more available`
                      }
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex gap-4">
          <Button className="flex-1 bg-gradient-primary" size="lg" onClick={handleGeneratePDF}>
            <Download className="h-5 w-5 mr-2" />
            Generate Final PDF Report
          </Button>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default TaxComputation;
