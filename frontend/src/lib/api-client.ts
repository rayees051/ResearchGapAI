const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export function getAuthToken(): string | null {
  if (typeof window !== "undefined") {
    return localStorage.getItem("token");
  }
  return null;
}

export function setAuthToken(token: string) {
  if (typeof window !== "undefined") {
    localStorage.setItem("token", token);
  }
}

export function removeAuthToken() {
  if (typeof window !== "undefined") {
    localStorage.removeItem("token");
  }
}

async function fetcher(endpoint: string, options: RequestInit = {}) {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      removeAuthToken();
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    const errText = await response.text();
    let errMsg = "Request failed";
    try {
      errMsg = JSON.parse(errText).detail || errMsg;
    } catch {
      errMsg = errText || errMsg;
    }
    throw new Error(errMsg);
  }

  return response.json();
}

export const api = {
  // Auth API
  async login(email: string, password: string) {
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const res = await fetch(`${API_BASE_URL}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData,
    });

    if (!res.ok) {
      const errText = await res.text();
      let errMsg = "Login failed";
      try {
        errMsg = JSON.parse(errText).detail || errMsg;
      } catch {
        errMsg = errText || errMsg;
      }
      throw new Error(errMsg);
    }

    const data = await res.json();
    setAuthToken(data.access_token);
    return data;
  },

  async register(email: string, password: string) {
    return fetcher("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  },

  async getMe() {
    return fetcher("/auth/me");
  },

  // Projects API
  async getProjects() {
    return fetcher("/projects/");
  },

  async createProject(title: string, description: string) {
    return fetcher("/projects/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description }),
    });
  },

  async getProject(id: string) {
    return fetcher(`/projects/${id}`);
  },

  async deleteProject(id: string) {
    return fetcher(`/projects/${id}`, {
      method: "DELETE",
    });
  },

  async runProject(id: string) {
    return fetcher(`/projects/${id}/run`, {
      method: "POST",
    });
  },

  // Papers API
  async getPapers(projectId: string) {
    return fetcher(`/papers/?project_id=${projectId}`);
  },

  async uploadPaper(projectId: string, file: File) {
    const formData = new FormData();
    formData.append("file", file);

    const token = getAuthToken();
    const headers = new Headers();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_BASE_URL}/papers/upload?project_id=${projectId}`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(errText || "File upload failed");
    }

    return response.json();
  },

  async searchAndImportPapers(projectId: string, query: string, limit = 5) {
    return fetcher(`/papers/search?project_id=${projectId}&query=${encodeURIComponent(query)}&limit=${limit}`, {
      method: "POST",
    });
  },

  // Gaps & Synthesis API
  async getGaps(projectId: string) {
    return fetcher(`/gaps/?project_id=${projectId}`);
  },

  async getSynthesis(projectId: string) {
    return fetcher(`/gaps/synthesis?project_id=${projectId}`);
  },

  async updateSynthesis(projectId: string, content: string) {
    return fetcher(`/gaps/synthesis?project_id=${projectId}&content=${encodeURIComponent(content)}`, {
      method: "PUT",
    });
  },

  // WebSocket URL Helper
  getWebSocketLogsUrl(projectId: string): string {
    const wsProto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const parsedBase = API_BASE_URL.replace(/^https?:\/\//, "");
    return `${wsProto}//${parsedBase}/projects/${projectId}/logs/stream`;
  }
};
