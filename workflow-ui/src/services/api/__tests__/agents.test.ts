import { describe, it, expect, vi, beforeEach } from 'vitest';
import * as agentsApi from '../agents';
import apiClient from '../client';

// Mock the API client
vi.mock('../client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

describe('Agents API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('listAgents', () => {
    it('should call GET /agents', async () => {
      const mockResponse = {
        data: {
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
        },
      };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await agentsApi.listAgents();

      expect(apiClient.get).toHaveBeenCalledWith('/agents', { params: undefined });
      expect(result).toEqual(mockResponse.data);
    });

    it('should pass pagination params', async () => {
      const mockResponse = { data: { items: [], total: 0, page: 1, page_size: 20 } };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      await agentsApi.listAgents({ page: 2, page_size: 20 });

      expect(apiClient.get).toHaveBeenCalledWith('/agents', {
        params: { page: 2, page_size: 20 },
      });
    });
  });

  describe('getAgent', () => {
    it('should call GET /agents/:id', async () => {
      const mockAgent = { id: '123', name: 'Test Agent', url: 'http://test.com' };
      const mockResponse = { data: mockAgent };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await agentsApi.getAgent('123');

      expect(apiClient.get).toHaveBeenCalledWith('/agents/123');
      expect(result).toEqual(mockAgent);
    });
  });

  describe('createAgent', () => {
    it('should call POST /agents', async () => {
      const newAgent = { name: 'New Agent', url: 'http://new.com' };
      const mockResponse = { data: { id: '456', ...newAgent } };
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse);

      const result = await agentsApi.createAgent(newAgent);

      expect(apiClient.post).toHaveBeenCalledWith('/agents', newAgent);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('updateAgent', () => {
    it('should call PUT /agents/:id', async () => {
      const updates = { description: 'Updated description', status: 'inactive' as const };
      const mockResponse = { data: { id: '123', name: 'Test Agent', ...updates } };
      vi.mocked(apiClient.put).mockResolvedValue(mockResponse);

      const result = await agentsApi.updateAgent('123', updates);

      expect(apiClient.put).toHaveBeenCalledWith('/agents/123', updates);
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe('deleteAgent', () => {
    it('should call DELETE /agents/:id', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined });

      await agentsApi.deleteAgent('123');

      expect(apiClient.delete).toHaveBeenCalledWith('/agents/123');
    });
  });

  describe('checkAgentHealth', () => {
    it('should call GET /agents/:id/health', async () => {
      const mockHealth = { status: 'healthy', response_time_ms: 50 };
      const mockResponse = { data: mockHealth };
      vi.mocked(apiClient.get).mockResolvedValue(mockResponse);

      const result = await agentsApi.checkAgentHealth('123');

      expect(apiClient.get).toHaveBeenCalledWith('/agents/123/health');
      expect(result).toEqual(mockHealth);
    });
  });
});
