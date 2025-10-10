import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Download, FileText, Calendar, IndianRupee } from "lucide-react";
import { toast } from "sonner";

const Reports = () => {
  const reports = [
    {
      fy: "2024-25",
      date: "2025-01-15",
      regime: "Old Regime",
      taxPayable: 115000,
      status: "latest"
    },
    {
      fy: "2023-24",
      date: "2024-07-20",
      regime: "Old Regime",
      taxPayable: 98000,
      status: "filed"
    },
    {
      fy: "2022-23",
      date: "2023-07-15",
      regime: "Old Regime",
      taxPayable: 85000,
      status: "filed"
    }
  ];

  const handleDownload = (fy: string) => {
    toast.success(`Downloading report for FY ${fy}`);
  };

  const handleGenerateNew = () => {
    toast.success("Generating new report with latest data");
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in pb-20 lg:pb-6">
        <div>
          <h1 className="font-['Poppins'] font-bold text-3xl mb-2">Tax Reports</h1>
          <p className="text-muted-foreground">
            Download CA-style PDF reports with complete tax analysis
          </p>
        </div>

        {/* Generate New Report Card */}
        <Card className="bg-gradient-primary text-primary-foreground shadow-lg">
          <CardContent className="py-8">
            <div className="max-w-2xl mx-auto text-center">
              <FileText className="h-12 w-12 mx-auto mb-4 opacity-90" />
              <h2 className="font-['Poppins'] text-2xl font-bold mb-3">
                Generate Complete Tax Report
              </h2>
              <p className="mb-6 opacity-90">
                Get a professional CA-style PDF with income breakdown, deductions, regime comparison, 
                investment suggestions, and digital signature
              </p>
              <Button 
                size="lg" 
                variant="secondary"
                onClick={handleGenerateNew}
                className="shadow-lg"
              >
                <Download className="h-5 w-5 mr-2" />
                Generate New Report
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Report Preview */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Poppins']">What's Included in Your Report</CardTitle>
            <CardDescription>Professional tax analysis with all details</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { title: "Personal Details", desc: "Name, PAN, Contact, Financial Year" },
                { title: "Income Breakdown", desc: "Salary, Interest, Capital Gains, Other Sources" },
                { title: "Deduction Summary", desc: "All claimed deductions under various sections" },
                { title: "Regime Comparison", desc: "Old vs New regime with detailed calculation" },
                { title: "Investment Plan", desc: "80C, 80D, NPS, and other recommendations" },
                { title: "Final Summary", desc: "Tax payable, TDS, refund with Virtunexa seal" }
              ].map((item, index) => (
                <div key={index} className="p-4 rounded-lg border bg-card hover:bg-muted/50 transition-colors">
                  <h3 className="font-semibold mb-1">{item.title}</h3>
                  <p className="text-sm text-muted-foreground">{item.desc}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Generated Reports History */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Poppins']">Report History</CardTitle>
            <CardDescription>Previously generated tax reports</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {reports.map((report, index) => (
                <div 
                  key={index} 
                  className="flex items-center gap-4 p-4 rounded-lg border hover:bg-muted/50 transition-colors"
                >
                  <div className="p-3 rounded-lg bg-primary/10">
                    <FileText className="h-6 w-6 text-primary" />
                  </div>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold">Tax Report FY {report.fy}</h3>
                      {report.status === "latest" && (
                        <Badge className="bg-success/10 text-success border-success/20">Latest</Badge>
                      )}
                      {report.status === "filed" && (
                        <Badge variant="outline">Filed</Badge>
                      )}
                    </div>
                    
                    <div className="flex flex-wrap gap-3 text-sm text-muted-foreground">
                      <div className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        <span>{report.date}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <IndianRupee className="h-3 w-3" />
                        <span>₹{report.taxPayable.toLocaleString()}</span>
                      </div>
                      <span>•</span>
                      <span>{report.regime}</span>
                    </div>
                  </div>

                  <div className="flex gap-2 shrink-0">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => handleDownload(report.fy)}
                    >
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Sample Report Info */}
        <Card className="bg-muted/50">
          <CardContent className="py-4">
            <p className="text-sm text-muted-foreground">
              <strong>Report Features:</strong> All reports include comprehensive tax analysis, 
              visual charts, investment recommendations, and are digitally signed by Virtunexa AI-CA. 
              Reports are generated in PDF format and can be used for record-keeping or sharing with your employer.
            </p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Reports;
