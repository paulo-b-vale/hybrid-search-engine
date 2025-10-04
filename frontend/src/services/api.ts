// Add these methods to your existing API service
class SearchAPI {
  private baseURL = 'http://localhost:8000';
  private authToken: string | null = null;

  setAuthToken(token: string | null) {
    this.authToken = token;
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`;
    }

    // Debug logging
    console.log('API Request:', {
      url,
      method: options.method || 'GET',
      headers,
      body: options.body
    });

    const response = await fetch(url, {
      ...options,
      headers,
    });

    console.log('API Response:', {
      status: response.status,
      statusText: response.statusText,
      headers: Object.fromEntries(response.headers.entries())
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error('API Error:', {
        status: response.status,
        errorData
      });
      throw {
        status: response.status,
        response: { data: errorData },
      };
    }

    return response.json();
  }

  async login(username: string, password: string) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    });
  }

  async register(username: string, email: string, password: string) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async logout() {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser() {
    return this.request('/auth/me');
  }

  async health() {
    return this.request('/health');
  }

  async search(query: string, index_name: string, search_method?: string, num_results?: number) {
    const requestBody = {
      query,
      index_name,
      search_method,
      num_results,
    };

    // Debug logging for search request
    console.log('Search Request Body:', requestBody);

    return this.request('/search', {
      method: 'POST',
      body: JSON.stringify(requestBody),
    });
  }
}

export default new SearchAPI();