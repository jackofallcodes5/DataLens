import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import DashboardPage from './pages/DashboardPage';
import UploadPage from './pages/UploadPage';
import DatasetPage from './pages/DatasetPage';
import CleaningPage from './pages/CleaningPage';
import VisualizationPage from './pages/VisualizationPage';
import ExportPage from './pages/ExportPage';

export default function App() {
  const [currentDataset, setCurrentDataset] = useState(null);

  return (
    <Router>
      <Layout currentDataset={currentDataset}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/upload" element={<UploadPage />} />
          <Route
            path="/datasets/:datasetId"
            element={<DatasetPage onDatasetLoaded={setCurrentDataset} />}
          />
          <Route
            path="/datasets/:datasetId/clean"
            element={<CleaningPage onDatasetMutated={() => {}} />}
          />
          <Route
            path="/datasets/:datasetId/visualize"
            element={<VisualizationPage />}
          />
          <Route
            path="/datasets/:datasetId/export"
            element={<ExportPage />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </Router>
  );
}
