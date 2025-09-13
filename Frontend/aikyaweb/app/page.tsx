"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Separator } from "@/components/ui/separator"
import { Upload, FileText, User, Shield, CheckCircle, XCircle, Clock, TrendingUp, AlertCircle } from "lucide-react"

interface TrustScoreRecord {
  id: number
  user_id: string
  name: string
  story: string
  trust_score: number
  face_match: boolean
  document_verified: boolean
  emotion_score: number
  engagement_score: number
  admin_adjustment: number
  supporting_doc_type: string
  supporting_doc_score: number
  aadhaar_number: string
  pan_number: string
  created_at: string
}

interface Notification {
  id: number
  type: "success" | "error"
  message: string
}

export default function AikyaDashboard() {
  const [records, setRecords] = useState<TrustScoreRecord[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [notifications, setNotifications] = useState<Notification[]>([])

  // Form state
  const [formData, setFormData] = useState({
    name: "",
    story: "",
    supporting_doc_type: "",
    aadhaar_number: "",
    pan_number: "",
    user_id: "",
  })

  const [files, setFiles] = useState({
    id_image: null as File | null,
    selfie_image: null as File | null,
    supporting_doc: null as File | null,
    aadhaar_doc: null as File | null,
    pan_doc: null as File | null,
  })

  const addNotification = (type: "success" | "error", message: string) => {
    const id = Date.now()
    setNotifications((prev) => [...prev, { id, type, message }])
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== id))
    }, 5000)
  }

  useEffect(() => {
    fetchRecords()
  }, [])

  const fetchRecords = async () => {
    setLoading(true)
    try {
      const response = await fetch("http://127.0.0.1:5000/records")
      if (response.ok) {
        const data = await response.json()
        setRecords(data.records || [])
      } else {
        addNotification("error", "Failed to fetch records")
      }
    } catch (error) {
      addNotification("error", "Unable to connect to the server")
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleFileChange = (field: string, file: File | null) => {
    setFiles((prev) => ({ ...prev, [field]: file }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSubmitting(true)

    const formDataToSend = new FormData()
    Object.entries(formData).forEach(([key, value]) => {
      formDataToSend.append(key, value)
    })
    Object.entries(files).forEach(([key, file]) => {
      if (file) formDataToSend.append(key, file)
    })

    try {
      const response = await fetch("http://127.0.0.1:5000/submit", {
        method: "POST",
        body: formDataToSend,
      })

      if (response.ok) {
        const result = await response.json()
        addNotification("success", `Trust score generated: ${result.trust_score}`)
        // Reset form
        setFormData({
          name: "",
          story: "",
          supporting_doc_type: "",
          aadhaar_number: "",
          pan_number: "",
          user_id: "",
        })
        setFiles({
          id_image: null,
          selfie_image: null,
          supporting_doc: null,
          aadhaar_doc: null,
          pan_doc: null,
        })
        fetchRecords() // Refresh records
      } else {
        const error = await response.json()
        addNotification("error", error.error || "Failed to submit")
      }
    } catch (error) {
      addNotification("error", "Unable to connect to the server")
    } finally {
      setSubmitting(false)
    }
  }

  const getTrustScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600"
    if (score >= 60) return "text-yellow-600"
    return "text-red-600"
  }

  const getTrustScoreBadge = (score: number) => {
    if (score >= 80) return "bg-green-100 text-green-800"
    if (score >= 60) return "bg-yellow-100 text-yellow-800"
    return "bg-red-100 text-red-800"
  }

  const averageTrustScore =
    records.length > 0 ? records.reduce((sum, record) => sum + record.trust_score, 0) / records.length : 0

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {notifications.map((notification) => (
          <Alert
            key={notification.id}
            className={`w-80 ${
              notification.type === "success" ? "border-green-500 bg-green-50" : "border-red-500 bg-red-50"
            }`}
          >
            {notification.type === "success" ? (
              <CheckCircle className="h-4 w-4 text-green-600" />
            ) : (
              <AlertCircle className="h-4 w-4 text-red-600" />
            )}
            <AlertDescription className={notification.type === "success" ? "text-green-800" : "text-red-800"}>
              {notification.message}
            </AlertDescription>
          </Alert>
        ))}
      </div>

      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold font-serif text-slate-500">AIKYA</h1>
          <p className="text-xl text-gray-600">Social Crowd Platform Trust Score Generation Module</p>
          <div className="flex items-center justify-center gap-4 text-sm text-gray-500">
            <div className="flex items-center gap-1">
              <Shield className="h-4 w-4" />
              <span>Secure Verification</span>
            </div>
            <div className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4" />
              <span>AI-Powered Analysis</span>
            </div>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Total Records</p>
                  <p className="text-2xl font-bold">{records.length}</p>
                </div>
                <User className="h-8 w-8 text-blue-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Average Trust Score</p>
                  <p className={`text-2xl font-bold ${getTrustScoreColor(averageTrustScore)}`}>
                    {averageTrustScore.toFixed(1)}
                  </p>
                </div>
                <TrendingUp className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Verified Users</p>
                  <p className="text-2xl font-bold text-green-600">
                    {records.filter((r) => r.face_match && r.document_verified).length}
                  </p>
                </div>
                <CheckCircle className="h-8 w-8 text-green-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">Pending Review</p>
                  <p className="text-2xl font-bold text-yellow-600">
                    {records.filter((r) => !r.face_match || !r.document_verified).length}
                  </p>
                </div>
                <Clock className="h-8 w-8 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Tabs defaultValue="submit" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="submit">Submit New Request</TabsTrigger>
            <TabsTrigger value="records">View Records</TabsTrigger>
          </TabsList>

          <TabsContent value="submit">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Trust Score Generation
                </CardTitle>
                <CardDescription>Upload documents and provide information to generate a trust score</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">Full Name</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleInputChange("name", e.target.value)}
                        placeholder="Enter full name"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="user_id">User ID</Label>
                      <Input
                        id="user_id"
                        value={formData.user_id}
                        onChange={(e) => handleInputChange("user_id", e.target.value)}
                        placeholder="Enter user ID"
                        required
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="aadhaar_number">Aadhaar Number</Label>
                      <Input
                        id="aadhaar_number"
                        value={formData.aadhaar_number}
                        onChange={(e) => handleInputChange("aadhaar_number", e.target.value)}
                        placeholder="Enter Aadhaar number"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="pan_number">PAN Number</Label>
                      <Input
                        id="pan_number"
                        value={formData.pan_number}
                        onChange={(e) => handleInputChange("pan_number", e.target.value)}
                        placeholder="Enter PAN number"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="story">Personal Story</Label>
                    <Textarea
                      id="story"
                      value={formData.story}
                      onChange={(e) => handleInputChange("story", e.target.value)}
                      placeholder="Share your story or reason for requesting support..."
                      className="min-h-[100px]"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="supporting_doc_type">Supporting Document Type</Label>
                    <Select
                      value={formData.supporting_doc_type}
                      onValueChange={(value) => handleInputChange("supporting_doc_type", value)}
                      required
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Select document type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="medical_report">Medical Report</SelectItem>
                        <SelectItem value="income_certificate">Income Certificate</SelectItem>
                        <SelectItem value="disability_certificate">Disability Certificate</SelectItem>
                        <SelectItem value="education_certificate">Education Certificate</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Separator />

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="id_image">ID Photo</Label>
                      <Input
                        id="id_image"
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange("id_image", e.target.files?.[0] || null)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="selfie_image">Selfie Photo</Label>
                      <Input
                        id="selfie_image"
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange("selfie_image", e.target.files?.[0] || null)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="aadhaar_doc">Aadhaar Document</Label>
                      <Input
                        id="aadhaar_doc"
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange("aadhaar_doc", e.target.files?.[0] || null)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="pan_doc">PAN Document</Label>
                      <Input
                        id="pan_doc"
                        type="file"
                        accept="image/*"
                        onChange={(e) => handleFileChange("pan_doc", e.target.files?.[0] || null)}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="supporting_doc">Supporting Document</Label>
                      <Input
                        id="supporting_doc"
                        type="file"
                        accept=".pdf,.jpg,.jpeg,.png"
                        onChange={(e) => handleFileChange("supporting_doc", e.target.files?.[0] || null)}
                        required
                      />
                    </div>
                  </div>

                  <Button type="submit" className="w-full" disabled={submitting}>
                    {submitting ? "Processing..." : "Generate Trust Score"}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="records">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Trust Score Records
                </CardTitle>
                <CardDescription>View all generated trust scores and verification results</CardDescription>
              </CardHeader>
              <CardContent>
                {loading ? (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="mt-2 text-gray-600">Loading records...</p>
                  </div>
                ) : records.length === 0 ? (
                  <Alert>
                    <AlertDescription>
                      No records found. Submit your first trust score request to get started.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="space-y-4">
                    {records.map((record) => (
                      <Card key={record.id} className="border-l-4 border-l-blue-500">
                        <CardContent className="p-4">
                          <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                            <div className="space-y-2">
                              <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-lg">{record.name}</h3>
                                <Badge className={getTrustScoreBadge(record.trust_score)}>
                                  Trust Score: {record.trust_score}
                                </Badge>
                              </div>
                              <p className="text-sm text-gray-600">User ID: {record.user_id}</p>
                              <p className="text-sm text-gray-700 max-w-2xl">{record.story}</p>
                            </div>

                            <div className="flex flex-col gap-2 min-w-[200px]">
                              <div className="flex items-center gap-2">
                                {record.face_match ? (
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                ) : (
                                  <XCircle className="h-4 w-4 text-red-600" />
                                )}
                                <span className="text-sm">Face Match</span>
                              </div>
                              <div className="flex items-center gap-2">
                                {record.document_verified ? (
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                ) : (
                                  <XCircle className="h-4 w-4 text-red-600" />
                                )}
                                <span className="text-sm">Document Verified</span>
                              </div>
                              <div className="space-y-1">
                                <div className="flex justify-between text-xs">
                                  <span>Emotion Score</span>
                                  <span>{record.emotion_score.toFixed(1)}</span>
                                </div>
                                <Progress value={record.emotion_score * 10} className="h-1" />
                              </div>
                              <p className="text-xs text-gray-500">
                                {new Date(record.created_at).toLocaleDateString()}
                              </p>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
