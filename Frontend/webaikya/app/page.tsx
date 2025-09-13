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
import {
  Upload,
  FileText,
  User,
  CheckCircle,
  XCircle,
  Clock,
  AlertCircle,
  BarChart3,
  Users,
  FileCheck,
  Code,
  Copy,
  Eye,
  EyeOff,
} from "lucide-react"
import Image from "next/image"

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
  const [lastJsonResponse, setLastJsonResponse] = useState<any>(null)
  const [showJsonResponse, setShowJsonResponse] = useState(false)
  const [expandedRecords, setExpandedRecords] = useState<Set<number>>(new Set())

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
    setLastJsonResponse(null)
    setShowJsonResponse(false)

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
        setLastJsonResponse(result)
        setShowJsonResponse(true)
        addNotification("success", `Trust score generated successfully: ${result.trust_score}`)
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
        fetchRecords()
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

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    addNotification("success", "JSON copied to clipboard")
  }

  const toggleRecordJson = (recordId: number) => {
    const newExpanded = new Set(expandedRecords)
    if (newExpanded.has(recordId)) {
      newExpanded.delete(recordId)
    } else {
      newExpanded.add(recordId)
    }
    setExpandedRecords(newExpanded)
  }

  const getTrustScoreColor = (score: number) => {
    if (score >= 80) return "text-emerald-600"
    if (score >= 60) return "text-amber-600"
    return "text-red-600"
  }

  const getTrustScoreBadge = (score: number) => {
    if (score >= 80) return "bg-emerald-50 text-emerald-700 border-emerald-200"
    if (score >= 60) return "bg-amber-50 text-amber-700 border-amber-200"
    return "bg-red-50 text-red-700 border-red-200"
  }

  const averageTrustScore =
    records.length > 0 ? records.reduce((sum, record) => sum + record.trust_score, 0) / records.length : 0

  return (
    <div className="min-h-screen relative overflow-hidden">
      <div className="fixed inset-0 bg-gradient-to-br from-emerald-50 via-sky-50 to-cyan-50">
        {/* Animated floating glass orbs */}
        <div className="absolute top-20 left-10 w-32 h-32 bg-gradient-to-br from-emerald-200/30 to-sky-200/30 rounded-full blur-xl animate-pulse"></div>
        <div
          className="absolute top-40 right-20 w-48 h-48 bg-gradient-to-br from-sky-200/20 to-cyan-200/20 rounded-full blur-2xl animate-bounce"
          style={{ animationDuration: "3s" }}
        ></div>
        <div
          className="absolute bottom-32 left-1/4 w-24 h-24 bg-gradient-to-br from-cyan-200/40 to-emerald-200/40 rounded-full blur-lg animate-pulse"
          style={{ animationDelay: "1s" }}
        ></div>
        <div
          className="absolute bottom-20 right-1/3 w-40 h-40 bg-gradient-to-br from-emerald-100/30 to-sky-100/30 rounded-full blur-xl animate-bounce"
          style={{ animationDuration: "4s", animationDelay: "2s" }}
        ></div>

        {/* Glass overlay */}
        <div className="absolute inset-0 backdrop-blur-[1px] bg-white/10"></div>
      </div>

      {/* Content */}
      <div className="relative z-10">
        {/* Notifications */}
        <div className="fixed top-4 right-4 z-50 space-y-2">
          {notifications.map((notification) => (
            <Alert
              key={notification.id}
              className={`w-80 shadow-lg border backdrop-blur-md ${
                notification.type === "success"
                  ? "bg-emerald-50/90 text-emerald-800 border-emerald-200"
                  : "bg-red-50/90 text-red-800 border-red-200"
              }`}
            >
              {notification.type === "success" ? (
                <CheckCircle className="h-4 w-4" />
              ) : (
                <AlertCircle className="h-4 w-4" />
              )}
              <AlertDescription>{notification.message}</AlertDescription>
            </Alert>
          ))}
        </div>

        <div className="bg-white/80 backdrop-blur-md border-b border-gray-200/50 shadow-lg">
          <div className="max-w-7xl mx-auto px-6 py-8">
            <div className="text-center space-y-4">
              <div className="flex items-center justify-center gap-4">
                <div className="relative">
                  <Image
                    src="/images/aikya-logo.png"
                    alt="AIKYA Logo"
                    width={80}
                    height={80}
                    className="drop-shadow-lg"
                  />
                </div>
                <h1 className="text-5xl font-bold bg-gradient-to-r from-emerald-600 to-sky-600 bg-clip-text text-transparent font-serif">
                  AIKYA
                </h1>
              </div>
              <p className="text-xl text-gray-700 max-w-2xl mx-auto font-medium">
                {"AI for Impact Kindness Youth & Action\n Social Crowd Platform Trust Score Generation Module"}
              </p>
              <p className="text-sm text-gray-600 bg-white/50 backdrop-blur-sm px-4 py-2 rounded-full inline-block">
                Empowering Your Crowdfunding Experience with Transparency
              </p>
            </div>
          </div>
        </div>

        <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="bg-white/70 backdrop-blur-md border-gray-200/50 hover:shadow-xl transition-all duration-300 hover:bg-white/80">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Total Records</p>
                    <p className="text-3xl font-bold text-gray-900">{records.length}</p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-sky-100 to-cyan-100 rounded-lg shadow-sm">
                    <Users className="h-6 w-6 text-sky-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 backdrop-blur-md border-gray-200/50 hover:shadow-xl transition-all duration-300 hover:bg-white/80">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Average Trust Score</p>
                    <p className={`text-3xl font-bold ${getTrustScoreColor(averageTrustScore)}`}>
                      {averageTrustScore.toFixed(1)}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-emerald-100 to-green-100 rounded-lg shadow-sm">
                    <BarChart3 className="h-6 w-6 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 backdrop-blur-md border-gray-200/50 hover:shadow-xl transition-all duration-300 hover:bg-white/80">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Verified Users</p>
                    <p className="text-3xl font-bold text-emerald-600">
                      {records.filter((r) => r.face_match && r.document_verified).length}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-emerald-100 to-green-100 rounded-lg shadow-sm">
                    <CheckCircle className="h-6 w-6 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 backdrop-blur-md border-gray-200/50 hover:shadow-xl transition-all duration-300 hover:bg-white/80">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Pending Review</p>
                    <p className="text-3xl font-bold text-amber-600">
                      {records.filter((r) => !r.face_match || !r.document_verified).length}
                    </p>
                  </div>
                  <div className="p-3 bg-gradient-to-br from-amber-100 to-yellow-100 rounded-lg shadow-sm">
                    <Clock className="h-6 w-6 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="submit" className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 bg-white/60 backdrop-blur-md p-1 rounded-lg border border-gray-200/50">
              <TabsTrigger
                value="submit"
                className="data-[state=active]:bg-white/90 data-[state=active]:text-emerald-600 data-[state=active]:shadow-sm font-medium backdrop-blur-sm"
              >
                Submit New Request
              </TabsTrigger>
              <TabsTrigger
                value="records"
                className="data-[state=active]:bg-white/90 data-[state=active]:text-emerald-600 data-[state=active]:shadow-sm font-medium backdrop-blur-sm"
              >
                View Records
              </TabsTrigger>
            </TabsList>

            <TabsContent value="submit">
              <div className="space-y-6">
                <Card className="bg-white/80 backdrop-blur-md border-gray-200/50 shadow-xl">
                  <CardHeader className="bg-gradient-to-r from-emerald-50/80 to-sky-50/80 backdrop-blur-sm border-b border-gray-200/50">
                    <CardTitle className="flex items-center gap-3 text-gray-900">
                      <div className="p-2 bg-gradient-to-br from-emerald-500 to-sky-500 rounded-lg shadow-sm">
                        <Upload className="h-5 w-5 text-white" />
                      </div>
                      Trust Score Generation
                    </CardTitle>
                    <CardDescription className="text-gray-600">
                      Upload documents and provide information to generate a comprehensive trust score
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-6">
                    {/* ... existing form content ... */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="name" className="text-sm font-medium text-gray-700">
                            Full Name *
                          </Label>
                          <Input
                            id="name"
                            value={formData.name}
                            onChange={(e) => handleInputChange("name", e.target.value)}
                            placeholder="Enter full name"
                            className="border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 bg-white/50 backdrop-blur-sm"
                            required
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="user_id" className="text-sm font-medium text-gray-700">
                            User ID *
                          </Label>
                          <Input
                            id="user_id"
                            value={formData.user_id}
                            onChange={(e) => handleInputChange("user_id", e.target.value)}
                            placeholder="Enter user ID"
                            className="border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 bg-white/50 backdrop-blur-sm"
                            required
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                          <Label htmlFor="aadhaar_number" className="text-sm font-medium text-gray-700">
                            Aadhaar Number *
                          </Label>
                          <Input
                            id="aadhaar_number"
                            value={formData.aadhaar_number}
                            onChange={(e) => handleInputChange("aadhaar_number", e.target.value)}
                            placeholder="Enter Aadhaar number"
                            className="border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 bg-white/50 backdrop-blur-sm"
                            required
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="pan_number" className="text-sm font-medium text-gray-700">
                            PAN Number *
                          </Label>
                          <Input
                            id="pan_number"
                            value={formData.pan_number}
                            onChange={(e) => handleInputChange("pan_number", e.target.value)}
                            placeholder="Enter PAN number"
                            className="border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 bg-white/50 backdrop-blur-sm"
                            required
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="story" className="text-sm font-medium text-gray-700">
                          Personal Story *
                        </Label>
                        <Textarea
                          id="story"
                          value={formData.story}
                          onChange={(e) => handleInputChange("story", e.target.value)}
                          placeholder="Share your story or reason for requesting support..."
                          className="min-h-[120px] border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 bg-white/50 backdrop-blur-sm"
                          required
                        />
                      </div>

                      <div className="space-y-2">
                        <Label htmlFor="supporting_doc_type" className="text-sm font-medium text-gray-700">
                          Supporting Document Type *
                        </Label>
                        <Select
                          value={formData.supporting_doc_type}
                          onValueChange={(value) => handleInputChange("supporting_doc_type", value)}
                          required
                        >
                          <SelectTrigger className="border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 bg-white/50 backdrop-blur-sm">
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

                      <Separator className="bg-gray-200" />

                      <div className="space-y-4">
                        <h3 className="text-lg font-medium text-gray-900">Document Upload</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {[
                            { key: "id_image", label: "ID Photo", icon: User },
                            { key: "selfie_image", label: "Selfie Photo", icon: User },
                            { key: "aadhaar_doc", label: "Aadhaar Document", icon: FileCheck },
                            { key: "pan_doc", label: "PAN Document", icon: FileCheck },
                            { key: "supporting_doc", label: "Supporting Document", icon: FileText },
                          ].map(({ key, label, icon: Icon }) => (
                            <div key={key} className="space-y-2">
                              <Label
                                htmlFor={key}
                                className="text-sm font-medium text-gray-700 flex items-center gap-2"
                              >
                                <Icon className="h-4 w-4" />
                                {label} *
                              </Label>
                              <Input
                                id={key}
                                type="file"
                                accept={key === "supporting_doc" ? ".pdf,.jpg,.jpeg,.png" : "image/*"}
                                onChange={(e) => handleFileChange(key, e.target.files?.[0] || null)}
                                className="border-gray-300 focus:border-emerald-500 focus:ring-emerald-500 file:bg-gray-50 file:text-gray-700 file:border-0 file:rounded-md file:px-3 file:py-2 bg-white/50 backdrop-blur-sm"
                                required
                              />
                            </div>
                          ))}
                        </div>
                      </div>

                      <Button
                        type="submit"
                        className="w-full bg-gradient-to-r from-emerald-600 to-sky-600 hover:from-emerald-700 hover:to-sky-700 text-white font-medium py-3 transition-all duration-200 shadow-lg"
                        disabled={submitting}
                      >
                        {submitting ? (
                          <div className="flex items-center gap-2">
                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                            Processing Request...
                          </div>
                        ) : (
                          "Generate Trust Score"
                        )}
                      </Button>
                    </form>
                  </CardContent>
                </Card>

                {showJsonResponse && lastJsonResponse && (
                  <Card className="bg-white/80 backdrop-blur-md border-emerald-200/50 shadow-xl">
                    <CardHeader className="bg-gradient-to-r from-emerald-50/80 to-green-50/80 backdrop-blur-sm border-b border-emerald-200/50">
                      <CardTitle className="flex items-center justify-between text-emerald-900">
                        <div className="flex items-center gap-3">
                          <div className="p-2 bg-gradient-to-br from-emerald-500 to-green-500 rounded-lg shadow-sm">
                            <Code className="h-5 w-5 text-white" />
                          </div>
                          JSON Response
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => copyToClipboard(JSON.stringify(lastJsonResponse, null, 2))}
                            className="border-emerald-300 text-emerald-700 hover:bg-emerald-100/80 backdrop-blur-sm"
                          >
                            <Copy className="h-4 w-4 mr-2" />
                            Copy JSON
                          </Button>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowJsonResponse(false)}
                            className="border-emerald-300 text-emerald-700 hover:bg-emerald-100/80 backdrop-blur-sm"
                          >
                            <EyeOff className="h-4 w-4 mr-2" />
                            Hide
                          </Button>
                        </div>
                      </CardTitle>
                      <CardDescription className="text-emerald-700">
                        Complete JSON response from the trust score generation
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="p-6">
                      <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm font-mono">
                        {JSON.stringify(lastJsonResponse, null, 2)}
                      </pre>
                    </CardContent>
                  </Card>
                )}
              </div>
            </TabsContent>

            <TabsContent value="records">
              <Card className="bg-white/80 backdrop-blur-md border-gray-200/50 shadow-xl">
                <CardHeader className="bg-gradient-to-r from-purple-50/80 to-sky-50/80 backdrop-blur-sm border-b border-gray-200/50">
                  <CardTitle className="flex items-center gap-3 text-gray-900">
                    <div className="p-2 bg-gradient-to-br from-purple-500 to-sky-500 rounded-lg shadow-sm">
                      <BarChart3 className="h-5 w-5 text-white" />
                    </div>
                    Trust Score Records
                  </CardTitle>
                  <CardDescription className="text-gray-600">
                    View all generated trust scores and verification results
                  </CardDescription>
                </CardHeader>
                <CardContent className="p-6">
                  {loading ? (
                    <div className="text-center py-12">
                      <div className="w-8 h-8 border-4 border-gray-200 border-t-emerald-600 rounded-full animate-spin mx-auto"></div>
                      <p className="mt-4 text-gray-600">Loading records...</p>
                    </div>
                  ) : records.length === 0 ? (
                    <Alert className="bg-sky-50/80 border-sky-200/50 backdrop-blur-sm">
                      <AlertCircle className="h-4 w-4 text-sky-600" />
                      <AlertDescription className="text-sky-800">
                        No records found. Submit your first trust score request to get started.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <div className="space-y-4">
                      {records.map((record) => (
                        <Card
                          key={record.id}
                          className="bg-white/70 backdrop-blur-sm border-l-4 border-l-emerald-500 hover:shadow-lg transition-all duration-200 hover:bg-white/80"
                        >
                          <CardContent className="p-6">
                            <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-6">
                              <div className="flex-1 space-y-4">
                                <div className="flex items-center gap-3">
                                  <h3 className="font-semibold text-xl text-gray-900">{record.name}</h3>
                                  <Badge
                                    className={`${getTrustScoreBadge(record.trust_score)} font-medium border backdrop-blur-sm`}
                                  >
                                    Trust Score: {record.trust_score}
                                  </Badge>
                                </div>
                                <p className="text-sm text-gray-600">User ID: {record.user_id}</p>
                                <p className="text-gray-700 leading-relaxed">{record.story}</p>

                                <div className="flex items-center gap-2 pt-2">
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={() => toggleRecordJson(record.id)}
                                    className="border-gray-300 text-gray-700 hover:bg-gray-100/80 backdrop-blur-sm"
                                  >
                                    {expandedRecords.has(record.id) ? (
                                      <>
                                        <EyeOff className="h-4 w-4 mr-2" />
                                        Hide JSON
                                      </>
                                    ) : (
                                      <>
                                        <Eye className="h-4 w-4 mr-2" />
                                        View JSON
                                      </>
                                    )}
                                  </Button>
                                  {expandedRecords.has(record.id) && (
                                    <Button
                                      variant="outline"
                                      size="sm"
                                      onClick={() => copyToClipboard(JSON.stringify(record, null, 2))}
                                      className="border-gray-300 text-gray-700 hover:bg-gray-100/80 backdrop-blur-sm"
                                    >
                                      <Copy className="h-4 w-4 mr-2" />
                                      Copy JSON
                                    </Button>
                                  )}
                                </div>

                                {expandedRecords.has(record.id) && (
                                  <div className="mt-4">
                                    <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
                                      <pre className="text-sm font-mono">{JSON.stringify(record, null, 2)}</pre>
                                    </div>
                                  </div>
                                )}
                              </div>

                              <div className="bg-gray-50/80 backdrop-blur-sm p-4 rounded-lg min-w-[280px] space-y-4">
                                <h4 className="font-medium text-gray-900">Verification Status</h4>
                                <div className="space-y-3">
                                  <div className="flex items-center gap-3">
                                    {record.face_match ? (
                                      <CheckCircle className="h-5 w-5 text-emerald-600" />
                                    ) : (
                                      <XCircle className="h-5 w-5 text-red-600" />
                                    )}
                                    <span className="text-sm text-gray-700">Face Verification</span>
                                  </div>
                                  <div className="flex items-center gap-3">
                                    {record.document_verified ? (
                                      <CheckCircle className="h-5 w-5 text-emerald-600" />
                                    ) : (
                                      <XCircle className="h-5 w-5 text-red-600" />
                                    )}
                                    <span className="text-sm text-gray-700">Document Verification</span>
                                  </div>
                                  <div className="space-y-2">
                                    <div className="flex justify-between text-sm">
                                      <span className="text-gray-600">Emotion Score</span>
                                      <span className="font-medium">{record.emotion_score.toFixed(1)}/10</span>
                                    </div>
                                    <Progress value={record.emotion_score * 10} className="h-2" />
                                  </div>
                                  <p className="text-xs text-gray-500 text-center pt-2">
                                    {new Date(record.created_at).toLocaleDateString("en-US", {
                                      year: "numeric",
                                      month: "long",
                                      day: "numeric",
                                    })}
                                  </p>
                                </div>
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
    </div>
  )
}
