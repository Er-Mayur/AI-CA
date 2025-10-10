import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { 
  Calculator, 
  TrendingUp, 
  FileText, 
  Shield, 
  Zap, 
  CheckCircle2,
  ArrowRight,
  Sparkles
} from "lucide-react";
import heroBg from "@/assets/hero-bg.jpg";

const Index = () => {
  const features = [
    {
      icon: Calculator,
      title: "Smart Tax Computation",
      description: "AI analyzes your AIS, Form 16 & 26AS to compute taxes under both regimes instantly"
    },
    {
      icon: TrendingUp,
      title: "Investment Suggestions",
      description: "Get personalized recommendations for 80C, 80D, NPS and more to maximize savings"
    },
    {
      icon: FileText,
      title: "CA-Style Reports",
      description: "Download professional PDF reports with complete tax breakdown and digital signature"
    },
    {
      icon: Shield,
      title: "Secure & Private",
      description: "Bank-grade encryption for your financial documents. Your data stays yours"
    },
    {
      icon: Zap,
      title: "Instant Processing",
      description: "Upload documents and get results in seconds, not days or weeks"
    },
    {
      icon: Sparkles,
      title: "AI Tax Assistant",
      description: "Chat with our AI-CA for instant answers to all your tax queries"
    }
  ];

  const benefits = [
    "Automated AIS data extraction",
    "Old vs New regime comparison",
    "Section 80C, 80D optimization",
    "HRA & Home Loan calculations",
    "Multi-year tax tracking",
    "Investment scenario simulator"
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calculator className="h-8 w-8 text-primary" />
            <div>
              <h1 className="font-bold text-xl font-['Poppins']">AI-CA</h1>
              <p className="text-xs text-muted-foreground">An AI-Powered Virtual Chartered Accountant</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/auth/login">
              <Button variant="ghost">Login</Button>
            </Link>
            <Link to="/auth/register">
              <Button className="bg-gradient-primary">Get Started</Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div 
          className="absolute inset-0 opacity-10"
          style={{
            backgroundImage: `url(${heroBg})`,
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        />
        <div className="relative container mx-auto px-4 py-20 md:py-32">
          <div className="max-w-4xl mx-auto text-center animate-fade-in">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary mb-6">
              <Sparkles className="h-4 w-4" />
              <span className="text-sm font-medium">India's First AI-Powered Virtual CA</span>
            </div>
            <h1 className="font-['Poppins'] font-bold text-5xl md:text-7xl mb-6 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Your Personal Chartered Accountant, Powered by AI
            </h1>
            <p className="text-xl md:text-2xl text-muted-foreground mb-8 max-w-2xl mx-auto">
              Upload your AIS, Form 16 & 26AS. Get instant tax computation, regime comparison, and investment suggestions—all automated.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link to="/auth/register">
                <Button size="lg" className="bg-gradient-primary text-lg px-8 shadow-glow">
                  Start Free Analysis <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/auth/login">
                <Button size="lg" variant="outline" className="text-lg px-8">
                  View Demo
                </Button>
              </Link>
            </div>
            <p className="text-sm text-muted-foreground mt-4">
              No credit card required • Free for FY 2024-25
            </p>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="text-center mb-12 animate-slide-up">
            <h2 className="font-['Poppins'] font-bold text-4xl mb-4">
              Everything You Need for Smart Tax Planning
            </h2>
            <p className="text-muted-foreground text-lg">
              Powered by advanced AI to give you CA-level insights instantly
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-6xl mx-auto">
            {features.map((feature, index) => (
              <Card 
                key={index} 
                className="p-6 hover:shadow-lg transition-all duration-300 hover:-translate-y-1 animate-scale-in border-border/50"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="h-12 w-12 rounded-lg bg-gradient-primary flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-primary-foreground" />
                </div>
                <h3 className="font-['Poppins'] font-semibold text-xl mb-2">
                  {feature.title}
                </h3>
                <p className="text-muted-foreground">
                  {feature.description}
                </p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="text-center mb-12">
              <h2 className="font-['Poppins'] font-bold text-4xl mb-4">
                Why Choose AI-CA?
              </h2>
              <p className="text-muted-foreground text-lg">
                Save time, money, and make smarter financial decisions
              </p>
            </div>
            <div className="grid md:grid-cols-2 gap-6">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-3 animate-fade-in" style={{ animationDelay: `${index * 0.1}s` }}>
                  <CheckCircle2 className="h-6 w-6 text-success shrink-0 mt-1" />
                  <div>
                    <p className="text-lg font-medium">{benefit}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-primary relative overflow-hidden">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wNSI+PHBhdGggZD0iTTM2IDE2djhIMTZ2LThoMjB6bTAgMTZ2OEgxNnYtOGgyMHoiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-20"></div>
        <div className="container mx-auto px-4 relative">
          <div className="max-w-3xl mx-auto text-center text-primary-foreground">
            <h2 className="font-['Poppins'] font-bold text-4xl md:text-5xl mb-6">
              Ready to Simplify Your Taxes?
            </h2>
            <p className="text-xl mb-8 text-primary-foreground/90">
              Join thousands of Indians who trust AI-CA for smart tax planning
            </p>
            <Link to="/auth/register">
              <Button size="lg" variant="secondary" className="text-lg px-8">
                Create Free Account <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-8 bg-card">
        <div className="container mx-auto px-4 text-center text-muted-foreground">
          <p className="mb-2">© 2025 An AI-Powered Virtual Chartered Accountant — India's Smart Tax Companion</p>
          <p className="text-sm">Empowering Indians with AI-driven tax intelligence</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
