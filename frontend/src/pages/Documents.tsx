import DashboardLayout from "@/components/layout/DashboardLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Upload, File, Trash2, CheckCircle2 } from "lucide-react";
import { toast } from "sonner";

const Documents = () => {
  const handleFileUpload = (docType: string) => {
    toast.success(`${docType} upload initiated`);
  };

  const handleDelete = (fileName: string) => {
    toast.success(`${fileName} deleted`);
  };

  const uploadedFiles = [
    { name: "AIS_2024-25.pdf", type: "AIS", date: "2024-12-15", size: "2.4 MB" },
    { name: "Form16_2024-25.pdf", type: "Form 16", date: "2024-12-14", size: "1.8 MB" }
  ];

  const documentTypes = [
    { 
      title: "AIS (Annual Information Statement)", 
      description: "Upload your AIS from the income tax portal",
      status: "complete"
    },
    { 
      title: "Form 16", 
      description: "Salary TDS certificate from your employer",
      status: "complete"
    },
    { 
      title: "Form 26AS", 
      description: "Tax credit statement",
      status: "pending"
    },
    { 
      title: "Other Supporting Documents", 
      description: "Investment proofs, rent receipts, etc.",
      status: "partial"
    }
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6 animate-fade-in pb-20 lg:pb-6">
        <div>
          <h1 className="font-['Poppins'] font-bold text-3xl mb-2">Document Management</h1>
          <p className="text-muted-foreground">Upload and manage your tax documents for FY 2024-25</p>
        </div>

        {/* Upload Cards */}
        <div className="grid md:grid-cols-2 gap-4">
          {documentTypes.map((doc, index) => (
            <Card key={index} className="animate-scale-in" style={{ animationDelay: `${index * 0.1}s` }}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="text-lg font-['Poppins'] mb-1">{doc.title}</CardTitle>
                    <CardDescription>{doc.description}</CardDescription>
                  </div>
                  {doc.status === "complete" && (
                    <CheckCircle2 className="h-5 w-5 text-success shrink-0" />
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <Button 
                  variant={doc.status === "complete" ? "outline" : "default"}
                  className={doc.status === "pending" ? "bg-gradient-primary w-full" : "w-full"}
                  onClick={() => handleFileUpload(doc.title)}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  {doc.status === "complete" ? "Re-upload" : "Upload Document"}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Uploaded Files Table */}
        <Card>
          <CardHeader>
            <CardTitle className="font-['Poppins']">Uploaded Documents</CardTitle>
            <CardDescription>Your uploaded files for FY 2024-25</CardDescription>
          </CardHeader>
          <CardContent>
            {uploadedFiles.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <File className="h-12 w-12 mx-auto mb-3 opacity-50" />
                <p>No documents uploaded yet</p>
              </div>
            ) : (
              <div className="space-y-3">
                {uploadedFiles.map((file, index) => (
                  <div key={index} className="flex items-center gap-4 p-4 rounded-lg border hover:bg-muted/50 transition-colors">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <File className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate">{file.name}</p>
                      <p className="text-sm text-muted-foreground">
                        {file.type} • {file.size} • Uploaded on {file.date}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">View</Button>
                      <Button 
                        variant="ghost" 
                        size="sm"
                        onClick={() => handleDelete(file.name)}
                      >
                        <Trash2 className="h-4 w-4 text-destructive" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Instructions */}
        <Card className="bg-primary/5 border-primary/20">
          <CardHeader>
            <CardTitle className="font-['Poppins'] text-lg">Upload Guidelines</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>• Accepted formats: PDF, JPG, PNG (max 10 MB per file)</p>
            <p>• Ensure all documents are clear and readable</p>
            <p>• AIS can be downloaded from the income tax e-filing portal</p>
            <p>• Form 16 is provided by your employer</p>
            <p>• All documents are encrypted and stored securely</p>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default Documents;
