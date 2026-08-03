const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type EligibilityFlag = {
  severity: "blocking" | "warning" | "info";
  category: string;
  message: string;
  related_document_type: string | null;
};

export type EligibilitySummary = {
  visa_category: string;
  documents_reviewed: number;
  overall_readiness: "ready_to_file" | "needs_attention" | "not_ready";
  flags: EligibilityFlag[];
  timeline_narrative: string;
  missing_document_types: string[];
  attorney_notes: string;
  disclaimer: string;
};

export type Case = {
  id: string;
  client_id: string;
  visa_category: string;
  status: string;
  eligibility_summary: EligibilitySummary | null;
};

export type DocumentDetail = {
  id: string;
  case_id: string;
  document_type: string | null;
  original_filename: string;
  status: string;
  extracted_fields: Record<string, unknown> | null;
  error_message: string | null;
};

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(detail.detail || "Request failed");
  }
  return res.json();
}

export const api = {
  signup: (data: { firm_name: string; full_name: string; email: string; password: string }) =>
    request<{ access_token: string }>("/api/auth/signup", { method: "POST", body: JSON.stringify(data) }),

  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.set("username", email);
    form.set("password", password);
    return request<{ access_token: string }>("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: form.toString(),
    });
  },

  listCases: () => request<Case[]>("/api/cases"),
  getCase: (id: string) => request<Case>(`/api/cases/${id}`),
  createCase: (data: { client_name: string; client_email?: string; visa_category: string }) =>
    request<Case>("/api/cases", { method: "POST", body: JSON.stringify(data) }),

  listDocuments: (caseId: string) => request<DocumentDetail[]>(`/api/cases/${caseId}/documents`),
  uploadDocument: (caseId: string, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    return request<{ id: string; original_filename: string; status: string }>(
      `/api/cases/${caseId}/documents`,
      { method: "POST", body: formData }
    );
  },

  createCheckoutSession: () =>
    request<{ checkout_url: string }>("/api/billing/create-checkout-session", { method: "POST" }),
};
