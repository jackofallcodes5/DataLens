import api from './api';

export const datasetService = {
  getDatasets: (projectId) => api.get('/datasets', { params: { project_id: projectId } }),
  getDataset: (id) => api.get(`/datasets/${id}`),
  deleteDataset: (id) => api.delete(`/datasets/${id}`),
  getVersions: (id) => api.get(`/datasets/${id}/versions`),
  getPreview: (id, versionId, page = 1, pageSize = 50) =>
    api.get(`/datasets/${id}/preview`, {
      params: { version_id: versionId, page, page_size: pageSize },
    }),
  uploadDataset: (formData) =>
    api.post('/datasets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  getProfile: (id, versionId) =>
    api.get(`/datasets/${id}/profile`, { params: { version_id: versionId } }),
  getIssues: (id, versionId) =>
    api.get(`/datasets/${id}/issues`, { params: { version_id: versionId } }),
  previewCleaning: (id, opType, params, versionId) =>
    api.post(
      `/datasets/${id}/clean/preview`,
      { operation_type: opType, parameters: params },
      { params: { version_id: versionId } }
    ),
  applyCleaning: (id, opType, params) =>
    api.post(`/datasets/${id}/clean/apply`, {
      operation_type: opType,
      parameters: params,
    }),
  getHistory: (id) => api.get(`/datasets/${id}/history`),
  undoCleaning: (id) => api.post(`/datasets/${id}/undo`),
  getChartData: (id, config, versionId) =>
    api.post(`/datasets/${id}/charts/data`, config, { params: { version_id: versionId } }),
  getRecommendations: (id, versionId) =>
    api.get(`/datasets/${id}/charts/recommendations`, { params: { version_id: versionId } }),
  getCharts: (datasetId, projectId) =>
    api.get('/charts', { params: { dataset_id: datasetId, project_id: projectId } }),
  saveChart: (chartData) => api.post('/charts', chartData),
  deleteChart: (chartId) => api.delete(`/charts/${chartId}`),
  getExportUrl: (id, format, versionId) =>
    `/api/datasets/${id}/export?format=${format}${versionId ? `&version_id=${versionId}` : ''}`,
};
