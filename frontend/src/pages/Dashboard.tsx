import { Link } from "react-router-dom";
import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { 
  TrendingUp, 
  TrendingDown, 
  Calculator, 
  FileText, 
  Upload,
  Receipt,
  IndianRupee,
  CheckCircle2,
  AlertCircle
} from "lucide-react";

const Dashboard = () => {
  // Mock data
  const stats = [
    {
      title: "Total Income",
      value: "₹12,50,000",
      change: "+8.2%",
      trend: "up",
      icon: IndianRupee,
      color: "text-primary"
    },
    {
      title: "Total Deductions",
      value: "₹2,50,000",
      change: "80C, 80D, HRA",
      trend: "neutral",
      icon: TrendingDown,
      color: "text-success"
    },
    {
      title: "Tax Payable",
      value: "₹1,15,000",
      change: "Old Regime",
      trend: "neutral",
      icon: Calculator,
      color: "text-warning"
    },
    {
      title: "Potential Savings",
      value: "₹45,000",
      change: "With investments",
      trend: "up",
      icon: TrendingUp,
      color: "text-success"
    }
  ];

  const recentActivity = [
    { icon: Upload, text: "Form 16 uploaded successfully", time: "2 hours ago", status: "success" },
    { icon: FileText, text: "AIS data processed", time: "1 day ago", status: "success" },
    { icon: Receipt, text: "Tax computation completed", time: "2 days ago", status: "success" },
    { icon: AlertCircle, text: "26AS pending upload", time: "3 days ago", status: "warning" }
  ];

  const uploadProgress = {
    ais: 100,
    form16: 100,
    form26as: 0,
    other: 50
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in pb-20 lg:pb-6">
        {/* Header */}
        <div>
          <h1 className="font-['Poppins'] font-bold text-3xl mb-2">Welcome back, Mayur Gopal Mahajan!</h1>
          <p className="text-muted-foreground">Here's your tax summary for FY 2024-25</p>
        </div>

        {/* Stats Grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <Card key={index} className="animate-scale-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.title}
                </CardTitle>
                <stat.icon className={`h-5 w-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold mb-1">{stat.value}</div>
                <p className="text-xs text-muted-foreground">{stat.change}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Regime Recommendation */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <CardTitle className="font-['Poppins']">Tax Regime Recommendation</CardTitle>
              <CardDescription>Based on your current financial data</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="p-4 rounded-lg bg-success/10 border border-success/20">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="h-6 w-6 text-success shrink-0 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-1">Old Tax Regime is Better for You</h3>
                    <p className="text-sm text-muted-foreground mb-3">
                      You can save ₹45,000 more by choosing the old regime with current deductions
                    </p>
                    <div className="grid sm:grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-muted-foreground">Old Regime</p>
                        <p className="text-xl font-bold text-success">₹1,15,000</p>
                      </div>
                      <div>
                        <p className="text-muted-foreground">New Regime</p>
                        <p className="text-xl font-bold">₹1,60,000</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex gap-3">
                <Link to="/tax" className="flex-1">
                  <Button className="w-full bg-gradient-primary">View Detailed Computation</Button>
                </Link>
                <Link to="/reports">
                  <Button variant="outline">Generate PDF</Button>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Upload Progress */}
          <Card>
            <CardHeader>
              <CardTitle className="font-['Poppins']">Document Status</CardTitle>
              <CardDescription>FY 2024-25 uploads</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>AIS</span>
                  <span className="text-success">Complete</span>
                </div>
                <Progress value={uploadProgress.ais} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Form 16</span>
                  <span className="text-success">Complete</span>
                </div>
                <Progress value={uploadProgress.form16} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Form 26AS</span>
                  <span className="text-warning">Pending</span>
                </div>
                <Progress value={uploadProgress.form26as} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Other Documents</span>
                  <span className="text-primary">50%</span>
                </div>
                <Progress value={uploadProgress.other} className="h-2" />
              </div>

              <Link to="/documents">
                <Button variant="outline" className="w-full mt-2">
                  <Upload className="h-4 w-4 mr-2" />
                  Upload Documents
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Poppins']">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((activity, index) => (
                <div key={index} className="flex items-start gap-3 pb-4 border-b last:border-0 last:pb-0">
                  <div className={`p-2 rounded-lg ${activity.status === 'success' ? 'bg-success/10' : 'bg-warning/10'}`}>
                    <activity.icon className={`h-4 w-4 ${activity.status === 'success' ? 'text-success' : 'text-warning'}`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{activity.text}</p>
                    <p className="text-xs text-muted-foreground">{activity.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <Link to="/investments">
            <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
              <TrendingUp className="h-6 w-6" />
              <span>Investment Tips</span>
            </Button>
          </Link>
          <Link to="/tax">
            <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
              <Calculator className="h-6 w-6" />
              <span>Tax Calculator</span>
            </Button>
          </Link>
          <Link to="/reports">
            <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
              <Receipt className="h-6 w-6" />
              <span>Download Report</span>
            </Button>
          </Link>
          <Link to="/chat">
            <Button variant="outline" className="w-full h-auto py-4 flex-col gap-2">
              <FileText className="h-6 w-6" />
              <span>Ask AI-CA</span>
            </Button>
          </Link>
        </div>
      </div>
    </DashboardLayout>
  );
};

export default Dashboard;
