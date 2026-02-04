import { Link } from 'react-router-dom'
import { FileText, Calculator, TrendingUp, MessageCircle, Shield, Zap, Brain, BarChart3 } from 'lucide-react'

function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-white">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Brain className="w-8 h-8 text-primary-600" />
            <h1 className="text-2xl font-bold text-gray-900">AI-CA</h1>
          </div>
          <div className="space-x-4">
            <Link to="/login" className="px-6 py-2 text-primary-600 hover:text-primary-700">
              Login
            </Link>
            <Link to="/register" className="btn-primary">
              Get Started
            </Link>
          </div>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            AI-Powered Virtual <span className="text-primary-600">Chartered Accountant</span>
          </h2>
          <p className="text-xl text-gray-600 mb-8">
            Simplify your tax filing with intelligent document parsing, accurate calculations, 
            and personalized recommendations powered by advanced AI.
          </p>
          <div className="flex justify-center gap-4">
            <Link to="/register" className="btn-primary text-lg px-8 py-3">
              Start Free Trial
            </Link>
            <button className="btn-secondary text-lg px-8 py-3">
              Watch Demo
            </button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="container mx-auto px-4 py-20">
        <h3 className="text-3xl font-bold text-center mb-12">Powerful Features</h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          <FeatureCard
            icon={<FileText className="w-8 h-8 text-primary-600" />}
            title="Document Verification"
            description="Automatically verify Form 16, Form 26AS, and AIS documents with AI-powered validation"
          />
          <FeatureCard
            icon={<Calculator className="w-8 h-8 text-primary-600" />}
            title="Smart Tax Calculation"
            description="Accurate tax computation under both old and new regimes with real-time updates"
          />
          <FeatureCard
            icon={<TrendingUp className="w-8 h-8 text-primary-600" />}
            title="Investment Suggestions"
            description="Get personalized investment recommendations to minimize your tax liability"
          />
          <FeatureCard
            icon={<MessageCircle className="w-8 h-8 text-primary-600" />}
            title="AI Tax Assistant"
            description="Ask questions and get instant answers about tax laws and filing requirements"
          />
          <FeatureCard
            icon={<Shield className="w-8 h-8 text-primary-600" />}
            title="Secure & Compliant"
            description="Your data is encrypted and stored securely with year-wise separation"
          />
          <FeatureCard
            icon={<Zap className="w-8 h-8 text-primary-600" />}
            title="Regime Comparison"
            description="Automatic recommendation of the best tax regime with detailed explanations"
          />
          <FeatureCard
            icon={<BarChart3 className="w-8 h-8 text-primary-600" />}
            title="Visual Dashboard"
            description="Beautiful charts and graphs for easy understanding of your tax situation"
          />
          <FeatureCard
            icon={<FileText className="w-8 h-8 text-primary-600" />}
            title="PDF Reports"
            description="Download comprehensive tax reports ready for ITR filing"
          />
        </div>
      </section>

      {/* How It Works */}
      <section className="container mx-auto px-4 py-20 bg-gray-50">
        <h3 className="text-3xl font-bold text-center mb-12">How It Works</h3>
        <div className="max-w-4xl mx-auto space-y-8">
          <StepCard
            step="1"
            title="Create Your Account"
            description="Register with your PAN card and basic details. Quick and secure setup."
          />
          <StepCard
            step="2"
            title="Upload Documents"
            description="Upload Form 16, Form 26AS, and AIS. Our AI verifies and extracts data automatically."
          />
          <StepCard
            step="3"
            title="Review Calculations"
            description="Get instant tax calculations for both regimes with personalized recommendations."
          />
          <StepCard
            step="4"
            title="Optimize & File"
            description="Receive investment suggestions and download your comprehensive tax report."
          />
        </div>
      </section>

      {/* Benefits */}
      <section className="container mx-auto px-4 py-20">
        <h3 className="text-3xl font-bold text-center mb-12">Why Choose AI-CA?</h3>
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          <BenefitCard
            title="Save Time"
            description="Automated data extraction and calculations save hours of manual work"
            stat="90% Faster"
          />
          <BenefitCard
            title="Save Money"
            description="AI-powered investment suggestions help you minimize tax liability"
            stat="₹50K+ Avg Savings"
          />
          <BenefitCard
            title="Stay Compliant"
            description="Always up-to-date with the latest tax rules and regulations"
            stat="100% Accurate"
          />
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-20 text-center">
        <div className="max-w-3xl mx-auto bg-primary-600 rounded-2xl p-12 text-white">
          <h3 className="text-3xl font-bold mb-4">Ready to Simplify Your Tax Filing?</h3>
          <p className="text-xl mb-8 opacity-90">
            Join thousands of users who trust AI-CA for their tax compliance needs
          </p>
          <Link to="/register" className="inline-block px-8 py-3 bg-white text-primary-600 rounded-lg font-medium hover:bg-gray-100 transition-colors">
            Get Started for Free
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="container mx-auto px-4 text-center">
          <div className="flex items-center justify-center space-x-2 mb-4">
            <Brain className="w-6 h-6" />
            <span className="text-lg font-semibold">AI-CA</span>
          </div>
          <p className="text-gray-400">
            AI-Powered Virtual Chartered Accountant for Indian Income Tax
          </p>
          <p className="text-gray-500 text-sm mt-4">
            © 2024 AI-CA. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="card text-center hover:shadow-lg transition-shadow">
      <div className="flex justify-center mb-4">{icon}</div>
      <h4 className="text-lg font-semibold mb-2">{title}</h4>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function StepCard({ step, title, description }) {
  return (
    <div className="flex items-start space-x-4">
      <div className="flex-shrink-0 w-12 h-12 bg-primary-600 text-white rounded-full flex items-center justify-center text-xl font-bold">
        {step}
      </div>
      <div>
        <h4 className="text-xl font-semibold mb-2">{title}</h4>
        <p className="text-gray-600">{description}</p>
      </div>
    </div>
  )
}

function BenefitCard({ title, description, stat }) {
  return (
    <div className="card text-center">
      <div className="text-4xl font-bold text-primary-600 mb-2">{stat}</div>
      <h4 className="text-xl font-semibold mb-2">{title}</h4>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

export default LandingPage

